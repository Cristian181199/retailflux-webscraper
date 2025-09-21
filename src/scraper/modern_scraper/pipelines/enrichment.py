"""
Enrichment Pipeline

Pipeline para enriquecer datos scrapeados con información procesada y parseada.
Incluye parsing de precios, extracción de datos estructurados, y preparación para IA.
"""
import logging
from typing import Dict, Any, Optional
from itemadapter import ItemAdapter
from scrapy import Spider
from datetime import datetime
import json

from ..utils.price_parser import PriceParser, DataEnricher

logger = logging.getLogger(__name__)


class EnrichmentPipeline:
    """
    Pipeline para enriquecer items con datos procesados y estructurados.
    
    - Parsea precios base desde texto
    - Extrae información estructurada
    - Genera SKUs si no existen
    - Detecta fabricantes
    - Prepara datos para IA
    """
    
    def __init__(self):
        self.stats = {
            'items_enriched': 0,
            'base_prices_parsed': 0,
            'skus_generated': 0,
            'manufacturers_detected': 0,
            'details_extracted': 0,
        }
    
    def process_item(self, item, spider: Spider):
        """
        Enriquece un item scrapeado con datos procesados.
        
        Args:
            item: Item scrapeado y validado
            spider: Spider que generó el item
            
        Returns:
            Item enriquecido
        """
        adapter = ItemAdapter(item)
        
        try:
            # Parse base price information
            self._parse_base_price(adapter, spider)
            
            # Generate or improve SKU
            self._handle_sku_generation(adapter, spider)
            
            # Extract and detect manufacturer
            self._extract_manufacturer(adapter, spider)
            
            # Extract structured details
            self._extract_structured_details(adapter, spider)
            
            # Detect and normalize availability
            self._process_availability(adapter, spider)
            
            # Generate slugs for relational data
            self._generate_slugs(adapter, spider)
            
            # Set processing flags
            self._set_processing_flags(adapter, spider)
            
            # Update metadata
            self._update_metadata(adapter, spider)
            
            self.stats['items_enriched'] += 1
            spider.crawler.stats.inc_value('enrichment_pipeline/items_enriched')
            
            logger.debug(f"Item enriched successfully: {adapter.get('name', 'Unknown')}")
            
            return item
            
        except Exception as e:
            logger.error(f"Error in enrichment pipeline: {e}")
            spider.crawler.stats.inc_value('enrichment_pipeline/errors')
            # Don't drop item on enrichment errors, just log and continue
            return item
    
    def _parse_base_price(self, adapter: ItemAdapter, spider: Spider):
        """
        Parsea información de precio base desde texto.
        """
        base_price_text = adapter.get('base_price_text')
        if not base_price_text:
            return
        
        try:
            parsed_price = PriceParser.parse_base_price(base_price_text)
            
            if parsed_price['amount'] is not None:
                adapter['base_price_amount'] = float(parsed_price['amount'])
                adapter['base_price_unit'] = parsed_price['unit']
                adapter['base_price_quantity'] = float(parsed_price['quantity'])
                
                self.stats['base_prices_parsed'] += 1
                spider.crawler.stats.inc_value('enrichment_pipeline/base_prices_parsed')
                
                logger.debug(f"Base price parsed: {parsed_price}")
            
        except Exception as e:
            logger.warning(f"Failed to parse base price '{base_price_text}': {e}")
            spider.crawler.stats.inc_value('enrichment_pipeline/base_price_parse_errors')
    
    def _handle_sku_generation(self, adapter: ItemAdapter, spider: Spider):
        """
        Genera SKU si no existe o mejora el existente.
        """
        current_sku = adapter.get('sku')
        product_url = adapter.get('product_url')
        
        # Generate SKU if missing or generic
        if (not current_sku or 
            current_sku in ['N/A', 'Unknown', ''] or 
            len(current_sku.strip()) < 3):
            
            try:
                generated_sku = DataEnricher.generate_sku_from_url(product_url)
                if generated_sku:
                    adapter['sku'] = generated_sku
                    self.stats['skus_generated'] += 1
                    spider.crawler.stats.inc_value('enrichment_pipeline/skus_generated')
                    logger.debug(f"Generated SKU: {generated_sku}")
            
            except Exception as e:
                logger.warning(f"Failed to generate SKU for {product_url}: {e}")
    
    def _extract_manufacturer(self, adapter: ItemAdapter, spider: Spider):
        """
        Extrae o detecta información del fabricante.
        """
        current_manufacturer = adapter.get('manufacturer_name')
        product_name = adapter.get('name', '')
        
        if not current_manufacturer and product_name:
            try:
                detected_manufacturer = DataEnricher.extract_manufacturer_from_name(product_name)
                if detected_manufacturer:
                    adapter['manufacturer_name'] = detected_manufacturer
                    self.stats['manufacturers_detected'] += 1
                    spider.crawler.stats.inc_value('enrichment_pipeline/manufacturers_detected')
                    logger.debug(f"Detected manufacturer: {detected_manufacturer}")
            
            except Exception as e:
                logger.warning(f"Failed to extract manufacturer from '{product_name}': {e}")
    
    def _extract_structured_details(self, adapter: ItemAdapter, spider: Spider):
        """
        Extrae información estructurada en formato JSON.
        """
        description = adapter.get('description', '')
        
        if not description:
            return
        
        try:
            # Extract structured details from description
            structured_details = DataEnricher.extract_product_details(
                description, 
                {}  # Additional selector data could be passed here
            )
            
            if structured_details:
                # Merge with existing details if any
                existing_details = adapter.get('details')
                if existing_details and isinstance(existing_details, dict):
                    structured_details.update(existing_details)
                
                adapter['details'] = structured_details
                self.stats['details_extracted'] += 1
                spider.crawler.stats.inc_value('enrichment_pipeline/details_extracted')
                
                logger.debug(f"Extracted {len(structured_details)} detail fields")
        
        except Exception as e:
            logger.warning(f"Failed to extract structured details: {e}")
    
    def _process_availability(self, adapter: ItemAdapter, spider: Spider):
        """
        Procesa y normaliza información de disponibilidad.
        """
        availability_text = adapter.get('availability_text')
        current_status = adapter.get('in_stock', 'unknown')
        
        if availability_text and current_status == 'unknown':
            try:
                detected_status, normalized_text = PriceParser.detect_availability(availability_text)
                
                adapter['in_stock'] = detected_status
                if normalized_text:
                    adapter['availability_text'] = normalized_text
                
                spider.crawler.stats.inc_value(f'enrichment_pipeline/availability_{detected_status}')
                logger.debug(f"Detected availability: {detected_status}")
            
            except Exception as e:
                logger.warning(f"Failed to process availability '{availability_text}': {e}")
    
    def _generate_slugs(self, adapter: ItemAdapter, spider: Spider):
        """
        Genera slugs para datos relacionales.
        """
        try:
            # Generate store slug
            store_name = adapter.get('store_name')
            if store_name and not adapter.get('store_slug'):
                store_slug = DataEnricher.create_store_slug(store_name)
                adapter['store_slug'] = store_slug
            
            # Process category slugs if needed (for structured data)
            category_path = adapter.get('category_path', [])
            if category_path:
                # Could generate category slugs here if needed for the database
                pass
                
        except Exception as e:
            logger.warning(f"Failed to generate slugs: {e}")
    
    def _set_processing_flags(self, adapter: ItemAdapter, spider: Spider):
        """
        Establece flags de procesamiento para pipelines posteriores.
        """
        # Flag for embedding generation
        adapter['needs_embedding'] = True
        
        # Check if this is a new product (will be determined by database pipeline)
        adapter['is_new_product'] = True
        
        # Check if price changed (will be determined by database pipeline)
        adapter['price_changed'] = False
        
        # Set scrape count (will be updated by database pipeline)
        if not adapter.get('scrape_count'):
            adapter['scrape_count'] = 1
    
    def _update_metadata(self, adapter: ItemAdapter, spider: Spider):
        """
        Actualiza metadatos del item.
        """
        # Ensure scraped_at is set
        if not adapter.get('scraped_at'):
            adapter['scraped_at'] = datetime.utcnow()
        
        # Set last_price_update if we have a price
        if adapter.get('price_amount') is not None:
            adapter['last_price_update'] = datetime.utcnow()
    
    def close_spider(self, spider: Spider):
        """
        Log estadísticas al finalizar el spider.
        """
        logger.info("=== ENRICHMENT PIPELINE STATS ===")
        logger.info(f"Items enriched: {self.stats['items_enriched']}")
        logger.info(f"Base prices parsed: {self.stats['base_prices_parsed']}")
        logger.info(f"SKUs generated: {self.stats['skus_generated']}")
        logger.info(f"Manufacturers detected: {self.stats['manufacturers_detected']}")
        logger.info(f"Details extracted: {self.stats['details_extracted']}")
        
        # Set final stats
        for key, value in self.stats.items():
            spider.crawler.stats.set_value(f'enrichment_pipeline/{key}_final', value)


