# PowerShell script to configure AWS S3 via API

Write-Host "`n=== AWS S3 Configuration via API ===" -ForegroundColor Cyan
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

# Get AWS S3 Credentials from environment variables or parameters
Write-Host "📋 AWS S3 Credentials:" -ForegroundColor Yellow
Write-Host ""

# Try environment variables first, then parameters, then prompt
$awsAccessKeyId = $env:AWS_ACCESS_KEY_ID
$awsSecretKeyPlain = $env:AWS_SECRET_ACCESS_KEY
$bucketName = $env:AWS_S3_BUCKET_NAME
$awsRegion = $env:AWS_REGION
$bucketPrefix = $env:AWS_S3_BUCKET_PREFIX

# Check if provided as script parameters
if ($args.Count -ge 3) {
    $awsAccessKeyId = $args[0]
    $awsSecretKeyPlain = $args[1]
    $bucketName = $args[2]
    if ($args.Count -ge 4) {
        $awsRegion = $args[3]
    }
    if ($args.Count -ge 5) {
        $bucketPrefix = $args[4]
    }
}

# Prompt if not provided
if (-not $awsAccessKeyId) {
    try {
        $awsAccessKeyId = Read-Host "AWS Access Key ID"
    } catch {
        Write-Host "❌ AWS Access Key ID is required" -ForegroundColor Red
        Write-Host "   Set environment variable: `$env:AWS_ACCESS_KEY_ID='your-key'" -ForegroundColor Yellow
        Write-Host "   Or pass as parameter: .\configure-s3-aws.ps1 'key' 'secret' 'bucket' 'region'" -ForegroundColor Yellow
        exit 1
    }
}

if (-not $awsSecretKeyPlain) {
    try {
        $awsSecretKey = Read-Host "AWS Secret Access Key" -AsSecureString
        $awsSecretKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($awsSecretKey)
        )
    } catch {
        Write-Host "❌ AWS Secret Access Key is required" -ForegroundColor Red
        Write-Host "   Set environment variable: `$env:AWS_SECRET_ACCESS_KEY='your-secret'" -ForegroundColor Yellow
        exit 1
    }
}

if (-not $bucketName) {
    try {
        $bucketName = Read-Host "S3 Bucket Name"
    } catch {
        Write-Host "❌ Bucket name is required" -ForegroundColor Red
        Write-Host "   Set environment variable: `$env:AWS_S3_BUCKET_NAME='your-bucket'" -ForegroundColor Yellow
        exit 1
    }
}

if (-not $awsRegion) {
    try {
        $awsRegion = Read-Host "AWS Region (e.g., us-east-1)"
    } catch {
        $awsRegion = "us-east-1"
    }
    if (-not $awsRegion) {
        $awsRegion = "us-east-1"
    }
    Write-Host "   Using region: $awsRegion" -ForegroundColor Gray
}

if (-not $bucketPrefix) {
    try {
        $bucketPrefix = Read-Host "Bucket Prefix (default: airweave-outbound/)"
    } catch {
        $bucketPrefix = "airweave-outbound/"
    }
    if (-not $bucketPrefix) {
        $bucketPrefix = "airweave-outbound/"
    }
}

# Set up headers with authentication
$headers = @{
    "Content-Type"  = "application/json"
    "Authorization" = "Bearer $apiKey"
}

# AWS S3 Configuration
$s3Config = @{
    aws_access_key_id     = $awsAccessKeyId
    aws_secret_access_key = $awsSecretKeyPlain
    bucket_name           = $bucketName
    bucket_prefix         = $bucketPrefix
    aws_region            = $awsRegion
    endpoint_url          = $null  # Empty for AWS S3 (uses default endpoints)
    use_ssl               = $true  # Always use SSL for AWS S3
}

$jsonConfig = $s3Config | ConvertTo-Json -Depth 10

