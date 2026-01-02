# Quick Start Guide - Connector Service

## Prerequisites

1. **Start Docker Desktop** - Make sure Docker Desktop is running on Windows
2. **Required Environment Variables** - Create a `.env` file with minimum required variables

## Step 1: Start Docker Desktop

Open Docker Desktop application on Windows and wait for it to fully start (whale icon in system tray should be steady).

## Step 2: Create .env File

The `.env` file needs these minimum variables for connector-only mode:

```env
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=airweave
POSTGRES_USER=airweave
POSTGRES_PASSWORD=airweave1234!

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Encryption (required)
ENCRYPTION_KEY=<generate-with-openssl-rand-base64-32>
STATE_SECRET=<generate-with-openssl-rand-base64-32>

# Temporal (optional, for sync orchestration)
TEMPORAL_HOST=temporal
TEMPORAL_PORT=7233
TEMPORAL_NAMESPACE=default
TEMPORAL_ENABLED=true

# Application
ENVIRONMENT=local
LOCAL_DEVELOPMENT=true
RUN_ALEMBIC_MIGRATIONS=true
RUN_DB_SYNC=true
```

## Step 3: Start Services

```bash
# Using dev compose (simpler, includes MinIO for S3)
docker compose -f docker/docker-compose.dev.yml up -d
```

## Step 4: Check Service Status

```bash
# Check all services
docker compose -f docker/docker-compose.dev.yml ps

# Check backend logs
docker logs airweave-backend

# Check if backend is healthy
curl http://localhost:8001/health
```

## Step 5: Access Services

- **Frontend UI**: http://localhost:8080
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **MinIO (S3)**: http://localhost:9001 (Console) / http://localhost:9000 (API)
  - Default credentials: `airweave` / `airweave-dev-password`
- **Temporal UI**: http://localhost:8088
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Step 6: Test Connector Service

### 1. List Available Connectors
```bash
curl http://localhost:8001/api/v1/sources/
```

### 2. Create a Source Connection
```bash
curl -X POST http://localhost:8001/api/v1/source-connections/ \
  -H "Content-Type: application/json" \
  -d '{
    "source_short_name": "sharepoint",
    "collection_id": "<your-collection-id>",
    "auth": {
      "method": "oauth_browser",
      "redirect_url": "http://localhost:8080"
    }
  }'
```

### 3. Run a Sync
```bash
curl -X POST http://localhost:8001/api/v1/source-connections/{connection-id}/run
```

## Troubleshooting

### Docker Desktop Not Running
- Open Docker Desktop application
- Wait for it to fully start (check system tray)

### Backend Won't Start
```bash
# Check logs
docker logs airweave-backend

# Common issues:
# - Missing ENCRYPTION_KEY or STATE_SECRET in .env
# - Database connection issues
# - Port conflicts (8001, 5432, 6379 already in use)
```

### Services Not Healthy
```bash
# Restart all services
docker compose -f docker/docker-compose.dev.yml restart

# Or rebuild and restart
docker compose -f docker/docker-compose.dev.yml up -d --build
```

### Stop All Services
```bash
docker compose -f docker/docker-compose.dev.yml down
```

### Clean Start (Remove All Data)
```bash
docker compose -f docker/docker-compose.dev.yml down -v
docker compose -f docker/docker-compose.dev.yml up -d
```

## What's Running?

In connector-only mode, these services are active:
- ✅ **PostgreSQL** - Metadata storage
- ✅ **Redis** - Pub/sub for sync progress
- ✅ **Backend** - FastAPI connector service
- ✅ **Temporal** - Sync orchestration
- ✅ **MinIO** - S3-compatible storage
- ❌ **Qdrant** - Removed (vector DB not needed)
- ❌ **text2vec-transformers** - Removed (embeddings not needed)
- ✅ **Frontend** - React UI at http://localhost:8080

