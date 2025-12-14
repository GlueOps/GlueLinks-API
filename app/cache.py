"""Cache manager using Valkey/Redis."""
import json
from typing import Optional
import valkey
import structlog

logger = structlog.get_logger()


class CacheManager:
    """Manages caching with Valkey/Redis."""
    
    def __init__(self, valkey_url: str, ttl_seconds: int):
        """Initialize cache manager."""
        self.client = valkey.from_url(valkey_url, decode_responses=True)
        self.ttl_seconds = ttl_seconds
        logger.info("cache_initialized", ttl_seconds=ttl_seconds)
    
    def get(self, key: str) -> Optional[dict]:
        """Get value from cache."""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning("cache_get_failed", key=key, error=str(e))
            return None
    
    def set(self, key: str, value: dict) -> None:
        """Set value in cache with TTL."""
        try:
            self.client.setex(
                key,
                self.ttl_seconds,
                json.dumps(value, default=str),
            )
            logger.debug("cache_set", key=key, ttl=self.ttl_seconds)
        except Exception as e:
            logger.warning("cache_set_failed", key=key, error=str(e))
    
    def ping(self) -> bool:
        """Check if cache is available."""
        try:
            return self.client.ping()
        except Exception:
            return False
    
    def close(self) -> None:
        """Close cache connection."""
        try:
            self.client.close()
            logger.info("cache_closed")
        except Exception as e:
            logger.warning("cache_close_failed", error=str(e))
