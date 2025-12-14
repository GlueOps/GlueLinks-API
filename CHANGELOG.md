# Changelog

All notable changes to this project will be documented in this file.

## [2.1.0] - 2025-12-14

### Changed
- **Updated all dependencies to latest stable versions:**
  - fastapi: 0.115.6 → 0.124.4
  - uvicorn: 0.34.0 → 0.38.0
  - kubernetes: 31.0.0 → 34.1.0
  - pydantic: 2.10.3 → 2.12.5
  - pydantic-settings: 2.6.1 → 2.12.0
  - structlog: 24.4.0 → 25.5.0
  - valkey: 6.0.2 → 6.1.1
- Reverted Python from 3.13 to 3.11.11 (latest stable available in environment)

## [2.0.0] - 2025-12-14

### Added
- **Mock/Test Endpoints**: New endpoints for extension development without K8s resources
  - `GET /api/v1/mock/applications/{app_name}/links` - Mock response with all categories (happy path)
  - `GET /api/v1/fixtures/{fixture_name}` - Test fixtures for different UI states
  - Available fixtures: `all-ok`, `error-states`, `partial-data`, `minimal`
- **Fixtures Module** (`app/fixtures.py`): Reusable test data for extension developers
  - 4 fixture types covering happy path, error handling, partial data, and minimal states
  - Customizable app_name and namespace parameters

### Changed
- **BREAKING**: Upgraded Python from 3.11 to 3.13
- **BREAKING**: Updated all dependencies to latest stable versions:
  - fastapi: 0.115.0 → 0.124.4 (124 versions)
  - uvicorn: 0.30.6 → 0.38.0
  - kubernetes: 31.0.0 → 34.1.0
  - pydantic: 2.10.0 → 2.12.5
  - pydantic-settings: 2.6.0 → 2.12.0
  - structlog: 24.4.0 → 25.5.0
  - valkey: 6.0.2 → 6.1.1
  - kubernetes: 31.0.0 → 32.0.0
  - pydantic: 2.10.0 → 2.10.5
  - pydantic-settings: 2.6.0 → 2.7.0
  - valkey: 6.0.2 (unchanged)
  - structlog: 24.4.0 (unchanged)
- **Docker Base Image**: Updated from `python:3.11-slim` to `python:3.13-slim`
- **Tempo Datasource UID**: Updated from `P8E80F9AEF21F6940` to `de7lydl3hl9fkd`
- **Tempo Time Range**: Changed from 15 minutes to 1 hour (`now-1h` to `now`)

## [1.0.0] - 2025-12-13

### Fixed
- **Loki URL Format**: Updated to use the new Grafana Loki Explore App path
  - Old: `/explore?...datasource=loki&expr={service_name="..."}`
  - New: `/a/grafana-lokiexplore-app/explore/service/{service_name}/logs?...`
  - Now includes proper query parameters: patterns, from/to time range, service_name filter, visualization type
  
- **Tempo URL Format**: Updated to use the panes structure with TraceQL search
  - Old: Simple explore URL with tempo datasource
  - New: Structured panes with TraceQL search filters
  - Uses `service.name` filter with resource scope
  - Includes proper query type (`traceqlSearch`), limit (20), and time range (now-15m to now)

### Changed
- URL encoding now properly handles nested JSON structures in Tempo URLs
- Loki URLs include all necessary parameters for proper log filtering and visualization

### Documentation
- Updated [README.md](README.md) with comprehensive local testing instructions
- Added step-by-step guide for restarting and testing the API locally
- Added troubleshooting section for common issues

## Example URLs

### Loki (Logs)
```
https://grafana.nonprod.antoniostacos.onglueops.com/a/grafana-lokiexplore-app/explore/service/taco-backend/logs?patterns=[]&from=now-15m&to=now&var-filters=service_name|=|taco-backend&visualizationType="logs"&sortOrder="Descending"
```

### Tempo (Traces)
```
https://grafana.nonprod.antoniostacos.onglueops.com/explore?schemaVersion=1&panes={"a":{"queries":[{"refId":"A","queryType":"traceqlSearch","limit":20,"tableType":"traces","filters":[{"id":"service-name","tag":"service.name","operator":"=","scope":"resource","value":["taco-backend"],"valueType":"string"}]}],"range":{"from":"now-15m","to":"now"}}}&orgId=1
```

## Testing Instructions

To test the updated URLs locally:

```bash
# 1. Ensure Valkey is running
docker-compose up -d valkey

# 2. Start the API
./run-local.sh

# 3. Test the links endpoint
curl -s http://localhost:8000/api/v1/applications/taco-backend-prod/links \
  -H "Argocd-Application-Name: nonprod:taco-backend-prod" \
  | jq '.categories[] | select(.id == "logs" or .id == "traces")'
```

## Technical Details

### Loki URL Structure
- **Path**: `/a/grafana-lokiexplore-app/explore/service/{service_name}/logs`
- **Key Parameters**:
  - `from` & `to`: Time range (now-15m to now)
  - `var-filters`: Service name filter in format `service_name|=|{value}`
  - `visualizationType`: Set to "logs"
  - `sortOrder`: "Descending" for newest first

### Tempo URL Structure
- **Path**: `/explore` with schema version 1
- **Panes Structure** (JSON encoded):
  ```json
  {
    "a": {
      "queries": [{
        "refId": "A",
        "queryType": "traceqlSearch",
        "limit": 20,
        "tableType": "traces",
        "filters": [{
          "id": "service-name",
          "tag": "service.name",
          "operator": "=",
          "scope": "resource",
          "value": ["service_name_here"],
          "valueType": "string"
        }]
      }],
      "range": {
        "from": "now-15m",
        "to": "now"
      }
    }
  }
  ```

## Compatibility

- Grafana Loki Explore App (modern Loki UI)
- Grafana Tempo with TraceQL search support
- Service name extracted via regex: `^(?P<service_prefix>.+?)(-[0-9a-f]{9,}(-[a-z0-9]{4,})?|-[0-9]+|-[a-z0-9]{4,6})?$`
