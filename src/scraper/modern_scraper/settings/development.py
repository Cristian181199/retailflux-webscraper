"""
Development Settings

Configuración específica para desarrollo con límites de seguridad
y configuraciones optimizadas para pruebas locales.
"""
import os
from .base import *  # Import all base settings

# Development environment marker
ENVIRONMENT = 'development'
DEBUG = True

# ============================================================================
# SPIDER LIMITS & SAFETY MEASURES
# ============================================================================

# Close spider after certain number of items/pages (safety limits)
CLOSESPIDER_ITEMCOUNT = 5  # Max 5 products in dev for testing
CLOSESPIDER_PAGECOUNT = 100  # Max 100 pages in dev
CLOSESPIDER_TIMEOUT = 300  # Max 5 minutes in dev
CLOSESPIDER_ERRORCOUNT = 10  # Stop after 10 errors

# Development-specific scraper settings
DEV_SCRAPER_SETTINGS = {
    'test_mode': True,
    'max_sitemaps': 2,  # Only process first 2 sitemaps
    'max_products_per_category': 10,  # Max 10 products per category
    'sample_categories_only': True,  # Only scrape a sample of categories
    'enable_stats_collection': True,
    'log_scraped_urls': True,
    'validate_items_strict': True,
}

# ============================================================================
# DOWNLOAD & REQUEST SETTINGS
# ============================================================================

# More conservative delays for development
DOWNLOAD_DELAY = 20  # 20 seconds between requests
RANDOMIZE_DELAY = 0.5  # ±50% randomization
DOWNLOAD_TIMEOUT = 30  # 30 second timeout

# Enable autothrottling with conservative settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 5
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = True  # Enable for debugging

# Concurrent requests (keep low for development)
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# ============================================================================
# RETRY SETTINGS
# ============================================================================

# Retry configuration - less aggressive in dev
RETRY_ENABLED = True
RETRY_TIMES = 2  # Only 2 retries in dev
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
RETRY_PRIORITY_ADJUST = -1

# ============================================================================
# USER AGENT & HEADERS
# ============================================================================

# Use a development-specific user agent
USER_AGENT = 'edeka-scraper-dev (+http://www.yourdomain.com/bot)'

# Additional headers for development
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'de,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': USER_AGENT,
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Enhanced logging for development
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/dev_scraper.log'

# Create logs directory if it doesn't exist
log_dir = os.path.dirname(LOG_FILE) if LOG_FILE else 'logs'
os.makedirs(log_dir, exist_ok=True)

# Custom logging format for development
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Enable request/response logging in development
DOWNLOADER_MIDDLEWARES.update({
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 590,
    'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
})

# ============================================================================
# PIPELINES CONFIGURATION
# ============================================================================

# Enable pipelines for development with debugging
ITEM_PIPELINES = {
    'modern_scraper.pipelines.dev_pipelines.DebugPipeline': 400,  # Debug-only pipeline
    'modern_scraper.pipelines.dev_pipelines.DevStoragePipeline': 500,  # Dev storage
}

# ============================================================================
# STORAGE CONFIGURATION
# ============================================================================

# Development storage settings (files instead of database)
DEV_STORAGE_SETTINGS = {
    'output_format': 'jsonl',  # JSON Lines format
    'output_file': 'data/dev_products_{timestamp}.jsonl',
    'create_backups': True,
    'max_file_size_mb': 50,  # Rotate after 50MB
    'compression': 'gzip',
    'include_metadata': True,
}

# ============================================================================
# CACHING CONFIGURATION
# ============================================================================

# Enable HTTP caching for faster development iterations
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hour cache
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 505, 500, 403, 404, 408]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# ============================================================================
# EXTENSIONS CONFIGURATION
# ============================================================================

# Enable useful extensions for development
EXTENSIONS = {
    'scrapy.extensions.logstats.LogStats': 0,
    'scrapy.extensions.telnet.TelnetConsole': 0,
    'scrapy.extensions.corestats.CoreStats': 0,
    'scrapy.extensions.memusage.MemoryUsage': 0,
    'scrapy.extensions.closespider.CloseSpider': 0,
    # 'modern_scraper.extensions.DevStatsExtension': 100,  # Custom dev stats - TODO: implement
}

# Memory usage monitoring
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 512  # 512MB limit for dev
MEMUSAGE_WARNING_MB = 256  # Warning at 256MB
MEMUSAGE_NOTIFY_MAIL = []  # No email notifications in dev

