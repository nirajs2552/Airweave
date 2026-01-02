# Verify S3 Configuration Script
# Run this after configuring S3 via Frontend UI

Write-Host "`n=== S3 Configuration Verification ===" -ForegroundColor Cyan
Write-Host ""

# Check S3 status
Write-Host "📋 Checking S3 configuration status..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v1/s3/status" -Method Get -ErrorAction Stop
    
    if ($response.configured) {
        Write-Host "✅ S3 is configured!" -ForegroundColor Green
        Write-Host "   Bucket: $($response.bucket_name)" -ForegroundColor White
        Write-Host "   Region: $($response.aws_region)" -ForegroundColor White
        Write-Host "   Prefix: $($response.bucket_prefix)" -ForegroundColor White
        if ($response.endpoint_url) {
            Write-Host "   Endpoint: $($response.endpoint_url)" -ForegroundColor White
        }
        Write-Host "   Status: $($response.status)" -ForegroundColor White
        Write-Host "`n✅ S3 configuration verified successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ S3 is not configured" -ForegroundColor Red
        Write-Host "   Please configure S3 via Frontend UI or API" -ForegroundColor Yellow
        Write-Host "   See FRONTEND_S3_GUIDE.md for instructions" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Failed to check S3 status: $_" -ForegroundColor Red
    Write-Host "   Make sure the backend is running: podman ps | grep backend" -ForegroundColor Yellow
}

Write-Host ""

