"""Application configuration."""
import sys
from pydantic_settings import BaseSettings
from pydantic import Field
import structlog

logger = structlog.get_logger()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Base URLs (required)
    grafana_base_url: str = Field(..., description="Grafana base URL")
    vault_base_url: str = Field(..., description="Vault base URL")
    
    # Valkey connection (required)
    valkey_url: str = Field(..., description="Valkey connection URL")
    
    # Captain domain for Quick Links
    captain_domain: str = Field(
        default="nonprod.antoniostacos.onglueops.com",
        description="Captain domain for Quick Links URLs"
    )
    
    # Grafana datasource UIDs (optional, but recommended for working Tempo links)
    tempo_datasource_uid: str = Field(default="", description="Tempo datasource UID in Grafana")
    
    # Cache configuration
    cache_ttl_seconds: int = Field(default=30, description="Cache TTL in seconds")
    
    # UI configuration
    max_rows: int = Field(default=4, description="Maximum number of rows to display per category")
    
    # Mock/demo mode configuration
    use_mock_data: bool = Field(default=False, description="Use mock data instead of real K8s queries")
    default_mock_fixture: str = Field(
        default="all-ok",
        description="Default fixture for mock responses (all-ok, error-states, partial-data, minimal)"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    
    class Config:
        env_file = ".env.local"
        case_sensitive = False


def load_settings() -> Settings:
    """Load and validate settings, exit if required vars are missing."""
    try:
        settings = Settings()
        logger.info(
            "settings_loaded",
            grafana_base_url=settings.grafana_base_url,
            vault_base_url=settings.vault_base_url,
            cache_ttl_seconds=settings.cache_ttl_seconds,
            log_level=settings.log_level,
        )
        return settings
    except Exception as e:
        logger.critical(
            "settings_load_failed",
            error=str(e),
            message="Required environment variables are missing. Check .env.local",
        )
        sys.exit(1)
