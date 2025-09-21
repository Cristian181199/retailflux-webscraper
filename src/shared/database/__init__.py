"""
Módulo principal de base de datos con modelos y repositorios.
"""
from .config import (
    Base, 
    engine, 
    SessionLocal, 
    db_manager,
    get_db,
    create_tables,
    test_connection
)

from .models import (
    BaseModel,
    Product,
    Category, 
    Store,
    Manufacturer
)

from .repositories import (
    BaseRepository,
    product_repository,
    category_repository,
    store_repository,
    manufacturer_repository
)

__all__ = [
    # Database config and utilities
    "Base",
    "engine", 
    "SessionLocal",
    "db_manager",
    "get_db",
    "create_tables",
    "test_connection",
    
    # Models
    "BaseModel",
    "Product",
    "Category",
    "Store", 
    "Manufacturer",
    
    # Repositories
    "BaseRepository",
    "product_repository",
    "category_repository", 
    "store_repository",
    "manufacturer_repository"
]
