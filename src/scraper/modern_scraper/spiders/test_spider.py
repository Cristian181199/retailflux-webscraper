"""
Test Spider

Spider de prueba para validar la infraestructura del scraper moderno.
Scrape de ejemplo usando httpbin.org para generar datos de prueba.
"""
import scrapy
import json
from datetime import datetime
from typing import Generator, Any

from .base_spider import BaseSpider
from ..items import ModernProductItem

import logging
logger = logging.getLogger(__name__)


class TestSpider(BaseSpider):
    """
    Spider de prueba que genera productos ficticios para probar pipelines.
    """
    
    name = 'test_spider'
    allowed_domains = ['httpbin.org']
    
    # Store information
    store_name = 'Test Store'
    store_slug = 'test-store'
    
    def __init__(self, *args, **kwargs):
        """Initialize test spider with sample data."""
        super().__init__(*args, **kwargs)
        
        # Sample product data for testing
        self.sample_products = [
            {
                'name': 'Apfel Granny Smith',
                'price_amount': 2.49,
                'currency': 'EUR',
                'unit': 'kg',
                'category': 'Obst & Gemüse',
                'brand': 'Regional',
                'description': 'Frische Äpfel der Sorte Granny Smith aus regionalem Anbau',
                'in_stock': True,
                'sku': 'APPLE-GS-001',
                'image_url': 'https://httpbin.org/image/png',
            },
            {
                'name': 'Vollmilch 3,5%',
                'price_amount': 1.29,
                'currency': 'EUR',
                'unit': '1L',
                'category': 'Milchprodukte',
                'brand': 'Testmilch',
                'description': 'Frische Vollmilch mit 3,5% Fettgehalt',
                'in_stock': True,
                'sku': 'MILK-35-001',
                'original_price': 1.49,
                'discount_percentage': 13.4,
                'image_url': 'https://httpbin.org/image/jpeg',
            },
            {
                'name': 'Brot Vollkorn',
                'price_amount': 3.99,
                'currency': 'EUR',
                'unit': '750g',
                'category': 'Backwaren',
                'brand': 'Testbäcker',
                'description': 'Frisches Vollkornbrot aus der Bäckerei',
                'in_stock': False,
                'sku': 'BREAD-VK-001',
                'nutritional_info': {
                    'calories_per_100g': 250,
                    'protein_per_100g': 8.5,
                    'carbs_per_100g': 45.2,
                    'fat_per_100g': 3.1,
                    'fiber_per_100g': 7.8,
                },
                'image_url': 'https://httpbin.org/image/webp',
            },
            {
                'name': 'Bananen',
                'price_amount': 1.99,
                'currency': 'EUR',
                'unit': 'kg',
                'category': 'Obst & Gemüse',
                'brand': 'Tropical',
                'description': 'Süße reife Bananen aus fairem Handel',
                'in_stock': True,
                'sku': 'BANANA-001',
                'certifications': ['Bio', 'Fairtrade'],
                'country_of_origin': 'Ecuador',
                'image_url': 'https://httpbin.org/image/png',
                'additional_images': [
                    'https://httpbin.org/image/jpeg?id=banana1',
                    'https://httpbin.org/image/png?id=banana2',
                ],
            },
            {
                'name': 'Pasta Spaghetti',
                'price_amount': 0.99,
                'currency': 'EUR',
                'unit': '500g',
                'category': 'Nudeln & Reis',
                'brand': 'Pasta Testino',
                'description': 'Klassische Spaghetti aus Hartweizengrieß',
                'in_stock': True,
                'sku': 'PASTA-SP-001',
                'ingredients': ['Hartweizengrieß', 'Wasser'],
                'allergens': ['Gluten'],
                'cooking_time': 8,
                'image_url': 'https://httpbin.org/image/svg',
            },
        ]
        
        # Generate start URLs for testing
        self.start_urls = [
            f'https://httpbin.org/json?product={i}' 
            for i in range(min(len(self.sample_products), self.dev_limits['max_items']))
        ]
        
        logger.info(f"🧪 Test spider initialized with {len(self.start_urls)} test URLs")
        logger.info(f"📦 Sample products: {len(self.sample_products)}")
    
    def parse(self, response) -> Generator[ModernProductItem, None, None]:
        """
        Parse response and yield test product items.
        """
        self.increment_counters(pages=1)
        
        if not self.should_continue_scraping():
            logger.info("🛑 Test spider stopped due to development limits")
            return
        
        try:
            # Extract product index from URL
            product_index = self._extract_product_index(response.url)
            
            if product_index < len(self.sample_products):
                product_data = self.sample_products[product_index]
                
                # Create product item using base spider method
                item = self.create_product_item()
                
                # Fill item with sample data
                item['name'] = product_data['name']
                item['price_amount'] = product_data['price_amount']
                item['price_currency'] = product_data.get('currency', 'EUR')
                item['category_path'] = [product_data.get('category', 'Test Category')]
                item['manufacturer_name'] = product_data.get('brand', 'Test Brand')
                item['description'] = product_data.get('description', '')
                item['in_stock'] = 'in_stock' if product_data.get('in_stock', True) else 'out_of_stock'
                item['sku'] = product_data.get('sku', f'TEST-{product_index:03d}')
                item['product_url'] = f'https://httpbin.org/product/{product_index}'
                item['image_url'] = product_data.get('image_url', '')
                
                # Optional fields - add to details dict for flexible data
                details = {}
                if 'unit' in product_data:
                    details['unit'] = product_data['unit']
                if 'nutritional_info' in product_data:
                    item['nutritional_info'] = product_data['nutritional_info']
                if 'certifications' in product_data:
                    details['certifications'] = product_data['certifications']
                if 'country_of_origin' in product_data:
                    details['country_of_origin'] = product_data['country_of_origin']
                if 'ingredients' in product_data:
                    details['ingredients'] = product_data['ingredients']
                if 'allergens' in product_data:
                    details['allergens'] = product_data['allergens']
                if 'cooking_time' in product_data:
                    details['cooking_time'] = product_data['cooking_time']
                
                if details:
                    item['details'] = details
                
                # Add to category tracking
                category_list = item.get('category_path', [])
                if category_list:
                    self.stats['categories_found'].add(category_list[0])
                
                # Simulate price change detection
                if product_data.get('discount_percentage', 0) > 0:
                    self.stats['price_changes_detected'] += 1
                
                self.increment_counters(items=1)
                
                logger.info(f"✅ Generated test item: {item['name']} - {item['price_amount']} {item['price_currency']}")
                
                yield item
                
                # Log progress
                if self.items_count % 5 == 0:
                    self.log_progress(f"Generated {self.items_count} test items")
            
            else:
                logger.warning(f"⚠️ Product index {product_index} out of range")
        
        except Exception as e:
            logger.error(f"❌ Error parsing test response: {e}")
            self.stats['errors_count'] += 1
    
    def _extract_product_index(self, url: str) -> int:
        """
        Extract product index from test URL.
        """
        try:
            # URL format: https://httpbin.org/json?product=N
            if '?product=' in url:
                return int(url.split('?product=')[1])
            else:
                return 0
        except (ValueError, IndexError):
            return 0
    
    def start(self) -> Generator[scrapy.Request, None, None]:
        """
        Generate initial requests for test URLs.
        """
        logger.info("🚀 Starting test spider requests")
        
        for i, url in enumerate(self.start_urls):
            if not self.should_continue_scraping():
                break
            
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.handle_error,
                meta={
                    'spider_start_time': datetime.utcnow(),
                    'product_index': i,
                    'test_data': True,
                },
                dont_filter=True,  # Allow duplicate URLs for testing
            )
    
    def handle_error(self, failure):
        """
        Handle test request errors gracefully.
        """
        logger.warning(f"🚨 Test request failed: {failure.value}")
        logger.debug(f"Failed test URL: {failure.request.url}")
        
        # In test mode, continue despite errors
        self.stats['errors_count'] += 1
        self.crawler.stats.inc_value('spider/test_errors_count')
        
        return None


