"""
Edeka24 Spider

Spider para scrapear productos de Edeka24.de con selectores optimizados
basados en la estructura real del HTML del sitio.
"""
import scrapy
import json
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
from typing import Generator, Any, List, Optional

from .base_spider import BaseSpider
from ..items.product_item import ModernProductItem

import logging
logger = logging.getLogger(__name__)


class Edeka24Spider(BaseSpider):
    """
    Spider para scrapear productos de Edeka24.de
    
    Basado en análisis de la estructura HTML real del sitio.
    Incluye manejo de precios, información nutricional y metadatos.
    """
    
    name = 'edeka24_spider'
    allowed_domains = ['edeka24.de']
    
    # Store information
    store_name = 'EDEKA24'
    store_slug = 'edeka24'
    
    def __init__(self, *args, **kwargs):
        """Initialize Edeka24 spider."""
        super().__init__(*args, **kwargs)
        
        # Development mode: start with main sitemap to autodiscover product sitemaps
        self.start_urls = [
            'https://www.edeka24.de/sitemaps/sitemap.xml',
        ]
        
        # Apply development limits to start URLs
        if self.dev_limits['max_sitemaps'] > 0:
            self.start_urls = self.start_urls[:self.dev_limits['max_sitemaps']]
        
        logger.info(f"🏪 Edeka24 spider initialized")
        logger.info(f"🔗 Starting with {len(self.start_urls)} category URLs")
        logger.info(f"📊 Dev limits: {self.dev_limits}")
    
    async def start(self):
        """Generate initial requests for category pages (Scrapy 2.13+)."""
        logger.info("🚀 Starting Edeka24 spider requests")
        
        for i, url in enumerate(self.start_urls):
            if not self.should_continue_scraping():
                break
            
            yield scrapy.Request(
                url=url,
                callback=self.parse_main_sitemap,
                errback=self.handle_error,
                meta={
                    'spider_start_time': datetime.utcnow(),
                    'category_index': i,
                    'category_name': 'Direct Product',
                    'category_url': url,
                },
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
    
    def parse_main_sitemap(self, response) -> Generator[Any, None, None]:
        """
        Parse main sitemap XML to find product sitemaps.
        """
        self.increment_counters(pages=1)
        
        if not self.should_continue_scraping():
            logger.info("🛑 Edeka24 spider stopped due to development limits")
            return
        
        try:
            logger.info(f"📄 Processing main sitemap: {response.url}")
            
            # Parse sitemap index XML to extract sitemap URLs
            # Usando local-name() para manejar namespaces XML
            sitemap_urls = response.xpath('//*[local-name()="sitemap"]/*[local-name()="loc"]/text()').getall()
            
            logger.info(f"🔗 Found {len(sitemap_urls)} sitemaps in index")
            
            # Filter to product sitemaps only (contain "products")
            product_sitemaps = [url for url in sitemap_urls if 'products' in url]
            
            logger.info(f"🛍️ Found {len(product_sitemaps)} product sitemaps")
            
            # Apply development limits to sitemaps
            max_sitemaps = self.dev_limits.get('max_sitemaps', 2)
            if max_sitemaps > 0:
                product_sitemaps = product_sitemaps[:max_sitemaps]
                logger.info(f"🧪 Dev mode: Limited to {len(product_sitemaps)} product sitemaps")
            
            # Generate requests for each product sitemap
            for sitemap_url in product_sitemaps:
                if not self.should_continue_scraping():
                    break
                
                yield scrapy.Request(
                    url=sitemap_url,
                    callback=self.parse_sitemap,
                    errback=self.handle_error,
                    meta={
                        'category_name': 'Product Sitemap',
                        'category_url': response.url,
                    },
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    }
                )
            
            # Log progress
            self.log_progress(f"Queued {len(product_sitemaps)} product sitemaps")
            
        except Exception as e:
            logger.error(f"❌ Error parsing main sitemap {response.url}: {e}")
            self.stats['errors_count'] += 1
    
    def parse_sitemap(self, response) -> Generator[Any, None, None]:
        """
        Parse sitemap XML to extract product URLs.
        """
        self.increment_counters(pages=1)
        
        if not self.should_continue_scraping():
            logger.info("🛑 Edeka24 spider stopped due to development limits")
            return
        
        try:
            logger.info(f"📄 Processing sitemap: {response.url}")
            
            # Parse sitemap XML to extract product URLs
            # Usando local-name() para manejar namespaces XML
            urls = response.xpath('//*[local-name()="url"]/*[local-name()="loc"]/text()').getall()
            
            logger.info(f"🔗 Found {len(urls)} URLs in sitemap")
            
            # Filter to product URLs only (contain .html)
            product_urls = [url for url in urls if url.endswith('.html')]
            
            # Apply development limits
            max_products = self.dev_limits.get('max_items', 5)
            if max_products > 0:
                product_urls = product_urls[:max_products]
                logger.info(f"🧪 Dev mode: Limited to {len(product_urls)} products from sitemap")
            
            # Generate requests for each product
            for product_url in product_urls:
                if not self.should_continue_scraping():
                    break
                
                yield scrapy.Request(
                    url=product_url,
                    callback=self.parse_product,
                    errback=self.handle_error,
                    meta={
                        'category_name': 'From Sitemap',
                        'category_url': response.url,
                    },
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    }
                )
            
            # Log progress
            self.log_progress(f"Queued {len(product_urls)} products from sitemap")
            
        except Exception as e:
            logger.error(f"❌ Error parsing sitemap {response.url}: {e}")
            self.stats['errors_count'] += 1
    
    def parse_category(self, response) -> Generator[Any, None, None]:
        """
        Parse category pages and extract product links.
        """
        self.increment_counters(pages=1)
        
        if not self.should_continue_scraping():
            logger.info("🛑 Edeka24 spider stopped due to development limits")
            return
        
        try:
            # Extract category name from breadcrumbs
            category_name = self._extract_category_name(response)
            logger.info(f"📂 Processing category: {category_name}")
            
            # Track category
            self.stats['categories_found'].add(category_name)
            
            # Extract product URLs from the category page
            product_links = self._extract_product_links(response)
            
            # Apply development limits
            max_products = self.dev_limits.get('max_products_per_category', 10)
            if max_products > 0:
                product_links = product_links[:max_products]
                logger.info(f"🧪 Dev mode: Limited to {len(product_links)} products from {category_name}")
            
            # Generate requests for each product
            for product_url in product_links:
                if not self.should_continue_scraping():
                    break
                
                absolute_url = self.build_absolute_url(response, product_url)
                
                yield scrapy.Request(
                    url=absolute_url,
                    callback=self.parse_product,
                    errback=self.handle_error,
                    meta={
                        'category_name': category_name,
                        'category_url': response.url,
                    },
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    }
                )
            
            # Log progress
            self.log_progress(f"Found {len(product_links)} products in {category_name}")
            
        except Exception as e:
            logger.error(f"❌ Error parsing category {response.url}: {e}")
            self.stats['errors_count'] += 1
    
    def parse_product(self, response) -> Generator[ModernProductItem, None, None]:
        """
        Parse individual product pages and extract product information.
        Basado en la estructura real de Edeka24.
        """
        self.increment_counters(pages=1)
        
        if not self.should_continue_scraping():
            return
        
        try:
            # Create product item
            item = self.create_product_item()
            
            # Basic product information
            item['name'] = self._extract_product_name(response)
            item['product_url'] = response.url
            item['category_path'] = self._extract_category_path(response)
            
            # Price information (basado en la estructura real)
            price_info = self._extract_price_info(response)
            item['price_amount'] = price_info.get('current_price')
            item['price_currency'] = price_info.get('currency', 'EUR')
            
            # Basic price information (precio por unidad)
            base_price_info = self._extract_base_price_info(response)
            if base_price_info:
                item['base_price_text'] = base_price_info.get('text')
                item['base_price_amount'] = base_price_info.get('amount')
                item['base_price_unit'] = base_price_info.get('unit')
            
            # Product details
            item['description'] = self._extract_description(response)
            item['sku'] = self._extract_sku(response)
            item['image_url'] = self._extract_main_image(response)
            
            # Stock status (basado en texto de disponibilidad)
            item['in_stock'] = self._extract_stock_status(response)
            item['availability_text'] = self._extract_availability_text(response)
            
            # Additional information
            manufacturer = self._extract_manufacturer(response)
            if manufacturer:
                item['manufacturer_name'] = manufacturer
            
            # Structured details (información adicional)
            details = self._extract_additional_details(response)
            if details:
                item['details'] = details
            
            # Validate required fields
            if self._validate_item(item):
                self.increment_counters(items=1)
                
                logger.info(f"✅ Scraped: {item.get('name', 'Unknown')} - {item.get('price_amount', 'N/A')} EUR")
                
                yield item
                
                # Log progress every 5 items
                if self.items_count % 5 == 0:
                    self.log_progress(f"Scraped {self.items_count} products")
            else:
                logger.warning(f"⚠️ Invalid item skipped: {response.url}")
        
        except Exception as e:
            logger.error(f"❌ Error parsing product {response.url}: {e}")
            self.stats['errors_count'] += 1
    
    def _extract_category_name(self, response) -> str:
        """Extract category name from breadcrumbs or URL."""
        # Extract from breadcrumbs (estructura real observada)
        breadcrumb_links = response.css('.breadcrumb ul li a::text').getall()
        if len(breadcrumb_links) >= 2:
            # Last breadcrumb is usually the category
            return breadcrumb_links[-1].strip()
        
        # Fallback: extract from URL
        path_segments = urlparse(response.url).path.strip('/').split('/')
        if path_segments:
            return path_segments[-1].replace('-', ' ').title()
        
        return 'Unknown Category'
    
    def _extract_product_links(self, response) -> List[str]:
        """Extract product links from category page."""
        # Selectores basados en la estructura observada
        product_selectors = [
            'a[href*=".html"]::attr(href)',  # Links que terminan en .html
            '.product-item a::attr(href)',
            '.product-tile a::attr(href)',
            '.item-link::attr(href)',
            '.product a::attr(href)',
        ]
        
        product_links = []
        for selector in product_selectors:
            links = response.css(selector).getall()
            if links:
                product_links.extend(links)
                break  # Use first working selector
        
        # Filter and deduplicate
        unique_links = list(set(product_links))
        
        # Filter to keep only product pages (ending in .html)
        filtered_links = [
            link for link in unique_links 
            if link.endswith('.html') and '/' in link
        ]
        
        logger.debug(f"Found {len(filtered_links)} product links")
        return filtered_links[:50]  # Reasonable limit
    
    def _extract_product_name(self, response) -> str:
        """Extract product name from h1 tag."""
        # Basado en estructura real: <h1>Bäuerliche EZG Schwäbisch Hall Demeter Bratwurst grob 200G</h1>
        name_selectors = [
            'h1::text',
            '.detail-description h1::text',
            'title::text',
        ]
        
        for selector in name_selectors:
            name = response.css(selector).get()
            if name:
                clean_name = self.extract_and_clean_text([name])
                # Remove "EDEKA24 |" prefix if present
                if 'EDEKA24 |' in clean_name:
                    clean_name = clean_name.replace('EDEKA24 |', '').strip()
                return clean_name
        
        return 'Unknown Product'
    
    def _extract_category_path(self, response) -> List[str]:
        """Extract category path from breadcrumbs."""
        # Estructura real: <div class="breadcrumb"> <ul> <li> <a>
        breadcrumb_links = response.css('.breadcrumb ul li a::text').getall()
        
        # Filter out "Startseite" and clean up
        category_path = []
        for breadcrumb in breadcrumb_links[1:]:  # Skip "Startseite"
            clean_breadcrumb = breadcrumb.strip()
            if clean_breadcrumb and clean_breadcrumb not in ['Startseite', 'Home']:
                category_path.append(clean_breadcrumb)
        
        return category_path if category_path else ['Unknown Category']
    
    def _extract_price_info(self, response) -> dict:
        """Extract price information based on real structure."""
        price_info = {
            'current_price': None,
            'currency': 'EUR',
        }
        
        # Estructura real: <div class="price">5,29 €</div>
        price_selectors = [
            '.price::text',
            '.price-wrap .price::text',
            '.price-wrap-inner .price::text',
            '[class*="price"]::text',
        ]
        
        price_text = None
        for selector in price_selectors:
            price_text = response.css(selector).get()
            if price_text:
                break
        
        if price_text:
            # Parse German price format: "5,29 €"
            from ..utils import PriceParser
            price_amount = PriceParser.parse_main_price(price_text.strip())
            if price_amount:
                price_info['current_price'] = price_amount
        
        return price_info
    
    def _extract_base_price_info(self, response) -> Optional[dict]:
        """Extract base price information (Grundpreis)."""
        # Estructura real: <li class="price-note clear-both ">Grundpreis: 26,45 €/kg</li>
        base_price_selectors = [
            '.price-note:contains("Grundpreis")::text',
            'li:contains("Grundpreis")::text',
            '[class*="grundpreis"]::text',
            '[class*="base-price"]::text',
        ]
        
        for selector in base_price_selectors:
            base_price_text = response.css(selector).get()
            if base_price_text:
                # Parse "Grundpreis: 26,45 €/kg"
                from ..utils import PriceParser
                parsed = PriceParser.parse_base_price(base_price_text)
                if parsed.get('amount'):
                    return {
                        'text': base_price_text.strip(),
                        'amount': parsed.get('amount'),
                        'unit': parsed.get('unit'),
                        'quantity': parsed.get('quantity'),
                    }
        
        return None
    
    def _extract_description(self, response) -> str:
        """Extract product description."""
        # Estructura real: <div id="description"> con contenido
        desc_selectors = [
            '#description .listing::text',
            '#description::text',
            '.article-long-description::text',
            '.product-description::text',
        ]
        
        description_parts = []
        for selector in desc_selectors:
            parts = response.css(selector).getall()
            if parts:
                description_parts.extend(parts)
        
        if description_parts:
            return self.extract_and_clean_text(description_parts)
        
        return ''
    
    def _extract_sku(self, response) -> str:
        """Extract product SKU from various sources."""
        # Check data attributes first
        sku_selectors = [
            '[data-ArToBaConf_sArticleNumber]::attr(data-ArToBaConf_sArticleNumber)',
            '[data-article-number]::attr(data-article-number)',
            '.sku::text',
            '.article-number::text',
        ]
        
        for selector in sku_selectors:
            sku = response.css(selector).get()
            if sku:
                return sku.strip()
        
        # Check in JavaScript/JSON data (estructura real observada)
        script_texts = response.css('script::text').getall()
        for script in script_texts:
            if 'content_ids' in script:
                # Facebook Pixel data: content_ids: '3078696007'
                match = re.search(r"content_ids:\s*['\"](\d+)['\"]", script)
                if match:
                    return match.group(1)
        
        # Generate SKU from URL if not found
        from ..utils import DataEnricher
        return DataEnricher.generate_sku_from_url(response.url) or 'UNKNOWN'
    
    def _extract_main_image(self, response) -> str:
        """Extract main product image URL."""
        # Estructura real: <img src="https://www.edeka24.de/out/pictures/generated/product/1/400_400_90/..." class="img-responsive jq-img-zoom">
        image_selectors = [
            '.detail-image img::attr(src)',
            '.product-image img::attr(src)',
            '.img-responsive::attr(src)',
            'img[class*="zoom"]::attr(src)',
        ]
        
        for selector in image_selectors:
            img_url = response.css(selector).get()
            if img_url:
                return self.build_absolute_url(response, img_url)
        
        return ''
    
    def _extract_stock_status(self, response) -> str:
        """Extract stock status based on availability text."""
        # Estructura real: <li class="delivery-text product-note available">
        availability_text = self._extract_availability_text(response)
        
        if availability_text:
            from ..utils import PriceParser
            status, _ = PriceParser.detect_availability(availability_text)
            return status
        
        # Default to in_stock if no clear indicator
        return 'in_stock'
    
    def _extract_availability_text(self, response) -> str:
        """Extract availability text."""
        # Estructura real: <span>lieferbar innerhalb von 2-5 Werktagen</span>
        availability_selectors = [
            '.delivery-text span::text',
            '.availability::text',
            '.stock-status::text',
            '.product-note.available span::text',
        ]
        
        for selector in availability_selectors:
            text = response.css(selector).get()
            if text:
                return text.strip()
        
        return ''
    
    def _extract_manufacturer(self, response) -> Optional[str]:
        """Extract manufacturer/brand name."""
        # Check meta tags first (estructura real observada)
        meta_brand = response.css('meta[property="product:brand"]::attr(content)').get()
        if meta_brand:
            return meta_brand.strip()
        
        # Check in JavaScript data
        script_texts = response.css('script::text').getall()
        for script in script_texts:
            # Facebook Pixel data might have brand info
            if 'content_name' in script:
                # Try to extract brand from product name
                match = re.search(r"content_name:\s*['\"]([^'\"]+)['\"]", script)
                if match:
                    product_name = match.group(1)
                    from ..utils import DataEnricher
                    return DataEnricher.extract_manufacturer_from_name(product_name)
        
        # Try to extract from product name
        product_name = self._extract_product_name(response)
        if product_name:
            from ..utils import DataEnricher
            return DataEnricher.extract_manufacturer_from_name(product_name)
        
        return None
    
    def _extract_additional_details(self, response) -> dict:
        """Extract additional product details."""
        details = {}
        
        # Extract company information (estructura real observada)
        company_info = response.css('.listing:contains("Anschrift des Unternehmens")').get()
        if company_info:
            # Extract text after "Anschrift des Unternehmens:"
            company_text = self.extract_and_clean_text([company_info])
            if 'Anschrift des Unternehmens:' in company_text:
                company_details = company_text.split('Anschrift des Unternehmens:')[1].strip()
                details['company_info'] = company_details
        
        # Extract characteristics (Bio, etc.)
        characteristics = response.css('ul.characteristics li::text').getall()
        if characteristics:
            details['characteristics'] = [char.strip() for char in characteristics if char.strip()]
        
        # Extract PAYBACK points
        payback_text = response.css('.payback-info strong::text').get()
        if payback_text:
            details['payback_points'] = payback_text.strip()
        
        # Extract article ID from form data
        article_id = response.css('input[name="aid"]::attr(value)').get()
        if article_id:
            details['article_id'] = article_id
        
        return details
    
    def _validate_item(self, item: ModernProductItem) -> bool:
        """Validate that the item has required fields."""
        required_fields = ['name', 'product_url']
        
        for field in required_fields:
            if not item.get(field):
                logger.debug(f"Missing required field '{field}' for item {item.get('product_url')}")
                return False
        
        # At least try to have a price
        price = item.get('price_amount')
        if price is not None:
            try:
                price_float = float(price)
                if price_float <= 0 or price_float > 10000:
                    logger.debug(f"Invalid price {price_float} for item {item.get('product_url')}")
                    return False
            except (ValueError, TypeError):
                logger.debug(f"Invalid price format {price} for item {item.get('product_url')}")
                return False
        
        return True
