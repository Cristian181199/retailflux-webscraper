"""
Development Settings for Modern Scraper

Configuración optimizada para desarrollo local con límites de seguridad.
Diseñada para testing con datasets pequeños y crawling respetuoso.
"""
from .base_settings import *

# ==========================================
# DEVELOPMENT-SPECIFIC OVERRIDES
# ==========================================

# Enhanced politeness for development
DOWNLOAD_DELAY = 20  # 20 seconds between requests
RANDOMIZE_DOWNLOAD_DELAY = 0.5  # 0.5 * to 1.5 * DOWNLOAD_DELAY
CONCURRENT_REQUESTS = 1  # Single request at a time
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # One request per domain

# AutoThrottle for development (conservative)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
AUTOTHROTTLE_DEBUG = True  # Enable debug logging

# Development limits (SAFETY FIRST)
CLOSESPIDER_ITEMCOUNT = 50   # Stop after 50 items
CLOSESPIDER_TIMEOUT = 300    # Stop after 5 minutes
CLOSESPIDER_PAGECOUNT = 100  # Stop after 100 pages

# Memory limits (conservative)
MEMUSAGE_LIMIT_MB = 512   # 512MB limit
MEMUSAGE_WARNING_MB = 256 # Warning at 256MB

# Enhanced logging for development
LOG_LEVEL = 'DEBUG'
LOG_FILE = 'logs/scrapy_development.log'

# Enable detailed stats
STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'

# Development pipelines (ordered by priority)
ITEM_PIPELINES = {
    'modern_scraper.pipelines.validation.ValidationPipeline': 100,
    'modern_scraper.pipelines.enrichment.EnrichmentPipeline': 200,
    'modern_scraper.pipelines.database.DatabasePipeline': 300,
}

# Custom development settings
DEV_SCRAPER_SETTINGS = {
    'max_products_per_category': 10,    # Limit products per category
    'max_categories': 3,                # Limit number of categories
    'max_sitemaps': 2,                  # Limit number of sitemaps to process
    'test_mode': True,                  # Enable test mode
    'dry_run': False,                   # Set to True for no database writes
    'debug_selectors': True,            # Debug CSS/XPath selectors
    'save_html_samples': True,          # Save HTML samples for debugging
}

# Override modern scraper settings for development
MODERN_SCRAPER_SETTINGS.update({
    'batch_size': 10,                   # Smaller batches for development
    'generate_embeddings': False,       # Disable AI features in dev by default
    'enable_ai_features': False,        # Disable AI features in dev by default
})

# Development-specific extensions
EXTENSIONS.update({
    'scrapy.extensions.closespider.CloseSpider': 500,
    'scrapy.extensions.debug.StackTraceDump': 0,  # Enable stack trace dumps
})

# Feed exports for development (save to JSON file)
FEEDS = {
    'logs/development_products_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'indent': 2,
        'fields': [
            'name', 'price_amount', 'price_currency', 'sku', 
            'product_url', 'category_path', 'store_name',
            'scraped_at', 'is_new_product'
        ]
    }
}

# Error handling for development (more lenient)
ERROR_HANDLING.update({
    'continue_on_error': True,
    'max_errors_per_spider': 20,  # Lower error threshold
    'debug_errors': True,         # Enhanced error debugging
})

# Development spider settings
SPIDER_SETTINGS = {
    'edeka': {
        'start_urls_limit': 2,        # Limit start URLs
        'follow_pagination': False,   # Don't follow pagination
        'max_depth': 2,              # Limit crawling depth
        'respect_robots_delay': True, # Respect robots.txt crawl delay
    }
}

# Cache settings for development (to avoid re-downloading during testing)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hour cache
HTTPCACHE_DIR = 'httpcache/dev'
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 505, 500, 403, 404, 408]

# Request/Response middleware for development
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 590,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 560,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 500,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'scrapy.downloadermiddlewares.ajaxcrawl.AjaxCrawlMiddleware': 560,
    'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': 300,
    'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
    'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
}

# Development middleware for debugging
SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 50,
    'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': 500,
    'scrapy.spidermiddlewares.referer.RefererMiddleware': 700,
    'scrapy.spidermiddlewares.urllength.UrlLengthMiddleware': 800,
    'scrapy.spidermiddlewares.depth.DepthMiddleware': 900,
}

print("🧪 DEVELOPMENT CONFIGURATION LOADED")
print("=" * 50)
print(f"📊 Max items: {CLOSESPIDER_ITEMCOUNT}")
print(f"⏰ Max time: {CLOSESPIDER_TIMEOUT}s")
print(f"🐌 Download delay: {DOWNLOAD_DELAY}s")
print(f"🔄 Concurrent requests: {CONCURRENT_REQUESTS}")
print(f"💾 Cache enabled: {HTTPCACHE_ENABLED}")
print(f"🤖 AI features: {MODERN_SCRAPER_SETTINGS['enable_ai_features']}")
print("=" * 50)
