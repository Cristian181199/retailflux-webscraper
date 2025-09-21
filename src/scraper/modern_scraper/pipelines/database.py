"""
Database Pipeline

Pipeline para integrar datos scrapeados con la nueva arquitectura de base de datos.
Usa los repositorios y servicios modernos para persistir datos de forma eficiente.
"""
import logging
import sys
import os
from typing import Dict, Any, Optional, List
from itemadapter import ItemAdapter
from scrapy import Spider
from scrapy.exceptions import DropItem
from datetime import datetime

# Initialize logger early
logger = logging.getLogger(__name__)

# Add project root to Python path to access shared modules
# From: /Users/.../services/scraper/modern_scraper/pipelines/database.py
# To:   /Users/.../edeka-scraper (project root)
project_root = os.path.dirname(__file__)  # pipelines dir
project_root = os.path.dirname(project_root)  # modern_scraper dir
project_root = os.path.dirname(project_root)  # scraper dir
project_root = os.path.dirname(project_root)  # services dir
project_root = os.path.dirname(project_root)  # edeka-scraper dir (project root)
project_root = os.path.abspath(project_root)

logger.info(f"Database pipeline trying to load shared modules from: {project_root}")

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Alternative approach: set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = f"{project_root}:{os.environ.get('PYTHONPATH', '')}"

try:
    from shared.database.config import db_manager
    from shared.database.repositories import (
        ProductRepository, StoreRepository, 
        CategoryRepository, ManufacturerRepository
    )
    from shared.database.services.product_service import ProductService
    logger.info("Successfully imported shared modules")
except ImportError as e:
    logger.error(f"Failed to import shared modules: {e}")
    logger.error(f"Project root: {project_root}")
    logger.error(f"Python path: {sys.path[:5]}...")
    logger.error(f"Contents of project root: {os.listdir(project_root) if os.path.exists(project_root) else 'Not found'}")
    # Check if shared directory exists
    shared_path = os.path.join(project_root, 'shared')
    logger.error(f"Shared directory exists: {os.path.exists(shared_path)}")
    if os.path.exists(shared_path):
        logger.error(f"Contents of shared: {os.listdir(shared_path)}")
    raise ImportError(f"Cannot import shared modules. Please ensure the shared directory is accessible. Error: {e}")


