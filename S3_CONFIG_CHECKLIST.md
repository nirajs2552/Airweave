# S3 Configuration Checklist

Quick checklist for configuring S3 via Frontend UI.

## Pre-flight Check

- [ ] Frontend is running: http://localhost:8080
- [ ] MinIO is running: http://localhost:9001
- [ ] Backend is running: http://localhost:8001

## Configuration Steps

### Step 1: Open Frontend
- [ ] Open browser
- [ ] Navigate to: **http://localhost:8080**

### Step 2: Navigate to Settings
- [ ] Click user/profile menu (top-right)
- [ ] Select "Settings" or "Organization Settings"
- [ ] OR go directly to: **http://localhost:8080/organization/settings**

### Step 3: Find S3 Section
- [ ] Scroll down on Settings page
- [ ] Look for **"S3 Event Streaming"** card
- [ ] If not visible, use API method (see FRONTEND_S3_GUIDE.md)

### Step 4: Open Configuration Modal
- [ ] Click **"Configure S3 Destination"** button
- [ ] Modal dialog opens

### Step 5: Fill in Credentials

Fill in these exact values:

- [ ] **AWS Access Key ID**: `minioadmin`
- [ ] **AWS Secret Access Key**: `minioadmin`
- [ ] **Bucket Name**: `airweave`
- [ ] **Bucket Prefix**: `airweave-outbound/`
- [ ] **AWS Region**: `us-east-1`
- [ ] **Custom Endpoint URL**: `http://localhost:9000`
- [ ] **Use SSL/TLS**: ☐ **Unchecked** (important for local MinIO!)

### Step 6: Test Connection
- [ ] Click **"Test Connection"** button
- [ ] Wait for success message (green checkmark)
- [ ] If fails, check MinIO is running

### Step 7: Save Configuration
- [ ] Click **"Save Configuration"** button
- [ ] Wait for success notification
- [ ] Modal closes automatically

### Step 8: Verify
- [ ] S3 Event Streaming card shows **"Configured"**
- [ ] Bucket name displayed: `airweave`
- [ ] Region displayed: `us-east-1`

## Troubleshooting

### S3 Card Not Visible
**Solution:** Use API method (see FRONTEND_S3_GUIDE.md Alternative section)

### Connection Test Fails
1. Check MinIO is running:
   ```bash
   podman ps | grep minio
   ```
2. Open MinIO UI: http://localhost:9001
3. Login: `minioadmin` / `minioadmin`
4. Create bucket `airweave` if it doesn't exist

### Save Fails
1. Check backend logs:
   ```bash
   podman logs -f airweave-backend
   ```
2. Verify backend is accessible:
   ```bash
   curl http://localhost:8001/health
   ```

## Next Steps

After S3 is configured:
- [ ] Test file browser API
- [ ] Upload files to S3
- [ ] Verify files in MinIO UI

See `QUICK_TEST.md` for API testing examples.

