"""
BotSOS - Multi-Session YouTube Automation Manager

A professional session manager for running multiple LLM-powered browser
automation instances with advanced anti-detection features.
"""

__version__ = "1.0.0"
__author__ = "BotSOS Team"

from .session_config import SessionConfig
from .proxy_manager import ProxyManager
from .fingerprint_manager import FingerprintManager

__all__ = [
    "SessionConfig",
    "ProxyManager", 
    "FingerprintManager",
]
