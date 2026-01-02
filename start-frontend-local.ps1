# PowerShell script to start frontend in local development mode

Write-Host "`n=== Starting Frontend in Local Development Mode ===" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the frontend directory
if (-not (Test-Path "package.json")) {
    Write-Host "⚠️  Not in frontend directory. Changing to frontend..." -ForegroundColor Yellow
    if (Test-Path "frontend/package.json") {
        Set-Location frontend
    } else {
        Write-Host "❌ Error: Cannot find frontend directory or package.json" -ForegroundColor Red
        exit 1
    }
}

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        npm install
    } elseif (Get-Command bun -ErrorAction SilentlyContinue) {
        bun install
    } else {
        Write-Host "❌ Error: npm or bun not found. Please install Node.js first." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}

# Check if containerized frontend is running
Write-Host "`n🔍 Checking for containerized frontend..." -ForegroundColor Yellow
$frontendContainer = podman ps --filter "name=airweave-frontend" --format "{{.Names}}" 2>$null
if ($frontendContainer) {
    Write-Host "⚠️  Containerized frontend is running. Stopping it..." -ForegroundColor Yellow
    podman stop airweave-frontend 2>$null
    Write-Host "✅ Containerized frontend stopped" -ForegroundColor Green
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "`n📝 Creating .env file..." -ForegroundColor Yellow
    @"
VITE_API_URL=http://localhost:8001
VITE_ENABLE_AUTH=false
VITE_LOCAL_DEVELOPMENT=true
"@ | Out-File -FilePath ".env" -Encoding utf8
    Write-Host "✅ Created .env file" -ForegroundColor Green
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

# Start development server
Write-Host "`n🚀 Starting development server..." -ForegroundColor Cyan
Write-Host "   Frontend will be available at: http://localhost:8080" -ForegroundColor White
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

if (Get-Command npm -ErrorAction SilentlyContinue) {
    npm run dev
} elseif (Get-Command bun -ErrorAction SilentlyContinue) {
    bun run dev
} else {
    Write-Host "❌ Error: npm or bun not found" -ForegroundColor Red
    exit 1
}