# ============================================================================
# STATS COLLECTION
# ============================================================================

# Enhanced stats collection for development
STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'

# Custom stats configuration
DEV_STATS_SETTINGS = {
    'collect_spider_stats': True,
    'collect_item_stats': True,
    'collect_response_stats': True,
    'collect_error_stats': True,
    'export_stats': True,
    'stats_export_file': 'data/dev_stats_{timestamp}.json',
    'real_time_stats': True,
}

# ============================================================================
# SPIDER-SPECIFIC SETTINGS
# ============================================================================

# Settings specific to individual spiders
SPIDER_SETTINGS = {
    'edeka_spider': {
        'max_categories': 5,  # Only 5 categories in dev
        'products_per_category': 10,
        'enable_price_tracking': True,
        'sitemap_urls': [
            'https://www.edeka24.de/sitemap.xml',  # Only main sitemap
        ],
        'category_filters': [
            'lebensmittel',
            'getraenke', 
            'drogerie',
        ],
        'skip_out_of_stock': False,  # Keep out of stock for testing
    },
    'rewe_spider': {
        'max_categories': 3,
        'products_per_category': 8,
        'enable_nutritional_data': True,
        'start_urls': [
            'https://shop.rewe.de/c/lebensmittel/',
        ],
    },
}

# ============================================================================
# MONITORING & ALERTING
# ============================================================================

# Development monitoring (console only)
MONITORING_SETTINGS = {
    'enable_console_monitoring': True,
    'enable_file_monitoring': True,
    'monitoring_interval': 30,  # 30 seconds
    'progress_log_interval': 50,  # Every 50 items
    'alert_on_errors': True,
    'alert_error_threshold': 5,
    'console_colors': True,
}

# ============================================================================
# TESTING & VALIDATION
# ============================================================================

# Validation settings for development
VALIDATION_SETTINGS = {
    'strict_validation': True,
    'require_all_fields': False,  # Allow partial items for testing
    'validate_prices': True,
    'validate_urls': True,
    'validate_images': False,  # Skip image validation in dev
    'log_validation_errors': True,
    'fail_on_validation_error': False,  # Don't fail pipeline on errors
}

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

# Reactor thread pool size
REACTOR_THREADPOOL_MAXSIZE = 10

# DNS timeout
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNS_TIMEOUT = 10

# TCP connection settings
DOWNLOAD_WARNSIZE = 33554432  # 32MB
DOWNLOAD_MAXSIZE = 67108864   # 64MB

# ============================================================================
# DEVELOPMENT UTILITIES
# ============================================================================

# Enable development utilities
DEV_UTILS = {
    'enable_scrapy_shell': True,
    'enable_request_fingerprinting': True,
    'enable_response_debugging': True,
    'save_failed_responses': True,
    'failed_responses_dir': 'debug/failed_responses/',
    'enable_item_export': True,
    'item_export_formats': ['json', 'csv'],
}

# Create debug directories
for debug_dir in ['debug', 'debug/failed_responses', 'data', 'logs']:
    os.makedirs(debug_dir, exist_ok=True)

# ============================================================================
# DEVELOPMENT OVERRIDES
# ============================================================================

# Allow command line overrides
COMMANDS_MODULE = 'modern_scraper.commands'

# Enable development-specific commands
DEV_COMMANDS = {
    'test_spider': 'modern_scraper.commands.test_spider',
    'validate_items': 'modern_scraper.commands.validate_items',
    'export_stats': 'modern_scraper.commands.export_stats',
    'debug_spider': 'modern_scraper.commands.debug_spider',
}

print("🧪 Development settings loaded successfully")
print(f"📊 Spider limits: {CLOSESPIDER_ITEMCOUNT} items, {CLOSESPIDER_PAGECOUNT} pages, {CLOSESPIDER_TIMEOUT}s timeout")
print(f"⏱️  Request delay: {DOWNLOAD_DELAY}s (±{int(RANDOMIZE_DELAY*100)}%)")
print(f"🔄 Concurrent requests: {CONCURRENT_REQUESTS} global, {CONCURRENT_REQUESTS_PER_DOMAIN} per domain")
print(f"💾 Caching: {'Enabled' if HTTPCACHE_ENABLED else 'Disabled'}")
print(f"📁 Outputs: logs/{LOG_FILE}, data/dev_products_*.jsonl")
