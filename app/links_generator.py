"""Links generator for ArgoCD applications."""
from datetime import datetime, timezone
from typing import List
from urllib.parse import quote
import structlog

from app.models import (
    LinksResponse,
    CategoryModel,
    LinkModel,
    ResourceMetadata,
    ResponseMetadata,
)
from app.k8s_client import K8sClient
from app.quick_links import generate_quick_links_category

logger = structlog.get_logger()


class LinksGenerator:
    """Generates links for ArgoCD applications."""
    
    def __init__(self, k8s_client: K8sClient, grafana_base_url: str, vault_base_url: str, captain_domain: str, max_rows: int):
        """Initialize links generator."""
        self.k8s_client = k8s_client
        self.grafana_base_url = grafana_base_url.rstrip("/")
        self.vault_base_url = vault_base_url.rstrip("/")
        self.captain_domain = captain_domain
        self.max_rows = max_rows
    
    async def generate_links(self, app_name: str, namespace: str) -> LinksResponse:
        """Generate all links for an application."""
        log = logger.bind(app_name=app_name, namespace=namespace)
        log.info("generating_links")
        
        # Use full app_name as service_name for OpenTelemetry queries
        service_name = app_name
        
        # Fetch ArgoCD application first (lives in argocd namespace like glueops-core)
        argocd_app = self.k8s_client.get_argocd_application(app_name, namespace)
        
        # Extract the target deployment namespace from ArgoCD app spec
        # The ArgoCD app lives in 'glueops-core', but deploys to 'nonprod' or similar
        target_namespace = namespace
        if argocd_app:
            target_namespace = argocd_app.get("spec", {}).get("destination", {}).get("namespace", namespace)
            if target_namespace != namespace:
                log.debug("using_target_namespace", argocd_namespace=namespace, target_namespace=target_namespace)
        
        # Fetch K8s resources from the TARGET namespace (where deployments/pods actually live)
        deployment = self.k8s_client.get_deployment(app_name, target_namespace)
        
        pods = []
        if deployment:
            pods = self.k8s_client.get_pods(deployment.metadata.name, target_namespace)
        
        external_secrets = self.k8s_client.get_external_secrets(app_name, target_namespace)
        
        # Build metadata
        now = datetime.now(timezone.utc)
        metadata = ResponseMetadata(
            generated_at=now,
            last_updated=now,
            max_rows=self.max_rows,
            version="v1",
            resources=ResourceMetadata(
                argocd_app=argocd_app is not None,
                deployment=deployment is not None,
                pods_found=len(pods),
                external_secrets_found=len(external_secrets),
            ),
        )
        
        # Generate categories with Quick Links first
        # Use target_namespace for categories that show deployment details
        categories = [
            generate_quick_links_category(self.captain_domain),
            self._generate_apm_category(service_name),
            self._generate_namespace_category(target_namespace),
            self._generate_pod_category(pods, target_namespace),
            self._generate_logs_category(service_name),
            self._generate_traces_category(service_name),
            self._generate_vault_category(external_secrets),
            self._generate_iaac_category(argocd_app),
        ]
        
        log.info("links_generated", service_name=service_name, categories_count=len(categories))
        
        return LinksResponse(
            app_name=app_name,
            namespace=target_namespace,
            service_name=service_name,
            categories=categories,
            metadata=metadata,
        )
    
    def _generate_apm_category(self, service_name: str) -> CategoryModel:
        """Generate APM overview links."""
        url = (
            f"{self.grafana_base_url}/d/opentelemetry-apm/apm-overview"
            f"?orgId=1&refresh=30s&from=now-1h&to=now&var-app={quote(service_name)}&var-route=All"
        )
        
        return CategoryModel(
            id="apm",
            label="APM Overview",
            icon="📊",
            status="ok",
            links=[
                LinkModel(
                    label=service_name,
                    url=url,
                )
            ],
        )
    
    def _generate_namespace_category(self, namespace: str) -> CategoryModel:
        """Generate Kubernetes overview links."""
        url = (
            f"{self.grafana_base_url}/d/ee58kcteeir5sf/kubernetes-overview"
            f"?orgId=1&var-namespace={quote(namespace)}"
        )
        
        return CategoryModel(
            id="namespace",
            label="Kubernetes Overview",
            icon="📦",
            status="ok",
            links=[
                LinkModel(
                    label=namespace,
                    url=url,
                )
            ],
        )
    
    def _generate_pod_category(self, pods: list, namespace: str) -> CategoryModel:
        """Generate pod metrics links for all pods."""
        if not pods:
            return CategoryModel(
                id="pod",
                label="Pod Metrics",
                icon="🔲",
                status="empty",
                message="No pods currently running",
                links=[],
            )
        
        links = []
        for pod in pods:
            pod_name = pod.metadata.name
            url = (
                f"{self.grafana_base_url}/d/ce60j8f8umhhcc/kubernetes-pod-overview"
                f"?orgId=1&refresh=10s&from=now-1h&to=now"
                f"&var-datasource=default&var-cluster=&var-namespace={quote(namespace)}"
                f"&var-pod={quote(pod_name)}"
            )
            links.append(LinkModel(label=pod_name, url=url))
        
        return CategoryModel(
            id="pod",
            label="Pod Metrics",
            icon="🔲",
            status="ok",
            links=links,
        )
    
    def _generate_logs_category(self, service_name: str) -> CategoryModel:
        """Generate logs links."""
        # Loki logs URL using the Loki explore app
        url = (
            f"{self.grafana_base_url}/a/grafana-lokiexplore-app/explore/service/{quote(service_name)}/logs"
            f"?patterns=%5B%5D&from=now-15m&to=now"
            f"&var-filters=service_name%7C%3D%7C{quote(service_name)}"
            f"&var-fields=&var-levels=&var-metadata=&var-patterns=&var-lineFilterV2=&var-lineFilters=&timezone=browser"
            f"&var-all-fields=&urlColumns=%5B%5D&visualizationType=%22logs%22&displayedFields=%5B%5D"
            f"&sortOrder=%22Descending%22&wrapLogMessage=false"
        )
        
        return CategoryModel(
            id="logs",
            label="Logs",
            icon="📋",
            status="ok",
            links=[
                LinkModel(
                    label=service_name,
                    url=url,
                )
            ],
        )
    
    def _generate_traces_category(self, service_name: str) -> CategoryModel:
        """Generate traces links."""
        import json
        from app.config import load_settings
        
        settings = load_settings()
        tempo_uid = settings.tempo_datasource_uid
        
        # Build the panes structure for Tempo explore matching Grafana's format
        panes_data = {
            "trc": {  # Random pane identifier
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
                        "value": [service_name],
                        "valueType": "string"
                    }]
                }],
                "range": {
                    "from": "now-1h",
                    "to": "now"
                }
            }
        }
        
        # Add datasource UID if configured
        if tempo_uid:
            panes_data["trc"]["datasource"] = tempo_uid
            panes_data["trc"]["queries"][0]["datasource"] = {
                "type": "tempo",
                "uid": tempo_uid
            }
        
        panes_encoded = quote(json.dumps(panes_data))
        
        url = (
            f"{self.grafana_base_url}/explore"
            f"?schemaVersion=1&panes={panes_encoded}&orgId=1"
        )
        
        return CategoryModel(
            id="traces",
            label="Traces",
            icon="🔍",
            status="ok",
            links=[
                LinkModel(
                    label=service_name,
                    url=url,
                )
            ],
        )
    
    def _generate_vault_category(self, external_secrets: List[dict]) -> CategoryModel:
        """Generate Vault secrets links."""
        if not external_secrets:
            return CategoryModel(
                id="vault",
                label="Vault Secrets",
                icon="🔐",
                status="empty",
                message="No ExternalSecrets configured for this application",
                links=[],
            )
        
        links = []
        for secret in external_secrets:
            spec = secret.get("spec", {})
            data_from = spec.get("dataFrom", [])
            
            for data_source in data_from:
                extract = data_source.get("extract", {})
                key = extract.get("key", "")
                
                if key:
                    # Extract path from key (e.g., "secret/postgres-details" -> "postgres-details")
                    path_parts = key.split("/", 1)
                    if len(path_parts) == 2:
                        secret_path = path_parts[1]
                        url = f"{self.vault_base_url}/ui/vault/secrets/secret/show/{secret_path}"
                        
                        links.append(
                            LinkModel(
                                label=secret_path,
                                url=url,
                            )
                        )
        
        if not links:
            return CategoryModel(
                id="vault",
                label="Vault Secrets",
                icon="🔐",
                status="empty",
                message="No secret paths found in ExternalSecrets",
                links=[],
            )
        
        return CategoryModel(
            id="vault",
            label="Vault Secrets",
            icon="🔐",
            status="ok",
            links=links,
        )
    
    def _generate_iaac_category(self, argocd_app: dict) -> CategoryModel:
        """Generate IaaC (Infrastructure as Code) links."""
        if not argocd_app:
            return CategoryModel(
                id="iaac",
                label="IaaC",
                icon="⚙️",
                status="error",
                message="ArgoCD application not found",
                links=[],
            )
        
        repo_url, app_path = K8sClient.parse_github_repo_from_argocd_app(argocd_app)
        
        if not repo_url or not app_path:
            return CategoryModel(
                id="iaac",
                label="IaaC",
                icon="⚙️",
                status="error",
                message="Unable to parse deployment configuration from ArgoCD manifest",
                links=[],
            )
        
        # Get target revision (branch)
        spec = argocd_app.get("spec", {})
        sources = spec.get("sources", [])
        branch = "main"  # default
        
        for source in sources:
            if source.get("ref") == "values":
                branch = source.get("targetRevision", "main")
                break
        
        # Construct GitHub URL
        github_url = f"{repo_url}/tree/{branch}/{app_path}"
        
        return CategoryModel(
            id="iaac",
            label="IaaC",
            icon="⚙️",
            status="ok",
            links=[
                LinkModel(
                    label="Deployment Configuration",
                    url=github_url,
                )
            ],
        )
