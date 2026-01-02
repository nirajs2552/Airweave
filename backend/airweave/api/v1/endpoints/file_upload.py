"""Selective file upload API endpoints.

This module provides endpoints for uploading selected files from source connections
directly to S3, bypassing the full sync pipeline.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from airweave import crud, schemas
from airweave.api import deps
from airweave.api.context import ApiContext
from airweave.api.router import TrailingSlashRouter
from airweave.core.exceptions import NotFoundException
from airweave.platform.destinations.s3 import S3Destination
from airweave.platform.destinations.s3 import S3AuthConfig as S3AuthConfigType
from airweave.platform.entities._base import Breadcrumb
from airweave.platform.locator import resource_locator
from airweave.platform.sync.factory import SyncFactory

router = TrailingSlashRouter()


class FileUploadRequest(BaseModel):
    """Request to upload selected files."""

    file_ids: List[str] = Body(..., description="List of SharePoint file item IDs to upload")
    collection_id: UUID = Body(..., description="Collection ID to associate files with")
    drive_id: str = Body(..., description="SharePoint drive ID containing the files")
    site_id: Optional[str] = Body(None, description="SharePoint site ID (optional)")


class FileUploadResult(BaseModel):
    """Result of uploading a single file."""

    file_id: str
    file_name: str
    status: str  # "success", "failed", "skipped"
    error: Optional[str] = None
    s3_path: Optional[str] = None


class FileUploadResponse(BaseModel):
    """Response from file upload operation."""

    total_files: int
    successful: int
    failed: int
    skipped: int
    results: List[FileUploadResult]


@router.post("/{source_connection_id}/upload-selected", response_model=FileUploadResponse)
async def upload_selected_files(
    *,
    db: AsyncSession = Depends(deps.get_db),
    source_connection_id: UUID,
    request: FileUploadRequest,
    ctx: ApiContext = Depends(deps.get_context),
) -> FileUploadResponse:
    """Upload selected files from SharePoint to S3.

    This endpoint:
    1. Fetches selected files from SharePoint
    2. Downloads the files
    3. Uploads them directly to S3
    4. Returns upload status for each file

    Args:
        source_connection_id: The SharePoint source connection ID
        request: File upload request with file IDs and collection ID

    Returns:
        FileUploadResponse with upload results
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
            detail=f"Selective upload is currently only supported for SharePoint and OneDrive. "
            f"Got: {source_connection.short_name}",
        )

    # Get collection
    try:
        collection = await crud.collection.get(db, id=request.collection_id, ctx=ctx)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Get S3 destination connection
    from sqlalchemy import and_, select
    from airweave.models.connection import Connection

    stmt = select(Connection).where(
        and_(
            Connection.organization_id == ctx.organization.id,
            Connection.short_name == "s3",
            Connection.integration_type == "DESTINATION",
        )
    )
    result = await db.execute(stmt)
    s3_connection = result.scalar_one_or_none()

    if not s3_connection:
        raise HTTPException(
            status_code=400,
            detail="S3 destination not configured. Please configure S3 destination first.",
        )

    # Get S3 credentials
    if not s3_connection.integration_credential_id:
        raise HTTPException(
            status_code=400, detail="S3 connection has no credentials configured"
        )

    credential = await crud.integration_credential.get(
        db, s3_connection.integration_credential_id, ctx
    )
    if not credential:
        raise HTTPException(status_code=400, detail="S3 credentials not found")

    # Decrypt S3 credentials
    from airweave.core.credentials import decrypt

    s3_config_dict = decrypt(credential.encrypted_credentials)
    s3_auth_config = S3AuthConfigType(**s3_config_dict)

    # Create S3 destination
    s3_destination = await S3Destination.create(
        credentials=s3_auth_config,
        config=None,
        collection_id=collection.id,
        organization_id=ctx.organization.id,
        logger=ctx.logger,
        collection_readable_id=collection.readable_id,
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

    # Create source instance without file downloader (similar to file_browser)
    # We use the same approach as file_browser but skip file downloader setup
    from airweave.platform.utils.source_factory_utils import (
        get_auth_configuration,
        process_credentials_for_source,
        wrap_source_with_airweave_client,
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
        except Exception as e:
            ctx.logger.warning(f"Failed to setup token manager: {e}")
    
    # Wrap HTTP client with AirweaveHttpClient for rate limiting
    wrap_source_with_airweave_client(
        source=source,
        source_short_name=source_connection_data["short_name"],
        source_connection_id=source_connection_data["source_connection_id"],
        ctx=ctx,
        logger=ctx.logger,
    )
    
    # Setup file downloader manually (without sync_job)
    # We need the file downloader for downloading files, but we don't have a sync_job
    # Create a temporary sync_job_id for the file downloader
    from airweave.platform.downloader import FileDownloadService
    from uuid import uuid4
    # Use a temporary ID for file uploads (not a real sync_job)
    temp_sync_job_id = f"upload-{uuid4()}"
    file_downloader = FileDownloadService(sync_job_id=temp_sync_job_id)
    source.set_file_downloader(file_downloader)
    ctx.logger.debug(f"File downloader configured for upload (temp_sync_job_id: {temp_sync_job_id})")

    # Upload files
    results: List[FileUploadResult] = []
    successful = 0
    failed = 0
    skipped = 0

    try:
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as client:
            for file_id in request.file_ids:
                try:
                    # Get file metadata from SharePoint/OneDrive
                    # OneDrive doesn't have GRAPH_BASE_URL, use hardcoded URL
                    if source_connection.short_name == "sharepoint":
                        file_url = (
                            f"{source.GRAPH_BASE_URL}/drives/{request.drive_id}/items/{file_id}"
                        )
                    else:  # onedrive
                        file_url = (
                            f"https://graph.microsoft.com/v1.0/drives/{request.drive_id}/items/{file_id}"
                        )
                    file_data = await source._get_with_auth(client, file_url)

                    if "file" not in file_data:
                        results.append(
                            FileUploadResult(
                                file_id=file_id,
                                file_name=file_data.get("name", "Unknown"),
                                status="skipped",
                                error="Not a file (may be a folder)",
                            )
                        )
                        skipped += 1
                        continue

                    # Get download URL
                    download_url = await source._get_download_url(
                        client, request.drive_id, file_id
                    )

                    if not download_url:
                        results.append(
                            FileUploadResult(
                                file_id=file_id,
                                file_name=file_data.get("name", "Unknown"),
                                status="failed",
                                error="Could not get download URL",
                            )
                        )
                        failed += 1
                        continue

                    # Create minimal breadcrumbs for the entity
                    if source_connection.short_name == "sharepoint":
                        site_id = request.site_id or "root"
                        site_breadcrumb = Breadcrumb(
                            entity_id=site_id,
                            name="Root Site",
                            entity_type="SharePointSiteEntity",
                        )
                        drive_breadcrumb = Breadcrumb(
                            entity_id=request.drive_id,
                            name="Selected Files",
                            entity_type="SharePointDriveEntity",
                        )
                        # Create file entity for SharePoint
                        file_entity = source._build_file_entity(
                            file_data,
                            drive_name="Selected Files",
                            site_id=site_id,
                            drive_id=request.drive_id,
                            site_breadcrumb=site_breadcrumb,
                            drive_breadcrumb=drive_breadcrumb,
                            download_url=download_url,
                        )
                    else:  # onedrive
                        # OneDrive doesn't have sites, use drive as top level
                        drive_breadcrumb = Breadcrumb(
                            entity_id=request.drive_id,
                            name="OneDrive",
                            entity_type="OneDriveDriveEntity",
                        )
                        # Create file entity for OneDrive (doesn't accept site_id parameter)
                        file_entity = source._build_file_entity(
                            item=file_data,
                            drive_name="OneDrive",
                            drive_id=request.drive_id,
                            download_url=download_url,
                        )

                    if not file_entity:
                        results.append(
                            FileUploadResult(
                                file_id=file_id,
                                file_name=file_data.get("name", "Unknown"),
                                status="skipped",
                                error="Could not create file entity",
                            )
                        )
                        skipped += 1
                        continue

                    # Download file using source's file downloader
                    await source.file_downloader.download_from_url(
                        entity=file_entity,
                        http_client_factory=source.http_client,
                        access_token_provider=source.get_access_token,
                        logger=ctx.logger,
                    )

                    if not file_entity.local_path:
                        results.append(
                            FileUploadResult(
                                file_id=file_id,
                                file_name=file_entity.name,
                                status="failed",
                                error="File download failed",
                            )
                        )
                        failed += 1
                        continue

                    # Upload to S3
                    await s3_destination.bulk_insert([file_entity])

                    # Get S3 path
                    s3_path = (
                        f"s3://{s3_destination.bucket_name}/"
                        f"{s3_destination.bucket_prefix}collections/{collection.readable_id}/"
                        f"blobs/{file_entity.id}"
                    )

                    results.append(
                        FileUploadResult(
                            file_id=file_id,
                            file_name=file_entity.name,
                            status="success",
                            s3_path=s3_path,
                        )
                    )
                    successful += 1

                except Exception as e:
                    ctx.logger.error(f"Error uploading file {file_id}: {e}", exc_info=True)
                    results.append(
                        FileUploadResult(
                            file_id=file_id,
                            file_name="Unknown",
                            status="failed",
                            error=str(e),
                        )
                    )
                    failed += 1

    except Exception as e:
        ctx.logger.error(f"Error in upload process: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Upload process failed: {str(e)}"
        ) from e

    return FileUploadResponse(
        total_files=len(request.file_ids),
        successful=successful,
        failed=failed,
        skipped=skipped,
        results=results,
    )

