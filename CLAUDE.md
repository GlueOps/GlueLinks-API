# Claude Context: GlueLinks-API

## Project Overview
FastAPI backend that serves dynamic links for ArgoCD extension UI. Generates links to Grafana dashboards, Loki logs, Tempo traces, Vault secrets, and GitHub IaaC repos based on Kubernetes resource discovery.

## Architecture Quick Reference

### Core Flow
1. ArgoCD extension calls API with app name + namespace in headers
2. API queries K8s for ArgoCD Application manifest
3. Discovers related resources via tracking IDs
4. Generates 7 categories of links (APM, Namespace, Pod, Logs, Traces, Vault, IaaC)
5. Caches response in Valkey for 30s

### Key Files
- `app/main.py` - FastAPI app, endpoints: /health, /ready, /applications/{app_name}/links, /fixtures/{name}, /mock/applications/{app_name}/links
- `app/links_generator.py` - Link generation logic, 7 categories, handles missing resources gracefully
- `app/k8s_client.py` - K8s API wrapper, uses tracking IDs: `argocd.argoproj.io/tracking-id: {app}:{group}/{kind}:{namespace}/{name}`
- `app/cache.py` - Valkey cache wrapper, 30s TTL, key format: `gluelinks:v1:{namespace}:{app_name}`
- `app/config.py` - Pydantic settings, env vars: GRAFANA_BASE_URL, VAULT_BASE_URL, VALKEY_URL, TEMPO_DATASOURCE_UID
- `app/fixtures.py` - Mock data for extension testing (all-ok, errors, partial, slow scenarios)
- `app/models.py` - Pydantic response models

### Dependencies (Latest as of Dec 2024)
- Python 3.13
- FastAPI 0.115.6
- Uvicorn 0.34.0
- Kubernetes 31.0.0
- Pydantic 2.10.5
- Structlog 24.4.0
- Valkey 6.0.2

## Common Tasks

### Running Locally
```bash
# Start Valkey cache
docker-compose up -d valkey

# Copy environment template
cp .env.local.template .env.local
# Edit .env.local with your values

# Install dependencies
pipenv install

# Run API
pipenv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing Docker Image with Kubernetes
```bash
# Test with local kubeconfig (mounts at .kubeconfig-test)
./test-with-kubeconfig.sh

# Note: K8s cluster must be accessible from Docker network
# Localhost clusters (k3d on 127.0.0.1) won't work from container
```

### Adding New Link Categories
1. Add category method to `LinksGenerator` class in `app/links_generator.py`
2. Call method in `generate_links()` method
3. Update fixtures in `app/fixtures.py` with sample data
4. Add to models if new status types needed

### Updating Dependencies
```bash
# Update Pipfile with new versions
# Then:
pipenv lock
pipenv install
# Test locally
# Test Docker build: docker build -t test .
# Run tests if they exist
```

## Important Patterns

### Service Name Convention
- **DO NOT** extract base service name from app name
- Use full app name as service name: `taco-backend-prod` not `taco-backend`
- OpenTelemetry reports full names, extracting prefix breaks traces/logs

### Grafana URL Patterns
- **Loki**: `/a/grafana-lokiexplore-app/explore/service/{service_name}/logs?...`
- **Tempo**: `/explore?schemaVersion=1&panes={...}` with datasource UID in panes structure
- Datasource UID must be in TWO places: top-level panes and in query.datasource

### Error Handling
- Graceful degradation: missing resources don't fail entire response
- Status field: `ok`, `empty`, `error`
- Empty arrays for missing links, message field explains why

### Caching Strategy
- Cache by namespace:appname (not just appname)
- 30s TTL balances freshness vs K8s API load
- Cache failures log warning but don't block requests

## Gotchas & Known Issues

### Docker Volume Mounts
- **CRITICAL**: Use `--mount type=bind` NOT `-v` for file mounts
- `-v` creates directories if target doesn't exist, breaking kubeconfig
- Mount kubeconfig to `/app/kubeconfig` (directory already exists in image)

### Kubeconfig in Container
- Must create `.kube` directory before mounting: `mkdir -p /home/appuser/.kube`
- Container runs as `appuser` (UID 1000) not root
- Kubeconfig must be readable by appuser

### Python 3.14
- Not available in most environments as of Dec 2024
- Use Python 3.13 (latest stable)
- Dockerfile uses `python:3.13-slim`

### Tempo Datasource UID
- Required for working Tempo traces links
- Find in Grafana: Settings → Data Sources → Tempo → Copy UID
- Set via `TEMPO_DATASOURCE_UID` env var
- Example UID: `de7lydl3hl9fkd`

### Import Paths
- Always use `from app.xxx` not `from xxx`
- App runs as package, relative imports fail

## Testing & Development

### Mock Endpoints for Extension Dev
```bash
# All categories with data
curl http://localhost:8000/api/v1/fixtures/all-ok

# Error states
curl http://localhost:8000/api/v1/fixtures/errors

# Partial data
curl http://localhost:8000/api/v1/fixtures/partial

# Slow response (3s delay)
curl http://localhost:8000/api/v1/fixtures/slow

