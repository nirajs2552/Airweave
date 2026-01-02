# Fixing "No valid destinations" Sync Error

## The Problem

You're seeing:
- **Sync Error**: "No valid destinations could be created for sync. Tried 0 connection(s)."
- **Status**: Failed
- **Entities**: 0

## Root Cause

The sync is failing because **S3 destination is not configured**. In connector-only mode, S3 is the only destination, so syncs can't proceed without it.

## Solution: Configure S3

### Step 1: Create MinIO Bucket

1. Open MinIO UI: **http://localhost:9001**
2. Login: `minioadmin` / `minioadmin`
3. Click **"Create Bucket"** button
4. Name: `airweave`
5. Click **"Create Bucket"**

### Step 2: Configure S3 via API

```powershell
# Set your API key
$env:AIRWEAVE_API_KEY = "KwRMHY4gernTdKIkB8AXEYf8Cr8BzHTM8zwwDN3b8CI"

# Run configuration script
.\configure-s3-api.ps1
```

### Step 3: Verify S3 Configuration

After configuration, the sync should work. The error should disappear.

## SharePoint Connection Status

### If SharePoint shows "Failed" or "Pending Auth"

1. **Check Authentication:**
   - Click on the SharePoint connection
   - If you see "Authenticate" or "Connect" button, click it
   - Complete the OAuth flow

2. **Re-authenticate if needed:**
   - Go to the connection settings
   - Click "Re-authenticate" or "Refresh Auth"

## File Selection Feature

### Where to Find It

After S3 is configured and SharePoint is authenticated:

1. **Navigate to your Collection**
2. **Click on the SharePoint Connection**
3. **Look for "Browse & Select Files" card** (newly added)
4. **Browse folders and files**
5. **Select files** using checkboxes
6. **Click "Upload X File(s)"** to upload to S3

### Features

- ✅ Browse SharePoint folders
- ✅ View files with size and date
- ✅ Select multiple files
- ✅ Upload selected files directly to S3
- ✅ No full sync required

## Troubleshooting

### S3 Configuration Fails

**Error: "Could not connect to endpoint"**
- Check MinIO is running: `podman ps | grep minio`
- Verify bucket exists in MinIO UI
- Check endpoint URL: `http://localhost:9000` (not `https://`)

**Error: "Bucket not found"**
- Create the bucket in MinIO UI first
- Verify bucket name is exactly `airweave`

### SharePoint Not Authenticated

**Status shows "Pending Auth"**
- Click the connection
- Click "Authenticate" or "Connect" button
- Complete OAuth flow in browser
- Return to the app

**Status shows "Failed"**
- Check the error message
- If it's auth-related, re-authenticate
- If it's destination-related, configure S3 first

### File Browser Not Showing

**"Browse & Select Files" card not visible**
- Ensure S3 is configured
- Ensure SharePoint is authenticated
- Refresh the page
- Check browser console for errors

## Quick Checklist

- [ ] MinIO bucket `airweave` created
- [ ] S3 configured via API (or Frontend UI)
- [ ] SharePoint connection authenticated
- [ ] Sync error resolved
- [ ] File browser visible
- [ ] Can browse and select files

## Next Steps

1. ✅ Configure S3 (see above)
2. ✅ Authenticate SharePoint (if needed)
3. ✅ Use File Browser to select and upload files
4. ✅ Files will be uploaded directly to S3

See `QUICK_TEST.md` for API testing examples.

