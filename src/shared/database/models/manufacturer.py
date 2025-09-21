"""
Modelo de fabricante/marca de productos.
"""
from sqlalchemy import Column, String, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from typing import Dict, Any, Optional

from .base import BaseModel


class Manufacturer(BaseModel):
    """
    Modelo de fabricante/marca de productos.
    """
    __tablename__ = 'manufacturers'
    
    # Basic information
    name = Column(String(255), nullable=False, index=True, unique=True)
    slug = Column(String(255), unique=True, nullable=True, index=True)
    display_name = Column(String(255), nullable=True)  # Brand display name
    
    # Company details
    description = Column(Text, nullable=True)
    website_url = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    # Geographic and contact info
    country = Column(String(2), nullable=True)  # ISO country code
    contact_info = Column(JSON, nullable=True)  # Email, phone, address, etc.
    
    # Brand information
    parent_company = Column(String(255), nullable=True)  # If it's a subsidiary
    brand_category = Column(String(100), nullable=True)  # Luxury, budget, organic, etc.
    
    # Operational status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # Verified manufacturer
    
    # Metadata for search and filtering
    keywords = Column(JSON, nullable=True)  # Search keywords and aliases
    certifications = Column(JSON, nullable=True)  # Organic, Fair Trade, etc.
    
    # Relationships
    products = relationship("Product", back_populates="manufacturer")
    
    def get_search_keywords(self) -> list:
        """
        Obtiene todas las palabras clave de búsqueda incluyendo nombre y alias.
        """
        keywords = [self.name]
        
        if self.display_name and self.display_name != self.name:
            keywords.append(self.display_name)
            
        if self.keywords and isinstance(self.keywords, list):
            keywords.extend(self.keywords)
            
        return list(set(keywords))  # Remove duplicates
    
    def get_contact_email(self) -> Optional[str]:
        """
        Obtiene el email de contacto principal.
        """
        if self.contact_info and 'email' in self.contact_info:
            return self.contact_info['email']
        return None
    
    def get_certifications_list(self) -> list:
        """
        Obtiene la lista de certificaciones.
        """
        if self.certifications and isinstance(self.certifications, list):
            return self.certifications
        return []
    
    def has_certification(self, certification: str) -> bool:
        """
        Verifica si el fabricante tiene una certificación específica.
        """
        certifications = self.get_certifications_list()
        return certification.lower() in [cert.lower() for cert in certifications]
    
    def is_organic_brand(self) -> bool:
        """
        Verifica si es una marca orgánica.
        """
        organic_keywords = ['organic', 'bio', 'orgánico', 'ecológico', 'eco']
        
        # Check in certifications
        if any(keyword in cert.lower() for cert in self.get_certifications_list() for keyword in organic_keywords):
            return True
            
        # Check in name or brand category
        if self.brand_category and any(keyword in self.brand_category.lower() for keyword in organic_keywords):
            return True
            
        return False
    
    def get_url_slug(self) -> str:
        """
        Genera un slug URL-friendly.
        """
        if self.slug:
            return self.slug
        return self.name.lower().replace(' ', '-').replace('&', 'and')
    
    def to_dict(self, include_contact: bool = False, exclude: set = None) -> Dict[str, Any]:
        """
        Convierte el modelo a diccionario.
        """
        default_exclude = set()
        if not include_contact:
            default_exclude.add('contact_info')
        
        if exclude:
            default_exclude.update(exclude)
            
        result = super().to_dict(exclude=default_exclude)
        
        # Add computed fields
        result['search_keywords'] = self.get_search_keywords()
        result['certifications_list'] = self.get_certifications_list()
        result['is_organic'] = self.is_organic_brand()
        result['url_slug'] = self.get_url_slug()
        
        if include_contact:
            result['contact_email'] = self.get_contact_email()
        
        return result
    
    def __repr__(self):
        return f"<Manufacturer(id={self.id}, name='{self.name}', country='{self.country}')>"
