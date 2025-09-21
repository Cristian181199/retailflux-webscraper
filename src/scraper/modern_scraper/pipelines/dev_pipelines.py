"""
Development Pipelines

Pipelines específicos para desarrollo con funcionalidades de debug,
validación y almacenamiento local.
"""
import os
import json
import gzip
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

import scrapy
from itemadapter import ItemAdapter

from ..items import ModernProductItem

logger = logging.getLogger(__name__)


class DebugPipeline:
    """
    Pipeline de debug que registra información detallada de cada item.
    Solo para desarrollo.
    """
    
    def __init__(self):
        self.items_processed = 0
        self.items_by_spider = {}
        self.debug_log_file = None
        
    def open_spider(self, spider):
        """Inicializa el pipeline de debug."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_dir = 'debug'
        os.makedirs(debug_dir, exist_ok=True)
        
        self.debug_log_file = os.path.join(debug_dir, f'debug_{spider.name}_{timestamp}.log')
        self.items_by_spider[spider.name] = 0
        
        logger.info(f"🔍 Debug pipeline initialized for {spider.name}")
        logger.info(f"📝 Debug log: {self.debug_log_file}")
    
    def process_item(self, item, spider):
        """Procesa cada item con información de debug."""
        adapter = ItemAdapter(item)
        self.items_processed += 1
        self.items_by_spider[spider.name] = self.items_by_spider.get(spider.name, 0) + 1
        
        # Log debug information
        debug_info = {
            'item_id': self.items_processed,
            'spider': spider.name,
            'item_type': type(item).__name__,
            'timestamp': datetime.now().isoformat(),
            'fields_present': list(adapter.keys()),
            'fields_count': len(adapter),
            'has_required_fields': self._check_required_fields(adapter),
            'price_info': self._extract_price_debug(adapter),
            'url_info': self._extract_url_debug(adapter),
        }
        
        # Write debug info to file
        if self.debug_log_file:
            with open(self.debug_log_file, 'a', encoding='utf-8') as f:
                f.write(f"{json.dumps(debug_info, ensure_ascii=False, default=str)}\n")
        
        # Log progress every 10 items
        if self.items_processed % 10 == 0:
            logger.info(
                f"🐛 Debug: Processed {self.items_processed} items "
                f"({self.items_by_spider[spider.name]} from {spider.name})"
            )
        
        # Log item details in verbose mode
        logger.debug(f"🔍 Item {self.items_processed}: {debug_info}")
        
        return item
    
    def _check_required_fields(self, adapter: ItemAdapter) -> Dict[str, bool]:
        """Verifica la presencia de campos requeridos."""
        required_fields = ['name', 'price_amount', 'product_url', 'store_name']
        return {field: field in adapter and adapter.get(field) is not None 
                for field in required_fields}
    
    def _extract_price_debug(self, adapter: ItemAdapter) -> Dict[str, Any]:
        """Extrae información de debug sobre precios."""
        return {
            'has_price': 'price_amount' in adapter and adapter.get('price_amount') is not None,
            'price_value': adapter.get('price_amount'),
            'currency': adapter.get('price_currency'),
            'original_price': adapter.get('details', {}).get('original_price'),
            'discount_percentage': adapter.get('details', {}).get('discount_percentage'),
            'has_discount': adapter.get('details', {}).get('discount_percentage', 0) > 0,
        }
    
    def _extract_url_debug(self, adapter: ItemAdapter) -> Dict[str, Any]:
        """Extrae información de debug sobre URLs."""
        return {
            'has_url': 'product_url' in adapter and adapter.get('product_url') is not None,
            'url_length': len(adapter.get('product_url', '')),
            'is_absolute_url': adapter.get('product_url', '').startswith('http') if adapter.get('product_url') else False,
            'has_image': 'image_url' in adapter and adapter.get('image_url') is not None,
            'image_count': len(adapter.get('details', {}).get('additional_images', [])),
        }
    
    def close_spider(self, spider):
        """Finaliza el pipeline de debug."""
        logger.info("=" * 50)
        logger.info("🔍 DEBUG PIPELINE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"📊 Total items processed: {self.items_processed}")
        for spider_name, count in self.items_by_spider.items():
            logger.info(f"🕷️  {spider_name}: {count} items")
        logger.info(f"📝 Debug log saved: {self.debug_log_file}")
        logger.info("=" * 50)


class DevStoragePipeline:
    """
    Pipeline de almacenamiento para desarrollo que guarda items en archivos JSON.
    """
    
    def __init__(self, storage_settings: Dict[str, Any]):
        self.storage_settings = storage_settings
        self.output_file = None
        self.file_handle = None
        self.items_written = 0
        self.current_file_size = 0
        
    @classmethod
    def from_crawler(cls, crawler):
        """Crea el pipeline desde la configuración del crawler."""
        storage_settings = crawler.settings.get('DEV_STORAGE_SETTINGS', {})
        return cls(storage_settings)
    
    def open_spider(self, spider):
        """Inicializa el pipeline de almacenamiento."""
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_template = self.storage_settings.get(
            'output_file', 
            'data/dev_products_{timestamp}.jsonl'
        )
        self.output_file = output_template.replace('{timestamp}', timestamp)
        
        # Create data directory
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Open file for writing
        if self.storage_settings.get('compression') == 'gzip':
            self.file_handle = gzip.open(f"{self.output_file}.gz", 'wt', encoding='utf-8')
            self.output_file = f"{self.output_file}.gz"
        else:
            self.file_handle = open(self.output_file, 'w', encoding='utf-8')
        
        logger.info(f"💾 Dev storage initialized: {self.output_file}")
        
        # Write metadata header if enabled
        if self.storage_settings.get('include_metadata', True):
            metadata = {
                '_metadata': {
                    'spider': spider.name,
                    'start_time': datetime.now().isoformat(),
                    'settings': dict(self.storage_settings),
                    'format': 'jsonl',
                    'version': '1.0'
                }
            }
            self.file_handle.write(f"{json.dumps(metadata, ensure_ascii=False)}\n")
            self.file_handle.flush()
    
    def process_item(self, item, spider):
        """Procesa y almacena cada item."""
        adapter = ItemAdapter(item)
        
        # Convert item to dict and add metadata
        item_dict = dict(adapter)
        item_dict['_scraped_at'] = datetime.now().isoformat()
        item_dict['_spider'] = spider.name
        item_dict['_item_id'] = self.items_written + 1
        
        # Write item to file
        line = json.dumps(item_dict, ensure_ascii=False, default=str)
        self.file_handle.write(f"{line}\n")
        self.file_handle.flush()
        
        # Update counters
        self.items_written += 1
        self.current_file_size += len(line.encode('utf-8'))
        
        # Log progress
        if self.items_written % 25 == 0:
            size_mb = self.current_file_size / (1024 * 1024)
            logger.info(
                f"💾 Stored {self.items_written} items ({size_mb:.1f} MB) to {self.output_file}"
            )
        
        # Check file rotation
        max_size_mb = self.storage_settings.get('max_file_size_mb', 50)
        if self.current_file_size > max_size_mb * 1024 * 1024:
            self._rotate_file(spider)
        
        return item
    
    def _rotate_file(self, spider):
        """Rota el archivo de salida cuando supera el tamaño máximo."""
        logger.info(f"🔄 Rotating output file (size limit reached)")
        
        # Close current file
        if self.file_handle:
            self.file_handle.close()
        
        # Create backup if enabled
        if self.storage_settings.get('create_backups', True):
            backup_name = f"{self.output_file}.backup_{datetime.now().strftime('%H%M%S')}"
            os.rename(self.output_file, backup_name)
            logger.info(f"📦 Backup created: {backup_name}")
        
        # Reset counters and open new file
        self.current_file_size = 0
        self.open_spider(spider)
    
    def close_spider(self, spider):
        """Finaliza el pipeline de almacenamiento."""
        if self.file_handle:
            # Write final metadata
            if self.storage_settings.get('include_metadata', True):
                final_metadata = {
                    '_final_metadata': {
                        'end_time': datetime.now().isoformat(),
                        'total_items': self.items_written,
                        'file_size_mb': self.current_file_size / (1024 * 1024),
                        'spider': spider.name,
                    }
                }
                self.file_handle.write(f"{json.dumps(final_metadata, ensure_ascii=False)}\n")
            
            self.file_handle.close()
        
        logger.info("=" * 50)
        logger.info("💾 DEV STORAGE PIPELINE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"📁 Output file: {self.output_file}")
        logger.info(f"📦 Items written: {self.items_written}")
        logger.info(f"💽 File size: {self.current_file_size / (1024 * 1024):.1f} MB")
        logger.info(f"📊 Format: {self.storage_settings.get('output_format', 'jsonl')}")
        logger.info("=" * 50)


class ValidationPipeline:
    """
    Pipeline de validación mejorado para desarrollo.
    """
    
    def __init__(self, validation_settings: Dict[str, Any]):
        self.validation_settings = validation_settings
        self.items_validated = 0
        self.validation_errors = []
        self.items_failed = 0
        self.items_passed = 0
        
    @classmethod
    def from_crawler(cls, crawler):
        """Crea el pipeline desde la configuración del crawler."""
        validation_settings = crawler.settings.get('VALIDATION_SETTINGS', {})
        return cls(validation_settings)
    
    def process_item(self, item, spider):
        """Valida cada item según las reglas configuradas."""
        adapter = ItemAdapter(item)
        self.items_validated += 1
        
        errors = []
        
        # Validate required fields
        if self.validation_settings.get('require_all_fields', False):
            errors.extend(self._validate_required_fields(adapter))
        
        # Validate prices
        if self.validation_settings.get('validate_prices', True):
            errors.extend(self._validate_price_fields(adapter))
        
        # Validate URLs
        if self.validation_settings.get('validate_urls', True):
            errors.extend(self._validate_url_fields(adapter))
        
        # Validate images
        if self.validation_settings.get('validate_images', False):
            errors.extend(self._validate_image_fields(adapter))
        
        # Handle validation results
        if errors:
            self.items_failed += 1
            self.validation_errors.extend(errors)
            
            # Log errors if enabled
            if self.validation_settings.get('log_validation_errors', True):
                logger.warning(f"❌ Validation errors in item {self.items_validated}:")
                for error in errors:
                    logger.warning(f"  - {error}")
            
            # Fail pipeline if configured
            if self.validation_settings.get('fail_on_validation_error', False):
                raise scrapy.exceptions.DropItem(f"Validation failed: {errors}")
        else:
            self.items_passed += 1
        
        # Log progress
        if self.items_validated % 20 == 0:
            pass_rate = (self.items_passed / self.items_validated) * 100
            logger.info(
                f"✅ Validation: {self.items_validated} items processed, "
                f"{pass_rate:.1f}% passed ({self.items_failed} failed)"
            )
        
        return item
    
    def _validate_required_fields(self, adapter: ItemAdapter) -> List[str]:
        """Valida campos requeridos."""
        errors = []
        required_fields = ['name', 'product_url', 'store_name']
        
        for field in required_fields:
            if field not in adapter or not adapter.get(field):
                errors.append(f"Missing required field: {field}")
        
        return errors
    
    def _validate_price_fields(self, adapter: ItemAdapter) -> List[str]:
        """Valida campos de precio."""
        errors = []
        
        price = adapter.get('price_amount')
        if price is not None:
            try:
                price_float = float(price)
                if price_float < 0:
                    errors.append("Price cannot be negative")
                elif price_float > 10000:
                    errors.append("Price seems unreasonably high")
            except (ValueError, TypeError):
                errors.append(f"Invalid price format: {price}")
        
        # Validate discount percentage
        discount = adapter.get('discount_percentage', 0)
        if discount is not None:
            try:
                discount_float = float(discount)
                if discount_float < 0 or discount_float > 100:
                    errors.append("Discount percentage must be between 0 and 100")
            except (ValueError, TypeError):
                errors.append(f"Invalid discount format: {discount}")
        
        return errors
    
    def _validate_url_fields(self, adapter: ItemAdapter) -> List[str]:
        """Valida campos de URL."""
        errors = []
        
        url = adapter.get('product_url')
        if url and not url.startswith(('http://', 'https://')):
            errors.append(f"Invalid URL format: {url}")
        
        image_url = adapter.get('image_url')
        if image_url and not image_url.startswith(('http://', 'https://')):
            errors.append(f"Invalid image URL format: {image_url}")
        
        return errors
    
    def _validate_image_fields(self, adapter: ItemAdapter) -> List[str]:
        """Valida campos de imagen."""
        errors = []
        
        # Basic image URL validation (extended validation would require HTTP requests)
        image_url = adapter.get('image_url')
        if image_url:
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
            if not any(image_url.lower().endswith(ext) for ext in valid_extensions):
                # Only warn, don't fail - many sites use dynamic image URLs
                logger.debug(f"Image URL may not have standard extension: {image_url}")
        
        return errors
    
    def close_spider(self, spider):
        """Finaliza el pipeline de validación."""
        pass_rate = (self.items_passed / self.items_validated * 100) if self.items_validated > 0 else 0
        
        logger.info("=" * 50)
        logger.info("✅ VALIDATION PIPELINE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"📊 Items validated: {self.items_validated}")
        logger.info(f"✅ Items passed: {self.items_passed} ({pass_rate:.1f}%)")
        logger.info(f"❌ Items failed: {self.items_failed}")
        logger.info(f"🚨 Total validation errors: {len(self.validation_errors)}")
        
        if self.validation_errors and self.validation_settings.get('log_validation_errors', True):
            logger.info("📝 Most common validation errors:")
            error_counts = {}
            for error in self.validation_errors:
                error_counts[error] = error_counts.get(error, 0) + 1
            
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                logger.info(f"  - {error}: {count} times")
        
        logger.info("=" * 50)
