# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-12-14

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
