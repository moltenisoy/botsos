"""
Clase base abstracta para ejecutores de sesión.

Elimina la duplicación de lógica entre SessionWorker y SessionRunnable
proporcionando una implementación común reutilizable.

Diseñado exclusivamente para Windows.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Callable

from ..session_config import SessionConfig

logger = logging.getLogger(__name__)


class BaseSessionExecutor(ABC):
    """
    Clase base abstracta para ejecutores de sesión.
    
    Proporciona la lógica común para ejecutar sesiones de automatización
    de navegador, incluyendo:
    - Gestión del ciclo de vida de la sesión
    - Ejecución asíncrona con asyncio
    - Integración con características avanzadas (retry, behavior simulation)
    - Señalización de estado y mensajes de log
    
    Las subclases deben implementar los métodos abstractos para
    proporcionar la interfaz de señalización específica (QThread signals vs QRunnable signals).
    """
    
    def __init__(self, session_config: SessionConfig):
        """
        Inicializar el ejecutor de sesión.
        
        Args:
            session_config: Configuración de la sesión a ejecutar.
        """
        if session_config is None:
            raise ValueError("session_config no puede ser None")
        
        self.session_config = session_config
        self._is_running = True
        self._retry_manager = None
        self._behavior_simulator = None
    
    @abstractmethod
    def emit_status_update(self, session_id: str, status: str) -> None:
        """
        Emitir actualización de estado de la sesión.
        
        Args:
            session_id: Identificador de la sesión.
            status: Nuevo estado ('ejecutando', 'inactivo', 'error').
        """
        pass
    
    @abstractmethod
    def emit_log_message(self, session_id: str, message: str) -> None:
        """
        Emitir mensaje de log de la sesión.
        
        Args:
            session_id: Identificador de la sesión.
            message: Mensaje a registrar.
        """
        pass
    
    @abstractmethod
    def emit_finished(self, session_id: str) -> None:
        """
        Emitir señal de finalización de la sesión.
        
        Args:
            session_id: Identificador de la sesión.
        """
        pass
    
    @abstractmethod
    def emit_error(self, session_id: str, error_message: str) -> None:
        """
        Emitir señal de error de la sesión.
        
        Args:
            session_id: Identificador de la sesión.
            error_message: Mensaje de error.
        """
        pass
    
    def _initialize_advanced_features(self) -> bool:
        """
        Inicializar características avanzadas (retry, behavior simulation).
        
        Returns:
            True si las características se inicializaron correctamente.
        """
        session_id = self.session_config.session_id
        
        try:
            from ..advanced_features import RetryManager, BehaviorSimulator, BehaviorSimulationConfig
            
            self._retry_manager = RetryManager(
                max_retries=self.session_config.max_retries,
                base_delay_sec=self.session_config.retry_delay_sec,
                exponential_backoff=self.session_config.exponential_backoff
            )
            
            self._behavior_simulator = BehaviorSimulator(BehaviorSimulationConfig(
                min_action_delay_ms=self.session_config.behavior.action_delay_min_ms,
                max_action_delay_ms=self.session_config.behavior.action_delay_max_ms,
                idle_time_min_sec=self.session_config.behavior.idle_time_min_sec,
                idle_time_max_sec=self.session_config.behavior.idle_time_max_sec,
                mouse_jitter_enabled=self.session_config.behavior.mouse_jitter_enabled,
                mouse_jitter_px=self.session_config.behavior.mouse_jitter_px,
                scroll_simulation_enabled=self.session_config.behavior.scroll_simulation_enabled
            ))
            
            self.emit_log_message(session_id, "Características avanzadas cargadas")
            return True
            
        except ImportError as e:
            self.emit_log_message(session_id, f"Características avanzadas no disponibles: {e}")
            return False
    
    def execute_session(self) -> None:
        """
        Ejecutar la sesión de automatización.
        
        Este método maneja el ciclo de vida completo de la sesión:
        1. Emitir estado 'ejecutando'
        2. Crear y ejecutar el bucle de eventos asyncio
        3. Manejar errores y emitir señales apropiadas
        4. Limpiar y emitir estado 'inactivo' al finalizar
        """
        session_id = self.session_config.session_id
        self.emit_status_update(session_id, "ejecutando")
        self.emit_log_message(session_id, f"Iniciando sesión: {self.session_config.name}")
        
        try:
            # Ejecutar la sesión async en un nuevo bucle de eventos
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._run_session_async())
            finally:
                loop.close()
                
        except Exception as e:
            error_msg = str(e)
            self.emit_log_message(session_id, f"Error: {error_msg}")
            self.emit_status_update(session_id, "error")
            self.emit_error(session_id, error_msg)
        finally:
            self.emit_status_update(session_id, "inactivo")
            self.emit_finished(session_id)
    
    async def _run_session_async(self) -> None:
        """
        Ejecución asíncrona de la sesión.
        
        Inicializa características avanzadas y ejecuta el bucle principal
        de la sesión hasta que se detenga.
        """
        session_id = self.session_config.session_id
        
        # Inicializar características avanzadas
        self._initialize_advanced_features()
        
        # Marcador de ejecución de sesión - integrar con browser_session.py
        self.emit_log_message(session_id, "Sesión iniciada - esperando integración de automatización del navegador")
        
        # Bucle principal de la sesión
        while self._is_running:
            await asyncio.sleep(1)
    
    def stop(self) -> None:
        """Detener la sesión."""
        self._is_running = False
    
    @property
    def is_running(self) -> bool:
        """Verificar si la sesión está ejecutándose."""
        return self._is_running
