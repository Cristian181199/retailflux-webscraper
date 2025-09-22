"""
Session and User-Agent Management Utilities

Provides utilities for coordinating user-agent rotation with proxy sessions
and managing browser fingerprinting resistance.
"""
import random
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BrowserProfile:
    """Browser profile for consistent session management."""
    
    user_agent: str
    accept_language: str
    accept_encoding: str
    accept: str
    platform: str
    browser_name: str
    browser_version: str
    
    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers dictionary."""
        return {
            'User-Agent': self.user_agent,
            'Accept-Language': self.accept_language,
            'Accept-Encoding': self.accept_encoding,
            'Accept': self.accept,
        }


class UserAgentPool:
    """Pool of realistic user agents for rotation."""
    
    def __init__(self):
        self.profiles = self._generate_browser_profiles()
        logger.info(f"🌐 Initialized user agent pool with {len(self.profiles)} profiles")
    
    def _generate_browser_profiles(self) -> List[BrowserProfile]:
        """Generate realistic browser profiles."""
        profiles = []
        
        # Chrome profiles (Windows)
        chrome_windows_versions = [
            "120.0.0.0", "119.0.0.0", "118.0.0.0", "117.0.0.0"
        ]
        
        for version in chrome_windows_versions:
            profiles.append(BrowserProfile(
                user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
                accept_language="de-DE,de;q=0.9,en;q=0.8",
                accept_encoding="gzip, deflate, br",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                platform="Windows",
                browser_name="Chrome",
                browser_version=version
            ))
        
        # Chrome profiles (macOS)
        for version in chrome_windows_versions:
            profiles.append(BrowserProfile(
                user_agent=f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36",
                accept_language="de-DE,de;q=0.9,en;q=0.8",
                accept_encoding="gzip, deflate, br",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                platform="macOS",
                browser_name="Chrome",
                browser_version=version
            ))
        
        # Firefox profiles (Windows)
        firefox_versions = ["120.0", "119.0", "118.0", "117.0"]
        
        for version in firefox_versions:
            profiles.append(BrowserProfile(
                user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}",
                accept_language="de-DE,de;q=0.8,en-US;q=0.5,en;q=0.3",
                accept_encoding="gzip, deflate",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                platform="Windows",
                browser_name="Firefox",
                browser_version=version
            ))
        
        # Safari profiles (macOS)
        safari_versions = ["17.1", "16.6", "16.5"]
        
        for version in safari_versions:
            profiles.append(BrowserProfile(
                user_agent=f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15",
                accept_language="de-DE,de;q=0.9",
                accept_encoding="gzip, deflate, br",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                platform="macOS",
                browser_name="Safari",
                browser_version=version
            ))
        
        return profiles
    
    def get_profile_for_session(self, session_id: str) -> BrowserProfile:
        """Get consistent browser profile for a session."""
        # Use session ID to consistently select profile
        profile_index = hash(session_id) % len(self.profiles)
        profile = self.profiles[profile_index]
        
        logger.debug(f"📱 Selected {profile.browser_name} {profile.browser_version} "
                    f"on {profile.platform} for session {session_id[:8]}...")
        
        return profile
    
    def get_random_profile(self) -> BrowserProfile:
        """Get random browser profile."""
        return random.choice(self.profiles)
    
    def get_profiles_by_browser(self, browser_name: str) -> List[BrowserProfile]:
        """Get all profiles for specific browser."""
        return [p for p in self.profiles if p.browser_name.lower() == browser_name.lower()]
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about browser profiles."""
        stats = {}
        
        for profile in self.profiles:
            key = f"{profile.browser_name} ({profile.platform})"
            stats[key] = stats.get(key, 0) + 1
        
        return stats


class SessionManager:
    """
    Manages session coordination between proxies and browser profiles.
    
    Ensures consistent browser fingerprinting for each proxy session.
    """
    
    def __init__(self):
        self.user_agent_pool = UserAgentPool()
        self.session_profiles: Dict[str, BrowserProfile] = {}
        self.session_created_at: Dict[str, datetime] = {}
        
        logger.info("🔧 SessionManager initialized")
    
    def get_session_headers(self, session_id: str, 
                           base_headers: Dict[str, str] = None) -> Dict[str, str]:
        """
        Get HTTP headers for a specific session.
        
        Ensures consistent browser fingerprinting for the session.
        """
        # Get or create profile for session
        if session_id not in self.session_profiles:
            profile = self.user_agent_pool.get_profile_for_session(session_id)
            self.session_profiles[session_id] = profile
            self.session_created_at[session_id] = datetime.now()
            
            logger.debug(f"🆕 Created browser profile for session {session_id[:8]}... "
                        f"({profile.browser_name} {profile.browser_version})")
        else:
            profile = self.session_profiles[session_id]
        
        # Start with profile headers
        headers = profile.to_headers()
        
        # Add base headers if provided
        if base_headers:
            headers.update(base_headers)
        
        # Add additional realistic headers
        headers.update({
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        
        # Add browser-specific headers
        if profile.browser_name == 'Chrome':
            headers.update({
                'sec-ch-ua': f'"Google Chrome";v="{profile.browser_version.split(".")[0]}", "Chromium";v="{profile.browser_version.split(".")[0]}", "Not_A Brand";v="8"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': f'"{profile.platform}"',
            })
        
        return headers
    
    def cleanup_expired_sessions(self, active_session_ids: List[str]):
        """
        Clean up profiles for expired sessions.
        """
        expired_sessions = [
            sid for sid in self.session_profiles.keys()
            if sid not in active_session_ids
        ]
        
        for session_id in expired_sessions:
            del self.session_profiles[session_id]
            if session_id in self.session_created_at:
                del self.session_created_at[session_id]
            
            logger.debug(f"🧹 Cleaned up profile for expired session {session_id[:8]}...")
        
        if expired_sessions:
            logger.info(f"🗑️ Cleaned up {len(expired_sessions)} expired session profiles")
    
    def get_session_profile(self, session_id: str) -> Optional[BrowserProfile]:
        """Get browser profile for a specific session."""
        return self.session_profiles.get(session_id)
    
    def get_stats(self) -> Dict[str, any]:
        """Get session manager statistics."""
        browser_usage = {}
        
        for profile in self.session_profiles.values():
            key = f"{profile.browser_name} {profile.browser_version}"
            browser_usage[key] = browser_usage.get(key, 0) + 1
        
        return {
            "active_sessions": len(self.session_profiles),
            "available_profiles": len(self.user_agent_pool.profiles),
            "browser_usage": browser_usage,
            "user_agent_stats": self.user_agent_pool.get_stats()
        }


# Global instance
session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    return session_manager