# Step 1: Test Connection
Write-Host "`n📋 Step 1: Testing AWS S3 Connection..." -ForegroundColor Yellow
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
    if ($_.ErrorDetails.Message) {
        $errorResponse = $_.ErrorDetails.Message
        try {
            $errorJson = $errorResponse | ConvertFrom-Json
            Write-Host "   Error: $($errorJson.detail)" -ForegroundColor Yellow
        } catch {
            Write-Host "   Error: $errorResponse" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    if ($_.Exception.Response) {
        $statusCode = [int]$_.Exception.Response.StatusCode
        Write-Host "   Status Code: $statusCode" -ForegroundColor Yellow
        
        if ($statusCode -eq 400) {
            Write-Host "`n   💡 Troubleshooting:" -ForegroundColor Cyan
            Write-Host "   - Verify AWS credentials are correct" -ForegroundColor White
            Write-Host "   - Check bucket name is correct" -ForegroundColor White
            Write-Host "   - Ensure bucket exists in the specified region" -ForegroundColor White
            Write-Host "   - Verify IAM user has S3 read/write permissions" -ForegroundColor White
        }
    }
    exit 1
}

# Step 2: Configure S3
Write-Host "📋 Step 2: Configuring AWS S3 Destination..." -ForegroundColor Yellow
try {
    $configResponse = Invoke-RestMethod -Uri "http://localhost:8001/s3/configure" `
        -Method Post `
        -Headers $headers `
        -Body $jsonConfig `
        -ErrorAction Stop
    
    Write-Host "✅ AWS S3 configuration saved successfully!" -ForegroundColor Green
    Write-Host "   Connection ID: $($configResponse.connection_id)" -ForegroundColor White
    Write-Host "   Status: $($configResponse.status)" -ForegroundColor White
    Write-Host "   Message: $($configResponse.message)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "❌ Configuration failed" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        $errorResponse = $_.ErrorDetails.Message
        try {
            $errorJson = $errorResponse | ConvertFrom-Json
            Write-Host "   Error: $($errorJson.detail)" -ForegroundColor Yellow
        } catch {
            Write-Host "   Error: $errorResponse" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    if ($_.Exception.Response) {
        $statusCode = [int]$_.Exception.Response.StatusCode
        Write-Host "   Status Code: $statusCode" -ForegroundColor Yellow
        
        if ($statusCode -eq 401 -or $statusCode -eq 403) {
            Write-Host "`n   ⚠️  Authentication Failed!" -ForegroundColor Yellow
            Write-Host "   The API key may be invalid or expired." -ForegroundColor White
        } elseif ($statusCode -eq 400) {
            Write-Host "`n   💡 Troubleshooting:" -ForegroundColor Cyan
            Write-Host "   - Verify AWS credentials are correct" -ForegroundColor White
            Write-Host "   - Check bucket name and region" -ForegroundColor White
            Write-Host "   - Ensure IAM user has S3 permissions" -ForegroundColor White
        }
    }
    exit 1
}

# Step 3: Verification
Write-Host "📋 Step 3: Verification" -ForegroundColor Yellow
Write-Host "✅ AWS S3 configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Verify Configuration:" -ForegroundColor Cyan
Write-Host "   1. Check Frontend UI: http://localhost:8080" -ForegroundColor White
Write-Host "      Go to: Settings → Organization Settings" -ForegroundColor Gray
Write-Host "      S3 Event Streaming card should show 'Configured'" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Test file upload:" -ForegroundColor White
Write-Host "      Use file browser API to browse SharePoint files" -ForegroundColor Gray
Write-Host "      Upload selected files to S3" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Check AWS S3 Console:" -ForegroundColor White
Write-Host "      Verify files appear in: s3://$bucketName/$bucketPrefix" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 Next Steps:" -ForegroundColor Yellow
Write-Host "   - Test file browser: GET /api/v1/file-browser/{id}/browse" -ForegroundColor White
Write-Host "   - Upload files: POST /api/v1/file-upload/{id}/upload-selected" -ForegroundColor White
Write-Host "   - See QUICK_TEST.md for API examples" -ForegroundColor White
Write-Host ""

# Clear sensitive data from memory
$awsSecretKeyPlain = $null
$awsSecretKey = $null

