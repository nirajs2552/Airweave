# PowerShell script to configure S3 via API
# Requires an API key from Frontend UI: Settings → API Keys

Write-Host "`n=== S3 Configuration via API ===" -ForegroundColor Cyan
Write-Host ""

# Get API Key
$apiKey = $env:AIRWEAVE_API_KEY
if (-not $apiKey) {
    Write-Host "🔑 API Key Required" -ForegroundColor Yellow
    Write-Host "`nTo get an API key:" -ForegroundColor White
    Write-Host "   1. Open Frontend: http://localhost:8080" -ForegroundColor Gray
    Write-Host "   2. Go to: Settings → API Keys" -ForegroundColor Gray
    Write-Host "   3. Create a new API key" -ForegroundColor Gray
    Write-Host "   4. Copy the key (you'll only see it once!)" -ForegroundColor Gray
    Write-Host ""
    $apiKey = Read-Host "Enter your API key (or set AIRWEAVE_API_KEY environment variable)"
    
    if (-not $apiKey) {
        Write-Host "❌ API key is required. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Using API key: $($apiKey.Substring(0, [Math]::Min(10, $apiKey.Length)))..." -ForegroundColor Green
Write-Host ""

# Set up headers with authentication
$headers = @{
    "Content-Type"  = "application/json"
    "Authorization" = "Bearer $apiKey"
}

# S3 Configuration (MinIO)
$s3Config = @{
    aws_access_key_id     = "minioadmin"
    aws_secret_access_key = "minioadmin"
    bucket_name           = "airweave"
    bucket_prefix         = "airweave-outbound/"
    aws_region            = "us-east-1"
    endpoint_url          = "http://minio:9000"  # Use container service name for backend
    use_ssl               = $false
}

$jsonConfig = $s3Config | ConvertTo-Json

# Step 1: Test Connection
Write-Host "📋 Step 1: Testing MinIO Connection..." -ForegroundColor Yellow
try {
    $testResponse = Invoke-RestMethod -Uri "http://localhost:8001/s3/test" `
        -Method Post `
        -Headers $headers `
        -Body $jsonConfig `
        -ErrorAction Stop
    
    Write-Host "✅ Connection test successful!" -ForegroundColor Green
    Write-Host "   Message: $($testResponse.message)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "❌ Connection test failed" -ForegroundColor Red
    $errorResponse = $_.ErrorDetails.Message
    if ($errorResponse) {
        Write-Host "   Error: $errorResponse" -ForegroundColor Yellow
    } else {
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    if ($_.Exception.Response) {
        $statusCode = [int]$_.Exception.Response.StatusCode
        Write-Host "   Status Code: $statusCode" -ForegroundColor Yellow
        
        if ($statusCode -eq 400) {
            Write-Host "`n   💡 Troubleshooting:" -ForegroundColor Cyan
            Write-Host "   - Check MinIO is running: podman ps | grep minio" -ForegroundColor White
            Write-Host "   - Verify MinIO UI: http://localhost:9001" -ForegroundColor White
            Write-Host "   - Create 'airweave' bucket in MinIO if needed" -ForegroundColor White
        }
    } else {
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   Make sure backend is running: podman ps | grep backend" -ForegroundColor Yellow
    }
    exit 1
}

# Step 2: Configure S3
Write-Host "📋 Step 2: Configuring S3 Destination..." -ForegroundColor Yellow
try {
    $configResponse = Invoke-RestMethod -Uri "http://localhost:8001/s3/configure" `
        -Method Post `
        -Headers $headers `
        -Body $jsonConfig `
        -ErrorAction Stop
    
    Write-Host "✅ S3 configuration saved successfully!" -ForegroundColor Green
    Write-Host "   Connection ID: $($configResponse.connection_id)" -ForegroundColor White
    Write-Host "   Status: $($configResponse.status)" -ForegroundColor White
    Write-Host "   Message: $($configResponse.message)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "❌ Configuration failed" -ForegroundColor Red
    $errorResponse = $_.ErrorDetails.Message
    if ($errorResponse) {
        Write-Host "   Error: $errorResponse" -ForegroundColor Yellow
    } else {
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    if ($_.Exception.Response) {
        $statusCode = [int]$_.Exception.Response.StatusCode
        Write-Host "   Status Code: $statusCode" -ForegroundColor Yellow
        
        if ($statusCode -eq 401 -or $statusCode -eq 403) {
            Write-Host "`n   ⚠️  Authentication Failed!" -ForegroundColor Yellow
            Write-Host "   The API key may be invalid or expired." -ForegroundColor White
            Write-Host "`n   To get a new API key:" -ForegroundColor Cyan
            Write-Host "   1. Open Frontend: http://localhost:8080" -ForegroundColor Gray
            Write-Host "   2. Go to: Settings → API Keys" -ForegroundColor Gray
            Write-Host "   3. Create a new API key" -ForegroundColor Gray
            Write-Host "   4. Run this script again with the new key" -ForegroundColor Gray
            Write-Host "`n   Or use Frontend UI (handles auth automatically)" -ForegroundColor Cyan
        } elseif ($statusCode -eq 400) {
            Write-Host "`n   💡 Troubleshooting:" -ForegroundColor Cyan
            Write-Host "   - Verify MinIO is accessible" -ForegroundColor White
            Write-Host "   - Check bucket name is correct" -ForegroundColor White
            Write-Host "   - Ensure credentials are correct" -ForegroundColor White
        }
    } else {
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   Make sure backend is running" -ForegroundColor Yellow
    }
    exit 1
}

# Step 3: Verification
Write-Host "📋 Step 3: Verification" -ForegroundColor Yellow
Write-Host "✅ S3 configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Verify Configuration:" -ForegroundColor Cyan
Write-Host "   1. Check MinIO UI: http://localhost:9001" -ForegroundColor White
Write-Host "      Login: minioadmin / minioadmin" -ForegroundColor Gray
Write-Host "      Verify 'airweave' bucket exists" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Check Frontend UI: http://localhost:8080" -ForegroundColor White
Write-Host "      Go to: Settings → Organization Settings" -ForegroundColor Gray
Write-Host "      S3 Event Streaming card should show 'Configured'" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Test file upload:" -ForegroundColor White
Write-Host "      Use file browser API to browse files" -ForegroundColor Gray
Write-Host "      Upload selected files to S3" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 Next Steps:" -ForegroundColor Yellow
Write-Host "   - Test file browser: GET /api/v1/file-browser/{id}/browse" -ForegroundColor White
Write-Host "   - Upload files: POST /api/v1/file-upload/{id}/upload-selected" -ForegroundColor White
Write-Host "   - See QUICK_TEST.md for API examples" -ForegroundColor White
Write-Host ""