class MockEdekaSpider(BaseSpider):
    """
    Mock spider que simula el comportamiento de Edeka spider sin hacer requests reales.
    Útil para probar pipelines y configuraciones.
    """
    
    name = 'mock_edeka_spider'
    allowed_domains = ['httpbin.org']  # Safe domain for testing
    
    store_name = 'EDEKA (Mock)'
    store_slug = 'edeka-mock'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Mock categories for testing
        self.mock_categories = [
            'Obst & Gemüse',
            'Fleisch & Wurst', 
            'Milchprodukte',
            'Backwaren',
            'Getränke',
            'Tiefkühl',
            'Süßwaren',
            'Drogerie',
            'Haushalt',
            'Baby & Kind',
        ]
        
        # Generate mock URLs
        max_categories = self.dev_limits.get('max_products_per_category', 10)
        self.start_urls = []
        
        for i, category in enumerate(self.mock_categories[:5]):  # Limit categories
            for j in range(min(3, max_categories)):  # 3 products per category in test
                url = f'https://httpbin.org/json?category={i}&product={j}'
                self.start_urls.append(url)
        
        logger.info(f"🏪 Mock Edeka spider initialized")
        logger.info(f"📦 Categories: {len(self.mock_categories[:5])}")
        logger.info(f"🔗 Test URLs: {len(self.start_urls)}")
    
    def parse(self, response):
        """Generate mock Edeka products."""
        self.increment_counters(pages=1)
        
        if not self.should_continue_scraping():
            return
        
        # Extract category and product indices
        category_idx, product_idx = self._extract_indices(response.url)
        
        if category_idx < len(self.mock_categories):
            category = self.mock_categories[category_idx]
            
            # Generate mock product
            item = self.create_product_item()
            
            # Mock product data based on category
            mock_data = self._generate_mock_product(category, product_idx)
            
            for key, value in mock_data.items():
                item[key] = value
            
            # Track category
            self.stats['categories_found'].add(category)
            self.increment_counters(items=1)
            
            logger.info(f"🏪 Generated mock Edeka item: {item['name']} ({category})")
            
            yield item
    
    def _extract_indices(self, url: str) -> tuple:
        """Extract category and product indices from URL."""
        try:
            parts = url.split('?')[1].split('&')
            category_idx = int([p for p in parts if p.startswith('category=')][0].split('=')[1])
            product_idx = int([p for p in parts if p.startswith('product=')][0].split('=')[1])
            return category_idx, product_idx
        except:
            return 0, 0
    
    def _generate_mock_product(self, category: str, product_idx: int) -> dict:
        """Generate mock product data based on category."""
        base_products = {
            'Obst & Gemüse': ['Äpfel', 'Bananen', 'Karotten'],
            'Fleisch & Wurst': ['Hackfleisch', 'Bratwurst', 'Hähnchenbrust'],
            'Milchprodukte': ['Vollmilch', 'Joghurt', 'Käse'],
            'Backwaren': ['Brot', 'Brötchen', 'Croissant'],
            'Getränke': ['Wasser', 'Apfelsaft', 'Cola'],
        }
        
        products = base_products.get(category, ['Test Produkt'])
        product_name = products[product_idx % len(products)]
        
        return {
            'name': f"{product_name} {product_idx + 1}",
            'price_amount': round(0.99 + product_idx * 0.50, 2),
            'currency': 'EUR',
            'category': category,
            'brand': f"Test Brand {product_idx + 1}",
            'description': f"Mock {product_name} für Testzwecke",
            'in_stock': product_idx % 4 != 0,  # 75% in stock
            'sku': f"MOCK-{category.replace(' & ', '-').upper()}-{product_idx:03d}",
            'url': f'https://httpbin.org/mock-product/{category.lower()}/{product_idx}',
            'image_url': f'https://httpbin.org/image/png?category={category}',
        }
