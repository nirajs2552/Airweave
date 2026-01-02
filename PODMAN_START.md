# Running Airweave Connector Service with Podman

## ✅ Infrastructure Services Running

All infrastructure services are now running with Podman:

- **PostgreSQL**: `localhost:5433` (mapped from container port 5432)
- **Redis**: `localhost:6380` (mapped from container port 6379)
- **Temporal**: `localhost:7233` (UI at `localhost:8088`)
- **MinIO (S3)**: `localhost:9000` (Console at `localhost:9001`)
  - Username: `airweave`
  - Password: `airweave-dev-password`

## Starting the Backend Service

The backend service should be run separately. You have two options:

### Option 1: Run Backend with Python (Recommended for Development)

```powershell
cd backend
poetry install
poetry run uvicorn airweave.main:app --host 0.0.0.0 --port 8001 --reload
```

### Option 2: Run Backend with Podman

If you want to run the backend in a container:

```powershell
# Build the backend image
podman build -t airweave-backend -f backend/Dockerfile backend/

# Run the backend container
podman run -d \
  --name airweave-backend \
  -p 8001:8001 \
  --env-file .env \
  -e POSTGRES_HOST=host.containers.internal \
  -e POSTGRES_PORT=5433 \
  -e REDIS_HOST=host.containers.internal \
  -e REDIS_PORT=6380 \
  -e TEMPORAL_HOST=host.containers.internal \
  airweave-backend
```

## Access Points

Once the backend is running:

- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **MinIO Console**: http://localhost:9001
- **Temporal UI**: http://localhost:8088

## Managing Services

### Check Status
```powershell
podman compose -f docker/docker-compose.dev.yml ps
```

### View Logs
```powershell
# All services
podman compose -f docker/docker-compose.dev.yml logs

# Specific service
podman logs airweave-db
podman logs airweave-redis
podman logs airweave-temporal
podman logs airweave-minio
```

### Stop Services
```powershell
podman compose -f docker/docker-compose.dev.yml down
```

### Stop and Remove Volumes (Clean Start)
```powershell
podman compose -f docker/docker-compose.dev.yml down -v
```

## Port Mappings

Due to existing services on your system, ports were changed:

| Service | Container Port | Host Port |
|---------|---------------|-----------|
| PostgreSQL | 5432 | 5433 |
| Redis | 6379 | 6380 |
| Temporal | 7233 | 7233 |
| Temporal UI | 8080 | 8088 |
| MinIO API | 9000 | 9000 |
| MinIO Console | 9001 | 9001 |
| Backend API | 8001 | 8001 |

## Environment Variables

The `.env` file has been configured with:
- `POSTGRES_HOST=localhost` (use `host.containers.internal` if backend runs in container)
- `POSTGRES_PORT=5433`
- `REDIS_HOST=localhost` (use `host.containers.internal` if backend runs in container)
- `REDIS_PORT=6380`
- `ENCRYPTION_KEY` (auto-generated)
- `STATE_SECRET` (auto-generated)
- `FIRST_SUPERUSER` and `FIRST_SUPERUSER_PASSWORD`

## Testing the Service

Once the backend is running, test it:

```powershell
# Health check
curl http://localhost:8001/health

# List available connectors
curl http://localhost:8001/api/v1/sources/
```

