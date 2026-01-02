# S3 Configuration via API

This guide shows how to configure S3 using the API endpoints.

## ⚠️ Authentication Required

The S3 API endpoints require authentication. You have two options:

### Option 1: Use Frontend UI (Recommended)

The Frontend UI handles authentication automatically. This is the easiest method:
- Open http://localhost:8080
- Go to Settings → Organization Settings
- Click "Configure S3 Destination"
- See `FRONTEND_S3_GUIDE.md` for details

### Option 2: Use API with Authentication

If you need to use the API, you'll need an API key.

## Getting an API Key

1. **Via Frontend UI:**
   - Open http://localhost:8080
   - Go to Settings → API Keys
   - Create a new API key
   - Copy the key (you'll only see it once!)

2. **Via API (if you have admin access):**
   ```bash
   # Create API key
   curl -X POST "http://localhost:8001/api/v1/api-keys" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_EXISTING_TOKEN" \
     -d '{"name": "S3 Config Key"}'
   ```

## API Endpoints

### 1. Test S3 Connection

```bash
curl -X POST "http://localhost:8001/api/v1/s3/test" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "aws_access_key_id": "minioadmin",
    "aws_secret_access_key": "minioadmin",
    "bucket_name": "airweave",
    "bucket_prefix": "airweave-outbound/",
    "aws_region": "us-east-1",
    "endpoint_url": "http://localhost:9000",
    "use_ssl": false
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Connection test successful"
}
```

### 2. Configure S3

```bash
curl -X POST "http://localhost:8001/api/v1/s3/configure" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "aws_access_key_id": "minioadmin",
    "aws_secret_access_key": "minioadmin",
    "bucket_name": "airweave",
    "bucket_prefix": "airweave-outbound/",
    "aws_region": "us-east-1",
    "endpoint_url": "http://localhost:9000",
    "use_ssl": false
  }'
```

**Response:**
```json
{
  "connection_id": "uuid-here",
  "status": "success",
  "message": "S3 destination configured successfully"
}
```

### 3. Check S3 Status

```bash
curl -X GET "http://localhost:8001/api/v1/s3/status" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response:**
```json
{
  "feature_enabled": true,
  "configured": true,
  "bucket_name": "airweave",
  "aws_region": "us-east-1",
  "bucket_prefix": "airweave-outbound/",
  "endpoint_url": "http://localhost:9000"
}
```

## PowerShell Script with Authentication

Update `configure-s3-api.ps1` to include your API key:

```powershell
$apiKey = "YOUR_API_KEY_HERE"

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $apiKey"
}

# Test connection
$testConfig = @{
    aws_access_key_id = "minioadmin"
    aws_secret_access_key = "minioadmin"
    bucket_name = "airweave"
    bucket_prefix = "airweave-outbound/"
    aws_region = "us-east-1"
    endpoint_url = "http://localhost:9000"
    use_ssl = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/api/v1/s3/test" `
    -Method Post `
    -Headers $headers `
    -Body $testConfig

# Configure S3
Invoke-RestMethod -Uri "http://localhost:8001/api/v1/s3/configure" `
    -Method Post `
    -Headers $headers `
    -Body $testConfig
```

## Troubleshooting

### 401 Unauthorized
- **Cause:** Missing or invalid API key
- **Solution:** Get a valid API key from Frontend UI

### 403 Forbidden
- **Cause:** API key doesn't have required permissions
- **Solution:** Use Frontend UI or check API key permissions

### 404 Not Found
- **Cause:** Endpoint path incorrect or requires authentication
- **Solution:** Verify endpoint path and include Authorization header

### Connection Test Fails
- **Check MinIO is running:** `podman ps | grep minio`
- **Verify MinIO UI:** http://localhost:9001
- **Create bucket:** Create `airweave` bucket in MinIO if needed
- **Check credentials:** Verify `minioadmin`/`minioadmin` are correct

## Recommended Approach

**For local development, use the Frontend UI:**
1. It handles authentication automatically
2. No need to manage API keys
3. Visual feedback and error messages
4. Easier to use

See `FRONTEND_S3_GUIDE.md` for Frontend UI instructions.

