"""
Production Settings for Modern Scraper

Configuración optimizada para scraping completo en producción.
Cumple con el requisito de 20s entre requests y objetivo de 2-3 horas.
"""
from .base_settings import *

# ==========================================
# PRODUCTION-SPECIFIC OVERRIDES
# ==========================================

# Production crawling parameters (compliance with requirements)
DOWNLOAD_DELAY = 20  # 20 seconds as required
RANDOMIZE_DOWNLOAD_DELAY = 0.1  # Small randomization (18-22 seconds)
CONCURRENT_REQUESTS = 3  # Multiple requests for efficiency
CONCURRENT_REQUESTS_PER_DOMAIN = 3  # Balanced concurrency per domain

# AutoThrottle for production (optimized)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 15
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False  # Disable debug in production

# Production limits (complete scraping)
CLOSESPIDER_ITEMCOUNT = 0      # No item limit (scrape all)
CLOSESPIDER_TIMEOUT = 10800    # 3 hours maximum (as required)
CLOSESPIDER_PAGECOUNT = 0      # No page limit

# Memory limits (production server)
MEMUSAGE_LIMIT_MB = 4096   # 4GB limit
MEMUSAGE_WARNING_MB = 2048 # Warning at 2GB

# Production logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/scrapy_production.log'

# Production pipelines (ordered by priority)
ITEM_PIPELINES = {
    'modern_scraper.pipelines.validation.ValidationPipeline': 100,
    'modern_scraper.pipelines.enrichment.EnrichmentPipeline': 200,
    'modern_scraper.pipelines.database.DatabasePipeline': 300,
}

# Custom production settings
PROD_SCRAPER_SETTINGS = {
    'max_products_per_category': 0,      # No limit per category
    'max_categories': 0,                 # No category limit
    'max_sitemaps': 0,                   # No sitemap limit
    'test_mode': False,                  # Disable test mode
    'dry_run': False,                    # Real database writes
    'debug_selectors': False,            # Disable debugging
    'save_html_samples': False,          # Don't save samples in prod
    'enable_progress_tracking': True,    # Enable progress monitoring
    'enable_eta_calculation': True,      # Calculate ETA
}

# Override modern scraper settings for production
MODERN_SCRAPER_SETTINGS.update({
    'batch_size': 200,                   # Larger batches for efficiency
    'generate_embeddings': True,         # Enable AI features if API key available
    'enable_ai_features': True,          # Enable AI features
})

# Production-specific extensions
EXTENSIONS.update({
    'scrapy.extensions.closespider.CloseSpider': 500,
    'scrapy.extensions.logstats.LogStats': 0,    # Enable stats logging
    'scrapy.extensions.statsmailer.StatsMailer': 500,  # Email stats (if configured)
})

# Smart throttling extension settings
SMART_THROTTLING = {
    'enabled': True,
    'target_time_hours': 3,        # Target 3 hours for completion
    'adjust_delay_dynamically': True,
    'monitor_progress': True,
    'estimate_total_items': True,
}

# Feed exports for production (multiple formats)
FEEDS = {
    'exports/production_products_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'indent': 2,
    },
    'exports/production_products_%(time)s.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': [
            'name', 'price_amount', 'price_currency', 'sku', 
            'product_url', 'category_path', 'store_name',
            'scraped_at', 'base_price_amount', 'base_price_unit'
        ]
    }
}

# Error handling for production (strict but resilient)
ERROR_HANDLING.update({
    'continue_on_error': True,
    'max_errors_per_spider': 500,  # Higher tolerance for large-scale scraping
    'debug_errors': False,         # Don't debug in production
    'log_critical_errors': True,   # Log critical errors only
})

# Production spider settings
SPIDER_SETTINGS = {
    'edeka': {
        'start_urls_limit': 0,           # No URL limit
        'follow_pagination': True,       # Follow all pagination
        'max_depth': 10,                 # Deep crawling
        'respect_robots_delay': True,    # Always respect robots.txt
        'enable_smart_throttling': True, # Dynamic delay adjustment
    }
}

# Disable cache in production (always get fresh data)
HTTPCACHE_ENABLED = False

# Production middleware optimized for performance
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 590,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 560,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 500,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'scrapy.downloadermiddlewares.ajaxcrawl.AjaxCrawlMiddleware': 560,
    'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': 300,
    'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
    'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
    # Custom middleware for smart throttling
    # 'modern_scraper.middlewares.SmartThrottlingMiddleware': 585,
}

# Production spider middleware
SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 50,
    'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': 500,
    'scrapy.spidermiddlewares.referer.RefererMiddleware': 700,
    'scrapy.spidermiddlewares.urllength.UrlLengthMiddleware': 800,
    'scrapy.spidermiddlewares.depth.DepthMiddleware': 900,
}

# Advanced retry configuration for production
RETRY_TIMES = 5  # More retries in production
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 520, 521]

# Download timeout for production
DOWNLOAD_TIMEOUT = 300  # 5 minutes timeout

# Database connection pooling for production
DATABASE_CONFIG.update({
    'pool_size': 20,           # Connection pool size
    'max_overflow': 10,        # Additional connections
    'pool_timeout': 30,        # Connection timeout
    'pool_recycle': 3600,      # Recycle connections after 1 hour
})

# Performance monitoring
PERFORMANCE_MONITORING = {
    'log_stats_interval': 300,    # Log stats every 5 minutes
    'track_memory_usage': True,   # Monitor memory
    'track_spider_progress': True, # Track progress per spider
    'estimate_completion_time': True, # ETA calculation
}

# Production alerts (can be integrated with monitoring systems)
ALERTS_CONFIG = {
    'enabled': False,  # Set to True when alert system is ready
    'error_threshold': 100,      # Alert after 100 errors
    'memory_threshold': 3072,    # Alert at 3GB memory usage
    'time_threshold': 14400,     # Alert if scraping takes > 4 hours
}

print("🚀 PRODUCTION CONFIGURATION LOADED")
print("=" * 50)
print(f"📊 Target completion: {CLOSESPIDER_TIMEOUT//3600} hours")
print(f"🐌 Download delay: {DOWNLOAD_DELAY}s")
print(f"🔄 Concurrent requests: {CONCURRENT_REQUESTS}")
print(f"💾 Cache disabled: {not HTTPCACHE_ENABLED}")
print(f"🤖 AI features: {MODERN_SCRAPER_SETTINGS['enable_ai_features']}")
print(f"📈 Batch size: {MODERN_SCRAPER_SETTINGS['batch_size']}")
print("=" * 50)
