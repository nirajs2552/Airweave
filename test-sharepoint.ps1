# SharePoint Connection Test Script
# This script helps you test SharePoint connector

param(
    [string]$BaseUrl = "http://localhost:8001",
    [string]$ApiKey = "",  # Optional: if you have an API key
    [string]$AccessToken = ""  # Optional: if you have a SharePoint access token
)

Write-Host "=== SharePoint Connection Test ===" -ForegroundColor Cyan
Write-Host ""

# Check if backend is running
Write-Host "Step 1: Checking backend health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8001/health" -ErrorAction Stop
    Write-Host "✅ Backend is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend is not running. Start it with:" -ForegroundColor Red
    Write-Host "   podman start airweave-backend" -ForegroundColor Yellow
    exit 1
}

# Prepare headers (if API key provided)
$headers = @{
    "Content-Type" = "application/json"
}
if ($ApiKey) {
    $headers["Authorization"] = "Bearer $ApiKey"
    Write-Host "✅ Using API key authentication" -ForegroundColor Green
} else {
    Write-Host "⚠️  No API key provided - some endpoints may require authentication" -ForegroundColor Yellow
    Write-Host "   You can create an API key at: $BaseUrl/api-keys/" -ForegroundColor Gray
}

Write-Host ""

# Step 2: Get SharePoint source details
Write-Host "Step 2: Getting SharePoint source information..." -ForegroundColor Yellow
try {
    $sources = Invoke-RestMethod -Uri "$BaseUrl/sources" -Headers $headers -ErrorAction Stop
    $sharepoint = $sources | Where-Object { $_.short_name -eq "sharepoint" }
    
    if ($sharepoint) {
        Write-Host "✅ SharePoint connector found!" -ForegroundColor Green
        Write-Host "   Name: $($sharepoint.name)" -ForegroundColor White
        Write-Host "   Auth Methods: $($sharepoint.auth_methods -join ', ')" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "❌ SharePoint connector not found" -ForegroundColor Red
        Write-Host "Available connectors:" -ForegroundColor Yellow
        $sources | Select-Object -First 10 name, short_name | Format-Table
        exit 1
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "   Authentication required. Create an API key or user first." -ForegroundColor Yellow
    }
    exit 1
}

# Step 3: Create a collection
Write-Host "Step 3: Creating a test collection..." -ForegroundColor Yellow
try {
    $collectionBody = @{
        name = "SharePoint Test Collection"
        description = "Testing SharePoint connector"
    } | ConvertTo-Json

    $collection = Invoke-RestMethod -Uri "$BaseUrl/collections" `
        -Method POST `
        -Headers $headers `
        -Body $collectionBody `
        -ErrorAction Stop

    Write-Host "✅ Collection created!" -ForegroundColor Green
    Write-Host "   Collection ID: $($collection.id)" -ForegroundColor White
    Write-Host "   Readable ID: $($collection.readable_id)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "❌ Error creating collection: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 4: Create SharePoint connection
Write-Host "Step 4: Creating SharePoint connection..." -ForegroundColor Yellow

if ($AccessToken) {
    # Option A: Use provided access token
    Write-Host "   Using OAuth token method..." -ForegroundColor Cyan
    $connectionBody = @{
        source_short_name = "sharepoint"
        collection_id = $collection.id
        name = "Test SharePoint Connection"
        auth = @{
            method = "oauth_token"
            access_token = $AccessToken
        }
        sync_immediately = $true
    } | ConvertTo-Json -Depth 10
} else {
    # Option B: OAuth browser flow
    Write-Host "   Using OAuth browser flow..." -ForegroundColor Cyan
    $connectionBody = @{
        source_short_name = "sharepoint"
        collection_id = $collection.id
        name = "Test SharePoint Connection"
        auth = @{
            method = "oauth_browser"
            redirect_url = "http://localhost:8080"
        }
        sync_immediately = $false
    } | ConvertTo-Json -Depth 10
}

try {
    $connection = Invoke-RestMethod -Uri "$BaseUrl/source-connections" `
        -Method POST `
        -Headers $headers `
        -Body $connectionBody `
        -ErrorAction Stop

    Write-Host "✅ Connection created!" -ForegroundColor Green
    Write-Host "   Connection ID: $($connection.id)" -ForegroundColor White
    
    if ($connection.auth.auth_url) {
        Write-Host ""
        Write-Host "🔐 OAuth Authentication Required:" -ForegroundColor Yellow
        Write-Host "   Visit this URL to authenticate:" -ForegroundColor White
        Write-Host "   $($connection.auth.auth_url)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "   After authentication, the connection will be ready." -ForegroundColor Gray
        Write-Host "   Then run: .\test-sharepoint.ps1 -RunSync -ConnectionId $($connection.id)" -ForegroundColor Gray
    } else {
        Write-Host "   Connection is ready!" -ForegroundColor Green
    }
    Write-Host ""
} catch {
    Write-Host "❌ Error creating connection: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response: $responseBody" -ForegroundColor Gray
    }
    exit 1
}

# Step 5: Run sync (if connection is ready and sync_immediately was true)
if ($AccessToken -or $connection.status -eq "connected") {
    Write-Host "Step 5: Running sync..." -ForegroundColor Yellow
    try {
        $syncJob = Invoke-RestMethod -Uri "$BaseUrl/source-connections/$($connection.id)/run" `
            -Method POST `
            -Headers $headers `
            -ErrorAction Stop

        Write-Host "✅ Sync started!" -ForegroundColor Green
        Write-Host "   Job ID: $($syncJob.id)" -ForegroundColor White
        Write-Host "   Status: $($syncJob.status)" -ForegroundColor White
        Write-Host ""
        Write-Host "📊 Monitor progress:" -ForegroundColor Cyan
        Write-Host "   Check job: $BaseUrl/source-connections/$($connection.id)/jobs/$($syncJob.id)" -ForegroundColor Gray
        Write-Host "   View logs: podman logs -f airweave-backend" -ForegroundColor Gray
        Write-Host ""
        Write-Host "📦 Check files in MinIO:" -ForegroundColor Cyan
        Write-Host "   Console: http://localhost:9001" -ForegroundColor Gray
        Write-Host "   Path: airweave-outbound/collections/$($collection.readable_id)/blobs/" -ForegroundColor Gray
    } catch {
        Write-Host "⚠️  Could not start sync: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ Test script completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. If OAuth flow: Visit the auth URL above" -ForegroundColor White
Write-Host "  2. Check connection status: GET $BaseUrl/source-connections/$($connection.id)" -ForegroundColor White
Write-Host "  3. Run sync: POST $BaseUrl/source-connections/$($connection.id)/run" -ForegroundColor White
Write-Host "  4. View files in MinIO console: http://localhost:9001" -ForegroundColor White

