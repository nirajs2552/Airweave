# S3 Configuration & File Selection Guide

This guide explains how to configure S3 storage and use the file selection workflow in connector-only mode.

## Part A: Configure S3 via Frontend UI

### Step 1: Access the Frontend
1. Open your browser and navigate to: `http://localhost:8080`
2. Log in (or create an account if needed)

### Step 2: Configure S3 Destination
1. Navigate to **Settings** → **Organization Settings**
2. Look for the **S3 Event Streaming** card
3. Click **"Configure S3 Destination"** button

### Step 3: Enter S3 Credentials

For **MinIO** (local development):
- **AWS Access Key ID**: `minioadmin`
- **AWS Secret Access Key**: `minioadmin`
- **Bucket Name**: `airweave` (or create a new bucket in MinIO)
- **Bucket Prefix**: `airweave-outbound/` (default)
- **AWS Region**: `us-east-1` (default)
- **Custom Endpoint URL**: `http://localhost:9000`
- **Use SSL/TLS**: Unchecked (for local MinIO)

For **AWS S3** (production):
- **AWS Access Key ID**: Your AWS access key
- **AWS Secret Access Key**: Your AWS secret key
- **Bucket Name**: Your S3 bucket name
- **Bucket Prefix**: `airweave-outbound/` (default)
- **AWS Region**: Your bucket region (e.g., `us-east-1`)
- **Custom Endpoint URL**: Leave empty
- **Use SSL/TLS**: Checked (recommended)

### Step 4: Test Connection
1. Click **"Test Connection"** to verify credentials
2. Wait for success message
3. Click **"Save Configuration"**

### Step 5: Verify Configuration
- The S3 Status Card should show "Configured" status
- You should see the bucket name and region displayed

## Part B: File Selection Workflow (API)

### API Endpoints

#### 1. Browse Files
**Endpoint**: `GET /api/v1/file-browser/{source_connection_id}/browse`

**Query Parameters**:
- `drive_id` (optional): SharePoint drive ID (defaults to root site's default drive)
- `folder_id` (optional): Folder ID to browse (defaults to drive root)
- `site_id` (optional): SharePoint site ID (defaults to root site)

**Example Request**:
```bash
curl -X GET "http://localhost:8001/api/v1/file-browser/{source_connection_id}/browse?drive_id=b!abc123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response**:
```json
{
  "files": [
    {
      "id": "file-id-123",
      "name": "document.pdf",
      "path": "/drives/drive-id/items/file-id-123",
      "size": 1024000,
      "modified_at": "2024-01-15T10:30:00Z",
      "type": "file",
      "mime_type": "application/pdf"
    }
  ],
  "folders": [
    {
      "id": "folder-id-456",
      "name": "Documents",
      "path": "/drives/drive-id/items/folder-id-456",
      "type": "folder"
    }
  ],
  "current_path": "/drives/drive-id",
  "parent_path": null
}
```

#### 2. Upload Selected Files
**Endpoint**: `POST /api/v1/file-upload/{source_connection_id}/upload-selected`

**Request Body**:
```json
{
  "file_ids": ["file-id-123", "file-id-456"],
  "collection_id": "collection-uuid",
  "drive_id": "drive-id-123",
  "site_id": "site-id-123"
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:8001/api/v1/file-upload/{source_connection_id}/upload-selected" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": ["file-id-123"],
    "collection_id": "your-collection-uuid",
    "drive_id": "drive-id-123"
  }'
```

**Response**:
```json
{
  "total_files": 2,
  "successful": 2,
  "failed": 0,
  "skipped": 0,
  "results": [
    {
      "file_id": "file-id-123",
      "file_name": "document.pdf",
      "status": "success",
      "s3_path": "s3://bucket-name/airweave-outbound/collections/collection-id/blobs/file-id-123"
    }
  ]
}
```

### Workflow Example

1. **Get Source Connection ID**:
   ```bash
   curl -X GET "http://localhost:8001/api/v1/source-connections" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. **Browse SharePoint Files**:
   ```bash
   curl -X GET "http://localhost:8001/api/v1/file-browser/{source_connection_id}/browse" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. **Select Files and Upload**:
   ```bash
   curl -X POST "http://localhost:8001/api/v1/file-upload/{source_connection_id}/upload-selected" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "file_ids": ["file-1", "file-2"],
       "collection_id": "collection-uuid",
       "drive_id": "drive-id"
     }'
   ```

## Troubleshooting

### S3 Configuration Issues

**Error: "S3 destination not configured"**
- Ensure you've completed the S3 configuration via the frontend UI
- Check that the S3 connection exists in the database

**Error: "Connection test failed"**
- Verify MinIO is running: `docker ps | grep minio`
- Check MinIO credentials match your configuration
- For MinIO, ensure endpoint URL is `http://localhost:9000` (not `https://`)

**Error: "Bucket not found"**
- Create the bucket in MinIO UI: `http://localhost:9001`
- Or use an existing bucket name

### File Upload Issues

**Error: "Source connection not found"**
- Verify the `source_connection_id` is correct
- Ensure the connection is authenticated

**Error: "Collection not found"**
- Verify the `collection_id` is correct
- Ensure you have access to the collection

**Error: "No valid destinations"**
- Ensure S3 is configured (see Part A)
- Check that the S3 connection is properly set up

## Next Steps

Once S3 is configured and files are uploaded:
- Files are stored in S3 at: `s3://{bucket}/{prefix}/collections/{collection_id}/blobs/{file_id}`
- You can access files via the S3 API or MinIO UI
- Files are not chunked or embedded (connector-only mode)

