"""
Proxy Manager for Brightdata Integration

Handles proxy rotation, session management, and failover logic
for residential IP proxies from Brightdata.
"""
import time
import random
import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..config.brightdata_config import BrightdataConfig, get_brightdata_config

logger = logging.getLogger(__name__)


@dataclass
class ProxyMetrics:
    """Metrics tracking for a specific proxy configuration."""
    
    requests_sent: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    blocked_requests: int = 0
    timeout_requests: int = 0
    last_used: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    average_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.requests_sent == 0:
            return 100.0
        return (self.successful_requests / self.requests_sent) * 100
    
    @property
    def is_healthy(self) -> bool:
        """Determine if proxy is healthy based on success rate."""
        # Consider healthy if success rate > 80% and recent success
        if self.success_rate < 80:
            return False
        
        # Check if we had a recent success (within last 5 minutes)
        if self.last_success:
            return datetime.now() - self.last_success < timedelta(minutes=5)
        
        return self.requests_sent < 5  # New proxy, give it a chance


@dataclass
class ProxySession:
    """Represents a proxy session with sticky IP."""
    
    session_id: str
    config: BrightdataConfig
    created_at: datetime
    last_used: datetime
    requests_count: int = 0
    max_requests: int = 100  # Max requests per session
    max_duration: int = 3600  # Max duration in seconds (1 hour)
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        now = datetime.now()
        duration_expired = (now - self.created_at).seconds > self.max_duration
        requests_exceeded = self.requests_count >= self.max_requests
        return duration_expired or requests_exceeded
    
    @property
    def proxy_url(self) -> str:
        """Get proxy URL with session ID."""
        return self.config.proxy_url
    
    def use(self):
        """Mark session as used."""
        self.last_used = datetime.now()
        self.requests_count += 1


class ProxyRotator:
    """Handles intelligent proxy rotation logic."""
    
    def __init__(self, rotation_strategy: str = "round_robin"):
        self.rotation_strategy = rotation_strategy
        self.current_index = 0
        self.last_rotation = datetime.now()
    
    def select_next(self, proxy_sessions: List[ProxySession], 
                   metrics: Dict[str, ProxyMetrics]) -> Optional[ProxySession]:
        """Select next proxy based on strategy."""
        
        if not proxy_sessions:
            return None
        
        # Filter healthy sessions
        healthy_sessions = [
            session for session in proxy_sessions
            if not session.is_expired and metrics[session.session_id].is_healthy
        ]
        
        if not healthy_sessions:
            logger.warning("⚠️ No healthy proxy sessions available")
            # Return least used session as fallback
            return min(proxy_sessions, key=lambda s: s.requests_count)
        
        # Apply rotation strategy
        if self.rotation_strategy == "round_robin":
            return self._round_robin_select(healthy_sessions)
        elif self.rotation_strategy == "weighted":
            return self._weighted_select(healthy_sessions, metrics)
        elif self.rotation_strategy == "random":
            return random.choice(healthy_sessions)
        else:
            return healthy_sessions[0]
    
    def _round_robin_select(self, sessions: List[ProxySession]) -> ProxySession:
        """Round robin selection."""
        session = sessions[self.current_index % len(sessions)]
        self.current_index += 1
        return session
    
    def _weighted_select(self, sessions: List[ProxySession], 
                        metrics: Dict[str, ProxyMetrics]) -> ProxySession:
        """Weighted selection based on success rate."""
        # Weight by success rate and inverse of usage
        weights = []
        for session in sessions:
            metric = metrics[session.session_id]
            success_weight = metric.success_rate / 100
            usage_weight = 1 / (session.requests_count + 1)
            total_weight = success_weight * usage_weight
            weights.append(total_weight)
        
        # Weighted random selection
        total_weight = sum(weights)
        if total_weight == 0:
            return sessions[0]
        
        rand_val = random.uniform(0, total_weight)
        current_weight = 0
        
        for i, weight in enumerate(weights):
            current_weight += weight
            if rand_val <= current_weight:
                return sessions[i]
        
        return sessions[-1]  # Fallback


