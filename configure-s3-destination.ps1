# Configure S3 Destination (MinIO) for Airweave
# This script configures MinIO as the S3 destination for syncing files

$baseUrl = "http://localhost:8001"

Write-Host "=== Configure S3 Destination (MinIO) ===" -ForegroundColor Cyan
Write-Host ""

# MinIO Configuration (from docker-compose.dev.yml)
# Note: endpoint_url should be accessible from backend container
# Backend uses 'minio' as hostname, but we configure it here
$s3Config = @{
    bucket_name = "airweave-outbound"
    bucket_prefix = ""
    aws_region = "us-east-1"
    endpoint_url = "http://minio:9000"  # Container network name (backend accesses via this)
    use_ssl = $false
    aws_access_key_id = "airweave"
    aws_secret_access_key = "airweave-dev-password"
} | ConvertTo-Json -Depth 10

Write-Host "Configuring S3 destination with MinIO..." -ForegroundColor Yellow
Write-Host "  Bucket: $($s3Config.bucket_name)" -ForegroundColor Gray
Write-Host "  Endpoint: $($s3Config.endpoint_url)" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/s3/configure" `
        -Method POST `
        -ContentType "application/json" `
        -Body $s3Config `
        -ErrorAction Stop

    Write-Host "✅ S3 destination configured successfully!" -ForegroundColor Green
    Write-Host "   Connection ID: $($response.connection_id)" -ForegroundColor White
    Write-Host "   Status: $($response.status)" -ForegroundColor White
    Write-Host "   Message: $($response.message)" -ForegroundColor White
    Write-Host ""
    Write-Host "🎉 You can now sync files to S3!" -ForegroundColor Green
} catch {
    Write-Host "❌ Error configuring S3: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "   Status Code: $statusCode" -ForegroundColor Yellow
        
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorStream)
            $errorBody = $reader.ReadToEnd()
            Write-Host "   Error Details: $errorBody" -ForegroundColor Gray
        } catch {
            Write-Host "   Check API docs at: $baseUrl/docs" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "Note: You may need to enable the S3_DESTINATION feature flag" -ForegroundColor Yellow
    Write-Host "      or configure S3 through the frontend UI." -ForegroundColor Yellow
}

