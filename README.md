# GlueLinks API

Backend API for the ArgoCD GlueOps Extension. Provides dynamic links to Grafana dashboards, Loki logs, Tempo traces, Vault secrets, and deployment configurations.

## Features

- **APM Overview**: Application performance monitoring dashboards
- **Namespace Overview**: Kubernetes namespace dashboards
- **Pod Overview**: Individual pod metrics
- **Logs**: Loki log aggregation
- **Traces**: Tempo distributed tracing
- **Vault Secrets**: ExternalSecret vault paths
- **IaaC**: GitHub deployment configuration links

## Local Development

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- `pipenv`
- Local kubeconfig with access to cluster

### Quick Start

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Create environment file:**
   ```bash
   cp .env.local.template .env.local
   # Edit .env.local with your actual values:
   # - GRAFANA_BASE_URL (e.g., https://grafana.nonprod.antoniostacos.onglueops.com)
   # - VAULT_BASE_URL (e.g., https://vault.nonprod.antoniostacos.onglueops.com)
   ```

3. **Run locally:**
   ```bash
   make run
   ```

   This will:
   - Start Valkey in Docker
   - Export environment variables from .env.local
   - Run the API on http://localhost:8000

4. **Test the API:**
   ```bash
   # Health check
   curl http://localhost:8000/api/v1/health

   # Readiness check
   curl http://localhost:8000/api/v1/ready | jq

   # Get links for an application
   curl http://localhost:8000/api/v1/applications/taco-backend-prod/links \
     -H "Argocd-Application-Name: nonprod:taco-backend-prod" | jq
   ```

### Mock Endpoints for Extension Development

Test your ArgoCD extension UI without requiring a real Kubernetes cluster:

```bash
# All categories with data (200 OK)
curl http://localhost:8000/api/v1/fixtures/all-ok | jq

# Various error states
curl http://localhost:8000/api/v1/fixtures/errors | jq

# Partial data (some categories empty)
curl http://localhost:8000/api/v1/fixtures/partial | jq

# Slow response (3 second delay)
curl http://localhost:8000/api/v1/fixtures/slow | jq

# Mock endpoint (alias for all-ok)
curl http://localhost:8000/api/v1/mock/applications/test-app/links | jq
```

Use these endpoints to:
- Test UI rendering of different states
- Verify error handling
- Demo the extension without cluster access
- Develop offline

### Docker Testing

Test the Docker image with your local kubeconfig:

```bash
# Run the test script (handles volume mounts correctly)
./test-with-kubeconfig.sh
```

This script:
1. Copies your `~/.kube/config` to `.kubeconfig-test`
2. Mounts it into the container at `/app/kubeconfig`
3. Starts the container on port 8001
4. Tests health, readiness, and mock endpoints

**Note**: Kubernetes clusters on `127.0.0.1` (like local k3d) won't be accessible from inside the Docker container. For real K8s testing:
- Use a remote cluster, OR
- Run with `--network host`, OR
- Deploy to the actual K8s cluster

Manual Docker run example:
```bash
# Copy kubeconfig
cp ~/.kube/config .kubeconfig-test
chmod 644 .kubeconfig-test

# Run container with kubeconfig and env mounted
docker run -d --name gluelinks-test \
  -p 8001:8000 \
  --mount type=bind,source="$(pwd)/.kubeconfig-test",target=/app/kubeconfig,readonly \
  --mount type=bind,source="$(pwd)/.env.local",target=/app/.env.local,readonly \
  -e KUBECONFIG=/app/kubeconfig \
  ghcr.io/glueops/gluelinks-api:latest

# Test it
curl http://localhost:8001/api/v1/health | jq
curl http://localhost:8001/api/v1/fixtures/all-ok | jq

# Cleanup
docker stop gluelinks-test && docker rm gluelinks-test
rm .kubeconfig-test
```

**Important**: Always use `--mount type=bind` instead of `-v` for file mounts. The `-v` flag creates directories if the target doesn't exist, which breaks kubeconfig mounting.

### Local Testing (Step-by-Step)

If you need to restart or test again after cleanup:

