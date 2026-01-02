# Testing SharePoint Connection

## Prerequisites

1. **Backend API running** at http://localhost:8001
2. **Microsoft Azure App Registration** (for OAuth)
   - You'll need a Microsoft Azure app with OAuth credentials
   - Or use the OAuth token method if you already have an access token

## Step 1: Get SharePoint Source Information

First, check what SharePoint connector requires:

```powershell
# Get SharePoint source details
curl http://localhost:8001/api/v1/sources/sharepoint
```

This will show:
- Authentication methods supported
- Configuration options
- Required OAuth scopes

## Step 2: Create a Collection (if needed)

You need a collection to attach the source connection to:

```powershell
# Create a collection
$collectionBody = @{
    name = "Test SharePoint Collection"
    description = "Testing SharePoint connector"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/collections/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $collectionBody

$collectionId = $response.id
Write-Host "Collection ID: $collectionId"
```

## Step 3: Create SharePoint Source Connection

### Option A: OAuth Browser Flow (Recommended)

This will return an OAuth URL you need to visit:

```powershell
$connectionBody = @{
    source_short_name = "sharepoint"
    collection_id = $collectionId
    name = "My SharePoint Connection"
    auth = @{
        method = "oauth_browser"
        redirect_url = "http://localhost:8080"
    }
    sync_immediately = $false
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/source-connections/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $connectionBody

# The response will contain an auth_url
$authUrl = $response.auth.auth_url
Write-Host "Visit this URL to authenticate: $authUrl"
```

After visiting the URL and authenticating, you'll be redirected back. The connection will be automatically completed.

### Option B: OAuth Token (If you have an access token)

If you already have a Microsoft Graph API access token:

```powershell
$connectionBody = @{
    source_short_name = "sharepoint"
    collection_id = $collectionId
    name = "My SharePoint Connection"
    auth = @{
        method = "oauth_token"
        access_token = "YOUR_ACCESS_TOKEN_HERE"
        refresh_token = "YOUR_REFRESH_TOKEN_HERE"  # Optional but recommended
    }
    sync_immediately = $true
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/source-connections/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $connectionBody

$connectionId = $response.id
Write-Host "Connection ID: $connectionId"
```

## Step 4: Verify Connection

Check the connection status:

```powershell
$connectionId = "YOUR_CONNECTION_ID"
$connection = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/source-connections/$connectionId"
$connection | ConvertTo-Json -Depth 5
```

## Step 5: Run a Sync (Test File Download & S3 Upload)

Trigger a sync to test downloading files from SharePoint and uploading to S3:

```powershell
$connectionId = "YOUR_CONNECTION_ID"
$syncJob = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/source-connections/$connectionId/run" `
    -Method POST

$jobId = $syncJob.id
Write-Host "Sync Job ID: $jobId"
Write-Host "Status: $($syncJob.status)"
```

## Step 6: Monitor Sync Progress

Check the sync job status:

```powershell
$jobId = "YOUR_JOB_ID"
$job = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/source-connections/$connectionId/jobs/$jobId"
$job | ConvertTo-Json -Depth 5
```

Or watch logs in real-time:

```powershell
# Check backend logs
podman logs -f airweave-backend
```

## Step 7: Verify Files in S3 (MinIO)

Once the sync completes, check MinIO console:

1. Open http://localhost:9001
2. Login with:
   - Username: `airweave`
   - Password: `airweave-dev-password`
3. Navigate to the bucket: `airweave-outbound/collections/{collection_readable_id}/blobs/`
4. You should see files downloaded from SharePoint

## Step 8: List Synced Files

Get a list of entities (files) that were synced:

```powershell
# Get sync details
$syncId = "YOUR_SYNC_ID"
$entities = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/entities/count-by-sync/$syncId"
$entities | ConvertTo-Json
```

## Troubleshooting

### OAuth Flow Issues

If OAuth browser flow doesn't work:
- Check that redirect URL matches your Azure app registration
- Ensure Microsoft Graph API permissions are granted
- Check backend logs: `podman logs airweave-backend`

### Sync Fails

If sync fails:
- Check connection status: `GET /source-connections/{id}`
- Check sync job details: `GET /source-connections/{id}/jobs/{job_id}`
- Review backend logs for errors

### No Files in S3

If files don't appear in S3:
- Verify S3 destination is configured in the collection
- Check sync job completed successfully
- Verify MinIO is running: `podman ps | grep minio`

## Quick Test Script

Here's a complete PowerShell script to test SharePoint:

```powershell
# Set variables
$baseUrl = "http://localhost:8001/api/v1"
$collectionName = "Test SharePoint"

# 1. Create collection
Write-Host "Creating collection..." -ForegroundColor Yellow
$collection = Invoke-RestMethod -Uri "$baseUrl/collections/" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{ name = $collectionName } | ConvertTo-Json)
Write-Host "Collection ID: $($collection.id)" -ForegroundColor Green

# 2. Create SharePoint connection (OAuth Token method - replace with your token)
Write-Host "`nCreating SharePoint connection..." -ForegroundColor Yellow
$connection = Invoke-RestMethod -Uri "$baseUrl/source-connections/" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        source_short_name = "sharepoint"
        collection_id = $collection.id
        name = "Test SharePoint Connection"
        auth = @{
            method = "oauth_token"
            access_token = "YOUR_ACCESS_TOKEN"
        }
        sync_immediately = $true
    } | ConvertTo-Json -Depth 10)
Write-Host "Connection ID: $($connection.id)" -ForegroundColor Green

# 3. Run sync
Write-Host "`nRunning sync..." -ForegroundColor Yellow
$syncJob = Invoke-RestMethod -Uri "$baseUrl/source-connections/$($connection.id)/run" `
    -Method POST
Write-Host "Sync Job ID: $($syncJob.id)" -ForegroundColor Green
Write-Host "Status: $($syncJob.status)" -ForegroundColor Green

# 4. Monitor progress
Write-Host "`nMonitoring sync (checking every 5 seconds)..." -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 5
    $job = Invoke-RestMethod -Uri "$baseUrl/source-connections/$($connection.id)/jobs/$($syncJob.id)"
    Write-Host "Status: $($job.status) - Processed: $($job.entities_processed)" -ForegroundColor Cyan
} while ($job.status -eq "running")

Write-Host "`nSync completed!" -ForegroundColor Green
```

