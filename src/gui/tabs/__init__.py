"""
Módulo de pestañas de configuración para la GUI.

Contiene los widgets de pestañas separados para una mejor
organización y mantenibilidad del código.

Diseñado exclusivamente para Windows.
"""

from .behavior_tab import create_behavior_tab
from .proxy_tab import create_proxy_tab
from .fingerprint_tab import create_fingerprint_tab
from .advanced_tabs import (
    create_advanced_spoof_tab,
    create_behavior_simulation_tab,
    create_captcha_tab,
    create_contingency_tab,
    create_advanced_behavior_tab,
    create_system_hiding_tab
)
from .phase5_tabs import (
    create_scaling_tab,
    create_performance_tab,
    create_ml_evasion_tab,
    create_scheduling_tab,
    create_analytics_tab,
    create_accounts_tab,
    create_logging_tab
)

__all__ = [
    'create_behavior_tab',
    'create_proxy_tab',
    'create_fingerprint_tab',
    'create_advanced_spoof_tab',
    'create_behavior_simulation_tab',
    'create_captcha_tab',
    'create_contingency_tab',
    'create_advanced_behavior_tab',
    'create_system_hiding_tab',
    'create_scaling_tab',
    'create_performance_tab',
    'create_ml_evasion_tab',
    'create_scheduling_tab',
    'create_analytics_tab',
    'create_accounts_tab',
    'create_logging_tab'
]
