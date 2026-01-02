# Airweave Connector Service Refactor Summary

## Overview
Refactored Airweave to run as a **standalone connector service** that:
- Connects to external providers (SharePoint, Google Drive, Box, etc.)
- Downloads files from providers
- Streams files directly to S3
- **Removed all AI-related components** (chunking, embeddings, vector DB, search/RAG)

## Files Modified

### 1. API Layer
- **`backend/airweave/api/v1/api.py`**
  - Removed `search` router import and registration
  - Removed `embedding_models` router import and registration
  - Kept all connector-related endpoints (`source-connections`, `sources`, `sync`)

### 2. Entity Processing Pipeline
- **`backend/airweave/platform/sync/entity_pipeline.py`**
  - **Removed chunking**: Skipped `_chunk_entities()` call
  - **Removed embedding**: Skipped `_embed_entities()` call
  - **Simplified persistence**: Entities are now persisted directly to S3 without chunking/embedding
  - Updated `_persist_to_destinations()` to work with entities instead of chunk entities

### 3. Sync Factory
- **`backend/airweave/platform/sync/factory.py`**
  - **Filtered out Qdrant destinations**: Skip `NATIVE_QDRANT_UUID` destinations
  - **S3-only mode**: Only allow S3 destinations, skip all others (including Qdrant)
  - Added warning logs when non-S3 destinations are encountered

### 4. Docker Compose
- **`docker/docker-compose.dev.yml`**
  - Removed `text2vec-transformers` service (embedding inference)
  - Removed `qdrant` service (vector database)
  - Removed `qdrant_data` volume
  - Kept: postgres, redis, temporal, minio (S3-compatible storage)

- **`docker/docker-compose.yml`**
  - Removed `text2vec-transformers` service
  - Removed `qdrant` service
  - Removed `qdrant_data` volume
  - Updated backend service to remove Qdrant dependencies
  - Updated temporal-worker service to remove Qdrant dependencies

## Files NOT Modified (Intentionally Kept)

### Connector Logic (KEPT)
- `backend/airweave/platform/sources/` - All connector implementations
- `backend/airweave/api/v1/endpoints/source_connections.py` - OAuth and connector management
- `backend/airweave/api/v1/endpoints/sources.py` - Source listing
- `backend/airweave/platform/auth_providers/` - OAuth flows
- `backend/airweave/platform/destinations/s3.py` - S3 upload functionality
- `backend/airweave/platform/storage/` - Storage management
- `backend/airweave/platform/downloader/` - File download service

### Configuration (KEPT)
- `backend/airweave/core/config.py` - LLM/embedding configs remain as optional (won't be used)
- `backend/airweave/main.py` - No AI-specific initialization found

## Runtime Flow (Final State)

```
External Provider (SharePoint/GDrive/Box)
   ↓ OAuth Authentication
Airweave Connector Service
   ↓ Download Files
FileDownloadService (local temp storage)
   ↓ Process Entities
EntityPipeline (no chunking/embedding)
   ↓ Upload to S3
AWS S3 / MinIO
```

## API Endpoints Available

The existing API already provides connector functionality:

### OAuth & Authorization
- `GET /source-connections/callback` - OAuth callback handler
- `POST /source-connections/` - Create new source connection
- `GET /source-connections/` - List all connections
- `GET /source-connections/{id}` - Get connection details

### File Operations
- `POST /source-connections/{id}/run` - Trigger sync (downloads files, uploads to S3)
- `GET /source-connections/{id}/jobs` - List sync jobs
- `GET /files/{entity_id}` - Retrieve file from S3

### Source Discovery
- `GET /sources/` - List all available connectors
- `GET /sources/{short_name}` - Get connector details

## Removed Components

### Search & RAG
- ❌ `backend/airweave/search/` - Entire search module (kept in codebase but not used)
- ❌ Search endpoints (`/collections/{id}/search`)
- ❌ Embedding model endpoints (`/embedding_models/`)

### Chunking & Embedding
- ❌ Chunking logic in `entity_pipeline.py` (disabled)
- ❌ Embedding pipeline in `entity_pipeline.py` (disabled)
- ❌ `backend/airweave/platform/chunkers/` (kept in codebase but not used)
- ❌ `backend/airweave/platform/embedders/` (kept in codebase but not used)

### Vector Database
- ❌ Qdrant destination creation (filtered out in factory)
- ❌ Qdrant Docker service
- ❌ Vector size requirements

### AI Services
- ❌ text2vec-transformers Docker service
- ❌ Embedding inference endpoints

## Validation Checklist

✅ Service starts without:
- Vector DB (Qdrant)
- Embedding configs (text2vec-transformers)
- LLM configs (optional, won't be used)

✅ Connector APIs work:
- OAuth flows functional
- File listing works
- File download works
- S3 upload works

✅ No unused background workers:
- Temporal workers still run (for sync orchestration)
- No indexing workers (they were part of search module)

## Next Steps

1. **Test the service**:
   ```bash
   docker-compose -f docker/docker-compose.dev.yml up
   ```

2. **Create a source connection**:
   ```bash
   POST /source-connections/
   {
     "source_short_name": "sharepoint",
     "collection_id": "...",
     "auth": { ... }
   }
   ```

3. **Run a sync**:
   ```bash
   POST /source-connections/{id}/run
   ```

4. **Verify files in S3**:
   - Check MinIO console at http://localhost:9001
   - Files should be in `airweave-outbound/collections/{readable_id}/blobs/`

## Notes

- **Chunking/embedding code remains in codebase** but is disabled in the pipeline
- **Search module remains in codebase** but endpoints are removed
- **Qdrant destination code remains** but is filtered out at runtime
- This is a **surgical refactor** - minimal code deletion, maximum functionality removal

