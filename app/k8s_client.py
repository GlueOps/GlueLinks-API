"""Kubernetes client wrapper."""
import re
from typing import List, Optional, Tuple
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import structlog

logger = structlog.get_logger()

# Service name regex pattern
SERVICE_NAME_REGEX = re.compile(
    r'^(?P<service_prefix>.+?)(-[0-9a-f]{9,}(-[a-z0-9]{4,})?|-[0-9]+|-[a-z0-9]{4,6})?$'
)


class K8sClient:
    """Kubernetes API client wrapper."""
    
    def __init__(self):
        """Initialize Kubernetes client."""
        try:
            # Try in-cluster config first, fall back to kubeconfig
            try:
                config.load_incluster_config()
                logger.info("k8s_client_initialized", mode="in-cluster")
            except config.ConfigException:
                config.load_kube_config()
                logger.info("k8s_client_initialized", mode="kubeconfig")
            
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            self.custom_objects = client.CustomObjectsApi()
            
        except Exception as e:
            logger.critical("k8s_client_init_failed", error=str(e))
            raise
    
    def ping(self) -> bool:
        """Check if K8s API is accessible."""
        try:
            self.core_v1.get_api_resources()
            return True
        except Exception:
            return False
    
    @staticmethod
    def extract_service_name(app_name: str) -> str:
        """
        Extract service name from app name using regex.
        
        Examples:
            taco-backend-prod -> taco-backend-prod (no suffix)
            taco-backend-prod-677bfb55b7-942nr -> taco-backend-prod
        """
        match = SERVICE_NAME_REGEX.match(app_name)
        if match:
            service_name = match.group('service_prefix')
            logger.debug("service_name_extracted", app_name=app_name, service_name=service_name)
            return service_name
        
        logger.warning("service_name_regex_failed", app_name=app_name)
        return app_name
    
    def get_argocd_application(self, name: str, namespace: str) -> Optional[dict]:
        """
        Get ArgoCD Application resource.
        
        ArgoCD applications are typically in glueops-core namespace,
        not in the target deployment namespace.
        """
        # Try glueops-core first (common convention)
        argocd_namespaces = ["glueops-core", "argocd", namespace]
        
        for argocd_ns in argocd_namespaces:
            try:
                app = self.custom_objects.get_namespaced_custom_object(
                    group="argoproj.io",
                    version="v1alpha1",
                    namespace=argocd_ns,
                    plural="applications",
                    name=name,
                )
                logger.debug("argocd_app_found", name=name, namespace=argocd_ns)
                return app
            except ApiException as e:
                if e.status == 404:
                    continue
                else:
                    logger.error("argocd_app_fetch_failed", name=name, namespace=argocd_ns, error=str(e))
        
        logger.warning("argocd_app_not_found", name=name, tried_namespaces=argocd_namespaces)
        return None
    
    def get_deployment(self, name: str, namespace: str) -> Optional[client.V1Deployment]:
        """Get Deployment by tracking ID annotation."""
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            
            tracking_id_prefix = f"{name}:apps/Deployment:{namespace}/"
            
            for deployment in deployments.items:
                annotations = deployment.metadata.annotations or {}
                tracking_id = annotations.get("argocd.argoproj.io/tracking-id", "")
                
                if tracking_id.startswith(tracking_id_prefix):
                    logger.debug(
                        "deployment_found",
                        name=deployment.metadata.name,
                        namespace=namespace,
                        tracking_id=tracking_id,
                    )
                    return deployment
            
            logger.warning("deployment_not_found", app_name=name, namespace=namespace)
            return None
            
        except ApiException as e:
            logger.error("deployment_fetch_failed", app_name=name, namespace=namespace, error=str(e))
            return None
    
    def get_first_pod(self, deployment_name: str, namespace: str) -> Optional[client.V1Pod]:
        """Get first pod from a deployment."""
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app.kubernetes.io/name={deployment_name}",
            )
            
            if pods.items:
                pod = pods.items[0]
                logger.debug("pod_found", name=pod.metadata.name, namespace=namespace)
                return pod
            
            logger.warning("no_pods_found", deployment=deployment_name, namespace=namespace)
            return None
            
        except ApiException as e:
            logger.error("pod_fetch_failed", deployment=deployment_name, namespace=namespace, error=str(e))
            return None
    
    def get_external_secrets(self, app_name: str, namespace: str) -> List[dict]:
        """Get ExternalSecret resources by tracking ID annotation."""
        try:
            secrets = self.custom_objects.list_namespaced_custom_object(
                group="external-secrets.io",
                version="v1",
                namespace=namespace,
                plural="externalsecrets",
            )
            
            tracking_id_prefix = f"{app_name}:external-secrets.io/ExternalSecret:{namespace}/"
            
            matching_secrets = []
            for secret in secrets.get("items", []):
                annotations = secret.get("metadata", {}).get("annotations", {})
                tracking_id = annotations.get("argocd.argoproj.io/tracking-id", "")
                
                if tracking_id.startswith(tracking_id_prefix):
                    matching_secrets.append(secret)
                    logger.debug(
                        "external_secret_found",
                        name=secret.get("metadata", {}).get("name"),
                        namespace=namespace,
                        tracking_id=tracking_id,
                    )
            
            logger.info(
                "external_secrets_fetched",
                app_name=app_name,
                namespace=namespace,
                count=len(matching_secrets),
            )
            return matching_secrets
            
        except ApiException as e:
            if e.status == 404:
                logger.warning("external_secrets_crd_not_found")
            else:
                logger.error("external_secrets_fetch_failed", app_name=app_name, namespace=namespace, error=str(e))
            return []
    
    @staticmethod
    def parse_github_repo_from_argocd_app(argocd_app: dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse GitHub repo URL and app path from ArgoCD application manifest.
        
        Returns:
            Tuple of (github_repo_url, app_path) or (None, None)
        """
        try:
            spec = argocd_app.get("spec", {})
            sources = spec.get("sources", [])
            
            # Find the values repo (has ref: values)
            values_repo = None
            for source in sources:
                if source.get("ref") == "values":
                    values_repo = source.get("repoURL")
                    break
            
            if not values_repo:
                logger.warning("values_repo_not_found")
                return None, None
            
            # Find the helm source with valueFiles
            helm_source = None
            for source in sources:
                if "helm" in source and "valueFiles" in source["helm"]:
                    helm_source = source
                    break
            
            if not helm_source:
                logger.warning("helm_source_not_found")
                return None, None
            
            # Parse the value files to extract app path
            # Example: $values/apps/taco-backend/base/base-values.yaml
            value_files = helm_source["helm"]["valueFiles"]
            
            for value_file in value_files:
                if "/apps/" in value_file and "/base/" in value_file:
                    # Extract: apps/taco-backend
                    parts = value_file.split("/")
                    try:
                        apps_idx = parts.index("apps")
                        app_name_part = parts[apps_idx + 1]
                        app_path = f"apps/{app_name_part}"
                        
                        logger.debug(
                            "github_repo_parsed",
                            repo_url=values_repo,
                            app_path=app_path,
                        )
                        return values_repo, app_path
                    except (ValueError, IndexError):
                        continue
            
            logger.warning("app_path_not_parsed", value_files=value_files)
            return None, None
            
        except Exception as e:
            logger.error("github_repo_parse_failed", error=str(e))
            return None, None
