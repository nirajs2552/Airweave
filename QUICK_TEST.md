# Quick Test Guide - File Browser & Upload

Quick commands to test the file selection workflow.

## Prerequisites

1. Services running: `podman compose -f docker/docker-compose.dev.yml ps`
2. SharePoint source connection created
3. Collection created

## Step 1: Configure S3 (MinIO)

### Via API:
```bash
# Test connection
curl -X POST "http://localhost:8001/api/v1/s3/test" \
  -H "Content-Type: application/json" \
  -d '{
    "aws_access_key_id": "minioadmin",
    "aws_secret_access_key": "minioadmin",
    "bucket_name": "airweave",
    "bucket_prefix": "airweave-outbound/",
    "aws_region": "us-east-1",
    "endpoint_url": "http://localhost:9000",
    "use_ssl": false
  }'

# Configure S3
curl -X POST "http://localhost:8001/api/v1/s3/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "aws_access_key_id": "minioadmin",
    "aws_secret_access_key": "minioadmin",
    "bucket_name": "airweave",
    "bucket_prefix": "airweave-outbound/",
    "aws_region": "us-east-1",
    "endpoint_url": "http://localhost:9000",
    "use_ssl": false
  }'

# Check status
curl "http://localhost:8001/api/v1/s3/status"
```

### Via Frontend:
1. Open http://localhost:8080
2. Go to Settings → Organization Settings
3. Click "Configure S3 Destination"
4. Enter MinIO credentials:
   - Access Key: `minioadmin`
   - Secret Key: `minioadmin`
   - Bucket: `airweave`
   - Endpoint: `http://localhost:9000`
   - Uncheck SSL

## Step 2: Get Source Connection ID

```bash
# List source connections
curl "http://localhost:8001/api/v1/source-connections" | jq '.[] | {id, name, short_name}'
```

## Step 3: Browse Files

```bash
# Replace {source_connection_id} with your actual ID
SOURCE_ID="your-source-connection-id"

# Browse root (will auto-detect drive)
curl "http://localhost:8001/api/v1/file-browser/${SOURCE_ID}/browse" | jq

# Browse specific folder
curl "http://localhost:8001/api/v1/file-browser/${SOURCE_ID}/browse?folder_id=your-folder-id" | jq

# Browse specific drive
curl "http://localhost:8001/api/v1/file-browser/${SOURCE_ID}/browse?drive_id=your-drive-id" | jq
```

## Step 4: Get Collection ID

```bash
# List collections
curl "http://localhost:8001/api/v1/collections" | jq '.[] | {id, readable_id, name}'
```

## Step 5: Upload Selected Files

```bash
# Replace these with your actual values
SOURCE_ID="your-source-connection-id"
COLLECTION_ID="your-collection-uuid"
DRIVE_ID="your-drive-id"
FILE_ID_1="file-id-1"
FILE_ID_2="file-id-2"

curl -X POST "http://localhost:8001/api/v1/file-upload/${SOURCE_ID}/upload-selected" \
  -H "Content-Type: application/json" \
  -d "{
    \"file_ids\": [\"${FILE_ID_1}\", \"${FILE_ID_2}\"],
    \"collection_id\": \"${COLLECTION_ID}\",
    \"drive_id\": \"${DRIVE_ID}\"
  }" | jq
```

## Step 6: Verify Upload in MinIO

1. Open MinIO Console: http://localhost:9001
2. Login: `minioadmin` / `minioadmin`
3. Navigate to `airweave` bucket
4. Check `airweave-outbound/collections/{collection_id}/blobs/`

## Using the Test Script

For an interactive experience:

```bash
# Install dependencies
pip install httpx

# Run the test script
python test_file_selection.py
```

The script will guide you through all steps interactively.

## Troubleshooting

### S3 Not Configured
```bash
# Check S3 status
curl "http://localhost:8001/api/v1/s3/status"
```

### Source Connection Not Found
```bash
# List all source connections
curl "http://localhost:8001/api/v1/source-connections"
```

### Files Not Found
- Ensure SharePoint connection is authenticated
- Check that you have access to the drive/folder
- Verify drive_id and folder_id are correct

### Upload Fails
- Ensure S3 is configured
- Check collection exists
- Verify file IDs are correct
- Check backend logs: `podman logs -f airweave-backend`

