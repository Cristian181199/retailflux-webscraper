"""
Repositorios de datos con Repository Pattern.
"""
from .base import BaseRepository
from .product import ProductRepository, product_repository
from .category import CategoryRepository, category_repository
from .store import StoreRepository, store_repository
from .manufacturer import ManufacturerRepository, manufacturer_repository

__all__ = [
    "BaseRepository",
    "ProductRepository", "product_repository",
    "CategoryRepository", "category_repository",
    "StoreRepository", "store_repository",
    "ManufacturerRepository", "manufacturer_repository",
]
