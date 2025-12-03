"""
SessionRunnable - Trabajador QRunnable para sesiones de automatización.

Implementa la ejecución de sesiones usando QRunnable/QThreadPool,
heredando la lógica común de BaseSessionExecutor.

Diseñado exclusivamente para Windows.
"""

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal

from ..session_config import SessionConfig
from .base_worker import BaseSessionExecutor


class WorkerSignals(QObject):
    """
    Señales para comunicación de trabajadores QRunnable.
    
    QRunnable no puede emitir señales directamente, por lo que
    se usa esta clase auxiliar para proporcionar las señales.
    """
    status_update = pyqtSignal(str, str)    # session_id, estado
    log_message = pyqtSignal(str, str)      # session_id, mensaje
    finished = pyqtSignal(str)               # session_id
    resource_update = pyqtSignal(float, float)  # CPU%, RAM%
    error = pyqtSignal(str, str)             # session_id, mensaje_error


class SessionRunnable(QRunnable, BaseSessionExecutor):
    """
    Trabajador QRunnable para ejecutar sesiones con QThreadPool.
    
    Combina QRunnable con BaseSessionExecutor para proporcionar
    ejecución de sesiones en el ThreadPool con señales Qt.
    """
    
    def __init__(self, session_config: SessionConfig):
        """
        Inicializar el trabajador de sesión.
        
        Args:
            session_config: Configuración de la sesión a ejecutar.
        """
        QRunnable.__init__(self)
        BaseSessionExecutor.__init__(self, session_config)
        self.signals = WorkerSignals()
        self.setAutoDelete(True)
    
    def run(self) -> None:
        """Ejecutar el trabajador."""
        self.execute_session()
    
    def emit_status_update(self, session_id: str, status: str) -> None:
        """Emitir actualización de estado."""
        self.signals.status_update.emit(session_id, status)
    
    def emit_log_message(self, session_id: str, message: str) -> None:
        """Emitir mensaje de log."""
        self.signals.log_message.emit(session_id, message)
    
    def emit_finished(self, session_id: str) -> None:
        """Emitir señal de finalización."""
        self.signals.finished.emit(session_id)
    
    def emit_error(self, session_id: str, error_message: str) -> None:
        """Emitir señal de error."""
        self.signals.error.emit(session_id, error_message)
