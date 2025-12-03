"""
SessionWorker - Trabajador QThread para sesiones de automatización.

Implementa la ejecución de sesiones usando QThread,
heredando la lógica común de BaseSessionExecutor.

Diseñado exclusivamente para Windows.
"""

from PyQt6.QtCore import QThread, pyqtSignal

from ..session_config import SessionConfig
from .base_worker import BaseSessionExecutor


class SessionWorker(QThread, BaseSessionExecutor):
    """
    Trabajador QThread para ejecutar sesiones de automatización.
    
    Combina QThread con BaseSessionExecutor para proporcionar
    ejecución de sesiones en un hilo separado con señales Qt.
    """
    
    # Señales Qt para comunicación
    status_update = pyqtSignal(str, str)  # session_id, estado
    log_message = pyqtSignal(str, str)    # session_id, mensaje
    finished_signal = pyqtSignal(str)     # session_id
    error = pyqtSignal(str, str)          # session_id, mensaje_error
    
    def __init__(self, session_config: SessionConfig):
        """
        Inicializar el trabajador de sesión.
        
        Args:
            session_config: Configuración de la sesión a ejecutar.
        """
        QThread.__init__(self)
        BaseSessionExecutor.__init__(self, session_config)
    
    def run(self) -> None:
        """Ejecutar el hilo de trabajo."""
        self.execute_session()
    
    def emit_status_update(self, session_id: str, status: str) -> None:
        """Emitir actualización de estado."""
        self.status_update.emit(session_id, status)
    
    def emit_log_message(self, session_id: str, message: str) -> None:
        """Emitir mensaje de log."""
        self.log_message.emit(session_id, message)
    
    def emit_finished(self, session_id: str) -> None:
        """Emitir señal de finalización."""
        self.finished_signal.emit(session_id)
    
    def emit_error(self, session_id: str, error_message: str) -> None:
        """Emitir señal de error."""
        self.error.emit(session_id, error_message)
