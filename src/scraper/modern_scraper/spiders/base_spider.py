"""
Base Spider

Spider base con funcionalidades comunes para todos los spiders del proyecto.
Incluye manejo de configuraciones, estadísticas, y utilidades compartidas.
"""
import scrapy
import logging
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime, timedelta
import re
import time

from ..items.product_item import ModernProductItem
from ..utils import PriceParser, DataEnricher

logger = logging.getLogger(__name__)


class BaseSpider(scrapy.Spider):
    """
    Spider base con funcionalidades comunes para todos los spiders.
    
    Proporciona:
    - Manejo de configuraciones por entorno
    - Estadísticas y monitoreo
    - Utilidades de parsing comunes
    - Manejo de errores robusto
    - Rate limiting inteligente
    """
    
    # Override in subclasses
    name = 'base_spider'
    allowed_domains = []
    start_urls = []
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize spider statistics
        self.stats = {
            'start_time': datetime.utcnow(),
            'items_scraped': 0,
            'pages_processed': 0,
            'errors_count': 0,
            'sitemaps_processed': 0,
            'categories_found': set(),
            'price_changes_detected': 0,
        }
        
        # Get spider-specific settings
        self.spider_config = self._get_spider_config()
        
        # Development limits (safety measures)
        self.dev_limits = self._get_development_limits()
        
        # Initialize counters for limits
        self.items_count = 0
        self.pages_count = 0
        self.sitemap_count = 0
        
        logger.info(f"🕷️ {self.name} spider initialized")
        logger.info(f"📊 Development limits: {self.dev_limits}")
    
    def _get_spider_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración específica del spider.
        """
        # Settings will be available after crawler is set
        if hasattr(self, 'crawler') and self.crawler:
            spider_settings = self.crawler.settings.get('SPIDER_SETTINGS', {})
            return spider_settings.get(self.name, {})
        return {}
    
    def _get_development_limits(self) -> Dict[str, Any]:
        """
        Obtiene los límites de desarrollo para scraping seguro.
        """
        if hasattr(self, 'crawler') and self.crawler:
            settings = self.crawler.settings
            dev_settings = settings.get('DEV_SCRAPER_SETTINGS', {})
            
            return {
                'max_items': settings.get('CLOSESPIDER_ITEMCOUNT', 50),
                'max_pages': settings.get('CLOSESPIDER_PAGECOUNT', 100),
                'max_time_minutes': settings.get('CLOSESPIDER_TIMEOUT', 300) // 60,
                'max_sitemaps': dev_settings.get('max_sitemaps', 2),
                'max_products_per_category': dev_settings.get('max_products_per_category', 10),
                'test_mode': dev_settings.get('test_mode', False),
            }
        else:
            # Default limits when crawler is not available yet
            return {
                'max_items': 5,  # Reduced for faster testing
                'max_pages': 20, # Reduced for faster testing
                'max_time_minutes': 3,
                'max_sitemaps': 1,
                'max_products_per_category': 5,
                'test_mode': True,
            }
    
    async def start(self):
        """
        Async method to generate initial requests (Scrapy 2.13+).
        Replaces the deprecated start_requests() method.
        """
        start_urls = self.start_urls.copy()
        
        # Apply sitemap limit in development
        if self.dev_limits['max_sitemaps'] > 0:
            start_urls = start_urls[:self.dev_limits['max_sitemaps']]
            logger.info(f"🧪 Development mode: Limited to {len(start_urls)} start URLs")
        
        for url in start_urls:
            yield scrapy.Request(
                url=url, 
                callback=self.parse,
                errback=self.handle_error,
                meta={'spider_start_time': datetime.utcnow()}
            )
    
    def parse(self, response):
        """
        Parse method base - override in subclasses.
        """
        raise NotImplementedError("Subclasses must implement parse method")
    
    def create_product_item(self, **kwargs) -> ModernProductItem:
        """
        Crea un item de producto con valores por defecto.
        """
        item = ModernProductItem()
        
        # Set default values
        item['scraped_at'] = datetime.utcnow()
        item['store_name'] = getattr(self, 'store_name', 'Unknown')
        item['store_slug'] = getattr(self, 'store_slug', 'unknown')
        
        # Apply provided values
        for key, value in kwargs.items():
            if key in item.fields:
                item[key] = value
        
        return item
    
    def extract_price_with_currency(self, price_text: str, default_currency: str = 'EUR') -> tuple:
        """
        Extrae precio y moneda de un texto.
        
        Returns:
            tuple: (price_amount, currency)
        """
        if not price_text:
            return None, default_currency
        
        try:
            price_amount = PriceParser.parse_main_price(price_text)
            return price_amount, default_currency
        except Exception as e:
            logger.debug(f"Failed to parse price '{price_text}': {e}")
            return None, default_currency
    
    def extract_and_clean_text(self, selector_result: List[str]) -> str:
        """
        Extrae y limpia texto de resultados de selectores.
        """
        if not selector_result:
            return ''
        
        # Join all text parts and clean
        text = ' '.join(part.strip() for part in selector_result if part.strip())
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def build_absolute_url(self, response, relative_url: str) -> str:
        """
        Construye URL absoluta desde una URL relativa.
        """
        if not relative_url:
            return ''
        
        return response.urljoin(relative_url)
    
    def extract_category_breadcrumbs(self, response, breadcrumb_selector: str) -> List[str]:
        """
        Extrae breadcrumbs de categorías desde un selector.
        """
        try:
            breadcrumbs = response.css(breadcrumb_selector).getall()
            
            # Clean and filter breadcrumbs
            clean_breadcrumbs = []
            for breadcrumb in breadcrumbs:
                clean_breadcrumb = self.extract_and_clean_text([breadcrumb])
                if clean_breadcrumb and clean_breadcrumb.lower() not in ['home', 'startseite', 'inicio']:
                    clean_breadcrumbs.append(clean_breadcrumb)
            
            return clean_breadcrumbs
            
        except Exception as e:
            logger.debug(f"Failed to extract breadcrumbs: {e}")
            return []
    
    def should_continue_scraping(self) -> bool:
        """
        Verifica si el spider debe continuar scrapeando basado en límites.
        """
        # Check item limit
        if self.dev_limits['max_items'] > 0 and self.items_count >= self.dev_limits['max_items']:
            logger.info(f"🛑 Item limit reached: {self.items_count}/{self.dev_limits['max_items']}")
            return False
        
        # Check page limit  
        if self.dev_limits['max_pages'] > 0 and self.pages_count >= self.dev_limits['max_pages']:
            logger.info(f"🛑 Page limit reached: {self.pages_count}/{self.dev_limits['max_pages']}")
            return False
        
        # Check time limit
        if self.dev_limits['max_time_minutes'] > 0:
            elapsed_minutes = (datetime.utcnow() - self.stats['start_time']).seconds // 60
            if elapsed_minutes >= self.dev_limits['max_time_minutes']:
                logger.info(f"🛑 Time limit reached: {elapsed_minutes}/{self.dev_limits['max_time_minutes']} minutes")
                return False
        
        # Check sitemap limit
        if self.dev_limits['max_sitemaps'] > 0 and self.sitemap_count >= self.dev_limits['max_sitemaps']:
            logger.info(f"🛑 Sitemap limit reached: {self.sitemap_count}/{self.dev_limits['max_sitemaps']}")
            return False
        
        return True
    
    def increment_counters(self, items: int = 0, pages: int = 0, sitemaps: int = 0):
        """
        Incrementa contadores de seguimiento.
        """
        self.items_count += items
        self.pages_count += pages
        self.sitemap_count += sitemaps
        
        # Update spider stats
        if items > 0:
            self.stats['items_scraped'] += items
            self.crawler.stats.inc_value('spider/items_scraped', items)
        
        if pages > 0:
            self.stats['pages_processed'] += pages
            self.crawler.stats.inc_value('spider/pages_processed', pages)
        
        if sitemaps > 0:
            self.stats['sitemaps_processed'] += sitemaps
            self.crawler.stats.inc_value('spider/sitemaps_processed', sitemaps)
    
    def handle_error(self, failure):
        """
        Maneja errores de requests de forma robusta.
        """
        self.stats['errors_count'] += 1
        self.crawler.stats.inc_value('spider/errors_count')
        
        logger.error(f"Request failed: {failure.value}")
        logger.debug(f"Failed URL: {failure.request.url}")
        
        # Don't re-raise in development mode
        if self.dev_limits['test_mode']:
            logger.warning("Test mode: Continuing despite error")
        
        return None
    
    def log_progress(self, message: str = None):
        """
        Registra el progreso actual del spider.
        """
        elapsed_time = datetime.utcnow() - self.stats['start_time']
        elapsed_str = str(elapsed_time).split('.')[0]  # Remove microseconds
        
        progress_msg = (
            f"📊 {self.name} Progress: "
            f"Items: {self.items_count}, "
            f"Pages: {self.pages_count}, "
            f"Errors: {self.stats['errors_count']}, "
            f"Elapsed: {elapsed_str}"
        )
        
        if message:
            progress_msg = f"{message} | {progress_msg}"
        
        logger.info(progress_msg)
        
        # Log to spider stats
        self.crawler.stats.set_value('spider/current_items', self.items_count)
        self.crawler.stats.set_value('spider/current_pages', self.pages_count)
        self.crawler.stats.set_value('spider/elapsed_seconds', elapsed_time.seconds)
    
    def closed(self, reason):
        """
        Called when spider closes. Log final statistics.
        """
        total_time = datetime.utcnow() - self.stats['start_time']
        
        logger.info("=" * 50)
        logger.info(f"🕷️ {self.name.upper()} SPIDER COMPLETED")
        logger.info("=" * 50)
        logger.info(f"📊 Reason: {reason}")
        logger.info(f"⏱️  Total time: {str(total_time).split('.')[0]}")
        logger.info(f"📦 Items scraped: {self.stats['items_scraped']}")
        logger.info(f"📄 Pages processed: {self.stats['pages_processed']}")
        logger.info(f"🗺️  Sitemaps processed: {self.stats['sitemaps_processed']}")
        logger.info(f"🏷️  Categories found: {len(self.stats['categories_found'])}")
        logger.info(f"💰 Price changes: {self.stats['price_changes_detected']}")
        logger.info(f"❌ Errors encountered: {self.stats['errors_count']}")
        
        # Calculate rates
        if total_time.seconds > 0:
            items_per_minute = (self.stats['items_scraped'] * 60) / total_time.seconds
            pages_per_minute = (self.stats['pages_processed'] * 60) / total_time.seconds
            logger.info(f"⚡ Rate: {items_per_minute:.1f} items/min, {pages_per_minute:.1f} pages/min")
        
        # Log category breakdown
        if self.stats['categories_found']:
            logger.info(f"🏷️  Categories: {', '.join(list(self.stats['categories_found'])[:10])}")
            if len(self.stats['categories_found']) > 10:
                logger.info(f"   ... and {len(self.stats['categories_found']) - 10} more")
        
        logger.info("=" * 50)
        
        # Set final spider statistics
        self.crawler.stats.set_value('spider/final_items', self.stats['items_scraped'])
        self.crawler.stats.set_value('spider/final_pages', self.stats['pages_processed'])
        self.crawler.stats.set_value('spider/final_errors', self.stats['errors_count'])
        self.crawler.stats.set_value('spider/final_duration_seconds', total_time.seconds)
