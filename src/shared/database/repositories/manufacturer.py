"""
Repository para fabricantes/marcas.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from .base import BaseRepository
from ..models.manufacturer import Manufacturer


class ManufacturerRepository(BaseRepository[Manufacturer]):
    """Repository para fabricantes con funciones específicas."""
    
    def __init__(self):
        super().__init__(Manufacturer)
    
    def get_by_name(self, db: Session, name: str) -> Optional[Manufacturer]:
        """Obtiene un fabricante por nombre exacto."""
        return db.query(Manufacturer).filter(
            func.lower(Manufacturer.name) == name.lower()
        ).first()
    
    def get_by_slug(self, db: Session, slug: str) -> Optional[Manufacturer]:
        """Obtiene un fabricante por su slug."""
        return db.query(Manufacturer).filter(Manufacturer.slug == slug).first()
    
    def search_by_name(self, db: Session, name_query: str, limit: int = 10) -> List[Manufacturer]:
        """Busca fabricantes por nombre (búsqueda parcial)."""
        return db.query(Manufacturer).filter(
            Manufacturer.name.ilike(f"%{name_query}%")
        ).limit(limit).all()
    
    def get_verified_manufacturers(self, db: Session) -> List[Manufacturer]:
        """Obtiene fabricantes verificados."""
        return db.query(Manufacturer).filter(
            Manufacturer.is_verified == True,
            Manufacturer.is_active == True
        ).all()
    
    def get_organic_brands(self, db: Session) -> List[Manufacturer]:
        """Obtiene marcas orgánicas."""
        return db.query(Manufacturer).filter(
            Manufacturer.brand_category.ilike('%organic%')
        ).all()
    
    def get_by_country(self, db: Session, country: str) -> List[Manufacturer]:
        """Obtiene fabricantes por país."""
        return db.query(Manufacturer).filter(
            Manufacturer.country == country,
            Manufacturer.is_active == True
        ).all()


# Global instance
manufacturer_repository = ManufacturerRepository()
