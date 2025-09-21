"""
Modelo de producto con soporte para embeddings vectoriales y búsqueda semántica.
"""
from sqlalchemy import (
    Column, String, Numeric, DateTime, ForeignKey, JSON, Text, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from .base import BaseModel
from ..config import Base


class Product(BaseModel):
    """
    Modelo de producto con capacidades de IA y búsqueda vectorial.
    """
    __tablename__ = 'products'
    
    # Basic product information
    name = Column(String, nullable=False, index=True)
    sku = Column(String(50), nullable=True, index=True)
    product_url = Column(String, unique=True, index=True, nullable=False)
    image_url = Column(String, nullable=True)
    
    # Price information
    price_amount = Column(Numeric(10, 2), nullable=True)
    price_currency = Column(String(10), default='EUR', nullable=False)
    base_price_amount = Column(Numeric(10, 2), nullable=True)
    base_price_unit = Column(String(20), nullable=True)  # e.g., 'kg', 'L', '100g'
    base_price_quantity = Column(Numeric(10, 2), nullable=True)
    
    # Detailed product information
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Structured product details
    
    # Nutritional information (if available)
    nutritional_info = Column(JSON, nullable=True)
    
    # Availability and stock
    in_stock = Column(String(20), default='unknown', nullable=False)  # 'in_stock', 'out_of_stock', 'unknown'
    availability_text = Column(String, nullable=True)
    
    # AI and Vector Search fields
    embedding = Column(Vector(1536), nullable=True)  # OpenAI embedding dimension
    embedding_model = Column(String(50), nullable=True)  # Model used for embedding
    embedding_updated_at = Column(DateTime, nullable=True)
    
    # Search optimization
    search_text = Column(Text, nullable=True, index=True)  # Concatenated searchable text
    search_vector = Column(Vector(1536), nullable=True)  # Search-optimized embedding
    
    # Metadata
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_price_update = Column(DateTime, nullable=True)
    scrape_count = Column(Numeric(10, 0), default=1, nullable=False)
    
    # Foreign keys
    store_id = Column(ForeignKey('stores.id'), nullable=False, index=True)
    category_id = Column(ForeignKey('categories.id'), nullable=True, index=True)
    manufacturer_id = Column(ForeignKey('manufacturers.id'), nullable=True, index=True)
    
    # Relationships
    store = relationship("Store", back_populates="products")
    category = relationship("Category", back_populates="products")
    manufacturer = relationship("Manufacturer", back_populates="products")
    
    # Indexes for performance
    __table_args__ = (
        # Index for vector similarity search
        Index('ix_products_embedding_vector', 'embedding', postgresql_using='ivfflat'),
        Index('ix_products_search_vector', 'search_vector', postgresql_using='ivfflat'),
        
        # Composite indexes for common queries
        Index('ix_products_store_category', 'store_id', 'category_id'),
        Index('ix_products_price_range', 'price_amount', 'store_id'),
        Index('ix_products_in_stock', 'in_stock', 'store_id'),
        
        # Full-text search index (using trigram similarity)
        Index('ix_products_search_text_gin', 'search_text', postgresql_using='gin', postgresql_ops={'search_text': 'gin_trgm_ops'}),
    )
    
    def generate_search_text(self) -> str:
        """
        Genera texto optimizado para búsqueda concatenando campos relevantes.
        """
        parts = []
        
        if self.name:
            parts.append(self.name)
        
        if self.description:
            parts.append(self.description)
            
        if self.details and isinstance(self.details, dict):
            # Extract text from structured details
            for key, value in self.details.items():
                if isinstance(value, str):
                    parts.append(value)
                elif isinstance(value, list):
                    parts.extend([str(v) for v in value if isinstance(v, str)])
        
        if self.category and hasattr(self.category, 'name'):
            parts.append(self.category.name)
            
        if self.manufacturer and hasattr(self.manufacturer, 'name'):
            parts.append(self.manufacturer.name)
        
        return ' '.join(parts).strip()
    
    def update_search_text(self):
        """Actualiza el campo search_text automáticamente."""
        self.search_text = self.generate_search_text()
    
    def needs_embedding_update(self) -> bool:
        """
        Verifica si el producto necesita actualizar su embedding.
        """
        if not self.embedding:
            return True
            
        if not self.embedding_updated_at:
            return True
            
        # Si el contenido ha cambiado después del último embedding
        if self.updated_at and self.embedding_updated_at:
            return self.updated_at > self.embedding_updated_at
            
        return False
    
    def get_embedding_text(self) -> str:
        """
        Genera el texto que será usado para crear embeddings.
        Optimizado para búsqueda semántica.
        """
        parts = []
        
        # Product name (most important)
        if self.name:
            parts.append(f"Producto: {self.name}")
        
        # Description
        if self.description:
            parts.append(f"Descripción: {self.description}")
        
        # Category information
        if self.category and hasattr(self.category, 'name'):
            parts.append(f"Categoría: {self.category.name}")
        
        # Brand/Manufacturer
        if self.manufacturer and hasattr(self.manufacturer, 'name'):
            parts.append(f"Marca: {self.manufacturer.name}")
        
        # Key details
        if self.details and isinstance(self.details, dict):
            key_fields = ['ingredients', 'features', 'benefits', 'usage', 'specifications']
            for field in key_fields:
                if field in self.details:
                    value = self.details[field]
                    if isinstance(value, str):
                        parts.append(f"{field.title()}: {value}")
                    elif isinstance(value, list):
                        parts.append(f"{field.title()}: {', '.join(map(str, value))}")
        
        # Nutritional info (for food products)
        if self.nutritional_info and isinstance(self.nutritional_info, dict):
            nutri_text = []
            for key, value in self.nutritional_info.items():
                if isinstance(value, (str, int, float)):
                    nutri_text.append(f"{key}: {value}")
            if nutri_text:
                parts.append(f"Información nutricional: {', '.join(nutri_text)}")
        
        # Price information
        if self.price_amount:
            price_text = f"Precio: {self.price_amount} {self.price_currency}"
            if self.base_price_amount and self.base_price_unit:
                price_text += f" ({self.base_price_amount} {self.price_currency}/{self.base_price_unit})"
            parts.append(price_text)
        
        return '\n'.join(parts)
    
    def to_dict(self, include_embedding: bool = False, exclude: set = None) -> Dict[str, Any]:
        """
        Convierte el modelo a diccionario con opciones específicas para embeddings.
        
        Args:
            include_embedding: Si incluir el campo embedding en el resultado
            exclude: Campos adicionales a excluir
        """
        default_exclude = {'embedding', 'search_vector'} if not include_embedding else {'search_vector'}
        if exclude:
            default_exclude.update(exclude)
            
        result = super().to_dict(exclude=default_exclude)
        
        # Add computed fields
        result['search_text_generated'] = self.generate_search_text()
        result['needs_embedding_update'] = self.needs_embedding_update()
        
        return result
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', store_id={self.store_id})>"