class ProxyManager:
    """
    Main proxy manager for Brightdata integration.
    
    Handles:
    - Session creation and rotation
    - Health monitoring
    - Failover logic
    - Performance metrics
    """
    
    def __init__(self, max_sessions: int = 5, rotation_interval: int = 10):
        self.config_manager = get_brightdata_config()
        self.max_sessions = max_sessions
        self.rotation_interval = rotation_interval  # requests
        
        # Session management
        self.sessions: Dict[str, ProxySession] = {}
        self.session_order: List[str] = []
        
        # Metrics tracking
        self.metrics: Dict[str, ProxyMetrics] = defaultdict(ProxyMetrics)
        
        # Rotation logic
        self.rotator = ProxyRotator("weighted")
        self.requests_since_rotation = 0
        
        # Blacklist for problematic proxies
        self.blacklisted_sessions: Dict[str, datetime] = {}
        self.blacklist_duration = timedelta(minutes=30)
        
        logger.info(f"🔄 ProxyManager initialized with {max_sessions} max sessions")
    
    def get_proxy(self, request) -> Optional[Tuple[str, Dict[str, any]]]:
        """
        Get a proxy for the request.
        
        Returns:
            Tuple of (proxy_url, meta_data) or None if no proxy available
        """
        if not self.config_manager.is_enabled():
            return None
        
        # Clean expired sessions and blacklist
        self._cleanup_expired()
        
        # Ensure we have active sessions
        self._ensure_sessions()
        
        # Get active sessions
        active_sessions = [s for s in self.sessions.values() if not s.is_expired]
        
        if not active_sessions:
            logger.error("❌ No active proxy sessions available")
            return None
        
        # Select next proxy
        selected_session = self.rotator.select_next(active_sessions, self.metrics)
        
        if not selected_session:
            logger.error("❌ Failed to select proxy session")
            return None
        
        # Update usage
        selected_session.use()
        self.requests_since_rotation += 1
        
        # Prepare meta data
        meta_data = {
            'proxy_session_id': selected_session.session_id,
            'proxy_created_at': selected_session.created_at,
            'proxy_requests_count': selected_session.requests_count,
        }
        
        logger.debug(f"🔄 Using proxy session {selected_session.session_id[:8]}... "
                    f"({selected_session.requests_count} requests)")
        
        return selected_session.proxy_url, meta_data
    
    def record_success(self, session_id: str, response_time: float = 0.0):
        """Record successful request for metrics."""
        if session_id in self.metrics:
            metric = self.metrics[session_id]
            metric.requests_sent += 1
            metric.successful_requests += 1
            metric.last_used = datetime.now()
            metric.last_success = datetime.now()
            
            if response_time > 0:
                metric.response_times.append(response_time)
                metric.average_response_time = sum(metric.response_times) / len(metric.response_times)
            
            logger.debug(f"✅ Recorded success for session {session_id[:8]}... "
                        f"(Success rate: {metric.success_rate:.1f}%)")
    
    def record_failure(self, session_id: str, error_type: str = "unknown"):
        """Record failed request for metrics."""
        if session_id in self.metrics:
            metric = self.metrics[session_id]
            metric.requests_sent += 1
            metric.failed_requests += 1
            metric.last_used = datetime.now()
            metric.last_failure = datetime.now()
            
            if error_type == "blocked":
                metric.blocked_requests += 1
            elif error_type == "timeout":
                metric.timeout_requests += 1
            
            # Blacklist if too many failures
            if metric.success_rate < 50 and metric.requests_sent > 10:
                self._blacklist_session(session_id)
            
            logger.debug(f"❌ Recorded {error_type} for session {session_id[:8]}... "
                        f"(Success rate: {metric.success_rate:.1f}%)")
    
    def _ensure_sessions(self):
        """Ensure we have enough active sessions."""
        config = self.config_manager.get_config()
        if not config:
            return
        
        active_count = len([s for s in self.sessions.values() if not s.is_expired])
        
        while active_count < self.max_sessions:
            session_id = self._generate_session_id()
            
            if session_id in self.blacklisted_sessions:
                continue
            
            session_config = BrightdataConfig(
                username=config.username,
                password=config.password,
                endpoint=config.endpoint,
                port=config.port,
                zone=config.zone,
                country=config.country,
                session_id=session_id
            )
            
            session = ProxySession(
                session_id=session_id,
                config=session_config,
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            
            self.sessions[session_id] = session
            self.session_order.append(session_id)
            
            logger.info(f"➕ Created new proxy session: {session_id[:8]}...")
            active_count += 1
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = str(int(time.time() * 1000))
        random_part = str(random.randint(1000, 9999))
        session_string = f"{timestamp}-{random_part}"
        
        # Create a short hash
        session_hash = hashlib.md5(session_string.encode()).hexdigest()[:16]
        return f"scraper-{session_hash}"
    
    def _cleanup_expired(self):
        """Remove expired sessions and clean blacklist."""
        # Remove expired sessions
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if session.is_expired
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            if session_id in self.session_order:
                self.session_order.remove(session_id)
            logger.info(f"🗑️ Removed expired session: {session_id[:8]}...")
        
        # Clean expired blacklist entries
        now = datetime.now()
        expired_blacklist = [
            sid for sid, blacklisted_at in self.blacklisted_sessions.items()
            if now - blacklisted_at > self.blacklist_duration
        ]
        
        for session_id in expired_blacklist:
            del self.blacklisted_sessions[session_id]
            logger.info(f"🔓 Removed from blacklist: {session_id[:8]}...")
    
    def _blacklist_session(self, session_id: str):
        """Blacklist a problematic session."""
        self.blacklisted_sessions[session_id] = datetime.now()
        
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        if session_id in self.session_order:
            self.session_order.remove(session_id)
        
        logger.warning(f"🚫 Blacklisted session: {session_id[:8]}... "
                      f"(Duration: {self.blacklist_duration})")
    
    def get_stats(self) -> Dict[str, any]:
        """Get comprehensive proxy statistics."""
        active_sessions = [s for s in self.sessions.values() if not s.is_expired]
        
        total_requests = sum(m.requests_sent for m in self.metrics.values())
        total_successful = sum(m.successful_requests for m in self.metrics.values())
        total_failed = sum(m.failed_requests for m in self.metrics.values())
        
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "enabled": self.config_manager.is_enabled(),
            "active_sessions": len(active_sessions),
            "total_sessions": len(self.sessions),
            "blacklisted_sessions": len(self.blacklisted_sessions),
            "max_sessions": self.max_sessions,
            "rotation_interval": self.rotation_interval,
            "requests_since_rotation": self.requests_since_rotation,
            "total_requests": total_requests,
            "successful_requests": total_successful,
            "failed_requests": total_failed,
            "overall_success_rate": round(overall_success_rate, 2),
            "session_details": [
                {
                    "id": s.session_id[:8],
                    "requests": s.requests_count,
                    "success_rate": round(self.metrics[s.session_id].success_rate, 2),
                    "created_minutes_ago": round((datetime.now() - s.created_at).seconds / 60, 1)
                }
                for s in active_sessions
            ]
        }