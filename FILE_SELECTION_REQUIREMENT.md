# File Selection Requirement

## Current System vs. Required Workflow

### Current System (Automatic Sync)
- **How it works**: When you create a SharePoint connection, it automatically syncs ALL files from SharePoint
- **Process**: Connection → Sync Job → Download all files → Upload to S3
- **No file selection**: Everything is synced automatically

### Required Workflow (Manual File Selection)
- **Step 1**: Browse SharePoint Document Library
- **Step 2**: Select specific files you want
- **Step 3**: Submit selected files to S3 bucket

## Implementation Options

### Option 1: Add File Selection to Sync Configuration
Modify the sync workflow to support:
- **File Filtering**: Add a `file_ids` or `file_paths` parameter to sync configuration
- **Selective Sync**: Only sync files that match the filter
- **UI Changes**: Add a file browser/picker in the frontend

### Option 2: New File Upload Endpoint
Create a new API endpoint specifically for manual file selection:
- `POST /api/v1/source-connections/{id}/files/select`
- Accepts list of file IDs/paths
- Downloads only selected files
- Uploads directly to S3

### Option 3: Two-Step Process
1. **Browse/List**: `GET /api/v1/source-connections/{id}/files` - List available files
2. **Select & Upload**: `POST /api/v1/source-connections/{id}/files/upload` - Upload selected files

## Immediate Fix Needed

Before implementing file selection, we need to:
1. ✅ Fix destination creation (remove Qdrant dependency) - **DONE**
2. ⏳ Configure S3 destination connection
3. ⏳ Test basic sync workflow
4. ⏳ Then add file selection capability

## Next Steps

1. **First**: Configure S3 destination so syncs can work
2. **Then**: Implement file selection UI and API endpoints
3. **Finally**: Test the complete workflow

