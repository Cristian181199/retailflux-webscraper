"""
Repository para tiendas/supermercados.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.store import Store


class StoreRepository(BaseRepository[Store]):
    """Repository para tiendas con funciones específicas."""
    
    def __init__(self):
        super().__init__(Store)
    
    def get_by_slug(self, db: Session, slug: str) -> Optional[Store]:
        """Obtiene una tienda por su slug."""
        return db.query(Store).filter(Store.slug == slug).first()
    
    def get_active_stores(self, db: Session) -> List[Store]:
        """Obtiene solo las tiendas activas."""
        return db.query(Store).filter(Store.is_active == True).all()
    
    def get_stores_with_scraping_enabled(self, db: Session) -> List[Store]:
        """Obtiene tiendas con scraping habilitado."""
        return db.query(Store).filter(
            Store.is_active == True,
            Store.is_scraping_enabled == True
        ).all()
    
    def get_by_country(self, db: Session, country: str) -> List[Store]:
        """Obtiene tiendas por país."""
        return db.query(Store).filter(
            Store.country == country,
            Store.is_active == True
        ).all()


# Global instance
store_repository = StoreRepository()
