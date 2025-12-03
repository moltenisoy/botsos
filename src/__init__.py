"""
BotSOS - Administrador de Automatización de YouTube Multi-Sesión

Un administrador de sesiones profesional para ejecutar múltiples instancias
de automatización de navegador con LLM, con características avanzadas de anti-detección.

Diseñado exclusivamente para Windows.

Implementa características de fase2.txt y fase3.txt:
- Gestión multi-sesión con QThreadPool
- Suplantación avanzada de huella digital (TLS, WebGPU, Canvas, Audio)
- Simulación de comportamiento (movimiento del ratón, escritura, desplazamiento)
- Manejo de CAPTCHA con integración de 2Captcha
- Validación y rotación de proxies
- Almacenamiento seguro de credenciales
- Registro en tiempo real con rotación
- Planificación de contingencia y recuperación (fase3.txt)
- Ocultación del sistema y bloqueo de puertos (fase3.txt)
- Detección de anomalías y monitoreo (fase3.txt)
- Huella digital polimórfica (fase3.txt)
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
