# Frontend Local Development (Self-Hosting Mode)

Run the frontend locally from source code to see your changes immediately, including the S3 configuration UI.

## Prerequisites

- **Node.js** v18 or higher
- **npm** or **bun** package manager
- Backend running at `http://localhost:8001`

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
# or
bun install
```

### 2. Set Environment Variables

Create a `.env` file in the `frontend` directory (or set environment variables):

```bash
# Frontend .env file
VITE_API_URL=http://localhost:8001
VITE_ENABLE_AUTH=false
```

**Note:** The frontend reads from `window.config` (from `public/config.js`) or environment variables. For local dev, environment variables work best.

### 3. Start Development Server

```bash
npm run dev
# or
bun run dev
```

The frontend will start at: **http://localhost:8080** (or another port if 8080 is in use)

### 4. Access the Frontend

Open your browser and navigate to:
- **http://localhost:8080**

## Configuration

### API URL

The frontend needs to know where the backend API is. It looks for:

1. `window.config.API_URL` (from `public/config.js`)
2. `VITE_API_URL` environment variable
3. Defaults to `http://localhost:8001`

### Authentication

For local development with `AUTH_ENABLED=false` in backend:
- Set `VITE_ENABLE_AUTH=false` in frontend
- Or modify `public/config.js`:
  ```javascript
  window.config = {
    API_URL: "http://localhost:8001",
    ENABLE_AUTH: false
  };
  ```

## What's Different in Local Dev?

✅ **S3 Configuration UI** - Always visible (feature flag bypassed)
✅ **Hot Reload** - Changes reflect immediately
✅ **Source Maps** - Better debugging
✅ **Local Code** - Your changes are live

## Troubleshooting

### Port Already in Use

If port 8080 is in use:
- The dev server will automatically use the next available port
- Check the terminal output for the actual port
- Or stop the containerized frontend: `podman stop airweave-frontend`

### API Connection Issues

- Verify backend is running: `curl http://localhost:8001/health`
- Check CORS settings if you see CORS errors
- Verify `VITE_API_URL` is set correctly

### Dependencies Issues

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Build Errors

```bash
# Check Node.js version
node --version  # Should be v18+

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

## Running Both (Container + Local)

You can run both the containerized frontend and local dev server:

1. **Stop containerized frontend:**
   ```bash
   podman stop airweave-frontend
   ```

2. **Start local dev server:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access local frontend:** http://localhost:8080

## Development Workflow

1. Make changes to frontend code
2. Save file
3. Vite automatically reloads
4. See changes immediately in browser

## Next Steps

After starting the local frontend:
1. ✅ Navigate to Settings → Organization Settings
2. ✅ You should see "S3 Event Streaming" card (always visible in local dev)
3. ✅ Configure S3 with MinIO credentials
4. ✅ Test file browser and upload features

## Stopping

Press `Ctrl+C` in the terminal running `npm run dev` to stop the development server.

