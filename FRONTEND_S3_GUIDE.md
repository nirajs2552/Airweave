# Frontend S3 Configuration Guide

## Step-by-Step Instructions

### 1. Open the Frontend
Navigate to: **http://localhost:8080**

### 2. Navigate to Organization Settings

**Path:** 
```
Frontend → User Menu (top right) → Settings → Organization Settings
```

Or directly: **http://localhost:8080/organization/settings**

### 3. Find S3 Configuration Section

Scroll down to find the **"S3 Event Streaming"** card. It should be located:
- Below the "Primary Organization" section
- Above the "Danger Zone" section

**If you don't see it:**
- The feature flag might be disabled in the containerized frontend
- Use the API method instead (see below)

### 4. Configure S3 (MinIO)

Click the **"Configure S3 Destination"** button.

Fill in the form with these MinIO credentials:

| Field | Value |
|-------|-------|
| **AWS Access Key ID** | `minioadmin` |
| **AWS Secret Access Key** | `minioadmin` |
| **Bucket Name** | `airweave` |
| **Bucket Prefix** | `airweave-outbound/` |
| **AWS Region** | `us-east-1` |
| **Custom Endpoint URL** | `http://localhost:9000` |
| **Use SSL/TLS** | ❌ **Unchecked** (for local MinIO) |

### 5. Test Connection

1. Click **"Test Connection"** button
2. Wait for the success message
3. You should see: ✅ "Connection test successful"

### 6. Save Configuration

1. Click **"Save Configuration"** button
2. Wait for the success message
3. The modal will close automatically

### 7. Verify Configuration

After saving, the S3 Status Card should show:
- ✅ **"Configured"** status
- Bucket name: `airweave`
- Region: `us-east-1`
- Prefix: `airweave-outbound/`

## Alternative: Configure via API

If the S3 configuration UI is not visible in the frontend, you can configure it via API:

```bash
# Test connection first
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

# Verify configuration
curl "http://localhost:8001/api/v1/s3/status"
```

## Troubleshooting

### S3 Card Not Visible
- The containerized frontend might have the feature flag disabled
- **Solution:** Use the API method above

### Connection Test Fails
- **Check MinIO is running:**
  ```bash
  podman ps | grep minio
  ```
- **Check MinIO UI:** http://localhost:9001 (login: `minioadmin`/`minioadmin`)
- **Verify bucket exists:** Create `airweave` bucket in MinIO if needed

### Save Fails
- Check backend logs: `podman logs -f airweave-backend`
- Verify API is accessible: `curl http://localhost:8001/health`
- Check network connectivity between frontend and backend

## Next Steps

After S3 is configured:
1. ✅ Test file browser: `GET /api/v1/file-browser/{id}/browse`
2. ✅ Upload files: `POST /api/v1/file-upload/{id}/upload-selected`
3. ✅ Verify files in MinIO: http://localhost:9001

See `QUICK_TEST.md` for API testing examples.
