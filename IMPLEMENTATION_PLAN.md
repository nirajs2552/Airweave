# Implementation Plan: File Selection from SharePoint to S3

## User Requirement
**Allow users to:**
1. Browse SharePoint Document Library
2. Select specific files
3. Submit selected files to S3 bucket

## Current System Limitations

### Current Workflow (Automatic Sync)
- Creates a source connection → automatically syncs ALL files
- No file selection capability
- Files are synced based on sync job configuration

### What's Missing
1. **File Browser API**: Endpoint to list files from SharePoint without syncing
2. **File Selection UI**: Interface to browse and select files
3. **Selective Upload API**: Endpoint to upload only selected files to S3

## Proposed Solution

### Phase 1: Fix Immediate Issues ✅
- [x] Remove Qdrant dependency from destination creation
- [x] Fix collection creation to work without Qdrant
- [ ] Configure S3 destination connection
- [ ] Enable S3_DESTINATION feature flag or bypass in connector-only mode

### Phase 2: Add File Browsing API
Create new endpoints:
- `GET /api/v1/source-connections/{id}/browse` - List files/folders from SharePoint
- `GET /api/v1/source-connections/{id}/browse/{path}` - Browse specific folder

**Response format:**
```json
{
  "files": [
    {
      "id": "file-id",
      "name": "document.pdf",
      "path": "/sites/site/drives/drive/items/file-id",
      "size": 12345,
      "modified_at": "2025-01-01T00:00:00Z",
      "type": "file"
    }
  ],
  "folders": [
    {
      "id": "folder-id",
      "name": "Documents",
      "path": "/sites/site/drives/drive/items/folder-id",
      "type": "folder"
    }
  ]
}
```

### Phase 3: Add File Selection Upload API
Create endpoint:
- `POST /api/v1/source-connections/{id}/upload-selected`

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
3. Upload directly to S3 (bypass full sync pipeline)
4. Return upload status

### Phase 4: Frontend UI
- Add file browser component
- Add file selection interface
- Add "Upload Selected" button
- Show upload progress

## Alternative: Use Existing Sync with Filters

Instead of new endpoints, we could:
1. Add `file_filter` or `file_ids` parameter to sync configuration
2. Modify sync pipeline to only process files matching the filter
3. This reuses existing infrastructure but adds filtering

## Recommendation

**Start with Phase 1** (fix S3 destination), then implement **Phase 2 & 3** (file browsing and selective upload) as it provides the exact workflow the user wants.

