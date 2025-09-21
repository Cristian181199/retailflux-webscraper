"""
Product Item Definition

Definición de items Scrapy compatible con los nuevos modelos de base de datos.
Incluye todos los campos necesarios para la nueva arquitectura.
"""
import scrapy
from datetime import datetime
from typing import Optional, Dict, List, Any


class ModernProductItem(scrapy.Item):
    """
    Item moderno para productos, compatible con el modelo Product de la nueva arquitectura.
    
    Incluye todos los campos del modelo Product más campos adicionales para 
    procesamiento y transformación de datos.
    """
    
    # ==========================================
    # BASIC PRODUCT INFORMATION
    # ==========================================
    name = scrapy.Field()  # Product name
    sku = scrapy.Field()   # Product SKU/identifier
    product_url = scrapy.Field()  # Product page URL (unique)
    image_url = scrapy.Field()    # Product image URL
    
    # ==========================================
    # PRICE INFORMATION
    # ==========================================
    price_amount = scrapy.Field()     # Main price as decimal
    price_currency = scrapy.Field()   # Currency (EUR, USD, etc.)
    
    # Base price information (per unit)
    base_price_text = scrapy.Field()     # Raw text "1.99 € / 100g"
    base_price_amount = scrapy.Field()   # Parsed base price
    base_price_unit = scrapy.Field()     # Unit (kg, L, 100g, etc.)
    base_price_quantity = scrapy.Field() # Quantity for base price
    
    # ==========================================
    # CONTENT & DESCRIPTION
    # ==========================================
    description = scrapy.Field()      # Product description
    details = scrapy.Field()          # Structured details (JSON)
    nutritional_info = scrapy.Field() # Nutritional information (JSON)
    
    # ==========================================
    # AVAILABILITY & STOCK
    # ==========================================
    in_stock = scrapy.Field()         # Stock status: 'in_stock', 'out_of_stock', 'unknown'
    availability_text = scrapy.Field() # Raw availability text from page
    
    # ==========================================
    # RELATIONAL DATA
    # ==========================================
    store_name = scrapy.Field()        # Store name
    store_slug = scrapy.Field()        # Store slug/identifier
    category_path = scrapy.Field()     # Category breadcrumb list
    manufacturer_name = scrapy.Field() # Brand/manufacturer name
    
    # ==========================================
    # METADATA & SCRAPING INFO
    # ==========================================
    scraped_at = scrapy.Field()        # Timestamp of scraping
    last_price_update = scrapy.Field() # When price was last updated
    scrape_count = scrapy.Field()      # Number of times scraped
    
    # ==========================================
    # PROCESSING FLAGS
    # ==========================================
    needs_embedding = scrapy.Field()   # Flag to generate embedding
    price_changed = scrapy.Field()     # Flag if price changed
    is_new_product = scrapy.Field()    # Flag if product is new
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values
        self.setdefault('scraped_at', datetime.utcnow())
        self.setdefault('price_currency', 'EUR')
        self.setdefault('in_stock', 'unknown')
        self.setdefault('scrape_count', 1)
        self.setdefault('needs_embedding', True)
        self.setdefault('is_new_product', True)
        self.setdefault('price_changed', False)


class CategoryItem(scrapy.Item):
    """Item para categorías de productos."""
    name = scrapy.Field()
    slug = scrapy.Field()
    description = scrapy.Field()
    parent_name = scrapy.Field()  # Parent category name
    level = scrapy.Field()        # Hierarchy level
    path = scrapy.Field()         # Full path
    

class StoreItem(scrapy.Item):
    """Item para información de tiendas."""
    name = scrapy.Field()
    slug = scrapy.Field()
    display_name = scrapy.Field()
    description = scrapy.Field()
    website_url = scrapy.Field()
    country = scrapy.Field()
    currency = scrapy.Field()


class ManufacturerItem(scrapy.Item):
    """Item para fabricantes/marcas."""
    name = scrapy.Field()
    slug = scrapy.Field()
    display_name = scrapy.Field()
    description = scrapy.Field()
    website_url = scrapy.Field()
    country = scrapy.Field()
