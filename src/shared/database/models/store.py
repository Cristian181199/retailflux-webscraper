"""
Modelo de tienda/supermercado.
"""
from sqlalchemy import Column, String, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from typing import Dict, Any, Optional

from .base import BaseModel


class Store(BaseModel):
    """
    Modelo de tienda/supermercado con información de configuración.
    """
    __tablename__ = 'stores'
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)  # Friendly display name
    
    # Store details
    description = Column(Text, nullable=True)
    website_url = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    # Geographic information
    country = Column(String(2), nullable=False, default='DE')  # ISO country code
    currency = Column(String(3), nullable=False, default='EUR')  # ISO currency code
    
    # Configuration for scraping
    scraper_config = Column(JSON, nullable=True)  # Store-specific scraper settings
    api_config = Column(JSON, nullable=True)      # API configuration if available
    
    # Operational status
    is_active = Column(Boolean, default=True, nullable=False)
    is_scraping_enabled = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    last_scrape_at = Column(String, nullable=True)
    scrape_frequency = Column(String(50), default='daily', nullable=False)  # daily, weekly, etc.
    
    # Relationships
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    
    def get_scraper_settings(self) -> Dict[str, Any]:
        """
        Obtiene la configuración específica del scraper para esta tienda.
        """
        default_config = {
            'concurrent_requests': 2,
            'download_delay': 1.0,
            'user_agent': 'Mozilla/5.0 (compatible; ProductScraper/1.0)',
            'respect_robots_txt': True,
            'enable_javascript': False
        }
        
        if self.scraper_config:
            default_config.update(self.scraper_config)
            
        return default_config
    
    def get_api_settings(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración de API si está disponible.
        """
        return self.api_config
    
    def supports_api(self) -> bool:
        """
        Verifica si la tienda tiene configuración de API.
        """
        return self.api_config is not None and len(self.api_config) > 0
    
    def get_base_url(self) -> Optional[str]:
        """
        Obtiene la URL base para scraping.
        """
        if self.scraper_config and 'base_url' in self.scraper_config:
            return self.scraper_config['base_url']
        return self.website_url
    
    def to_dict(self, include_config: bool = False, exclude: set = None) -> Dict[str, Any]:
        """
        Convierte el modelo a diccionario.
        """
        default_exclude = set()
        if not include_config:
            default_exclude.update({'scraper_config', 'api_config'})
        
        if exclude:
            default_exclude.update(exclude)
            
        result = super().to_dict(exclude=default_exclude)
        
        # Add computed fields
        result['supports_api'] = self.supports_api()
        result['base_url'] = self.get_base_url()
        
        return result
    
    def __repr__(self):
        return f"<Store(id={self.id}, name='{self.name}', country='{self.country}')>"