class DatabasePipeline:
    """
    Pipeline principal para integrar datos con la base de datos usando
    la nueva arquitectura modular.
    """
    
    def __init__(self):
        self.stats = {
            'items_saved': 0,
            'items_updated': 0,
            'items_skipped': 0,
            'new_stores': 0,
            'new_categories': 0,
            'new_manufacturers': 0,
            'database_errors': 0,
        }
        
        # Initialize repositories
        self.product_repo = ProductRepository()
        self.store_repo = StoreRepository()
        self.category_repo = CategoryRepository()
        self.manufacturer_repo = ManufacturerRepository()
        
        # Initialize services
        self.product_service = ProductService()
        
        # Cache for database IDs to avoid repeated lookups (store IDs instead of objects)
        self.store_cache = {}
        self.category_cache = {}
        self.manufacturer_cache = {}
    
    def process_item(self, item, spider: Spider):
        """
        Procesa un item y lo guarda en la base de datos usando los nuevos repositorios.
        """
        adapter = ItemAdapter(item)
        
        try:
            with db_manager.get_session() as session:
                # Process and get/create store
                store = self._get_or_create_store(session, adapter, spider)
                
                # Process and get/create category hierarchy
                category = self._get_or_create_category_hierarchy(session, adapter, spider)
                
                # Process and get/create manufacturer
                manufacturer = self._get_or_create_manufacturer(session, adapter, spider)
                
                # Process product (create or update)
                product = self._process_product(session, adapter, spider, store, category, manufacturer)
                
                if product:
                    self.stats['items_saved'] += 1
                    spider.crawler.stats.inc_value('database_pipeline/items_saved')
                    logger.debug(f"Product saved: {product.name} (ID: {product.id})")
                else:
                    self.stats['items_skipped'] += 1
                    spider.crawler.stats.inc_value('database_pipeline/items_skipped')
                
                return item
                
        except Exception as e:
            self.stats['database_errors'] += 1
            spider.crawler.stats.inc_value('database_pipeline/errors')
            logger.error(f"Database error processing item '{adapter.get('name', 'Unknown')}': {e}")
            
            # Don't drop item on database errors in development
            spider_settings = getattr(spider, 'settings', {})
            if spider_settings.get('DEV_SCRAPER_SETTINGS', {}).get('test_mode', False):
                logger.warning("Test mode: continuing despite database error")
                return item
            else:
                raise DropItem(f"Database error: {e}")
    
    def _get_or_create_store(self, session, adapter: ItemAdapter, spider: Spider):
        """
        Obtiene o crea una tienda usando el repositorio de tiendas.
        """
        store_name = adapter.get('store_name')
        store_slug = adapter.get('store_slug') or store_name.lower().replace(' ', '-')
        
        # Check cache first (store ID instead of object)
        cache_key = f"{store_name}:{store_slug}"
        if cache_key in self.store_cache:
            store_id = self.store_cache[cache_key]
            existing_store = session.query(self.store_repo.model).filter_by(id=store_id).first()
            if existing_store:
                return existing_store
        
        try:
            # Try to get existing store by slug
            existing_store = session.query(
                self.store_repo.model
            ).filter_by(slug=store_slug).first()
            
            if existing_store:
                self.store_cache[cache_key] = existing_store.id  # Cache ID, not object
                return existing_store
            
            # Create new store
            store_data = {
                'name': store_name,
                'slug': store_slug,
                'display_name': store_name,
                'website_url': spider.allowed_domains[0] if spider.allowed_domains else None,
                'country': 'DE',  # Default for Edeka
                'currency': 'EUR',
                'is_active': True,
                'is_scraping_enabled': True,
            }
            
            new_store = self.store_repo.create(session, obj_in=store_data)
            session.flush()  # Ensure ID is available
            self.store_cache[cache_key] = new_store.id  # Cache ID, not object
            self.stats['new_stores'] += 1
            spider.crawler.stats.inc_value('database_pipeline/new_stores')
            
            logger.info(f"Created new store: {store_name}")
            return new_store
            
        except Exception as e:
            logger.error(f"Error processing store '{store_name}': {e}")
            raise
    
    def _get_or_create_category_hierarchy(self, session, adapter: ItemAdapter, spider: Spider):
        """
        Crea la jerarquía de categorías y retorna la categoría hoja.
        """
        category_hierarchy = adapter.get('category_hierarchy', [])
        category_path = adapter.get('category_path', [])
        
        if not category_path:
            return None
        
        # Use category_hierarchy if available, otherwise build from category_path
        if not category_hierarchy:
            category_hierarchy = []
            for level, name in enumerate(category_path):
                category_hierarchy.append({
                    'name': name.strip(),
                    'slug': name.lower().replace(' ', '-').replace('/', '-'),
                    'level': level,
                    'parent_name': category_path[level-1] if level > 0 else None
                })
        
        try:
            parent_category = None
            
            for cat_info in category_hierarchy:
                cat_name = cat_info['name']
                cat_slug = cat_info['slug']
                cat_level = cat_info['level']
                
                # Check cache (use ID instead of object)
                cache_key = f"{cat_slug}:{cat_level}:{parent_category.id if parent_category else 'root'}"
                if cache_key in self.category_cache:
                    category_id = self.category_cache[cache_key]
                    cached_category = session.query(self.category_repo.model).filter_by(id=category_id).first()
                    if cached_category:
                        parent_category = cached_category
                        continue
                
                # Try to find existing category
                query = session.query(self.category_repo.model).filter_by(
                    slug=cat_slug,
                    parent_id=parent_category.id if parent_category else None
                )
                existing_category = query.first()
                
                if existing_category:
                    parent_category = existing_category
                    self.category_cache[cache_key] = existing_category.id  # Cache ID, not object
                    continue
                
                # Create new category
                category_data = {
                    'name': cat_name,
                    'slug': cat_slug,
                    'level': str(cat_level),  # Model expects string
                    'parent_id': parent_category.id if parent_category else None,
                    'is_active': '1',  # Model expects string
                    'sort_order': str(cat_level * 10),  # Model expects string
                }
                
                # Generate path
                if parent_category:
                    parent_path = parent_category.path or parent_category.name
                    category_data['path'] = f"{parent_path}/{cat_name}"
                else:
                    category_data['path'] = cat_name
                
                new_category = self.category_repo.create(session, obj_in=category_data)
                session.flush()  # Ensure ID is available
                self.category_cache[cache_key] = new_category.id  # Cache ID, not object
                parent_category = new_category
                
                self.stats['new_categories'] += 1
                spider.crawler.stats.inc_value('database_pipeline/new_categories')
                
                logger.debug(f"Created category: {cat_name} (level {cat_level})")
            
            return parent_category  # Return leaf category
            
        except Exception as e:
            logger.error(f"Error processing category hierarchy {category_path}: {e}")
            return None
    
    def _get_or_create_manufacturer(self, session, adapter: ItemAdapter, spider: Spider):
        """
        Obtiene o crea un fabricante.
        """
        manufacturer_name = adapter.get('manufacturer_name')
        
        if not manufacturer_name:
            return None
        
        # Check cache (use ID instead of object)
        cache_key = manufacturer_name
        if cache_key in self.manufacturer_cache:
            manufacturer_id = self.manufacturer_cache[cache_key]
            cached_manufacturer = session.query(self.manufacturer_repo.model).filter_by(id=manufacturer_id).first()
            if cached_manufacturer:
                return cached_manufacturer
        
        try:
            # Try to find existing manufacturer
            existing_manufacturer = session.query(
                self.manufacturer_repo.model
            ).filter_by(name=manufacturer_name).first()
            
            if existing_manufacturer:
                self.manufacturer_cache[cache_key] = existing_manufacturer.id  # Cache ID, not object
                return existing_manufacturer
            
            # Create new manufacturer
            manufacturer_data = {
                'name': manufacturer_name,
                'slug': manufacturer_name.lower().replace(' ', '-'),
                'display_name': manufacturer_name,
                'is_active': True,
                'is_verified': False,
            }
            
            new_manufacturer = self.manufacturer_repo.create(session, obj_in=manufacturer_data)
            session.flush()  # Ensure ID is available
            self.manufacturer_cache[cache_key] = new_manufacturer.id  # Cache ID, not object
            self.stats['new_manufacturers'] += 1
            spider.crawler.stats.inc_value('database_pipeline/new_manufacturers')
            
            logger.debug(f"Created manufacturer: {manufacturer_name}")
            return new_manufacturer
            
        except Exception as e:
            logger.error(f"Error processing manufacturer '{manufacturer_name}': {e}")
            return None
    
    def _process_product(self, session, adapter: ItemAdapter, spider: Spider, 
                        store, category, manufacturer):
        """
        Procesa el producto principal (crear o actualizar).
        """
        product_url = adapter.get('product_url')
        
        try:
            # Check if product exists by URL
            existing_product = self.product_repo.get_by_url(session, product_url)
            
            # Prepare product data
            product_data = self._prepare_product_data(adapter, store, category, manufacturer)
            
            if existing_product:
                # Update existing product
                updated_product = self._update_existing_product(
                    session, existing_product, product_data, adapter, spider
                )
                self.stats['items_updated'] += 1
                spider.crawler.stats.inc_value('database_pipeline/items_updated')
                return updated_product
            else:
                # Create new product
                new_product = self.product_repo.create(session, obj_in=product_data)
                
                # Generate search text
                new_product.update_search_text()
                session.commit()
                session.refresh(new_product)
                
                logger.debug(f"Created new product: {new_product.name}")
                return new_product
                
        except Exception as e:
            logger.error(f"Error processing product '{adapter.get('name')}': {e}")
            raise
    
    def _prepare_product_data(self, adapter: ItemAdapter, store, category, manufacturer) -> Dict[str, Any]:
        """
        Prepara los datos del producto para la base de datos.
        """
        # Get current timestamp
        now = datetime.utcnow()
        
        product_data = {
            # Basic information
            'name': adapter.get('name'),
            'sku': adapter.get('sku'),
            'product_url': adapter.get('product_url'),
            'image_url': adapter.get('image_url'),
            
            # Price information
            'price_amount': adapter.get('price_amount'),
            'price_currency': adapter.get('price_currency', 'EUR'),
            'base_price_amount': adapter.get('base_price_amount'),
            'base_price_unit': adapter.get('base_price_unit'),
            'base_price_quantity': adapter.get('base_price_quantity'),
            
            # Content
            'description': adapter.get('description'),
            'details': adapter.get('details'),
            'nutritional_info': adapter.get('nutritional_info'),
            
            # Availability
            'in_stock': adapter.get('in_stock', 'unknown'),
            'availability_text': adapter.get('availability_text'),
            
            # Relationships
            'store_id': store.id if store else None,
            'category_id': category.id if category else None,
            'manufacturer_id': manufacturer.id if manufacturer else None,
            
            # Metadata
            'scraped_at': adapter.get('scraped_at', now),
            'scrape_count': adapter.get('scrape_count', 1),
        }
        
        # Set last_price_update if we have a price
        if product_data['price_amount'] is not None:
            product_data['last_price_update'] = now
        
        # Remove None values
        return {k: v for k, v in product_data.items() if v is not None}
    
    def _update_existing_product(self, session, existing_product, product_data, 
                                adapter: ItemAdapter, spider: Spider):
        """
        Actualiza un producto existente, detectando cambios de precio.
        """
        # Check for price changes
        old_price = existing_product.price_amount
        new_price = product_data.get('price_amount')
        
        price_changed = False
        if old_price != new_price and new_price is not None:
            price_changed = True
            product_data['last_price_update'] = datetime.utcnow()
            spider.crawler.stats.inc_value('database_pipeline/price_changes')
            logger.info(f"Price change detected: {existing_product.name} "
                       f"{old_price} → {new_price}")
        
        # Update scrape count
        product_data['scrape_count'] = existing_product.scrape_count + 1
        
        # Update the product
        updated_product = self.product_repo.update(
            session, db_obj=existing_product, obj_in=product_data
        )
        
        # Update search text if content changed
        if any(field in product_data for field in ['name', 'description', 'details']):
            updated_product.update_search_text()
            session.commit()
        
        # Set flags for potential embedding update
        adapter['price_changed'] = price_changed
        adapter['is_new_product'] = False
        
        return updated_product
    
    def close_spider(self, spider: Spider):
        """
        Log estadísticas finales de la base de datos.
        """
        logger.info("=== DATABASE PIPELINE STATS ===")
        logger.info(f"Items saved: {self.stats['items_saved']}")
        logger.info(f"Items updated: {self.stats['items_updated']}")
        logger.info(f"Items skipped: {self.stats['items_skipped']}")
        logger.info(f"New stores: {self.stats['new_stores']}")
        logger.info(f"New categories: {self.stats['new_categories']}")
        logger.info(f"New manufacturers: {self.stats['new_manufacturers']}")
        logger.info(f"Database errors: {self.stats['database_errors']}")
        
        # Set final spider stats
        for key, value in self.stats.items():
            spider.crawler.stats.set_value(f'database_pipeline/{key}_final', value)


