# SharePoint Connection Test Guide

## Quick Start

The API endpoints are at the root level (not `/api/v1`). Here's how to test SharePoint:

## Step 1: Get SharePoint Source Info

```powershell
# List all sources
$sources = Invoke-RestMethod -Uri "http://localhost:8001/sources"
$sharepoint = $sources | Where-Object { $_.short_name -eq "sharepoint" }
$sharepoint | ConvertTo-Json -Depth 5
```

## Step 2: Create a Collection

```powershell
$collection = Invoke-RestMethod -Uri "http://localhost:8001/collections" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        name = "SharePoint Test"
    } | ConvertTo-Json)

Write-Host "Collection ID: $($collection.id)"
Write-Host "Readable ID: $($collection.readable_id)"
```

## Step 3: Create SharePoint Connection

### Option A: OAuth Browser Flow (Recommended)

This returns an OAuth URL you need to visit:

```powershell
$connection = Invoke-RestMethod -Uri "http://localhost:8001/source-connections" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        source_short_name = "sharepoint"
        collection_id = $collection.id
        name = "My SharePoint Connection"
        auth = @{
            method = "oauth_browser"
            redirect_url = "http://localhost:8080"
        }
    } | ConvertTo-Json -Depth 10)

# Visit this URL to authenticate
Write-Host "Visit: $($connection.auth.auth_url)"
```

After visiting the URL and authenticating, the connection will be ready.

### Option B: OAuth Token (If you have an access token)

```powershell
$connection = Invoke-RestMethod -Uri "http://localhost:8001/source-connections" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        source_short_name = "sharepoint"
        collection_id = $collection.id
        name = "My SharePoint Connection"
        auth = @{
            method = "oauth_token"
            access_token = "YOUR_MICROSOFT_GRAPH_ACCESS_TOKEN"
            refresh_token = "YOUR_REFRESH_TOKEN"  # Optional
        }
    } | ConvertTo-Json -Depth 10)

Write-Host "Connection ID: $($connection.id)"
```

## Step 4: Run a Sync

Once the connection is ready, trigger a sync:

```powershell
$connectionId = "YOUR_CONNECTION_ID"
$syncJob = Invoke-RestMethod -Uri "http://localhost:8001/source-connections/$connectionId/run" `
    -Method POST

Write-Host "Sync Job ID: $($syncJob.id)"
Write-Host "Status: $($syncJob.status)"
```

## Step 5: Monitor Sync Progress

```powershell
$connectionId = "YOUR_CONNECTION_ID"
$jobId = "YOUR_JOB_ID"

# Check job status
$job = Invoke-RestMethod -Uri "http://localhost:8001/source-connections/$connectionId/jobs/$jobId"
$job | ConvertTo-Json -Depth 5

# Or watch backend logs
podman logs -f airweave-backend
```

## Step 6: Verify Files in S3

1. Open MinIO Console: http://localhost:9001
   - Username: `airweave`
   - Password: `airweave-dev-password`

2. Navigate to: `airweave-outbound/collections/{collection_readable_id}/blobs/`

3. You should see files downloaded from SharePoint

## Getting a Microsoft Graph Access Token

If you need to get an access token for testing:

### Using Azure CLI

```bash
az login
az account get-access-token --resource https://graph.microsoft.com
```

### Using PowerShell (MSAL)

```powershell
# Install MSAL.PS module if needed
# Install-Module MSAL.PS

Import-Module MSAL.PS

$clientId = "YOUR_AZURE_APP_CLIENT_ID"
$tenantId = "YOUR_TENANT_ID"
$scopes = @("https://graph.microsoft.com/.default")

$token = Get-MsalToken -ClientId $clientId -TenantId $tenantId -Scopes $scopes
$token.AccessToken
```

### Required Microsoft Graph Permissions

Your Azure app needs these permissions:
- `Sites.Read.All` - Read all site collections
- `Files.Read.All` - Read all files
- `User.Read` - Read user profile

## Complete Test Script

```powershell
# 1. Get SharePoint info
$sharepoint = (Invoke-RestMethod -Uri "http://localhost:8001/sources") | 
    Where-Object { $_.short_name -eq "sharepoint" }
Write-Host "SharePoint connector: $($sharepoint.name)" -ForegroundColor Green

# 2. Create collection
$collection = Invoke-RestMethod -Uri "http://localhost:8001/collections" `
    -Method POST -ContentType "application/json" `
    -Body (@{ name = "SharePoint Test" } | ConvertTo-Json)
Write-Host "Collection: $($collection.readable_id)" -ForegroundColor Green

# 3. Create connection (replace YOUR_TOKEN with actual token)
$connection = Invoke-RestMethod -Uri "http://localhost:8001/source-connections" `
    -Method POST -ContentType "application/json" `
    -Body (@{
        source_short_name = "sharepoint"
        collection_id = $collection.id
        name = "Test Connection"
        auth = @{
            method = "oauth_token"
            access_token = "YOUR_TOKEN_HERE"
        }
    } | ConvertTo-Json -Depth 10)
Write-Host "Connection: $($connection.id)" -ForegroundColor Green

# 4. Run sync
$syncJob = Invoke-RestMethod -Uri "http://localhost:8001/source-connections/$($connection.id)/run" `
    -Method POST
Write-Host "Sync started: $($syncJob.id)" -ForegroundColor Green

# 5. Monitor
do {
    Start-Sleep -Seconds 5
    $job = Invoke-RestMethod -Uri "http://localhost:8001/source-connections/$($connection.id)/jobs/$($syncJob.id)"
    Write-Host "Status: $($job.status) - Processed: $($job.entities_processed)" -ForegroundColor Cyan
} while ($job.status -eq "running")

Write-Host "Sync completed!" -ForegroundColor Green
```

## Troubleshooting

### 401 Unauthorized
- Check if you need an API key (check backend logs)
- Verify AUTH_ENABLED setting in backend

### Connection Fails
- Verify access token is valid
- Check token has required Microsoft Graph permissions
- Review backend logs: `podman logs airweave-backend`

### No Files in S3
- Verify S3 destination is configured in collection
- Check sync job completed successfully
- Verify MinIO is running

### OAuth Browser Flow Issues
- Ensure redirect URL matches Azure app registration
- Check Microsoft Graph API permissions are granted
- Verify OAuth callback endpoint is accessible

## API Documentation

Full API documentation available at:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

