"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
import structlog

from app.config import load_settings
from app.logging_config import configure_logging
from app.models import HealthResponse, ReadyResponse, LinksResponse
from app.cache import CacheManager
from app.k8s_client import K8sClient
from app.links_generator import LinksGenerator
from app.fixtures import get_fixture, FIXTURES

# Load settings and configure logging
settings = load_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("app_starting")
    
    # Initialize cache
    app.state.cache = CacheManager(settings.valkey_url, settings.cache_ttl_seconds)
    
    # Initialize K8s client
    app.state.k8s_client = K8sClient()
    
    # Initialize links generator
    app.state.links_generator = LinksGenerator(
        k8s_client=app.state.k8s_client,
        grafana_base_url=settings.grafana_base_url,
        vault_base_url=settings.vault_base_url,
        captain_domain=settings.captain_domain,
        max_rows=settings.max_rows,
    )
    
    logger.info("app_started")
    
    yield
    
    logger.info("app_shutting_down")
    app.state.cache.close()
    logger.info("app_stopped")


app = FastAPI(
    title="GlueLinks API",
    description="Backend API for ArgoCD GlueOps Extension",
    version="2.1.0",
    lifespan=lifespan,
)


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/api/v1/ready", response_model=ReadyResponse, tags=["Health"])
async def readiness_check(request: Request):
    """Readiness check endpoint."""
    checks = {
        "cache": False,
        "kubernetes": False,
    }
    
    # Check cache
    try:
        request.app.state.cache.ping()
        checks["cache"] = True
    except Exception as e:
        logger.warning("readiness_cache_failed", error=str(e))
    
    # Check K8s
    try:
        request.app.state.k8s_client.ping()
        checks["kubernetes"] = True
    except Exception as e:
        logger.warning("readiness_k8s_failed", error=str(e))
    
    ready = all(checks.values())
    
    return ReadyResponse(
        ready=ready,
        checks=checks,
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/api/v1/applications/{app_name}/links", response_model=LinksResponse, tags=["Links"])
async def get_application_links(
    request: Request,
    app_name: str,
    argocd_application_name: str = Header(..., alias="Argocd-Application-Name"),
):
    """
    Get links for an ArgoCD application.
    
    - **app_name**: Application name from URL path
    - **Argocd-Application-Name**: Header in format 'namespace:app_name'
    """
    log = logger.bind(app_name=app_name, header=argocd_application_name)
    log.info("request_received")
    
    # Check if mock mode is enabled
    if settings.use_mock_data:
        log.info("using_mock_data", fixture=settings.default_mock_fixture)
        return get_fixture(settings.default_mock_fixture, app_name=app_name)
    
    # Parse header
    try:
        namespace, header_app_name = argocd_application_name.split(":", 1)
    except ValueError:
        log.error("invalid_header_format", header=argocd_application_name)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Argocd-Application-Name header format. Expected 'namespace:app_name', got '{argocd_application_name}'",
        )
    
    # Validate app_name matches
    if app_name != header_app_name:
        log.warning(
            "app_name_mismatch",
            url_app_name=app_name,
            header_app_name=header_app_name,
        )
        raise HTTPException(
            status_code=400,
            detail=f"Application name mismatch: URL has '{app_name}' but header has '{header_app_name}'",
        )
    
    log = log.bind(namespace=namespace)
    
    # Check cache
    cache_key = f"gluelinks:v1:{namespace}:{app_name}"
    cached = request.app.state.cache.get(cache_key)
    
    if cached:
        log.info("cache_hit")
        return LinksResponse(**cached)
    
    log.info("cache_miss")
    
    # Generate links
    try:
        response = await request.app.state.links_generator.generate_links(
            app_name=app_name,
            namespace=namespace,
        )
        
        # Cache the response
        request.app.state.cache.set(cache_key, response.model_dump())
        
        log.info("links_generated", categories=len(response.categories))
        return response
        
    except Exception as e:
        log.error("links_generation_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate links. Check logs for details.",
        )


@app.get("/api/v1/mock/applications/{app_name}/links", tags=["Mock"])
async def get_mock_application_links(app_name: str):
    """
    Get mock links for an application.
    Uses the DEFAULT_MOCK_FIXTURE environment variable (defaults to 'all-ok').
    
    - **app_name**: Application name to use in the mock response
    
    No authentication or headers required.
    """
    fixture_name = settings.default_mock_fixture
    logger.info("mock_request", app_name=app_name, fixture=fixture_name)
    return get_fixture(fixture_name, app_name=app_name)


@app.get("/api/v1/fixtures/{fixture_name}", tags=["Mock"])
async def get_fixture_data(fixture_name: str):
    """
    Get a specific test fixture by name.
    Use these endpoints to test different UI states in the extension.
    
    Available fixtures:
    - **all-ok**: All categories populated with working links (happy path)
    - **error-states**: Various error and empty states for testing error handling
    - **partial-data**: Mix of working and empty/error categories
    - **minimal**: Only namespace and IaaC links, everything else empty
    
    Returns mock data with default app_name and namespace.
    """
    logger.info("fixture_request", fixture_name=fixture_name)
    
    if fixture_name not in FIXTURES:
        available = ", ".join(FIXTURES.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Fixture '{fixture_name}' not found. Available fixtures: {available}"
        )
    
    return get_fixture(fixture_name)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
