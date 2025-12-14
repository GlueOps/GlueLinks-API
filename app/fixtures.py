"""
Mock fixtures for testing the ArgoCD extension UI.
Provides sample responses with various states for development.
"""
import os
from datetime import datetime
from typing import Dict, Any

from app.quick_links import get_quick_links_dict

# Default captain domain from environment or fallback
DEFAULT_CAPTAIN_DOMAIN = os.environ.get("CAPTAIN_DOMAIN", "nonprod.antoniostacos.onglueops.com")
DEFAULT_MAX_ROWS = int(os.environ.get("MAX_ROWS", "4"))


def get_mock_all_ok(app_name: str = "test-app-prod", namespace: str = "nonprod") -> Dict[str, Any]:
    """
    Mock response with all categories populated and working.
    Use this to test the extension's happy path rendering.
    """
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "app_name": app_name,
        "namespace": namespace,
        "service_name": app_name,
        "categories": [
            get_quick_links_dict(DEFAULT_CAPTAIN_DOMAIN),
            {
                "id": "apm",
                "label": "APM Overview",
                "icon": "📊",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Application Performance Monitoring",
                        "url": f"https://grafana.nonprod.example.com/d/opentelemetry-apm/apm-overview?orgId=1&refresh=30s&from=now-1h&to=now&var-app={app_name}&var-route=All"
                    }
                ]
            },
            {
                "id": "namespace",
                "label": "Namespace Overview",
                "icon": "📦",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Kubernetes Overview",
                        "url": f"https://grafana.nonprod.example.com/d/ee58kcteeir5sf/kubernetes-overview?orgId=1&var-namespace={namespace}"
                    }
                ]
            },
            {
                "id": "pod",
                "label": "Pod Overview",
                "icon": "🔲",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": f"{app_name}-abc123-xyz",
                        "url": f"https://grafana.nonprod.example.com/d/ce60j8f8umhhcc/kubernetes-pod-overview?orgId=1&refresh=10s&from=now-1h&to=now&var-datasource=default&var-cluster=&var-namespace={namespace}&var-workload={app_name}&var-pod={app_name}-abc123-xyz"
                    },
                    {
                        "label": f"{app_name}-def456-uvw",
                        "url": f"https://grafana.nonprod.example.com/d/ce60j8f8umhhcc/kubernetes-pod-overview?orgId=1&refresh=10s&from=now-1h&to=now&var-datasource=default&var-cluster=&var-namespace={namespace}&var-workload={app_name}&var-pod={app_name}-def456-uvw"
                    }
                ]
            },
            {
                "id": "logs",
                "label": "Logs",
                "icon": "📋",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Application Logs (Loki)",
                        "url": f"https://grafana.nonprod.example.com/a/grafana-lokiexplore-app/explore/service/{app_name}/logs?patterns=%5B%5D&from=now-15m&to=now&var-filters=service_name%7C%3D%7C{app_name}&var-fields=&var-levels=&var-metadata=&var-patterns=&var-lineFilterV2=&var-lineFilters=&timezone=browser&var-all-fields=&urlColumns=%5B%5D&visualizationType=%22logs%22&displayedFields=%5B%5D&sortOrder=%22Descending%22&wrapLogMessage=false"
                    }
                ]
            },
            {
                "id": "traces",
                "label": "Traces",
                "icon": "🔍",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Tempo Traces",
                        "url": f"https://grafana.nonprod.example.com/explore?schemaVersion=1&panes=%7B%22trc%22%3A%20%7B%22queries%22%3A%20%5B%7B%22refId%22%3A%20%22A%22%2C%20%22queryType%22%3A%20%22traceqlSearch%22%2C%20%22limit%22%3A%2020%2C%20%22tableType%22%3A%20%22traces%22%2C%20%22filters%22%3A%20%5B%7B%22id%22%3A%20%22service-name%22%2C%20%22tag%22%3A%20%22service.name%22%2C%20%22operator%22%3A%20%22%3D%22%2C%20%22scope%22%3A%20%22resource%22%2C%20%22value%22%3A%20%5B%22{app_name}%22%5D%2C%20%22valueType%22%3A%20%22string%22%7D%5D%2C%20%22datasource%22%3A%20%7B%22type%22%3A%20%22tempo%22%2C%20%22uid%22%3A%20%22de7lydl3hl9fkd%22%7D%7D%5D%2C%20%22range%22%3A%20%7B%22from%22%3A%20%22now-1h%22%2C%20%22to%22%3A%20%22now%22%7D%2C%20%22datasource%22%3A%20%22de7lydl3hl9fkd%22%7D%7D&orgId=1"
                    }
                ]
            },
            {
                "id": "vault",
                "label": "Vault Secrets",
                "icon": "🔐",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "database-credentials",
                        "url": "https://vault.nonprod.example.com/ui/vault/secrets/secret/show/database-credentials"
                    },
                    {
                        "label": "api-keys",
                        "url": "https://vault.nonprod.example.com/ui/vault/secrets/secret/show/api-keys"
                    }
                ]
            },
            {
                "id": "iaac",
                "label": "IaaC",
                "icon": "⚙️",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Deployment Configuration",
                        "url": f"https://github.com/example/deployment-configurations/tree/main/apps/{app_name.rsplit('-', 1)[0] if '-prod' in app_name or '-stage' in app_name else app_name}"
                    }
                ]
            }
        ],
        "metadata": {
            "generated_at": now,
            "last_updated": now,
            "max_rows": DEFAULT_MAX_ROWS,
            "version": "v1",
            "resources": {
                "argocd_app": True,
                "deployment": True,
                "pods_found": 2,
                "external_secrets_found": 2
            }
        }
    }


