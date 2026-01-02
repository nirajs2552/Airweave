# Simple SharePoint Connection Test
# This script tests SharePoint connector step by step

$baseUrl = "http://localhost:8001"

Write-Host "=== SharePoint Connection Test ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify SharePoint connector exists
Write-Host "Step 1: Checking SharePoint connector..." -ForegroundColor Yellow
try {
    $sources = Invoke-RestMethod -Uri "$baseUrl/sources"
    $sharepoint = $sources | Where-Object { $_.short_name -eq "sharepoint" }
    if ($sharepoint) {
        Write-Host "✅ SharePoint connector found!" -ForegroundColor Green
        Write-Host "   Name: $($sharepoint.name)" -ForegroundColor White
        Write-Host "   Auth Methods: $($sharepoint.auth_methods -join ', ')" -ForegroundColor White
    } else {
        Write-Host "❌ SharePoint connector not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Create collection
Write-Host "Step 2: Creating collection..." -ForegroundColor Yellow
try {
    $collectionBody = @{
        name = "SharePoint Test Collection"
    } | ConvertTo-Json

    $collection = Invoke-RestMethod -Uri "$baseUrl/collections" `
        -Method POST `
        -ContentType "application/json" `
        -Body $collectionBody

    Write-Host "✅ Collection created!" -ForegroundColor Green
    Write-Host "   ID: $($collection.id)" -ForegroundColor White
    Write-Host "   Readable ID: $($collection.readable_id)" -ForegroundColor White
    $collectionId = $collection.readable_id
} catch {
    Write-Host "❌ Error creating collection: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Check backend logs: podman logs airweave-backend" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 3: Create SharePoint connection
Write-Host "Step 3: Creating SharePoint connection..." -ForegroundColor Yellow
Write-Host "   Method: OAuth Browser (will return auth URL)" -ForegroundColor Gray

try {
    $connectionBody = @{
        short_name = "sharepoint"
        readable_collection_id = $collectionId
        name = "Test SharePoint Connection"
        authentication = @{
            method = "oauth_browser"
            redirect_url = "http://localhost:8080"
        }
    } | ConvertTo-Json -Depth 10

    $connection = Invoke-RestMethod -Uri "$baseUrl/source-connections" `
        -Method POST `
        -ContentType "application/json" `
        -Body $connectionBody

    Write-Host "✅ Connection created!" -ForegroundColor Green
    Write-Host "   Connection ID: $($connection.id)" -ForegroundColor White
    Write-Host "   Status: $($connection.status)" -ForegroundColor White

    if ($connection.authentication -and $connection.authentication.auth_url) {
        Write-Host ""
        Write-Host "🔐 OAuth Authentication Required" -ForegroundColor Yellow
        Write-Host "   Visit this URL to authenticate with Microsoft:" -ForegroundColor White
        Write-Host "   $($connection.authentication.auth_url)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "   After authentication, you'll be redirected back." -ForegroundColor Gray
        Write-Host "   Then the connection will be ready to use." -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Error creating connection: $($_.Exception.Message)" -ForegroundColor Red
    
    # Try to get error details
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   Status Code: $statusCode" -ForegroundColor Yellow
        
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorStream)
            $errorBody = $reader.ReadToEnd()
            Write-Host "   Error Details: $errorBody" -ForegroundColor Gray
        } catch {
            # PowerShell's Invoke-RestMethod doesn't expose response stream easily
            Write-Host "   Check API docs at: $baseUrl/docs" -ForegroundColor Yellow
        }
    }
    exit 1
}

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. If OAuth flow: Visit the auth URL above" -ForegroundColor White
Write-Host "2. Check connection status:" -ForegroundColor White
Write-Host "   Invoke-RestMethod -Uri '$baseUrl/source-connections/$($connection.id)'" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Once connected, run a sync:" -ForegroundColor White
Write-Host "   `$syncJob = Invoke-RestMethod -Uri '$baseUrl/source-connections/$($connection.id)/run' -Method POST" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Monitor sync progress:" -ForegroundColor White
Write-Host "   podman logs -f airweave-backend" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Check files in MinIO:" -ForegroundColor White
Write-Host "   http://localhost:9001" -ForegroundColor Gray
Write-Host "   Path: airweave-outbound/collections/$collectionId/blobs/" -ForegroundColor Gray

