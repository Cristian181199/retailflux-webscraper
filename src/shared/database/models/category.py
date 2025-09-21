"""
Modelo de categoría de productos con soporte jerárquico.
"""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from typing import List, Optional, Dict, Any

from .base import BaseModel


class Category(BaseModel):
    """
    Modelo de categoría de productos con soporte para jerarquías.
    """
    __tablename__ = 'categories'
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=True, index=True)  # URL-friendly name
    description = Column(Text, nullable=True)
    
    # Hierarchy support
    parent_id = Column(ForeignKey('categories.id'), nullable=True, index=True)
    level = Column(String(10), default=0, nullable=False)  # Depth in hierarchy
    path = Column(String(1000), nullable=True)  # Full path like "food/dairy/milk"
    
    # Metadata
    is_active = Column(String(1), default=True, nullable=False)
    sort_order = Column(String(10), default=0, nullable=False)
    
    # Relationships
    parent = relationship("Category", remote_side="Category.id", back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="category")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'parent_id', name='_category_parent_uc'),
        UniqueConstraint('slug', name='_category_slug_uc'),
    )
    
    def get_full_path(self) -> str:
        """
        Genera la ruta completa de la categoría.
        Ej: "Alimentación > Lácteos > Leche"
        """
        if not self.parent:
            return self.name
        return f"{self.parent.get_full_path()} > {self.name}"
    
    def get_url_path(self) -> str:
        """
        Genera la ruta URL-friendly de la categoría.
        Ej: "alimentacion/lacteos/leche"
        """
        if not self.parent:
            return self.slug or self.name.lower().replace(' ', '-')
        return f"{self.parent.get_url_path()}/{self.slug or self.name.lower().replace(' ', '-')}"
    
    def get_all_children_ids(self) -> List[int]:
        """
        Obtiene todos los IDs de categorías hijas (recursivo).
        """
        child_ids = [self.id]
        for child in self.children:
            child_ids.extend(child.get_all_children_ids())
        return child_ids
    
    def get_breadcrumbs(self) -> List[Dict[str, Any]]:
        """
        Genera breadcrumbs para navegación.
        """
        breadcrumbs = []
        if self.parent:
            breadcrumbs.extend(self.parent.get_breadcrumbs())
        
        breadcrumbs.append({
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'url_path': self.get_url_path()
        })
        return breadcrumbs
    
    def update_path(self):
        """Actualiza automáticamente el campo path basado en la jerarquía."""
        if self.parent:
            parent_path = self.parent.path or self.parent.name
            self.path = f"{parent_path}/{self.name}"
            self.level = self.parent.level + 1
        else:
            self.path = self.name
            self.level = 0
    
    def to_dict(self, include_children: bool = False, exclude: set = None) -> Dict[str, Any]:
        """
        Convierte el modelo a diccionario con opciones específicas.
        """
        result = super().to_dict(exclude=exclude)
        
        # Add computed fields
        result['full_path'] = self.get_full_path()
        result['url_path'] = self.get_url_path()
        result['breadcrumbs'] = self.get_breadcrumbs()
        
        if include_children and self.children:
            result['children'] = [child.to_dict(include_children=False) for child in self.children]
        
        return result
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"
