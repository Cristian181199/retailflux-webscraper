"""
Items Package

Contiene las definiciones de items Scrapy para la nueva arquitectura.
"""

from .product_item import (
    ModernProductItem,
    CategoryItem,
    StoreItem,
    ManufacturerItem
)

__all__ = [
    'ModernProductItem',
    'CategoryItem', 
    'StoreItem',
    'ManufacturerItem'
]