class CategoryHierarchyPipeline:
    """
    Pipeline especializado para procesar jerarquías de categorías.
    """
    
    def __init__(self):
        self.category_cache = {}  # Cache for category processing
        self.stats = {
            'categories_processed': 0,
            'new_categories': 0,
        }
    
    def process_item(self, item, spider: Spider):
        """
        Procesa la jerarquía de categorías del item.
        """
        adapter = ItemAdapter(item)
        category_path = adapter.get('category_path', [])
        
        if not category_path:
            return item
        
        try:
            # Process category hierarchy
            processed_categories = []
            
            for level, category_name in enumerate(category_path):
                if category_name and category_name.strip():
                    clean_name = category_name.strip()
                    category_slug = DataEnricher.create_category_slug(clean_name)
                    
                    category_info = {
                        'name': clean_name,
                        'slug': category_slug,
                        'level': level,
                        'parent_name': processed_categories[level-1]['name'] if level > 0 else None
                    }
                    
                    processed_categories.append(category_info)
            
            # Store processed category information
            if processed_categories:
                adapter['category_hierarchy'] = processed_categories
                adapter['category_path'] = [cat['name'] for cat in processed_categories]
                
                self.stats['categories_processed'] += 1
                spider.crawler.stats.inc_value('category_hierarchy_pipeline/categories_processed')
            
            return item
            
        except Exception as e:
            logger.warning(f"Failed to process category hierarchy {category_path}: {e}")
            return item
    
    def close_spider(self, spider: Spider):
        """
        Log estadísticas de categorías.
        """
        logger.info(f"Category hierarchy: {self.stats['categories_processed']} items processed")
        spider.crawler.stats.set_value('category_hierarchy_pipeline/final_processed', 
                                     self.stats['categories_processed'])
