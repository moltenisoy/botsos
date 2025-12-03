"""
BotSOS - Multi-Session YouTube Automation Manager

A professional session manager for running multiple LLM-powered browser
automation instances with advanced anti-detection features.

Implements features from fase2.txt:
- Multi-session management with QThreadPool
- Advanced fingerprint spoofing (TLS, WebGPU, Canvas, Audio)
- Behavior simulation (mouse jitter, typing, scrolling)
- CAPTCHA handling with 2Captcha integration
- Proxy validation and rotation
- Secure credential storage
- Real-time logging with rotation
"""

__version__ = "1.1.0"
__author__ = "BotSOS Team"

from .session_config import SessionConfig, BehaviorConfig, ProxyConfig, FingerprintConfig, CaptchaConfig
from .proxy_manager import ProxyManager, ProxyEntry
from .fingerprint_manager import FingerprintManager, DeviceFingerprint
from .advanced_features import (
    AdvancedSpoofingConfig,
    BehaviorSimulationConfig,
    CaptchaSolver,
    ProxyValidator,
    RetryManager,
    SecureCredentialStore,
    BehaviorSimulator,
    AdvancedLogging
)

__all__ = [
    "SessionConfig",
    "BehaviorConfig",
    "ProxyConfig",
    "FingerprintConfig",
    "CaptchaConfig",
    "ProxyManager",
    "ProxyEntry",
    "FingerprintManager",
    "DeviceFingerprint",
    "AdvancedSpoofingConfig",
    "BehaviorSimulationConfig",
    "CaptchaSolver",
    "ProxyValidator",
    "RetryManager",
    "SecureCredentialStore",
    "BehaviorSimulator",
    "AdvancedLogging",
]