class AIIntegrationPipeline:
    """
    Pipeline para integrar con funcionalidades de IA después del guardado en DB.
    """
    
    def __init__(self):
        self.stats = {
            'items_processed': 0,
            'embeddings_queued': 0,
        }
        self.product_service = ProductService()
    
    def process_item(self, item, spider: Spider):
        """
        Procesa items para funcionalidades de IA.
        """
        adapter = ItemAdapter(item)
        
        # Check if AI features are enabled
        spider_settings = getattr(spider, 'settings', {})
        modern_settings = spider_settings.get('MODERN_SCRAPER_SETTINGS', {})
        
        if not modern_settings.get('enable_ai_features', False):
            return item
        
        try:
            # Queue for embedding generation if needed
            needs_embedding = adapter.get('needs_embedding', True)
            is_new_product = adapter.get('is_new_product', True)
            price_changed = adapter.get('price_changed', False)
            
            if needs_embedding or is_new_product or price_changed:
                # In a real implementation, this could queue the item for
                # background embedding generation
                self.stats['embeddings_queued'] += 1
                spider.crawler.stats.inc_value('ai_integration_pipeline/embeddings_queued')
                
                logger.debug(f"Queued for AI processing: {adapter.get('name')}")
            
            self.stats['items_processed'] += 1
            spider.crawler.stats.inc_value('ai_integration_pipeline/items_processed')
            
            return item
            
        except Exception as e:
            logger.warning(f"AI integration error: {e}")
            return item  # Don't fail the pipeline on AI errors
    
    def close_spider(self, spider: Spider):
        """
        Log estadísticas de AI integration.
        """
        if self.stats['items_processed'] > 0:
            logger.info("=== AI INTEGRATION PIPELINE STATS ===")
            logger.info(f"Items processed: {self.stats['items_processed']}")
            logger.info(f"Embeddings queued: {self.stats['embeddings_queued']}")
            
            for key, value in self.stats.items():
                spider.crawler.stats.set_value(f'ai_integration_pipeline/{key}_final', value)
