"""
Brightdata Proxy Configuration

Configuration management for Brightdata residential proxy service.
Handles credentials, zones, and proxy settings securely.
"""
import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BrightdataConfig:
    """Configuration for Brightdata proxy service."""
    
    username: str
    password: str
    endpoint: str
    port: int
    zone: str
    country: str = "DE"  # Germany by default for Edeka24
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not all([self.username, self.password, self.endpoint, self.port, self.zone]):
            raise ValueError("Missing required Brightdata configuration parameters")
    
    @property
    def proxy_url(self) -> str:
        """Generate complete proxy URL."""
        # Username ya incluye country y zone, usar directamente como en ejemplo oficial
        auth = f"{self.username}:{self.password}"
        return f"http://{auth}@{self.endpoint}:{self.port}"
    
    @property
    def proxy_dict(self) -> Dict[str, str]:
        """Generate proxy dictionary for requests."""
        proxy_url = self.proxy_url
        return {
            'http': proxy_url,
            'https': proxy_url
        }


class BrightdataConfigManager:
    """Manager for Brightdata configurations and multiple zones."""
    
    def __init__(self):
        self.configs: Dict[str, BrightdataConfig] = {}
        self.current_config_name: str = "default"
        self._load_from_environment()
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        try:
            # Default configuration
            default_config = BrightdataConfig(
                username=os.getenv('BRIGHTDATA_USERNAME', ''),
                password=os.getenv('BRIGHTDATA_PASSWORD', ''),
                endpoint=os.getenv('BRIGHTDATA_ENDPOINT', 'brd.superproxy.io'),
                port=int(os.getenv('BRIGHTDATA_PORT', '33335')),
                zone=os.getenv('BRIGHTDATA_ZONE', 'residential'),
                country=os.getenv('BRIGHTDATA_COUNTRY', 'DE')
            )
            
            self.configs['default'] = default_config
            logger.info("✅ Brightdata configuration loaded successfully")
            
        except ValueError as e:
            logger.warning(f"⚠️ Brightdata configuration incomplete: {e}")
        except Exception as e:
            logger.error(f"❌ Error loading Brightdata configuration: {e}")
    
    def add_config(self, name: str, config: BrightdataConfig):
        """Add a new configuration."""
        self.configs[name] = config
        logger.info(f"➕ Added Brightdata configuration: {name}")
    
    def get_config(self, name: str = None) -> Optional[BrightdataConfig]:
        """Get configuration by name or current default."""
        config_name = name or self.current_config_name
        return self.configs.get(config_name)
    
    def set_current_config(self, name: str):
        """Set the current active configuration."""
        if name in self.configs:
            self.current_config_name = name
            logger.info(f"🔄 Switched to Brightdata configuration: {name}")
        else:
            logger.error(f"❌ Configuration '{name}' not found")
    
    def get_available_configs(self) -> List[str]:
        """Get list of available configuration names."""
        return list(self.configs.keys())
    
    def is_enabled(self) -> bool:
        """Check if proxy is enabled and configured."""
        use_proxies = os.getenv('USE_PROXIES', 'false').lower() == 'true'
        has_config = bool(self.get_config())
        
        if use_proxies and not has_config:
            logger.warning("⚠️ USE_PROXIES is true but no valid Brightdata configuration found")
            return False
        
        return use_proxies and has_config
    
    def get_proxy_stats(self) -> Dict[str, any]:
        """Get current proxy configuration stats."""
        config = self.get_config()
        if not config:
            return {"enabled": False}
        
        return {
            "enabled": self.is_enabled(),
            "current_config": self.current_config_name,
            "endpoint": config.endpoint,
            "port": config.port,
            "zone": config.zone,
            "country": config.country,
            "available_configs": len(self.configs)
        }


# Global instance
brightdata_config = BrightdataConfigManager()


def get_brightdata_config() -> BrightdataConfigManager:
    """Get the global Brightdata configuration manager."""
    return brightdata_config