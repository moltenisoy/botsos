"""
BotSOS - Multi-Session YouTube Automation Manager

A professional session manager for running multiple LLM-powered browser
automation instances with advanced anti-detection features.

Implements features from fase2.txt and fase3.txt:
- Multi-session management with QThreadPool
- Advanced fingerprint spoofing (TLS, WebGPU, Canvas, Audio)
- Behavior simulation (mouse jitter, typing, scrolling)
- CAPTCHA handling with 2Captcha integration
- Proxy validation and rotation
- Secure credential storage
- Real-time logging with rotation
- Contingency planning and recovery (fase3.txt)
- System hiding and port blocking (fase3.txt)
- Anomaly detection and monitoring (fase3.txt)
- Polymorphic fingerprinting (fase3.txt)
"""

__version__ = "1.2.0"
__author__ = "BotSOS Team"

from .session_config import (
    SessionConfig, 
    BehaviorConfig, 
    ProxyConfig, 
    FingerprintConfig, 
    CaptchaConfig,
    ContingencyConfig,
    AdvancedBehaviorConfig,
    SystemHidingConfig,
    MfaConfig
)
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
    AdvancedLogging,
    ContingencyState,
    ContingencyManager,
    SystemHidingManager,
    AnomalyDetector,
    PolymorphicFingerprint
)

__all__ = [
    "SessionConfig",
    "BehaviorConfig",
    "ProxyConfig",
    "FingerprintConfig",
    "CaptchaConfig",
    "ContingencyConfig",
    "AdvancedBehaviorConfig",
    "SystemHidingConfig",
    "MfaConfig",
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
    "ContingencyState",
    "ContingencyManager",
    "SystemHidingManager",
    "AnomalyDetector",
    "PolymorphicFingerprint",
]
