# Scrapy settings for the modern_scraper project.
# For a full list of settings and their documentation, see:
# https://docs.scrapy.org/en/latest/topics/settings.html

import os
from dotenv import load_dotenv

# --- Load Environment Variables ---
# Load variables from the .env file located at the project root.
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(dotenv_path=env_path)

# --- General Project Settings ---
BOT_NAME = "modern_scraper"
SPIDER_MODULES = ["modern_scraper.spiders"]
NEWSPIDER_MODULE = "modern_scraper.spiders"

ADDONS = {}

# --- Crawling Politeness ---
# 1. Identify your bot with a descriptive User-Agent.
# It's good practice to include contact information.
USER_AGENT = "ModernEdekaScraper/1.0 (+cristian181199@gmail.com)"

# 2. Obey the rules defined in the target website's robots.txt file.
ROBOTSTXT_OBEY = True

# 3. Configure a download delay to avoid overwhelming the server.
# This helps to be a responsible crawler.
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 2  # Reduced for faster testing

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#     "modern_scraper.middlewares.ModernScraperSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#     "modern_scraper.middlewares.ModernScraperDownloaderMiddleware": 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#     "scrapy.extensions.telnet.TelnetConsole": None,
# }

# --- Item Pipelines ---
# Configure data processing pipelines in order of execution
ITEM_PIPELINES = {
    "modern_scraper.pipelines.validation.ValidationPipeline": 100,
    "modern_scraper.pipelines.validation.DuplicateDetectionPipeline": 200,
    "modern_scraper.pipelines.enrichment.EnrichmentPipeline": 300,
    # Database pipeline for full integration testing
    "modern_scraper.pipelines.database.DatabasePipeline": 400,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# --- Feed Export Settings ---
# Set a future-proof value for feed export encoding.
FEED_EXPORT_ENCODING = "utf-8"

# --- Logging Settings ---
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(levelname)s: %(message)s'

# --- Development Configuration ---
DEV_SCRAPER_SETTINGS = {
    'max_sitemaps': 1,  # Limit sitemaps for testing
    'max_products_per_category': 5,  # Reduced for faster testing
    'test_mode': True,  # Continue on errors in development
    'enable_data_export': True,
}

# --- Database Configuration ---
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'products_db')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
