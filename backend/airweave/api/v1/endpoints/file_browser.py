"""File browser API endpoints for browsing and selecting files from source connections.

This module provides endpoints for:
- Browsing files/folders from SharePoint (and other sources)
- Selecting specific files
- Uploading selected files to S3
"""

from typing import List, Optional
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from airweave import crud, schemas
from airweave.api import deps
from airweave.api.context import ApiContext
from airweave.api.router import TrailingSlashRouter
from airweave.core.exceptions import NotFoundException
from airweave.platform.locator import resource_locator
from airweave.platform.sync.factory import SyncFactory

router = TrailingSlashRouter()


class FileItem(BaseModel):
    """Represents a file in the browser."""

    id: str
    name: str
    path: str
    size: Optional[int] = None
    modified_at: Optional[str] = None
    type: str  # "file" or "folder"
    mime_type: Optional[str] = None


class FolderItem(BaseModel):
    """Represents a folder in the browser."""

    id: str
    name: str
    path: str
    type: str = "folder"


class BrowseResponse(BaseModel):
    """Response from browsing a source connection."""

    files: List[FileItem]
    folders: List[FolderItem]
    current_path: Optional[str] = None
    parent_path: Optional[str] = None


@router.get("/{source_connection_id}/browse", response_model=BrowseResponse)
async def browse_files(
    *,
    db: AsyncSession = Depends(deps.get_db),
    source_connection_id: UUID,
    drive_id: Optional[str] = Query(None, description="SharePoint drive ID"),
    folder_id: Optional[str] = Query(None, description="Folder ID to browse"),
    site_id: Optional[str] = Query(None, description="SharePoint site ID"),
    ctx: ApiContext = Depends(deps.get_context),
) -> BrowseResponse:
    """Browse files and folders from a SharePoint source connection.

    This endpoint allows browsing SharePoint without triggering a full sync.
    Returns a list of files and folders that can be selected for upload.

    Args:
        source_connection_id: The source connection ID
        drive_id: Optional SharePoint drive ID (defaults to root site's default drive)
        folder_id: Optional folder ID to browse (defaults to drive root)
        site_id: Optional site ID (defaults to root site)

    Returns:
        BrowseResponse with files and folders
    """
    # Get source connection
    try:
        source_connection = await crud.source_connection.get(
            db, id=source_connection_id, ctx=ctx
        )
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Source connection not found")

    if source_connection.short_name not in ["sharepoint", "onedrive"]:
        raise HTTPException(
            status_code=400,
            detail=f"File browsing is currently only supported for SharePoint and OneDrive. "
            f"Got: {source_connection.short_name}",
        )

    # Build source connection data similar to SyncFactory
    connection = await crud.connection.get(db, source_connection.connection_id, ctx)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    source_model = await crud.source.get_by_short_name(db, source_connection.short_name)
    if not source_model:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_connection.short_name}")

    source_class = resource_locator.get_source(source_model)
    
    # Build source connection data dict
    source_connection_data = {
        "source_model": source_model,
        "source_class": source_class,
        "config_fields": source_connection.config_fields or {},
        "short_name": source_connection.short_name,
        "source_connection_id": source_connection.id,
        "auth_config_class": source_model.auth_config_class,
        "connection_id": connection.id,
        "integration_credential_id": connection.integration_credential_id,
        "readable_auth_provider_id": getattr(source_connection, "readable_auth_provider_id", None),
        "auth_provider_config": getattr(source_connection, "auth_provider_config", None),
    }

    # Create source instance for browsing (without file downloader setup)
    # We use the same approach as _create_source_instance_with_data but skip file downloader
    from airweave.platform.sync.factory import SyncFactory
    from airweave.platform.utils.source_factory_utils import (
        get_auth_configuration,
        process_credentials_for_source,
    )
    
    # Get auth configuration (credentials + proxy setup if needed)
    auth_config = await get_auth_configuration(
        db=db,
        source_connection_data=source_connection_data,
        ctx=ctx,
        logger=ctx.logger,
        access_token=None,  # Will fetch from credentials
    )
    
    # Process credentials for source consumption
    source_credentials = await process_credentials_for_source(
        raw_credentials=auth_config["credentials"],
        source_connection_data=source_connection_data,
        logger=ctx.logger,
    )
    
    # Create the source instance with processed credentials
    source = await source_connection_data["source_class"].create(
        source_credentials, config=source_connection_data.get("config_fields")
    )
    
    # Configure source with logger
    if hasattr(source, "set_logger"):
        source.set_logger(ctx.logger)
    
    # Set sync identifiers
    try:
        organization_id = ctx.organization.id
        source_connection_id = source_connection_data.get("source_connection_id")
        if hasattr(source, "set_sync_identifiers") and source_connection_id:
            source.set_sync_identifiers(
                organization_id=str(organization_id),
                source_connection_id=str(source_connection_id),
            )
    except Exception:
        pass  # Non-fatal
    
    # Setup token manager for OAuth sources (if applicable)
    from airweave.platform.auth_providers.auth_result import AuthProviderMode
    auth_mode = auth_config.get("auth_mode")
    auth_provider_instance = auth_config.get("auth_provider_instance")
    is_proxy_mode = auth_mode == AuthProviderMode.PROXY
    
    if not is_proxy_mode:
        try:
            await SyncFactory._setup_token_manager(
                db=db,
                source=source,
                source_connection_data=source_connection_data,
                source_credentials=auth_config["credentials"],
                ctx=ctx,
                logger=ctx.logger,
                auth_provider_instance=auth_provider_instance,
            )
            # Verify token manager was set
            if not hasattr(source, 'token_manager') or source.token_manager is None:
                ctx.logger.warning("Token manager was not set on source instance")
        except Exception as e:
            ctx.logger.error(f"Failed to setup token manager: {e}", exc_info=True)
            # Don't fail completely, but log the error
    
    # Wrap HTTP client with AirweaveHttpClient for rate limiting
    from airweave.platform.utils.source_factory_utils import wrap_source_with_airweave_client
    wrap_source_with_airweave_client(
        source=source,
        source_short_name=source_connection_data["short_name"],
        source_connection_id=source_connection_data["source_connection_id"],
        ctx=ctx,
        logger=ctx.logger,
    )
    
    # NOTE: We intentionally skip _setup_file_downloader since we don't need it for browsing

    # Browse SharePoint/OneDrive files
    files: List[FileItem] = []
    folders: List[FolderItem] = []

    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            ctx.logger.info(
                f"Browsing {source_connection.short_name} files for connection {source_connection_id}"
            )

            if source_connection.short_name == "sharepoint":
                # SharePoint-specific logic with hierarchical browsing
                # Level 1: If no site_id, show all sites
                if not site_id:
                    sites_list = []
                    
                    # Get root site first (always available)
                    try:
                        root_site_url = f"{source.GRAPH_BASE_URL}/sites/root"
                        root_site_data = await source._get_with_auth(client, root_site_url)
                        root_site_id = root_site_data.get("id")
                        sites_list.append({
                            "id": root_site_id,
                            "displayName": root_site_data.get("displayName", "Root Site"),
                            "webUrl": root_site_data.get("webUrl"),
                            "description": root_site_data.get("description"),
                            "name": root_site_data.get("name", "Root Site"),
                        })
                    except Exception as e:
                        ctx.logger.warning(f"Could not fetch root site: {e}")
                    
                    # Try to get all sites (requires Sites.Read.All permission)
                    # Use /sites endpoint with search to get all sites user has access to
                    all_sites = []
                    try:
                        # First try /sites?search=* to get all sites (includes Team sites)
                        sites_url = f"{source.GRAPH_BASE_URL}/sites?search=*&$top=100&$select=id,displayName,webUrl,description,name,siteCollection"
                        try:
                            sites_data = await source._get_with_auth(client, sites_url)
                            all_sites = sites_data.get("value", [])
                            ctx.logger.info(f"Found {len(all_sites)} sites via search")
                        except Exception as e:
                            # If search fails, try without search (may need Sites.Read.All permission)
                            ctx.logger.warning(f"Sites search failed: {e}, trying without search parameter")
                            sites_url = f"{source.GRAPH_BASE_URL}/sites?$top=100&$select=id,displayName,webUrl,description,name,siteCollection"
                            sites_data = await source._get_with_auth(client, sites_url)
                            all_sites = sites_data.get("value", [])
                            ctx.logger.info(f"Found {len(all_sites)} sites without search")
                        
                        # Also try /me/followedSites to get sites user follows (includes Team sites)
                        try:
                            followed_sites_url = f"{source.GRAPH_BASE_URL}/me/followedSites?$top=100&$select=id,displayName,webUrl,description,name,siteCollection"
                            followed_data = await source._get_with_auth(client, followed_sites_url)
                            followed_sites = followed_data.get("value", [])
                            ctx.logger.info(f"Found {len(followed_sites)} followed sites")
                            # Merge followed sites into all_sites
                            for site in followed_sites:
                                site_id_val = site.get("id")
                                if site_id_val and not any(s.get("id") == site_id_val for s in all_sites):
                                    all_sites.append(site)
                        except Exception as e:
                            ctx.logger.debug(f"Could not fetch followed sites: {e}")
                        
                        # Also try to get Team sites via /groups endpoint
                        # Team sites are associated with Microsoft Teams groups
                        try:
                            groups_url = f"{source.GRAPH_BASE_URL}/groups?$filter=groupTypes/any(g:g eq 'Unified')&$top=100&$select=id,displayName"
                            groups_data = await source._get_with_auth(client, groups_url)
                            teams_groups = groups_data.get("value", [])
                            ctx.logger.info(f"Found {len(teams_groups)} Teams groups")
                            
                            # For each Teams group, try to get its associated site
                            for group in teams_groups[:20]:  # Limit to first 20 to avoid too many API calls
                                try:
                                    group_id = group.get("id")
                                    group_site_url = f"{source.GRAPH_BASE_URL}/groups/{group_id}/sites/root"
                                    group_site_data = await source._get_with_auth(client, group_site_url)
                                    site_id_val = group_site_data.get("id")
                                    if site_id_val and not any(s.get("id") == site_id_val for s in all_sites):
                                        # Add Team site with group name
                                        all_sites.append({
                                            "id": site_id_val,
                                            "displayName": group.get("displayName", "Team Site"),
                                            "webUrl": group_site_data.get("webUrl"),
                                            "description": f"Microsoft Teams: {group.get('displayName', '')}",
                                            "name": group_site_data.get("name", "Team Site"),
                                            "siteCollection": group_site_data.get("siteCollection"),
                                        })
                                except Exception as e:
                                    ctx.logger.debug(f"Could not fetch site for group {group.get('id')}: {e}")
                                    continue
                        except Exception as e:
                            ctx.logger.debug(f"Could not fetch Teams groups: {e}")
                        
                        # Add sites that aren't the root site
                        root_site_id = sites_list[0].get("id") if sites_list else None
                        for site in all_sites:
                            site_id_val = site.get("id")
                            if site_id_val and site_id_val != root_site_id:
                                # Check if already added
                                if not any(s.get("id") == site_id_val for s in sites_list):
                                    sites_list.append(site)
                        
                        # Handle pagination
                        next_url = sites_data.get("@odata.nextLink")
                        page_count = 1
                        while next_url and len(sites_list) < 200 and page_count < 10:  # Limit to 200 sites, 10 pages
                            next_data = await source._get_with_auth(client, next_url)
                            more_sites = next_data.get("value", [])
                            for site in more_sites:
                                site_id_val = site.get("id")
                                if site_id_val and site_id_val != root_site_id:
                                    if not any(s.get("id") == site_id_val for s in sites_list):
                                        sites_list.append(site)
                            next_url = next_data.get("@odata.nextLink")
                            page_count += 1
                            
                        ctx.logger.info(f"Fetched {len(sites_list)} sites (including root)")
                    except Exception as e:
                        ctx.logger.warning(
                            f"Could not fetch all sites (may need Sites.Read.All permission): {e}. "
                            f"Showing root site only."
                        )
                        # If we can't get all sites, at least show root site
                    
                    # Return sites as folders (so user can click to navigate)
                    for site in sites_list:
                        site_name = site.get("displayName") or site.get("name", "Unknown Site")
                        folders.append(
                            FolderItem(
                                id=site.get("id"),
                                name=site_name,
                                path=f"/sites/{site.get('id')}",
                            )
                        )
                    
                    ctx.logger.info(f"Returning {len(folders)} SharePoint sites for browsing")
                    return BrowseResponse(
                        files=files,
                        folders=folders,
                        current_path="/sites",
                    )
                
                # Level 2: If site_id but no drive_id, show all drives (document libraries) for the site
                if not drive_id:
                    drives_url = f"{source.GRAPH_BASE_URL}/sites/{site_id}/drives"
                    drives_data = await source._get_with_auth(client, drives_url)
                    drives_list = drives_data.get("value", [])
                    
                    if not drives_list:
                        raise HTTPException(
                            status_code=404, detail="No document libraries found in this SharePoint site"
                        )
                    
                    # Return drives as folders (so user can click to navigate)
                    for drive in drives_list:
                        folders.append(
                            FolderItem(
                                id=drive.get("id"),
                                name=drive.get("name", "Unknown Document Library"),
                                path=f"/sites/{site_id}/drives/{drive.get('id')}",
                            )
                        )
                    
                    # Get site name for breadcrumb
                    site_url = f"{source.GRAPH_BASE_URL}/sites/{site_id}"
                    site_data = await source._get_with_auth(client, site_url)
                    site_name = site_data.get("displayName", "Site")
                    
                    ctx.logger.info(f"Found {len(folders)} document libraries in site {site_name}")
                    return BrowseResponse(
                        files=files,
                        folders=folders,
                        current_path=f"/sites/{site_id}/drives",
                    )
                
                # Level 3: If both site_id and drive_id, show files and folders in the drive
                # folder_id can be None (root), or a specific folder ID for nested navigation
                try:
                    ctx.logger.info(
                        f"Listing items in drive {drive_id}, folder: {folder_id or 'root'}"
                    )
                    async for item in source._list_drive_items(client, drive_id, folder_id):
                        item_id = item.get("id")
                        item_name = item.get("name", "Unknown")
                        # Use full path for nested folders to maintain navigation context
                        item_path = f"/drives/{drive_id}/items/{item_id}"

                        if "folder" in item:
                            folders.append(
                                FolderItem(
                                    id=item_id,
                                    name=item_name,
                                    path=item_path,
                                )
                            )
                        elif "file" in item:
                            file_info = item.get("file", {})
                            files.append(
                                FileItem(
                                    id=item_id,
                                    name=item_name,
                                    path=item_path,
                                    size=item.get("size"),
                                    modified_at=item.get("lastModifiedDateTime"),
                                    type="file",
                                    mime_type=file_info.get("mimeType"),
                                )
                            )
                    
                    ctx.logger.info(
                        f"Found {len(files)} files and {len(folders)} folders in "
                        f"drive {drive_id}, folder: {folder_id or 'root'}"
                    )
                except Exception as e:
                    ctx.logger.error(f"Error listing drive items: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to list files in folder: {str(e)}"
                    )

            elif source_connection.short_name == "onedrive":
                # OneDrive-specific logic
                if not drive_id:
                    # Get default drive (user's OneDrive)
                    # OneDrive doesn't have GRAPH_BASE_URL, use hardcoded URL
                    try:
                        drive_url = "https://graph.microsoft.com/v1.0/me/drive"
                        drive_data = await source._get_with_auth(client, drive_url)
                        drive_id = drive_data.get("id")
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 401:
                            ctx.logger.error(
                                "Authentication failed for OneDrive. Token may be expired. "
                                "Please reconnect your OneDrive account."
                            )
                            raise HTTPException(
                                status_code=401,
                                detail="OneDrive authentication failed. Your access token has expired. "
                                "Please disconnect and reconnect your OneDrive account in the settings."
                            ) from e
                        raise
                    except Exception as e:
                        ctx.logger.error(f"Error accessing OneDrive: {e}", exc_info=True)
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to access OneDrive: {str(e)}"
                        ) from e

                if not drive_id:
                    raise HTTPException(
                        status_code=404, detail="No OneDrive found"
                    )

                # Use OneDrive's _list_drive_items method to list items
                async for item in source._list_drive_items(client, drive_id, folder_id):
                    item_id = item.get("id")
                    item_name = item.get("name", "Unknown")
                    item_path = f"/drives/{drive_id}/items/{item_id}"

                    if "folder" in item:
                        folders.append(
                            FolderItem(
                                id=item_id,
                                name=item_name,
                                path=item_path,
                            )
                        )
                    elif "file" in item:
                        file_info = item.get("file", {})
                        files.append(
                            FileItem(
                                id=item_id,
                                name=item_name,
                                path=item_path,
                                size=item.get("size"),
                                modified_at=item.get("lastModifiedDateTime"),
                                type="file",
                                mime_type=file_info.get("mimeType"),
                            )
                        )

            ctx.logger.info(
                f"Found {len(files)} files and {len(folders)} folders in {source_connection.short_name}"
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except httpx.HTTPStatusError as e:
        # Handle HTTP errors from Microsoft Graph API
        if e.response.status_code == 401:
            ctx.logger.error(
                f"Authentication failed for {source_connection.short_name}. "
                "Token may be expired. Please reconnect your account."
            )
            raise HTTPException(
                status_code=401,
                detail=f"{source_connection.short_name} authentication failed. "
                "Your access token has expired. Please disconnect and reconnect your account in the settings."
            ) from e
        ctx.logger.error(f"HTTP error browsing files: {e}", exc_info=True)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to browse files: {str(e)}"
        ) from e
    except Exception as e:
        ctx.logger.error(f"Error browsing files: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to browse files: {str(e)}"
        ) from e

    return BrowseResponse(
        files=files,
        folders=folders,
        current_path=f"/drives/{drive_id}" + (f"/items/{folder_id}" if folder_id else ""),
    )

