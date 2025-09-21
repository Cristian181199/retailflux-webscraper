"""
Price Parser Utilities

Utilidades para parsing y transformación de precios e información
de productos desde texto sin estructura a datos estructurados.
"""
import re
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)


class PriceParser:
    """Parser especializado para precios de productos."""
    
    # Regex patterns for price parsing
    PRICE_PATTERNS = {
        # Main price: "2,99 €", "€2.99", "1.50EUR"
        'main_price': re.compile(r'(?:€\s*)?(\d+[,.]\d{2})(?:\s*€|EUR)?', re.IGNORECASE),
        
        # Base price: "1,99 € / 100 g", "(2.50 €/kg)", "€1.20 per 100ml"
        'base_price': re.compile(
            r'(?:\()?(?:€\s*)?(\d+[,.]\d{2})(?:\s*€)?\s*[/]?\s*(?:per\s+)?(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)(?:\))?',
            re.IGNORECASE
        ),
        
        # Units normalization
        'unit_normalize': {
            'g': 'g', 'gr': 'g', 'gram': 'g', 'gramos': 'g',
            'kg': 'kg', 'kilo': 'kg', 'kilogram': 'kg', 'kilos': 'kg',
            'ml': 'ml', 'milliliter': 'ml', 'millilitro': 'ml',
            'l': 'L', 'liter': 'L', 'litro': 'L', 'litre': 'L',
            'st': 'piece', 'stück': 'piece', 'piece': 'piece', 'pcs': 'piece',
            'm': 'm', 'meter': 'm', 'metre': 'm',
            'cm': 'cm', 'centimeter': 'cm', 'centimetre': 'cm',
        }
    }
    
    @classmethod
    def parse_main_price(cls, price_text: str) -> Optional[Decimal]:
        """
        Extrae el precio principal de un texto.
        
        Args:
            price_text: Texto que contiene el precio
            
        Returns:
            Decimal con el precio o None si no se puede parsear
        """
        if not price_text:
            return None
            
        match = cls.PRICE_PATTERNS['main_price'].search(price_text)
        if match:
            try:
                price_str = match.group(1).replace(',', '.')
                return Decimal(price_str)
            except (InvalidOperation, ValueError) as e:
                logger.warning(f"Error parsing main price '{price_text}': {e}")
                return None
        
        return None
    
    @classmethod 
    def parse_base_price(cls, base_price_text: str) -> Dict[str, Any]:
        """
        Parsea el precio base (precio por unidad).
        
        Args:
            base_price_text: Texto como "1,99 € / 100 g"
            
        Returns:
            Dict con 'amount', 'unit', 'quantity' o valores None
        """
        result = {
            'amount': None,
            'unit': None,
            'quantity': None
        }
        
        if not base_price_text:
            return result
            
        match = cls.PRICE_PATTERNS['base_price'].search(base_price_text)
        if match:
            try:
                # Parse price amount
                price_str = match.group(1).replace(',', '.')
                result['amount'] = Decimal(price_str)
                
                # Parse quantity
                quantity_str = match.group(2).replace(',', '.')
                result['quantity'] = Decimal(quantity_str)
                
                # Parse and normalize unit
                unit_str = match.group(3).lower().strip()
                result['unit'] = cls.PRICE_PATTERNS['unit_normalize'].get(unit_str, unit_str)
                
            except (InvalidOperation, ValueError, AttributeError) as e:
                logger.warning(f"Error parsing base price '{base_price_text}': {e}")
        
        return result
    
    @classmethod
    def detect_availability(cls, text: str) -> Tuple[str, Optional[str]]:
        """
        Detecta el estado de disponibilidad del producto.
        
        Args:
            text: Texto de la página que puede contener información de stock
            
        Returns:
            Tuple (status, availability_text) donde status es:
            'in_stock', 'out_of_stock', o 'unknown'
        """
        if not text:
            return 'unknown', None
        
        text_lower = text.lower()
        
        # Patterns for in stock
        in_stock_patterns = [
            'verfügbar', 'available', 'auf lager', 'in stock', 
            'lieferbar', 'sofort verfügbar', 'vorrätig'
        ]
        
        # Patterns for out of stock
        out_of_stock_patterns = [
            'nicht verfügbar', 'out of stock', 'ausverkauft', 
            'nicht lieferbar', 'temporär nicht verfügbar',
            'nicht vorrätig', 'sold out'
        ]
        
        for pattern in in_stock_patterns:
            if pattern in text_lower:
                return 'in_stock', text.strip()
        
        for pattern in out_of_stock_patterns:
            if pattern in text_lower:
                return 'out_of_stock', text.strip()
        
        return 'unknown', text.strip() if text.strip() else None


