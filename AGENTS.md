# AGENTS.md - AI Agent Instructions for GlueLinks-API

> This file provides context for AI coding agents. See [agents.md](https://agents.md/) for the specification.

## Project Overview

FastAPI backend that serves dynamic links for ArgoCD extension UI. Generates links to Grafana dashboards, Loki logs, Tempo traces, Vault secrets, and GitHub IaaC repos based on Kubernetes resource discovery.

**Tech Stack**: Python 3.13, FastAPI, Pydantic, Kubernetes client, Valkey (Redis-compatible), Structlog

## Architecture

### Core Flow
1. ArgoCD extension calls API with app name + namespace in headers
2. API queries K8s for ArgoCD Application manifest
3. Discovers related resources via tracking IDs
4. Generates 8 categories of links (Quick Links, APM, Namespace, Pod, Logs, Traces, Vault, IaaC)
5. Caches response in Valkey for 30s

### Key Files
| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app, endpoints: /health, /ready, /applications/{app_name}/links, /fixtures/{name}, /mock/... |
| `app/links_generator.py` | Link generation logic, 8 categories, handles missing resources gracefully |
| `app/quick_links.py` | Shared Quick Links category generator (used by links_generator and fixtures) |
| `app/k8s_client.py` | K8s API wrapper, uses tracking IDs |
| `app/cache.py` | Valkey cache wrapper, 30s TTL |
| `app/config.py` | Pydantic settings from environment variables |
| `app/fixtures.py` | Mock data for extension testing |
| `app/models.py` | Pydantic response models |

### Environment Variables
```bash
# Required
GRAFANA_BASE_URL=https://grafana.example.com
VAULT_BASE_URL=https://vault.example.com
VALKEY_URL=redis://localhost:6379

# Optional with defaults
CAPTAIN_DOMAIN=nonprod.antoniostacos.onglueops.com  # Quick Links URLs
MAX_ROWS=4                                           # UI row limit in metadata
TEMPO_DATASOURCE_UID=                                # Grafana Tempo datasource
CACHE_TTL_SECONDS=30
LOG_LEVEL=INFO

# Mock/demo mode
USE_MOCK_DATA=false                                  # Bypass K8s, return mock data
DEFAULT_MOCK_FIXTURE=all-ok                          # all-ok, error-states, partial-data, minimal
```

## Commands

```bash
# Install dependencies
pipenv install

# Run locally
pipenv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Valkey cache
docker-compose up -d valkey

# Build Docker image
docker build -t ghcr.io/glueops/gluelinks-api:latest .

# Test with kubeconfig
./test-with-kubeconfig.sh
```

## Code Style & Conventions

### Import Paths
- **Always** use `from app.xxx` not `from xxx`
- App runs as package; relative imports fail

### Service Name Convention
- **DO NOT** extract base service name from app name
- Use full app name as service name: `taco-backend-prod` not `taco-backend`
- OpenTelemetry reports full names; extracting prefix breaks traces/logs

### Response Structure
```python
{
    "app_name": "...",
    "namespace": "...",
    "service_name": "...",
    "categories": [...],          # Quick Links first, then APM, Namespace, etc.
    "metadata": {
        "generated_at": "...",
        "last_updated": "...",    # Moved from top-level to metadata
        "max_rows": 4,            # Configurable via MAX_ROWS env var
        "version": "v1",
        "resources": {...}
    }
}
```

### Error Handling Pattern
- Graceful degradation: missing resources don't fail entire response
- Status field: `ok`, `empty`, `error`
- Empty arrays for missing links, `message` field explains why

### Adding New Link Categories
1. Add category method to `LinksGenerator` class in `app/links_generator.py`
2. Call method in `generate_links()` method (Quick Links stays first)
3. For hardcoded/shared content: add to `app/quick_links.py`
4. Update fixtures in `app/fixtures.py` with sample data
5. Update models if new status types needed

### Quick Links (Shared Utility)
- `app/quick_links.py` contains shared Quick Links generation
- `generate_quick_links_category()` - returns Pydantic model (for links_generator)
- `get_quick_links_dict()` - returns dict (for fixtures)
- Both use `CAPTAIN_DOMAIN` env var for cluster-info URL
- Always keep Quick Links as the **first** category

## Common Gotchas

### Docker Volume Mounts
- **Use `--mount type=bind`** NOT `-v` for file mounts
- `-v` creates directories if target doesn't exist, breaking kubeconfig

### Kubeconfig in Container
- Container runs as `appuser` (UID 1000) not root
- Mount kubeconfig to `/app/kubeconfig`
- Kubeconfig must be readable by appuser

### Tempo Datasource UID
- Required for working Tempo traces links
- Find in Grafana: Settings → Data Sources → Tempo → Copy UID
- Set via `TEMPO_DATASOURCE_UID` env var
- UID must appear in TWO places in panes structure

### Grafana URL Patterns
- **Loki**: `/a/grafana-lokiexplore-app/explore/service/{service_name}/logs?...`
- **Tempo**: `/explore?schemaVersion=1&panes={...}` with datasource UID

## Testing

### Mock Endpoints (no K8s required)
```bash
# All categories working
curl http://localhost:8000/api/v1/fixtures/all-ok

# Error states
curl http://localhost:8000/api/v1/fixtures/error-states

# Partial data
curl http://localhost:8000/api/v1/fixtures/partial-data

# Minimal data
curl http://localhost:8000/api/v1/fixtures/minimal

# Mock with custom app name
curl http://localhost:8000/api/v1/mock/applications/my-app/links
```

### Real Request Format
```bash
curl http://localhost:8000/api/v1/applications/{app_name}/links \
  -H "Argocd-Application-Name: {namespace}:{app_name}"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No configuration found" K8s error | Check KUBECONFIG env var, file permissions |
| "Connection refused" to K8s API | Container can't reach host's localhost; use accessible IP |
| "Connection refused" to Valkey | Check VALKEY_URL; API continues with cache warnings |
| Links not working in Grafana | Check BASE_URLs (no trailing slash), TEMPO_DATASOURCE_UID |
| "IsADirectoryError" on kubeconfig | Use `--mount type=bind` not `-v` |

## Dependencies

- Python 3.13 (use `python:3.13-slim` Docker image)
- FastAPI 0.115.6
- Pydantic 2.10.5
- Kubernetes 31.0.0
- Valkey 6.0.2
- Structlog 24.4.0

## Links & References

- [FastAPI docs](https://fastapi.tiangolo.com/)
- [Kubernetes Python client](https://github.com/kubernetes-client/python)
- [ArgoCD tracking IDs](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_tracking/)
- [agents.md spec](https://agents.md/)
