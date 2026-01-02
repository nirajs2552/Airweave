# How to Get an API Key

Follow these steps to get an API key from the Frontend UI:

## Step-by-Step Instructions

### 1. Open the Frontend
Navigate to: **http://localhost:8080**

### 2. Navigate to API Keys Settings

**Path:**
```
Frontend → User Menu (top right) → Settings → API Keys
```

Or directly: **http://localhost:8080/organization/settings** → API Keys tab

### 3. Create a New API Key

1. Click **"Create API Key"** or **"New API Key"** button
2. Enter a name for the key (e.g., "S3 Configuration Key")
3. Click **"Create"** or **"Generate"**
4. **IMPORTANT:** Copy the API key immediately - you'll only see it once!
5. Store it securely

### 4. Use the API Key

You can use the API key in two ways:

#### Option A: Environment Variable (Recommended)
```powershell
# Set environment variable
$env:AIRWEAVE_API_KEY = "your-api-key-here"

# Run the script (it will use the env var)
.\configure-s3-api.ps1
```

#### Option B: Enter When Prompted
```powershell
# Just run the script
.\configure-s3-api.ps1

# It will prompt you for the API key
```

#### Option C: Manual API Calls
```powershell
$apiKey = "your-api-key-here"
$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $apiKey"
}

# Use in API calls
Invoke-RestMethod -Uri "http://localhost:8001/api/v1/s3/configure" `
    -Method Post -Headers $headers -Body $jsonConfig
```

## Security Notes

- ⚠️ **API keys are sensitive** - treat them like passwords
- ⚠️ **Never commit API keys to version control**
- ⚠️ **Rotate keys regularly**
- ⚠️ **Delete unused keys**

## Troubleshooting

### Can't Find API Keys Section
- Make sure you're logged in
- Check you have the right permissions
- Try refreshing the page

### Key Not Working
- Verify the key was copied correctly (no extra spaces)
- Check if the key has expired
- Create a new key and try again

### Key Works But API Calls Fail
- Check the Authorization header format: `Bearer YOUR_KEY`
- Verify the backend is running
- Check backend logs for errors

## Alternative: Use Frontend UI

If getting an API key is too complex, use the Frontend UI instead:
- No API key needed
- Handles authentication automatically
- Visual feedback

See `FRONTEND_S3_GUIDE.md` for Frontend UI instructions.

