"""
BotSOS - Administrador de Automatización de YouTube Multi-Sesión

Un administrador de sesiones profesional para ejecutar múltiples instancias
de automatización de navegador con LLM, con características avanzadas de anti-detección.

Versión: 1.0.0
Diseñado exclusivamente para Windows.

Implementa características de fase2.txt, fase3.txt, fase5.txt y fase6.txt:
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
- Escalabilidad Docker/AWS (fase5.txt)
- Analíticas con Prometheus (fase5.txt)
- Selección de proxy con ML (fase5.txt)
- Sistema de plugins de evasión (fase6.txt)
- Gestión específica de Windows (fase6.txt)
- Sistema de ayuda y tooltips (fase6.txt)
- Empaquetado para distribución (fase6.txt)
"""

__version__ = "1.0.0"
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
    MfaConfig,
    ScalingConfig,
    PerformanceConfig,
    MLEvasionConfig,
    SchedulingConfig,
    AnalyticsConfig,
    AccountManagementConfig,
    MLProxyConfig
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

# Módulos de fase 5
from .scaling_manager import ScalingManager, DockerManager, AWSCloudManager, ResourceMonitor
from .analytics_manager import AnalyticsManager, PrometheusMetrics
from .scheduler_manager import SchedulingManager, SessionScheduler, SessionQueue
from .ml_proxy_selector import MLProxySelector
from .account_manager import AccountManager, EncryptionManager

# Módulos de fase 6
from .windows_manager import WindowsManager, UACManager, DockerManager as WinDockerManager, HardwareDetector
from .plugin_system import PluginManager, EvasionPlugin, RLFeedbackLoop
from .help_system import HelpSystem, TooltipManager, TutorialWizard, EthicalConsentManager
from .packaging_manager import PackagingManager, BuildConfig, VersionManager

__all__ = [
    # Configuración
    "SessionConfig",
    "BehaviorConfig",
    "ProxyConfig",
    "FingerprintConfig",
    "CaptchaConfig",
    "ContingencyConfig",
    "AdvancedBehaviorConfig",
    "SystemHidingConfig",
    "MfaConfig",
    "ScalingConfig",
    "PerformanceConfig",
    "MLEvasionConfig",
    "SchedulingConfig",
    "AnalyticsConfig",
    "AccountManagementConfig",
    "MLProxyConfig",
    
    # Core
    "ProxyManager",
    "ProxyEntry",
    "FingerprintManager",
    "DeviceFingerprint",
    
    # Anti-detección
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
    
    # Escalabilidad (fase 5)
    "ScalingManager",
    "DockerManager",
    "AWSCloudManager",
    "ResourceMonitor",
    "AnalyticsManager",
    "PrometheusMetrics",
    "SchedulingManager",
    "SessionScheduler",
    "SessionQueue",
    "MLProxySelector",
    "AccountManager",
    "EncryptionManager",
    
    # Windows y empaquetado (fase 6)
    "WindowsManager",
    "UACManager",
    "HardwareDetector",
    "PluginManager",
    "EvasionPlugin",
    "RLFeedbackLoop",
    "HelpSystem",
    "TooltipManager",
    "TutorialWizard",
    "EthicalConsentManager",
    "PackagingManager",
    "BuildConfig",
    "VersionManager",
]
