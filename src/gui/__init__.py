"""
Módulo GUI para BotSOS.

Organiza la interfaz gráfica en componentes modulares:
- tabs/: Pestañas de configuración
- widgets/: Widgets reutilizables
- workers/: Trabajadores de sesión (QThread, QRunnable)

Diseñado exclusivamente para Windows.
"""

from .main_window import SessionManagerGUI

__all__ = ['SessionManagerGUI']
