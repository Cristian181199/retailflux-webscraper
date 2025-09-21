"""
Base Settings for Modern Scraper

Configuración base compartida entre entornos de desarrollo y producción.
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent  # Back to project root
SHARED_PATH = PROJECT_ROOT / "shared"

# Basic Scrapy settings
BOT_NAME = "modern_edeka_scraper"
SPIDER_MODULES = ["modern_scraper.spiders"]
NEWSPIDER_MODULE = "modern_scraper.spiders"

# User agent and politeness
USER_AGENT = "ModernEdekaScraper/2.0 (+cristian181199@gmail.com; AI-Powered Product Analysis)"
ROBOTSTXT_OBEY = True

# Basic request settings
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'de,en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Disable cookies (can be enabled if needed)
COOKIES_ENABLED = False

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False

# Enable and configure extensions
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,  # Disable telnet
    'scrapy.extensions.stats.StatsCollector': 0,     # Enable stats
    'scrapy.extensions.closespider.CloseSpider': 500, # Auto close settings
}

# Pipelines - will be overridden in environment-specific configs
ITEM_PIPELINES = {}

# Database configuration from environment
DATABASE_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres_db'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'products_db'),
    'user': os.getenv('POSTGRES_USER', 'cristian'),
    'password': os.getenv('POSTGRES_PASSWORD', 'cristian'),
}

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FILE = None  # Set to filename to enable file logging

# Feed exports (can be customized per environment)
FEED_EXPORT_ENCODING = 'utf-8'
FEEDS = {}

# AutoThrottle base configuration
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Memory usage monitoring
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048
MEMUSAGE_WARNING_MB = 1024

# Retry configuration
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Download timeout
DOWNLOAD_TIMEOUT = 180

# Enable compression
COMPRESSION_ENABLED = True

# Custom settings for the modern scraper
MODERN_SCRAPER_SETTINGS = {
    'enable_ai_features': os.getenv('ENABLE_AI_FEATURES', 'false').lower() == 'true',
    'openai_api_key': os.getenv('OPENAI_API_KEY'),
    'generate_embeddings': os.getenv('GENERATE_EMBEDDINGS', 'false').lower() == 'true',
    'batch_size': int(os.getenv('SCRAPER_BATCH_SIZE', 100)),
}

# Store-specific configuration
STORE_CONFIG = {
    'edeka': {
        'name': 'Edeka24',
        'display_name': 'EDEKA Online Shop',
        'website_url': 'https://www.edeka24.de',
        'country': 'DE',
        'currency': 'EUR',
        'slug': 'edeka24'
    }
}

# Category mapping and hierarchy settings
CATEGORY_SETTINGS = {
    'auto_create_hierarchy': True,
    'max_depth': 5,
    'default_parent': None,
}

# Product settings
PRODUCT_SETTINGS = {
    'auto_generate_sku': True,
    'detect_duplicates': True,
    'update_existing': True,
    'price_change_detection': True,
}

# Error handling
ERROR_HANDLING = {
    'continue_on_error': True,
    'log_errors': True,
    'max_errors_per_spider': 100,
}