```bash
# 1. Ensure Valkey is running
docker-compose up -d valkey

# 2. Verify Valkey is healthy
docker ps | grep valkey

# 3. Start the API (uses .env.local for environment variables)
./run-local.sh
# OR manually:
# pipenv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. In another terminal, test endpoints
curl -s http://localhost:8000/api/v1/health | jq

# 5. Test with real application
curl -s http://localhost:8000/api/v1/applications/taco-backend-prod/links \
  -H "Argocd-Application-Name: nonprod:taco-backend-prod" | jq '.categories[] | {id, label, status, link_count: (.links | length)}'

# 6. Test caching (should return same timestamp twice)
echo "First request:" && curl -s http://localhost:8000/api/v1/applications/taco-backend-prod/links \
  -H "Argocd-Application-Name: nonprod:taco-backend-prod" | jq -r '.last_updated'
sleep 1
echo "Second request (cached):" && curl -s http://localhost:8000/api/v1/applications/taco-backend-prod/links \
  -H "Argocd-Application-Name: nonprod:taco-backend-prod" | jq -r '.last_updated'

# 7. Stop when done
make stop
```

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Development Commands

```bash
make install    # Install dependencies
make run        # Start API locally
make stop       # Stop containers
make clean      # Clean up containers and volumes
make test       # Test with curl
make logs       # View Valkey logs
```

### Troubleshooting

**API won't start:**
- Ensure `.env.local` exists with proper values
- Check if port 8000 is already in use: `lsof -i :8000`
- View logs: Check terminal output or container logs

**Cache connection issues:**
- Verify Valkey is running: `docker ps | grep valkey`
- Check Valkey health: `docker exec gluelinks-valkey redis-cli ping`

**Kubernetes connection issues:**
- Verify kubeconfig is valid: `kubectl cluster-info`
- Check if you have access: `kubectl get pods -n nonprod`

## Environment Variables

### Required

- `GRAFANA_BASE_URL`: Base URL for Grafana (e.g., `https://grafana.nonprod.example.com`)
- `VAULT_BASE_URL`: Base URL for Vault (e.g., `https://vault.nonprod.example.com`)
- `VALKEY_URL`: Valkey/Redis connection URL (e.g., `redis://localhost:6379`)

### Optional