# Mock endpoint (same as all-ok but different path)
curl http://localhost:8000/api/v1/mock/applications/test-app/links
```

### Real Request Format
```bash
curl http://localhost:8000/api/v1/applications/{app_name}/links \
  -H "Argocd-Application-Name: {namespace}:{app_name}" \
  -H "Argocd-Project-Name: {project_name}"
```

### Log Levels
- `DEBUG`: Full request/response details, cache operations, K8s queries
- `INFO`: Request received, cache hit/miss, links generated
- `WARNING`: Cache failures (continues with degraded service)
- `ERROR`: Link generation failures, K8s API errors
- Set via `LOG_LEVEL` env var

## Deployment

### Kubernetes
- Manifests in `k8s/manifests.yaml`
- ServiceAccount with RBAC (read-only)
- Requires access to: Applications (argoproj.io), Deployments, Pods, ExternalSecrets
- Valkey as separate service

### Environment Variables Required
```bash
# Required
GRAFANA_BASE_URL=https://grafana.example.com
VAULT_BASE_URL=https://vault.example.com
VALKEY_URL=valkey://valkey-service:6379

# Optional
TEMPO_DATASOURCE_UID=de7lydl3hl9fkd  # Get from Grafana
CACHE_TTL_SECONDS=30
LOG_LEVEL=INFO
```

### Docker Build
```bash
# Build
docker build -t ghcr.io/glueops/gluelinks-api:latest .

# Test locally without K8s
docker run -p 8000:8000 \
  -v $(pwd)/.env.local:/app/.env.local:ro \
  ghcr.io/glueops/gluelinks-api:latest

# Access mock endpoints
curl http://localhost:8000/api/v1/fixtures/all-ok
```

## Recent Changes (Dec 2024)

### v2.0.0 - Major Dependency Update
- Upgraded Python 3.11 → 3.13
- Updated all dependencies to latest stable versions
- Added mock/fixture endpoints for extension testing
- Fixed Tempo datasource UID configuration
- Fixed service name extraction (now uses full app name)
- Updated Loki URL format to `/a/grafana-lokiexplore-app/...`
- Added test script with kubeconfig mounting

### Breaking Changes from v1.x
- Service names now match app names exactly (no prefix extraction)
- Tempo URLs require TEMPO_DATASOURCE_UID env var for full functionality
- Loki URL format changed (old format may still work but deprecated)

## Future Improvements (Not Implemented)

### Considered but Deferred
- ❌ Prometheus metrics endpoint - not needed yet
- ❌ Automated testing (pytest) - manual testing sufficient for now
- ❌ Rate limiting - internal API, not exposed publicly
- ❌ Multi-cluster support - single cluster use case
- ❌ Code quality tools (black, ruff, mypy) - team preference TBD

### Helpful for Extension Development
- ✅ Mock endpoints with various states
- ✅ Fixture library with consistent test data
- ✅ Docker testing with local kubeconfig
- ❌ TypeScript/React examples (could add to docs/)
- ❌ OpenAPI schema in extension-friendly format

## Troubleshooting

### "Invalid kube-config file. No configuration found."
- Check KUBECONFIG env var points to valid file
- Verify file permissions (must be readable)
- In Docker: ensure parent directory exists before mounting

### "Connection refused" to K8s API
- Kubeconfig uses 127.0.0.1 but container can't reach host
- Use `--network host` for Docker, or
- Update kubeconfig to use accessible IP, or
- Deploy to K8s cluster instead

### "Connection refused" to Valkey
- Check VALKEY_URL in environment
- Verify Valkey container is running: `docker ps`
- API continues with cache warnings but reduced performance

### "IsADirectoryError" when mounting kubeconfig
- Using `-v` instead of `--mount type=bind`
- File doesn't exist before docker run
- See "Docker Volume Mounts" section above

### Links not working in Grafana
- Check GRAFANA_BASE_URL is correct (no trailing slash)
- Verify TEMPO_DATASOURCE_UID matches Grafana datasource
- Check service names in Grafana match app names exactly
- Time ranges default to last 15m (logs) or 1h (traces)

## Quick Reference Commands

```bash
# Local development
pipenv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Docker build & test
docker build -t ghcr.io/glueops/gluelinks-api:latest .
./test-with-kubeconfig.sh

# Check versions
pipenv run pip list | grep -E "(fastapi|kubernetes|pydantic)"

# View logs (structured JSON)
docker logs -f <container-name> 2>&1 | jq .

# Test specific app
curl -s http://localhost:8000/api/v1/applications/my-app/links \
  -H "Argocd-Application-Name: production:my-app" | jq .

# Test mock data
curl -s http://localhost:8000/api/v1/fixtures/all-ok | jq .
```

## Links & References
- FastAPI docs: https://fastapi.tiangolo.com/
- Kubernetes Python client: https://github.com/kubernetes-client/python
- Grafana Explore: https://grafana.com/docs/grafana/latest/explore/
- ArgoCD tracking IDs: https://argo-cd.readthedocs.io/en/stable/user-guide/resource_tracking/