def get_mock_error_states(app_name: str = "broken-app-prod", namespace: str = "nonprod") -> Dict[str, Any]:
    """
    Mock response with various error and empty states.
    Use this to test extension error handling and empty state rendering.
    """
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "app_name": app_name,
        "namespace": namespace,
        "service_name": app_name,
        "categories": [
            get_quick_links_dict(DEFAULT_CAPTAIN_DOMAIN),
            {
                "id": "apm",
                "label": "APM Overview",
                "icon": "📊",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Application Performance Monitoring",
                        "url": f"https://grafana.nonprod.example.com/d/opentelemetry-apm/apm-overview?orgId=1&refresh=30s&from=now-1h&to=now&var-app={app_name}&var-route=All"
                    }
                ]
            },
            {
                "id": "namespace",
                "label": "Namespace Overview",
                "icon": "📦",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Kubernetes Overview",
                        "url": f"https://grafana.nonprod.example.com/d/ee58kcteeir5sf/kubernetes-overview?orgId=1&var-namespace={namespace}"
                    }
                ]
            },
            {
                "id": "pod",
                "label": "Pod Overview",
                "icon": "🔲",
                "status": "empty",
                "message": "No pods currently running",
                "links": []
            },
            {
                "id": "logs",
                "label": "Logs",
                "icon": "📋",
                "status": "error",
                "message": "Failed to query logs. Grafana API unavailable.",
                "links": []
            },
            {
                "id": "traces",
                "label": "Traces",
                "icon": "🔍",
                "status": "empty",
                "message": "No traces found for this service",
                "links": []
            },
            {
                "id": "vault",
                "label": "Vault Secrets",
                "icon": "🔐",
                "status": "empty",
                "message": "No ExternalSecrets configured for this application",
                "links": []
            },
            {
                "id": "iaac",
                "label": "IaaC",
                "icon": "⚙️",
                "status": "error",
                "message": "Unable to parse deployment configuration from ArgoCD manifest",
                "links": []
            }
        ],
        "metadata": {
            "generated_at": now,
            "last_updated": now,
            "max_rows": DEFAULT_MAX_ROWS,
            "version": "v1",
            "resources": {
                "argocd_app": True,
                "deployment": False,
                "pods_found": 0,
                "external_secrets_found": 0
            }
        }
    }


def get_mock_partial_data(app_name: str = "partial-app-prod", namespace: str = "nonprod") -> Dict[str, Any]:
    """
    Mock response with some categories working and others empty/error.
    Use this to test mixed state rendering.
    """
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "app_name": app_name,
        "namespace": namespace,
        "service_name": app_name,
        "categories": [
            get_quick_links_dict(DEFAULT_CAPTAIN_DOMAIN),
            {
                "id": "apm",
                "label": "APM Overview",
                "icon": "📊",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Application Performance Monitoring",
                        "url": f"https://grafana.nonprod.example.com/d/opentelemetry-apm/apm-overview?orgId=1&refresh=30s&from=now-1h&to=now&var-app={app_name}&var-route=All"
                    }
                ]
            },
            {
                "id": "namespace",
                "label": "Namespace Overview",
                "icon": "📦",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Kubernetes Overview",
                        "url": f"https://grafana.nonprod.example.com/d/ee58kcteeir5sf/kubernetes-overview?orgId=1&var-namespace={namespace}"
                    }
                ]
            },
            {
                "id": "pod",
                "label": "Pod Overview",
                "icon": "🔲",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": f"{app_name}-xyz789-abc",
                        "url": f"https://grafana.nonprod.example.com/d/ce60j8f8umhhcc/kubernetes-pod-overview?orgId=1&refresh=10s&from=now-1h&to=now&var-datasource=default&var-cluster=&var-namespace={namespace}&var-workload={app_name}&var-pod={app_name}-xyz789-abc"
                    }
                ]
            },
            {
                "id": "logs",
                "label": "Logs",
                "icon": "📋",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Application Logs (Loki)",
                        "url": f"https://grafana.nonprod.example.com/a/grafana-lokiexplore-app/explore/service/{app_name}/logs?patterns=%5B%5D&from=now-15m&to=now&var-filters=service_name%7C%3D%7C{app_name}&var-fields=&var-levels=&var-metadata=&var-patterns=&var-lineFilterV2=&var-lineFilters=&timezone=browser&var-all-fields=&urlColumns=%5B%5D&visualizationType=%22logs%22&displayedFields=%5B%5D&sortOrder=%22Descending%22&wrapLogMessage=false"
                    }
                ]
            },
            {
                "id": "traces",
                "label": "Traces",
                "icon": "🔍",
                "status": "empty",
                "message": "No traces found - service may not be instrumented",
                "links": []
            },
            {
                "id": "vault",
                "label": "Vault Secrets",
                "icon": "🔐",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "app-config",
                        "url": "https://vault.nonprod.example.com/ui/vault/secrets/secret/show/app-config"
                    }
                ]
            },
            {
                "id": "iaac",
                "label": "IaaC",
                "icon": "⚙️",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Deployment Configuration",
                        "url": f"https://github.com/example/deployment-configurations/tree/main/apps/{app_name.rsplit('-', 1)[0] if '-prod' in app_name or '-stage' in app_name else app_name}"
                    }
                ]
            }
        ],
        "metadata": {
            "generated_at": now,
            "last_updated": now,
            "max_rows": DEFAULT_MAX_ROWS,
            "version": "v1",
            "resources": {
                "argocd_app": True,
                "deployment": True,
                "pods_found": 1,
                "external_secrets_found": 1
            }
        }
    }


