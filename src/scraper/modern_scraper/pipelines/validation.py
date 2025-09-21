"""
Validation Pipeline

Pipeline para validar datos scrapeados antes del procesamiento.
Asegura la calidad e integridad de los datos.
"""
import logging
from typing import Dict, Any, List, Optional
from itemadapter import ItemAdapter
from scrapy import Spider
from scrapy.exceptions import DropItem

from ..items import ModernProductItem

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """
    Pipeline para validar items scrapeados.
    
    Valida campos requeridos, formatos de datos, y consistency checks.
    """
    
    def __init__(self):
        self.stats = {
            'items_validated': 0,
            'items_dropped': 0,
            'validation_errors': {},
        }
    
    def process_item(self, item, spider: Spider):
        """
        Procesa y valida un item scrapeado.
        
        Args:
            item: Item scrapeado
            spider: Spider que generó el item
            
        Returns:
            Item validado o None si debe ser descartado
            
        Raises:
            DropItem: Si la validación falla
        """
        adapter = ItemAdapter(item)
        
        try:
            # Validate required fields
            self._validate_required_fields(adapter, spider)
            
            # Validate data types and formats
            self._validate_data_formats(adapter, spider)
            
            # Validate business rules
            self._validate_business_rules(adapter, spider)
            
            # Clean and normalize data
            self._clean_and_normalize(adapter, spider)
            
            self.stats['items_validated'] += 1
            spider.crawler.stats.inc_value('validation_pipeline/items_validated')
            
            logger.debug(f"Item validated successfully: {adapter.get('name', 'Unknown')}")
            
            return item
            
        except DropItem as e:
            self.stats['items_dropped'] += 1
            spider.crawler.stats.inc_value('validation_pipeline/items_dropped')
            
            error_type = str(type(e).__name__)
            self.stats['validation_errors'][error_type] = \
                self.stats['validation_errors'].get(error_type, 0) + 1
            
            logger.warning(f"Item dropped during validation: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error in validation pipeline: {e}")
            spider.crawler.stats.inc_value('validation_pipeline/unexpected_errors')
            raise DropItem(f"Validation failed with unexpected error: {e}")
    
    def _validate_required_fields(self, adapter: ItemAdapter, spider: Spider):
        """
        Valida que los campos requeridos estén presentes y no vacíos.
        """
        required_fields = {
            'name': 'Product name is required',
            'product_url': 'Product URL is required',  
            'store_name': 'Store name is required',
            'scraped_at': 'Scraped timestamp is required',
        }
        
        for field, error_msg in required_fields.items():
            value = adapter.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                spider.crawler.stats.inc_value(f'validation_pipeline/missing_{field}')
                raise DropItem(f"Missing required field '{field}': {error_msg}")
    
    def _validate_data_formats(self, adapter: ItemAdapter, spider: Spider):
        """
        Valida formatos de datos específicos.
        """
        # Validate URL format
        product_url = adapter.get('product_url')
        if product_url and not self._is_valid_url(product_url):
            spider.crawler.stats.inc_value('validation_pipeline/invalid_url')
            raise DropItem(f"Invalid product URL format: {product_url}")
        
        # Validate price format
        price_amount = adapter.get('price_amount')
        if price_amount is not None:
            try:
                # Handle Decimal, int, float types
                from decimal import Decimal
                if isinstance(price_amount, (int, float, Decimal)):
                    price_float = float(price_amount)
                    if price_float < 0:
                        spider.crawler.stats.inc_value('validation_pipeline/invalid_price')
                        raise DropItem(f"Negative price amount: {price_amount}")
                else:
                    spider.crawler.stats.inc_value('validation_pipeline/invalid_price_type')
                    raise DropItem(f"Invalid price type {type(price_amount)}: {price_amount}")
            except (ValueError, TypeError) as e:
                spider.crawler.stats.inc_value('validation_pipeline/invalid_price')
                raise DropItem(f"Invalid price amount: {price_amount} - {e}")
        
        # Validate currency format
        currency = adapter.get('price_currency')
        if currency and len(currency) != 3:
            spider.crawler.stats.inc_value('validation_pipeline/invalid_currency')
            raise DropItem(f"Invalid currency format: {currency}")
        
        # Validate base price components consistency
        base_amount = adapter.get('base_price_amount')
        base_unit = adapter.get('base_price_unit')
        base_quantity = adapter.get('base_price_quantity')
        
        if any([base_amount, base_unit, base_quantity]):
            if not all([base_amount, base_unit, base_quantity]):
                spider.crawler.stats.inc_value('validation_pipeline/incomplete_base_price')
                raise DropItem("Base price information is incomplete")
    
    def _validate_business_rules(self, adapter: ItemAdapter, spider: Spider):
        """
        Valida reglas de negocio específicas.
        """
        # Validate stock status
        in_stock = adapter.get('in_stock')
        if in_stock and in_stock not in ['in_stock', 'out_of_stock', 'unknown']:
            spider.crawler.stats.inc_value('validation_pipeline/invalid_stock_status')
            raise DropItem(f"Invalid stock status: {in_stock}")
        
        # Validate category path
        category_path = adapter.get('category_path')
        if category_path and not isinstance(category_path, list):
            spider.crawler.stats.inc_value('validation_pipeline/invalid_category_path')
            raise DropItem("Category path must be a list")
        
        # Validate store name
        store_name = adapter.get('store_name')
        if store_name and len(store_name.strip()) < 2:
            spider.crawler.stats.inc_value('validation_pipeline/invalid_store_name')
            raise DropItem(f"Store name too short: {store_name}")
    
    def _clean_and_normalize(self, adapter: ItemAdapter, spider: Spider):
        """
        Limpia y normaliza los datos.
        """
        # Clean and normalize text fields
        text_fields = ['name', 'description', 'sku', 'store_name', 'manufacturer_name']
        for field in text_fields:
            value = adapter.get(field)
            if value and isinstance(value, str):
                adapter[field] = self._clean_text(value)
        
        # Normalize URLs
        for url_field in ['product_url', 'image_url']:
            url = adapter.get(url_field)
            if url:
                adapter[url_field] = url.strip()
        
        # Set default values
        if not adapter.get('price_currency'):
            adapter['price_currency'] = 'EUR'
        
        if not adapter.get('in_stock'):
            adapter['in_stock'] = 'unknown'
            
        # Clean category path
        category_path = adapter.get('category_path')
        if category_path and isinstance(category_path, list):
            adapter['category_path'] = [self._clean_text(cat) for cat in category_path if cat and cat.strip()]
    
    def _clean_text(self, text: str) -> str:
        """
        Limpia y normaliza texto.
        """
        if not text:
            return text
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        return text.strip()
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Valida formato básico de URL.
        """
        return url.startswith(('http://', 'https://')) and len(url) > 10
    
    def close_spider(self, spider: Spider):
        """
        Se ejecuta cuando el spider termina. Log de estadísticas.
        """
        logger.info("=== VALIDATION PIPELINE STATS ===")
        logger.info(f"Items validated: {self.stats['items_validated']}")
        logger.info(f"Items dropped: {self.stats['items_dropped']}")
        
        if self.stats['validation_errors']:
            logger.info("Validation errors breakdown:")
            for error_type, count in self.stats['validation_errors'].items():
                logger.info(f"  {error_type}: {count}")
        
        # Set spider-level stats
        spider.crawler.stats.set_value('validation_pipeline/final_validated', 
                                      self.stats['items_validated'])
        spider.crawler.stats.set_value('validation_pipeline/final_dropped', 
                                      self.stats['items_dropped'])


class DuplicateDetectionPipeline:
    """
    Pipeline para detectar y manejar productos duplicados basado en URL.
    """
    
    def __init__(self):
        self.seen_urls = set()
        self.duplicate_count = 0
    
    def process_item(self, item, spider: Spider):
        """
        Detecta duplicados basado en product_url.
        """
        adapter = ItemAdapter(item)
        product_url = adapter.get('product_url')
        
        if not product_url:
            return item  # Let validation pipeline handle this
        
        if product_url in self.seen_urls:
            self.duplicate_count += 1
            spider.crawler.stats.inc_value('duplicate_detection_pipeline/duplicates_dropped')
            logger.debug(f"Duplicate product detected: {product_url}")
            raise DropItem(f"Duplicate product URL: {product_url}")
        
        self.seen_urls.add(product_url)
        spider.crawler.stats.inc_value('duplicate_detection_pipeline/unique_products')
        
        return item
    
    def close_spider(self, spider: Spider):
        """
        Log estadísticas de duplicados al finalizar.
        """
        logger.info(f"Duplicate detection: {self.duplicate_count} duplicates found")
        spider.crawler.stats.set_value('duplicate_detection_pipeline/final_duplicates', 
                                     self.duplicate_count)