class DataEnricher:
    """Enriquece datos de productos con información estructurada."""
    
    @classmethod
    def extract_product_details(cls, description: str, selectors_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae detalles estructurados del producto.
        
        Args:
            description: Descripción del producto
            selectors_data: Datos extraídos de selectores específicos
            
        Returns:
            Dict con información estructurada
        """
        details = {}
        
        if description:
            details['description_length'] = len(description)
            
            # Extract key-value pairs from description
            # Pattern: "Key: Value" or "Key - Value"
            kv_pattern = re.compile(r'([A-Za-z\s]+):\s*([^\n\r]+)', re.MULTILINE)
            matches = kv_pattern.findall(description)
            
            for key, value in matches:
                clean_key = key.strip().lower().replace(' ', '_')
                details[clean_key] = value.strip()
        
        # Add selector-based data
        if selectors_data:
            details.update(selectors_data)
        
        return details
    
    @classmethod
    def extract_manufacturer_from_name(cls, product_name: str) -> Optional[str]:
        """
        Intenta extraer el nombre del fabricante del nombre del producto.
        
        Args:
            product_name: Nombre del producto
            
        Returns:
            Nombre del fabricante o None
        """
        if not product_name:
            return None
        
        # Common manufacturer patterns
        known_brands = [
            'coca-cola', 'pepsi', 'nestle', 'unilever', 'procter', 'johnson',
            'kellogg', 'mars', 'ferrero', 'kraft', 'danone', 'löwenbräu',
            'beck', 'warsteiner', 'krombacher', 'bitburger', 'franziskaner'
        ]
        
        name_lower = product_name.lower()
        
        for brand in known_brands:
            if brand in name_lower:
                return brand.title()
        
        # Try to extract first word if it looks like a brand
        first_word = product_name.split()[0] if product_name.split() else ''
        if len(first_word) > 2 and first_word.isalpha():
            return first_word
        
        return None
    
    @classmethod
    def generate_sku_from_url(cls, product_url: str) -> Optional[str]:
        """
        Genera un SKU basado en la URL del producto si no hay uno disponible.
        
        Args:
            product_url: URL del producto
            
        Returns:
            SKU generado o None
        """
        if not product_url:
            return None
        
        # Extract product ID from URL patterns
        patterns = [
            r'/products?/(\d+)',
            r'/item/(\d+)',
            r'[?&]id=(\d+)',
            r'/p/([a-zA-Z0-9-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, product_url)
            if match:
                return f"EDEKA-{match.group(1)}"
        
        # Fallback: use hash of URL
        import hashlib
        url_hash = hashlib.md5(product_url.encode()).hexdigest()[:8]
        return f"EDEKA-{url_hash.upper()}"
    
    @classmethod
    def create_category_slug(cls, category_name: str) -> str:
        """
        Crea un slug para una categoría.
        
        Args:
            category_name: Nombre de la categoría
            
        Returns:
            Slug de la categoría
        """
        if not category_name:
            return ''
        
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', category_name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    @classmethod
    def create_store_slug(cls, store_name: str) -> str:
        """
        Crea un slug para una tienda.
        
        Args:
            store_name: Nombre de la tienda
            
        Returns:
            Slug de la tienda
        """
        return cls.create_category_slug(store_name)
