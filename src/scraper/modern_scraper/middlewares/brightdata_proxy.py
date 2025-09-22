"""
Brightdata Proxy Middleware

Scrapy downloader middleware for integrating with Brightdata residential proxies.
Handles proxy rotation, session management, error handling, and metrics collection.
"""
import time
import logging
from urllib.parse import urlparse
from typing import Union, Optional

import scrapy
from scrapy import signals
from scrapy.http import Request, Response
from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from twisted.internet.error import TimeoutError, DNSLookupError, ConnectionRefusedError

from .proxy_manager import ProxyManager
from ..config.brightdata_config import get_brightdata_config

logger = logging.getLogger(__name__)


class BrightdataProxyMiddleware:
    """
    Scrapy middleware for Brightdata residential proxy integration.
    
    Features:
    - Automatic proxy rotation
    - Session management with sticky IPs
    - Error detection and failover
    - Performance metrics and monitoring
    - User-Agent coordination
    """
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.config_manager = get_brightdata_config()
        
        # Get settings
        settings = crawler.settings
        self.max_sessions = settings.getint('BRIGHTDATA_MAX_SESSIONS', 5)
        self.rotation_interval = settings.getint('BRIGHTDATA_ROTATION_INTERVAL', 10)
        self.timeout = settings.getint('BRIGHTDATA_TIMEOUT', 30)
        self.max_retries = settings.getint('BRIGHTDATA_MAX_RETRIES', 3)
        
        # Initialize proxy manager
        self.proxy_manager = ProxyManager(
            max_sessions=self.max_sessions,
            rotation_interval=self.rotation_interval
        )
        
        # Stats
        self.stats = crawler.stats
        self.enabled = self.config_manager.is_enabled()
        
        # User agent pool for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        ]
        
        if not self.enabled:
            logger.info("🚫 Brightdata proxy middleware disabled")
            raise NotConfigured("Brightdata proxy middleware is disabled")
        
        logger.info("🚀 Brightdata proxy middleware initialized")
        logger.info(f"📊 Config: {self.max_sessions} sessions, {self.rotation_interval} rotation interval")
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware instance from crawler."""
        middleware = cls(crawler)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware
    
    def spider_opened(self, spider):
        """Called when spider is opened."""
        logger.info(f"🕷️ Spider {spider.name} opened with Brightdata proxies")
        self.stats.set_value('brightdata/enabled', True)
        
        # Log initial proxy stats
        proxy_stats = self.proxy_manager.get_stats()
        logger.info(f"🔄 Proxy stats: {proxy_stats}")
    
    def spider_closed(self, spider, reason):
        """Called when spider is closed."""
        proxy_stats = self.proxy_manager.get_stats()
        
        logger.info("=" * 50)
        logger.info("🔄 BRIGHTDATA PROXY STATISTICS")
        logger.info("=" * 50)
        logger.info(f"📊 Total requests: {proxy_stats.get('total_requests', 0)}")
        logger.info(f"✅ Successful: {proxy_stats.get('successful_requests', 0)}")
        logger.info(f"❌ Failed: {proxy_stats.get('failed_requests', 0)}")
        logger.info(f"📈 Success rate: {proxy_stats.get('overall_success_rate', 0)}%")
        logger.info(f"🔄 Active sessions: {proxy_stats.get('active_sessions', 0)}")
        logger.info(f"🚫 Blacklisted: {proxy_stats.get('blacklisted_sessions', 0)}")
        
        # Log session details
        for session in proxy_stats.get('session_details', []):
            logger.info(f"   Session {session['id']}: {session['requests']} req, "
                       f"{session['success_rate']}% success, "
                       f"{session['created_minutes_ago']}min old")
        
        logger.info("=" * 50)
        
        # Update spider stats
        for key, value in proxy_stats.items():
            if isinstance(value, (int, float)):
                self.stats.set_value(f'brightdata/{key}', value)
    
    def process_request(self, request: Request, spider) -> Optional[Request]:
        """
        Process outgoing requests to add proxy configuration.
        
        This is called for each request before it's sent to the downloader.
        """
        if not self.enabled:
            return None
        
        # Skip if request already has proxy set (manual override)
        if request.meta.get('proxy'):
            return None
        
        # Skip certain request types
        if self._should_skip_request(request):
            return None
        
        # Get proxy from manager
        proxy_info = self.proxy_manager.get_proxy(request)
        
        if not proxy_info:
            logger.warning(f"⚠️ No proxy available for {request.url}")
            return None
        
        proxy_url, proxy_meta = proxy_info
        
        # Set proxy in request
        request.meta['proxy'] = proxy_url
        request.meta.update(proxy_meta)
        
        # Add proxy info to meta for tracking
        request.meta['brightdata_enabled'] = True
        request.meta['request_start_time'] = time.time()
        
        # Rotate User-Agent with proxy
        if 'User-Agent' not in request.headers:
            user_agent = self._get_rotated_user_agent(proxy_meta['proxy_session_id'])
            request.headers['User-Agent'] = user_agent
        
        logger.debug(f"🔄 Using proxy for {request.url}: {proxy_meta['proxy_session_id'][:8]}...")
        
        return None
    
    def process_response(self, request: Request, response: Response, spider) -> Union[Request, Response]:
        """
        Process responses to track proxy performance.
        
        This is called for each response after it's received.
        """
        if not request.meta.get('brightdata_enabled'):
            return response
        
        session_id = request.meta.get('proxy_session_id')
        start_time = request.meta.get('request_start_time', 0)
        response_time = time.time() - start_time if start_time > 0 else 0
        
        # Check if response indicates success or failure
        if self._is_successful_response(response):
            self.proxy_manager.record_success(session_id, response_time)
            self.stats.inc_value('brightdata/successful_requests')
            logger.debug(f"✅ Successful response via proxy {session_id[:8]}... ({response.status})")
        else:
            # Determine error type
            error_type = self._classify_response_error(response)
            self.proxy_manager.record_failure(session_id, error_type)
            self.stats.inc_value(f'brightdata/{error_type}_requests')
            
            logger.warning(f"❌ Failed response via proxy {session_id[:8]}... "
                          f"({response.status}, {error_type})")
            
            # Retry with different proxy for certain errors
            if self._should_retry_with_different_proxy(response, request):
                return self._retry_with_different_proxy(request, spider)
        
        return response
    
    def process_exception(self, request: Request, exception, spider) -> Optional[Request]:
        """
        Process exceptions to handle proxy errors.
        
        This is called when a request raises an exception.
        """
        if not request.meta.get('brightdata_enabled'):
            return None
        
        session_id = request.meta.get('proxy_session_id', 'unknown')
        error_type = self._classify_exception_error(exception)
        
        self.proxy_manager.record_failure(session_id, error_type)
        self.stats.inc_value(f'brightdata/{error_type}_requests')
        
        logger.warning(f"❌ Request exception via proxy {session_id[:8]}... "
                      f"({type(exception).__name__}: {str(exception)})")
        
        # Retry with different proxy for certain exceptions
        if self._should_retry_exception_with_different_proxy(exception, request):
            return self._retry_with_different_proxy(request, spider)
        
        return None
    
    def _should_skip_request(self, request: Request) -> bool:
        """
        Determine if a request should skip proxy usage.
        """
        url = request.url.lower()
        
        # Skip robots.txt and other meta files
        if any(pattern in url for pattern in ['/robots.txt', '/favicon.ico', '/sitemap']):
            return True
        
        # Skip if explicitly disabled for this request
        if request.meta.get('skip_brightdata_proxy'):
            return True
        
        return False
    
    def _get_rotated_user_agent(self, session_id: str) -> str:
        """
        Get a user agent coordinated with the proxy session.
        """
        # Use session ID to consistently select user agent
        agent_index = hash(session_id) % len(self.user_agents)
        return self.user_agents[agent_index]
    
    def _is_successful_response(self, response: Response) -> bool:
        """
        Determine if response indicates success.
        """
        # 2xx and 3xx status codes are generally successful
        if 200 <= response.status < 400:
            return True
        
        # Some 4xx codes might be acceptable (depends on use case)
        acceptable_4xx = [404]  # Product not found is acceptable
        if response.status in acceptable_4xx:
            return True
        
        return False
    
    def _classify_response_error(self, response: Response) -> str:
        """
        Classify the type of error based on response status.
        """
        if response.status == 403:
            return "blocked"
        elif response.status == 429:
            return "rate_limited"
        elif 500 <= response.status < 600:
            return "server_error"
        else:
            return "http_error"
    
    def _classify_exception_error(self, exception) -> str:
        """
        Classify the type of error based on exception.
        """
        if isinstance(exception, TimeoutError):
            return "timeout"
        elif isinstance(exception, (DNSLookupError, ConnectionRefusedError)):
            return "connection_error"
        else:
            return "unknown_error"
    
    def _should_retry_with_different_proxy(self, response: Response, request: Request) -> bool:
        """
        Determine if we should retry the request with a different proxy.
        """
        # Don't retry if we've already retried too many times
        retry_count = request.meta.get('brightdata_retry_count', 0)
        if retry_count >= self.max_retries:
            return False
        
        # Retry for certain status codes that might be proxy-related
        retry_statuses = [403, 429, 502, 503, 504]
        return response.status in retry_statuses
    
    def _should_retry_exception_with_different_proxy(self, exception, request: Request) -> bool:
        """
        Determine if we should retry the request with a different proxy for exceptions.
        """
        # Don't retry if we've already retried too many times
        retry_count = request.meta.get('brightdata_retry_count', 0)
        if retry_count >= self.max_retries:
            return False
        
        # Retry for connection-related exceptions
        retry_exceptions = (TimeoutError, DNSLookupError, ConnectionRefusedError)
        return isinstance(exception, retry_exceptions)
    
    def _retry_with_different_proxy(self, request: Request, spider) -> Request:
        """
        Create a new request with a different proxy.
        """
        # Increment retry count
        retry_count = request.meta.get('brightdata_retry_count', 0) + 1
        
        # Create new request
        new_request = request.copy()
        new_request.meta['brightdata_retry_count'] = retry_count
        
        # Clear old proxy info to get a new one
        new_request.meta.pop('proxy', None)
        new_request.meta.pop('proxy_session_id', None)
        new_request.meta.pop('proxy_created_at', None)
        new_request.meta.pop('proxy_requests_count', None)
        
        logger.info(f"🔄 Retrying with different proxy ({retry_count}/{self.max_retries}): {request.url}")
        
        return new_request
