"""
Módulo de trabajadores para ejecución de sesiones.

Contiene clases base y especializadas para ejecutar
sesiones de automatización de navegador.

Diseñado exclusivamente para Windows.
"""

from .base_worker import BaseSessionExecutor
from .session_worker import SessionWorker
from .session_runnable import SessionRunnable, WorkerSignals

__all__ = [
    'BaseSessionExecutor',
    'SessionWorker', 
    'SessionRunnable',
    'WorkerSignals'
]