def get_mock_minimal(app_name: str = "minimal-app", namespace: str = "default") -> Dict[str, Any]:
    """
    Mock response with minimal data - only namespace and IaaC.
    Use this to test rendering when most categories are empty.
    """
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "app_name": app_name,
        "namespace": namespace,
        "service_name": app_name,
        "categories": [
            get_quick_links_dict(DEFAULT_CAPTAIN_DOMAIN),
            {
                "id": "apm",
                "label": "APM Overview",
                "icon": "📊",
                "status": "empty",
                "message": "No APM data available",
                "links": []
            },
            {
                "id": "namespace",
                "label": "Namespace Overview",
                "icon": "📦",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Kubernetes Overview",
                        "url": f"https://grafana.nonprod.example.com/d/ee58kcteeir5sf/kubernetes-overview?orgId=1&var-namespace={namespace}"
                    }
                ]
            },
            {
                "id": "pod",
                "label": "Pod Overview",
                "icon": "🔲",
                "status": "empty",
                "message": "No pods currently running",
                "links": []
            },
            {
                "id": "logs",
                "label": "Logs",
                "icon": "📋",
                "status": "empty",
                "message": "No logs available",
                "links": []
            },
            {
                "id": "traces",
                "label": "Traces",
                "icon": "🔍",
                "status": "empty",
                "message": "No traces available",
                "links": []
            },
            {
                "id": "vault",
                "label": "Vault Secrets",
                "icon": "🔐",
                "status": "empty",
                "message": "No ExternalSecrets configured for this application",
                "links": []
            },
            {
                "id": "iaac",
                "label": "IaaC",
                "icon": "⚙️",
                "status": "ok",
                "message": None,
                "links": [
                    {
                        "label": "Deployment Configuration",
                        "url": f"https://github.com/example/deployment-configurations/tree/main/apps/{app_name}"
                    }
                ]
            }
        ],
        "metadata": {
            "generated_at": now,
            "last_updated": now,
            "max_rows": DEFAULT_MAX_ROWS,
            "version": "v1",
            "resources": {
                "argocd_app": True,
                "deployment": False,
                "pods_found": 0,
                "external_secrets_found": 0
            }
        }
    }


# Map fixture names to their generator functions
FIXTURES = {
    "all-ok": get_mock_all_ok,
    "error-states": get_mock_error_states,
    "partial-data": get_mock_partial_data,
    "minimal": get_mock_minimal,
}


def get_fixture(fixture_name: str, app_name: str = None, namespace: str = None) -> Dict[str, Any]:
    """
    Get a fixture by name with optional custom app_name and namespace.
    
    Args:
        fixture_name: One of: all-ok, error-states, partial-data, minimal
        app_name: Override the default app name
        namespace: Override the default namespace
    
    Returns:
        Mock response dictionary
    
    Raises:
        KeyError: If fixture_name is not found
    """
    if fixture_name not in FIXTURES:
        available = ", ".join(FIXTURES.keys())
        raise KeyError(f"Fixture '{fixture_name}' not found. Available: {available}")
    
    fixture_func = FIXTURES[fixture_name]
    kwargs = {}
    if app_name:
        kwargs["app_name"] = app_name
    if namespace:
        kwargs["namespace"] = namespace
    
    return fixture_func(**kwargs)
