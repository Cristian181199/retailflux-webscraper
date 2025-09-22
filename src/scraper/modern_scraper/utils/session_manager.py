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
            ))\n        \n        # Chrome profiles (macOS)\n        for version in chrome_windows_versions:\n            profiles.append(BrowserProfile(\n                user_agent=f\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36\",\n                accept_language=\"de-DE,de;q=0.9,en;q=0.8\",\n                accept_encoding=\"gzip, deflate, br\",\n                accept=\"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\",\n                platform=\"macOS\",\n                browser_name=\"Chrome\",\n                browser_version=version\n            ))\n        \n        # Firefox profiles (Windows)\n        firefox_versions = [\"120.0\", \"119.0\", \"118.0\", \"117.0\"]\n        \n        for version in firefox_versions:\n            profiles.append(BrowserProfile(\n                user_agent=f\"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}\",\n                accept_language=\"de-DE,de;q=0.8,en-US;q=0.5,en;q=0.3\",\n                accept_encoding=\"gzip, deflate\",\n                accept=\"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\",\n                platform=\"Windows\",\n                browser_name=\"Firefox\",\n                browser_version=version\n            ))\n        \n        # Safari profiles (macOS)\n        safari_versions = [\"17.1\", \"16.6\", \"16.5\"]\n        \n        for version in safari_versions:\n            profiles.append(BrowserProfile(\n                user_agent=f\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15\",\n                accept_language=\"de-DE,de;q=0.9\",\n                accept_encoding=\"gzip, deflate, br\",\n                accept=\"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\",\n                platform=\"macOS\",\n                browser_name=\"Safari\",\n                browser_version=version\n            ))\n        \n        return profiles\n    \n    def get_profile_for_session(self, session_id: str) -> BrowserProfile:\n        \"\"\"Get consistent browser profile for a session.\"\"\"\n        # Use session ID to consistently select profile\n        profile_index = hash(session_id) % len(self.profiles)\n        profile = self.profiles[profile_index]\n        \n        logger.debug(f\"📱 Selected {profile.browser_name} {profile.browser_version} \"\n                    f\"on {profile.platform} for session {session_id[:8]}...\")\n        \n        return profile\n    \n    def get_random_profile(self) -> BrowserProfile:\n        \"\"\"Get random browser profile.\"\"\"\n        return random.choice(self.profiles)\n    \n    def get_profiles_by_browser(self, browser_name: str) -> List[BrowserProfile]:\n        \"\"\"Get all profiles for specific browser.\"\"\"\n        return [p for p in self.profiles if p.browser_name.lower() == browser_name.lower()]\n    \n    def get_stats(self) -> Dict[str, int]:\n        \"\"\"Get statistics about browser profiles.\"\"\"\n        stats = {}\n        \n        for profile in self.profiles:\n            key = f\"{profile.browser_name} ({profile.platform})\"\n            stats[key] = stats.get(key, 0) + 1\n        \n        return stats\n\n\nclass SessionManager:\n    \"\"\"\n    Manages session coordination between proxies and browser profiles.\n    \n    Ensures consistent browser fingerprinting for each proxy session.\n    \"\"\"\n    \n    def __init__(self):\n        self.user_agent_pool = UserAgentPool()\n        self.session_profiles: Dict[str, BrowserProfile] = {}\n        self.session_created_at: Dict[str, datetime] = {}\n        \n        logger.info(\"🔧 SessionManager initialized\")\n    \n    def get_session_headers(self, session_id: str, \n                           base_headers: Dict[str, str] = None) -> Dict[str, str]:\n        \"\"\"\n        Get HTTP headers for a specific session.\n        \n        Ensures consistent browser fingerprinting for the session.\n        \"\"\"\n        # Get or create profile for session\n        if session_id not in self.session_profiles:\n            profile = self.user_agent_pool.get_profile_for_session(session_id)\n            self.session_profiles[session_id] = profile\n            self.session_created_at[session_id] = datetime.now()\n            \n            logger.debug(f\"🆕 Created browser profile for session {session_id[:8]}... \"\n                        f\"({profile.browser_name} {profile.browser_version})\")\n        else:\n            profile = self.session_profiles[session_id]\n        \n        # Start with profile headers\n        headers = profile.to_headers()\n        \n        # Add base headers if provided\n        if base_headers:\n            headers.update(base_headers)\n        \n        # Add additional realistic headers\n        headers.update({\n            'DNT': '1',\n            'Connection': 'keep-alive',\n            'Upgrade-Insecure-Requests': '1',\n            'Sec-Fetch-Dest': 'document',\n            'Sec-Fetch-Mode': 'navigate',\n            'Sec-Fetch-Site': 'none',\n            'Cache-Control': 'max-age=0',\n        })\n        \n        # Add browser-specific headers\n        if profile.browser_name == 'Chrome':\n            headers.update({\n                'sec-ch-ua': f'\"Google Chrome\";v=\"{profile.browser_version.split(\".\")[0]}\", \"Chromium\";v=\"{profile.browser_version.split(\".\")[0]}\", \"Not_A Brand\";v=\"8\"',\n                'sec-ch-ua-mobile': '?0',\n                'sec-ch-ua-platform': f'\"{profile.platform}\"',\n            })\n        \n        return headers\n    \n    def cleanup_expired_sessions(self, active_session_ids: List[str]):\n        \"\"\"\n        Clean up profiles for expired sessions.\n        \"\"\"\n        expired_sessions = [\n            sid for sid in self.session_profiles.keys()\n            if sid not in active_session_ids\n        ]\n        \n        for session_id in expired_sessions:\n            del self.session_profiles[session_id]\n            if session_id in self.session_created_at:\n                del self.session_created_at[session_id]\n            \n            logger.debug(f\"🧹 Cleaned up profile for expired session {session_id[:8]}...\")\n        \n        if expired_sessions:\n            logger.info(f\"🗑️ Cleaned up {len(expired_sessions)} expired session profiles\")\n    \n    def get_session_profile(self, session_id: str) -> Optional[BrowserProfile]:\n        \"\"\"Get browser profile for a specific session.\"\"\"\n        return self.session_profiles.get(session_id)\n    \n    def get_stats(self) -> Dict[str, any]:\n        \"\"\"Get session manager statistics.\"\"\"\n        browser_usage = {}\n        \n        for profile in self.session_profiles.values():\n            key = f\"{profile.browser_name} {profile.browser_version}\"\n            browser_usage[key] = browser_usage.get(key, 0) + 1\n        \n        return {\n            \"active_sessions\": len(self.session_profiles),\n            \"available_profiles\": len(self.user_agent_pool.profiles),\n            \"browser_usage\": browser_usage,\n            \"user_agent_stats\": self.user_agent_pool.get_stats()\n        }\n\n\n# Global instance\nsession_manager = SessionManager()\n\n\ndef get_session_manager() -> SessionManager:\n    \"\"\"Get the global session manager instance.\"\"\"\n    return session_manager