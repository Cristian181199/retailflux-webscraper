"""
Repository para categorías con soporte jerárquico.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .base import BaseRepository
from ..models.category import Category


class CategoryRepository(BaseRepository[Category]):
    """Repository especializado para categorías con funciones jerárquicas."""
    
    def __init__(self):
        super().__init__(Category)
    
    def get_root_categories(self, db: Session) -> List[Category]:
        """Obtiene categorías raíz (sin padre)."""
        return db.query(Category).filter(Category.parent_id.is_(None)).all()
    
    def get_children(self, db: Session, parent_id: int) -> List[Category]:
        """Obtiene categorías hijas de una categoría padre."""
        return db.query(Category).filter(Category.parent_id == parent_id).all()
    
    def get_by_slug(self, db: Session, slug: str) -> Optional[Category]:
        """Obtiene una categoría por su slug."""
        return db.query(Category).filter(Category.slug == slug).first()
    
    def get_category_tree(self, db: Session, parent_id: Optional[int] = None) -> List[dict]:
        """
        Obtiene el árbol de categorías de forma recursiva.
        """
        if parent_id is None:
            categories = self.get_root_categories(db)
        else:
            categories = self.get_children(db, parent_id)
        
        result = []
        for category in categories:
            children = self.get_category_tree(db, category.id)
            result.append({
                'category': category,
                'children': children
            })
        
        return result
    
    def get_all_descendants(self, db: Session, parent_id: int) -> List[Category]:
        """
        Obtiene todos los descendientes de una categoría de forma recursiva.
        """
        descendants = []
        children = self.get_children(db, parent_id)
        
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_all_descendants(db, child.id))
        
        return descendants


# Global instance
category_repository = CategoryRepository()
