#!/usr/bin/env python3
"""Test script for file browser and selective upload functionality.

This script helps test:
1. S3 configuration status
2. File browsing from SharePoint
3. Selective file upload to S3
"""

import json
import sys
from typing import Optional
from uuid import UUID

import httpx


class AirweaveClient:
    """Client for testing Airweave API endpoints."""

    def __init__(self, base_url: str = "http://localhost:8001", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = httpx.request(method, url, headers=self.headers, timeout=30.0, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Request failed: {e}")
            raise

    def get_s3_status(self) -> dict:
        """Get S3 configuration status."""
        return self._request("GET", "/api/v1/s3/status")

    def test_s3_connection(self, config: dict) -> dict:
        """Test S3 connection with provided config."""
        return self._request("POST", "/api/v1/s3/test", json=config)

    def configure_s3(self, config: dict) -> dict:
        """Configure S3 destination."""
        return self._request("POST", "/api/v1/s3/configure", json=config)

    def list_source_connections(self) -> list:
        """List all source connections."""
        return self._request("GET", "/api/v1/source-connections")

    def browse_files(
        self,
        source_connection_id: str,
        drive_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        site_id: Optional[str] = None,
    ) -> dict:
        """Browse files from a source connection."""
        params = {}
        if drive_id:
            params["drive_id"] = drive_id
        if folder_id:
            params["folder_id"] = folder_id
        if site_id:
            params["site_id"] = site_id

        return self._request("GET", f"/api/v1/file-browser/{source_connection_id}/browse", params=params)

    def upload_selected_files(
        self,
        source_connection_id: str,
        file_ids: list,
        collection_id: str,
        drive_id: str,
        site_id: Optional[str] = None,
    ) -> dict:
        """Upload selected files to S3."""
        payload = {
            "file_ids": file_ids,
            "collection_id": collection_id,
            "drive_id": drive_id,
        }
        if site_id:
            payload["site_id"] = site_id

        return self._request(
            "POST", f"/api/v1/file-upload/{source_connection_id}/upload-selected", json=payload
        )

    def list_collections(self) -> list:
        """List all collections."""
        return self._request("GET", "/api/v1/collections")


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_s3_configuration(client: AirweaveClient):
    """Test S3 configuration."""
    print_section("1. Testing S3 Configuration")

    # Check current status
    print("📋 Checking S3 status...")
    try:
        status = client.get_s3_status()
        if status.get("configured"):
            print("✅ S3 is already configured!")
            print(f"   Bucket: {status.get('bucket_name')}")
            print(f"   Region: {status.get('aws_region')}")
            print(f"   Prefix: {status.get('bucket_prefix')}")
            return True
        else:
            print("⚠️  S3 is not configured yet.")
            return False
    except Exception as e:
        print(f"❌ Failed to check S3 status: {e}")
        return False


def configure_s3_minio(client: AirweaveClient):
    """Configure S3 with MinIO settings."""
    print_section("2. Configuring S3 (MinIO)")

    minio_config = {
        "aws_access_key_id": "minioadmin",
        "aws_secret_access_key": "minioadmin",
        "bucket_name": "airweave",
        "bucket_prefix": "airweave-outbound/",
        "aws_region": "us-east-1",
        "endpoint_url": "http://localhost:9000",
        "use_ssl": False,
    }

    print("🧪 Testing MinIO connection...")
    try:
        test_result = client.test_s3_connection(minio_config)
        print(f"✅ Connection test successful: {test_result.get('message', 'OK')}")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("   Make sure MinIO is running at http://localhost:9000")
        return False

    print("\n💾 Saving S3 configuration...")
    try:
        result = client.configure_s3(minio_config)
        print("✅ S3 configuration saved successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False


def test_file_browser(client: AirweaveClient, source_connection_id: str):
    """Test file browser functionality."""
    print_section("3. Testing File Browser")

    print(f"📂 Browsing files from source connection: {source_connection_id}")
    try:
        result = client.browse_files(source_connection_id)
        files = result.get("files", [])
        folders = result.get("folders", [])

        print(f"✅ Found {len(files)} files and {len(folders)} folders")
        print(f"\n📁 Current path: {result.get('current_path', 'root')}")

        if files:
            print("\n📄 Sample files:")
            for file in files[:5]:  # Show first 5 files
                size_mb = (file.get("size", 0) / (1024 * 1024)) if file.get("size") else 0
                print(f"   - {file.get('name')} ({size_mb:.2f} MB)")

        if folders:
            print("\n📁 Folders:")
            for folder in folders[:5]:  # Show first 5 folders
                print(f"   - {folder.get('name')}")

        return result
    except Exception as e:
        print(f"❌ Failed to browse files: {e}")
        return None


def test_file_upload(
    client: AirweaveClient,
    source_connection_id: str,
    file_ids: list,
    collection_id: str,
    drive_id: str,
):
    """Test selective file upload."""
    print_section("4. Testing File Upload")

    print(f"📤 Uploading {len(file_ids)} file(s) to S3...")
    print(f"   Collection ID: {collection_id}")
    print(f"   Drive ID: {drive_id}")

    try:
        result = client.upload_selected_files(
            source_connection_id=source_connection_id,
            file_ids=file_ids,
            collection_id=collection_id,
            drive_id=drive_id,
        )

        print(f"\n✅ Upload completed!")
        print(f"   Total files: {result.get('total_files')}")
        print(f"   Successful: {result.get('successful')}")
        print(f"   Failed: {result.get('failed')}")
        print(f"   Skipped: {result.get('skipped')}")

        if result.get("results"):
            print("\n📋 Upload results:")
            for file_result in result.get("results", []):
                status_icon = "✅" if file_result.get("status") == "success" else "❌"
                print(f"   {status_icon} {file_result.get('file_name')}: {file_result.get('status')}")
                if file_result.get("s3_path"):
                    print(f"      → {file_result.get('s3_path')}")
                if file_result.get("error"):
                    print(f"      Error: {file_result.get('error')}")

        return result
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None


def main():
    """Main test function."""
    print("🚀 Airweave File Selection Test Script")
    print("=" * 60)

    # Initialize client
    api_key = input("\nEnter API key (or press Enter to skip auth): ").strip() or None
    client = AirweaveClient(api_key=api_key)

    # Step 1: Check S3 configuration
    s3_configured = test_s3_configuration(client)

    # Step 2: Configure S3 if needed
    if not s3_configured:
        configure = input("\n❓ Configure S3 with MinIO? (y/n): ").strip().lower()
        if configure == "y":
            configure_s3_minio(client)

    # Step 3: List source connections
    print_section("Source Connections")
    try:
        connections = client.list_source_connections()
        print(f"📋 Found {len(connections)} source connection(s):")
        for conn in connections:
            print(f"   - {conn.get('name')} ({conn.get('short_name')}) - ID: {conn.get('id')}")
    except Exception as e:
        print(f"❌ Failed to list connections: {e}")
        return

    if not connections:
        print("⚠️  No source connections found. Please create one first.")
        return

    # Step 4: Select source connection
    source_id = input("\n❓ Enter source connection ID to test: ").strip()
    if not source_id:
        print("❌ Source connection ID required")
        return

    # Step 5: Browse files
    browse_result = test_file_browser(client, source_id)

    if not browse_result or not browse_result.get("files"):
        print("⚠️  No files found to upload")
        return

    # Step 6: Select files to upload
    print("\n📋 Available files:")
    files = browse_result.get("files", [])
    for i, file in enumerate(files[:10], 1):  # Show first 10
        size_mb = (file.get("size", 0) / (1024 * 1024)) if file.get("size") else 0
        print(f"   {i}. {file.get('name')} ({size_mb:.2f} MB)")

    file_selection = input("\n❓ Enter file numbers to upload (comma-separated, e.g., 1,2,3): ").strip()
    if not file_selection:
        print("⚠️  No files selected")
        return

    try:
        selected_indices = [int(x.strip()) - 1 for x in file_selection.split(",")]
        selected_files = [files[i] for i in selected_indices if 0 <= i < len(files)]
        file_ids = [f.get("id") for f in selected_files]
        drive_id = browse_result.get("current_path", "").split("/")[2] if "/drives/" in browse_result.get("current_path", "") else None

        if not drive_id:
            drive_id = input("❓ Enter drive ID: ").strip()

        # Get collection ID
        collections = client.list_collections()
        if not collections:
            print("❌ No collections found. Please create a collection first.")
            return

        print("\n📋 Available collections:")
        for i, coll in enumerate(collections[:10], 1):
            print(f"   {i}. {coll.get('name')} ({coll.get('readable_id')})")

        coll_selection = input("\n❓ Enter collection number: ").strip()
        if not coll_selection:
            print("❌ Collection required")
            return

        collection = collections[int(coll_selection) - 1]
        collection_id = collection.get("id")

        # Step 7: Upload files
        test_file_upload(client, source_id, file_ids, collection_id, drive_id)

    except (ValueError, IndexError) as e:
        print(f"❌ Invalid selection: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