- `CACHE_TTL_SECONDS`: Cache TTL in seconds (default: `30`)
- `LOG_LEVEL`: Logging level (default: `INFO`, options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

## API Endpoints

### Health & Readiness

- `GET /api/v1/health` - Health check
- `GET /api/v1/ready` - Readiness check (validates K8s and cache connectivity)

### Links

- `GET /api/v1/applications/{app_name}/links` - Get links for an application
  - Header: `Argocd-Application-Name: {namespace}:{app_name}`

## Deployment

### Build Docker Image

```bash
docker build -t gluelinks-api:latest .
```

### Deploy to Kubernetes

1. **Update the manifest:**
   Edit `k8s/manifests.yaml` and update:
   - Image: `gluelinks-api:latest`
   - Secret values (GRAFANA_BASE_URL, VAULT_BASE_URL)

2. **Apply manifests:**
   ```bash
   kubectl apply -f k8s/manifests.yaml
   ```

This creates:
- Namespace: `gluelinks-api`
- ServiceAccount with ClusterRole for read-only access
- Valkey deployment and service
- API deployment (2 replicas) and service
- ConfigMap and Secret for configuration

### RBAC Permissions

The API requires read-only access to:
- ArgoCD Applications (`argoproj.io/applications`)
- Deployments (`apps/deployments`)
- Pods (`core/pods`)
- ExternalSecrets (`external-secrets.io/externalsecrets`)

**Note**: No access to actual Secrets is required.

## Architecture

### Service Name Extraction

Application names are parsed using regex to extract the service name:
```regex
^(?P<service_prefix>.+?)(-[0-9a-f]{9,}(-[a-z0-9]{4,})?|-[0-9]+|-[a-z0-9]{4,6})?$
```

Examples:
- `taco-backend-prod` → `taco-backend-prod`
- `taco-backend-prod-677bfb55b7-942nr` → `taco-backend-prod`

### Caching

Responses are cached in Valkey with:
- Key format: `gluelinks:v1:{namespace}:{app_name}`
- TTL: Configurable via `CACHE_TTL_SECONDS`
- `lastUpdated` field reflects cache timestamp

### Resource Discovery

Resources are discovered using ArgoCD tracking IDs:
- Deployments: `{app}:apps/Deployment:{namespace}/{name}`
- ExternalSecrets: `{app}:external-secrets.io/ExternalSecret:{namespace}/{name}`

### Logging

All logs are structured JSON with proper log levels:
- **DEBUG**: Request details, K8s queries
- **INFO**: Successful operations
- **WARNING**: Missing resources
- **ERROR**: API failures, parsing errors
- **CRITICAL**: Fatal errors

## Response Format

```json
{
  "appName": "taco-backend-prod",
  "namespace": "nonprod",
  "serviceName": "taco-backend-prod",
  "lastUpdated": "2025-12-14T00:00:00Z",
  "categories": [
    {
      "id": "apm",
      "label": "APM Overview",
      "icon": "📊",
      "status": "ok",
      "message": null,
      "links": [
        {
          "label": "Application Performance Monitoring",
          "url": "https://..."
        }
      ]
    }
  ],
  "metadata": {
    "generatedAt": "2025-12-14T00:00:00Z",
    "version": "v1",
    "resources": {
      "argocdApp": true,
      "deployment": true,
      "podsFound": 2,
      "externalSecretsFound": 1
    }
  }
}
```

### Category Status

- `ok`: Links present, everything worked
- `empty`: No resources found (legitimate, `message` field explains why)
- `error`: Something went wrong (`message` field contains error details)

## Updating Dependencies

The project uses Python 3.13 and the latest stable versions of all dependencies (as of December 2024).

To update dependencies:

```bash
# Edit Pipfile with new version constraints
nano Pipfile

# Update lock file
pipenv lock

# Install updated dependencies
pipenv install

# Test locally
pipenv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test Docker build
docker build -t test-image .

# If all tests pass, commit Pipfile and Pipfile.lock
git add Pipfile Pipfile.lock
git commit -m "chore: update dependencies"
```

**Current versions:**
- Python: 3.13
- FastAPI: 0.115.6
- Uvicorn: 0.34.0
- Kubernetes: 31.0.0
- Pydantic: 2.10.5
- Structlog: 24.4.0
- Valkey: 6.0.2

## Troubleshooting

### Docker Volume Mount Issues

**Problem**: "IsADirectoryError: [Errno 21] Is a directory: '/app/kubeconfig'"

**Solution**: Use `--mount type=bind` instead of `-v` for file mounts:
```bash
# ❌ Wrong - creates directory
-v ~/.kube/config:/app/kubeconfig:ro

# ✅ Correct - mounts file
--mount type=bind,source=$HOME/.kube/config,target=/app/kubeconfig,readonly
```

### Kubeconfig Not Found in Container

**Problem**: "Invalid kube-config file. No configuration found."

**Solutions**:
1. Ensure kubeconfig file exists before `docker run`
2. Use absolute paths in mount source
3. Verify file permissions (must be readable)
4. Check KUBECONFIG environment variable is set correctly

### Connection Refused to Kubernetes

**Problem**: "Max retries exceeded with url: /apis/... Connection refused"

**Cause**: Kubeconfig uses `127.0.0.1:6443` which isn't accessible from inside Docker container.

**Solutions**:
- Use remote cluster (not localhost)
- Run with `--network host` (Linux only)
- Deploy API to K8s cluster instead of Docker
- Update kubeconfig to use Docker-accessible IP

### Tempo Traces Links Not Working

**Problem**: Tempo links don't load traces in Grafana

**Solutions**:
1. Set `TEMPO_DATASOURCE_UID` in `.env.local`
2. Find UID in Grafana: Settings → Data Sources → Tempo → Copy UID
3. Verify service names match exactly (use full app name, not base name)

Example:
```bash
# In .env.local
TEMPO_DATASOURCE_UID=de7lydl3hl9fkd
```

## Contributing

See [CLAUDE.md](CLAUDE.md) for comprehensive project context and architecture documentation for AI assistants.

## License

[Add your license here]
