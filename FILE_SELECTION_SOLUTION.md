# Solution: File Selection from SharePoint to S3

## Your Requirement
**Allow users to:**
1. Browse SharePoint Document Library
2. Select specific files
3. Submit selected files to S3 bucket

## Current System vs. Your Need

### Current System (Automatic Sync)
- ❌ Syncs ALL files automatically
- ❌ No file selection
- ❌ No browsing interface

### What You Need (Manual Selection)
- ✅ Browse files in SharePoint
- ✅ Select specific files
- ✅ Upload only selected files to S3

## Implementation Approach

### Option 1: New File Selection API (Recommended)

Create new endpoints for file browsing and selective upload:

#### 1. File Browser Endpoint
```
GET /api/v1/source-connections/{connection_id}/browse
GET /api/v1/source-connections/{connection_id}/browse?drive_id={drive_id}&folder_id={folder_id}
```

**Returns:**
```json
{
  "files": [
    {
      "id": "item-id",
      "name": "document.pdf",
      "size": 12345,
      "modified_at": "2025-01-01T00:00:00Z",
      "path": "/sites/site/drives/drive/items/item-id",
      "type": "file"
    }
  ],
  "folders": [
    {
      "id": "folder-id",
      "name": "Documents",
      "type": "folder"
    }
  ]
}
```

#### 2. Selective Upload Endpoint
```
POST /api/v1/source-connections/{connection_id}/upload-selected
```

**Request:**
```json
{
  "file_ids": ["file-id-1", "file-id-2"],
  "collection_id": "collection-uuid",
  "destination_connection_id": "s3-connection-uuid"
}
```

**Process:**
1. Fetch selected files from SharePoint
2. Download files
3. Upload directly to S3
4. Return upload status

### Option 2: Use Sync with File Filter

Modify existing sync to accept file filters:
- Add `file_ids` parameter to sync configuration
- Only sync files matching the filter
- Reuses existing infrastructure

## Immediate Steps

### Step 1: Fix S3 Destination Configuration
The error "No valid destinations" means S3 isn't configured. We need to:
1. Configure S3 destination via API or UI
2. Ensure MinIO bucket exists
3. Test connection

### Step 2: Implement File Browser
- Create endpoint to list SharePoint files
- Return file metadata (id, name, size, path)
- Support folder navigation

### Step 3: Implement Selective Upload
- Create endpoint to upload selected files
- Download from SharePoint
- Upload to S3
- Track upload status

### Step 4: Add UI
- File browser component
- File selection interface
- Upload button and progress

## Quick Start: Configure S3 First

Before implementing file selection, we need S3 configured. You can:

1. **Via Frontend UI** (if available):
   - Go to Organization Settings
   - Configure S3 Destination
   - Enter MinIO credentials

2. **Via API** (once feature flag is bypassed):
   ```powershell
   POST /s3/configure
   {
     "bucket_name": "airweave-outbound",
     "endpoint_url": "http://minio:9000",
     "aws_access_key_id": "airweave",
     "aws_secret_access_key": "airweave-dev-password",
     "aws_region": "us-east-1",
     "use_ssl": false,
     "bucket_prefix": ""
   }
   ```

3. **Create bucket in MinIO**:
   - Open http://localhost:9001
   - Login: airweave / airweave-dev-password
   - Create bucket: `airweave-outbound`

## Next Steps

Would you like me to:
1. **Fix S3 configuration** (ensure it works)
2. **Implement file browser API** (browse SharePoint files)
3. **Implement selective upload API** (upload selected files)
4. **All of the above**

Let me know which you'd like to prioritize!

