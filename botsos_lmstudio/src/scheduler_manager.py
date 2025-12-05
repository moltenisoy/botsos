"""
Módulo de Programación de Tareas.

Maneja la programación de sesiones usando APScheduler
para automatización basada en tiempo.

Implementa características de fase5.txt:
- Programación con expresiones cron.
- Cola de sesiones pendientes.
- Ventanas de tiempo de ejecución.
- Reinicio automático de sesiones fallidas.

Diseñado exclusivamente para Windows.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta, time
from pathlib import Path
from queue import Queue, Empty
from threading import Lock
import json

logger = logging.getLogger(__name__)


@dataclass
class ScheduledSession:
    """Representa una sesión programada."""
    session_id: str
    session_config: Dict[str, Any]
    schedule_id: str
    cron_expression: str = ""
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    enabled: bool = True
    
    # Restricciones de tiempo
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    days_of_week: List[str] = field(default_factory=lambda: [
        "lunes", "martes", "miércoles", "jueves", "viernes"
    ])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "session_id": self.session_id,
            "schedule_id": self.schedule_id,
            "cron_expression": self.cron_expression,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "enabled": self.enabled,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "days_of_week": self.days_of_week
        }


@dataclass
class QueuedSession:
    """Representa una sesión en cola de ejecución."""
    session_id: str
    session_config: Dict[str, Any]
    priority: int = 5  # 1 = más alta, 10 = más baja
    added_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """Comparación para ordenar por prioridad."""
        return self.priority < other.priority


class SessionScheduler:
    """Programador de sesiones con APScheduler.
    
    Permite programar sesiones para ejecución automática
    usando expresiones cron y ventanas de tiempo.
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        on_session_due: Optional[Callable] = None
    ):
        """Inicializa el programador.
        
        Args:
            data_dir: Directorio para persistencia.
            on_session_due: Callback cuando una sesión debe ejecutarse.
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data/schedules")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.on_session_due = on_session_due
        self._scheduler = None
        self._scheduler_available = False
        self._scheduled_sessions: Dict[str, ScheduledSession] = {}
        self._lock = Lock()
        
        self._init_scheduler()
        self._load_schedules()
    
    def _init_scheduler(self):
        """Inicializa APScheduler."""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            from apscheduler.triggers.interval import IntervalTrigger
            
            self._scheduler = BackgroundScheduler(
                timezone='America/Mexico_City',
                job_defaults={
                    'coalesce': True,
                    'max_instances': 1
                }
            )
            self._scheduler_available = True
            logger.info("APScheduler inicializado correctamente")
            
        except ImportError:
            logger.warning(
                "APScheduler no está instalado. "
                "Instale con: pip install APScheduler"
            )
    
    @property
    def is_available(self) -> bool:
        """Verifica si el programador está disponible."""
        return self._scheduler_available
    
    def _load_schedules(self):
        """Carga las programaciones guardadas."""
        schedules_file = self.data_dir / "schedules.json"
        if schedules_file.exists():
            try:
                with open(schedules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for schedule_data in data.get('schedules', []):
                        session = ScheduledSession(
                            session_id=schedule_data['session_id'],
                            session_config=schedule_data.get('session_config', {}),
                            schedule_id=schedule_data['schedule_id'],
                            cron_expression=schedule_data.get('cron_expression', ''),
                            enabled=schedule_data.get('enabled', True)
                        )
                        self._scheduled_sessions[session.schedule_id] = session
                logger.info(f"Cargadas {len(self._scheduled_sessions)} programaciones")
            except Exception as e:
                logger.error(f"Error cargando programaciones: {e}")
    
    def _save_schedules(self):
        """Guarda las programaciones."""
        try:
            schedules_file = self.data_dir / "schedules.json"
            data = {
                'schedules': [s.to_dict() for s in self._scheduled_sessions.values()],
                'last_saved': datetime.now().isoformat()
            }
            with open(schedules_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando programaciones: {e}")
    
    def start(self):
        """Inicia el programador."""
        if self._scheduler and not self._scheduler.running:
            self._scheduler.start()
            logger.info("Programador iniciado")
            
            # Restaurar trabajos
            for schedule_id, session in self._scheduled_sessions.items():
                if session.enabled and session.cron_expression:
                    self._add_job(session)
    
    def stop(self):
        """Detiene el programador."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Programador detenido")
    
    def _add_job(self, session: ScheduledSession):
        """Agrega un trabajo al programador."""
        if not self._scheduler_available:
            return
        
        try:
            from apscheduler.triggers.cron import CronTrigger
            
            # Parsear expresión cron
            parts = session.cron_expression.split()
            if len(parts) >= 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
                
                self._scheduler.add_job(
                    self._execute_scheduled_session,
                    trigger=trigger,
                    args=[session.schedule_id],
                    id=session.schedule_id,
                    replace_existing=True
                )
                
                # Calcular próxima ejecución
                job = self._scheduler.get_job(session.schedule_id)
                if job:
                    session.next_run = job.next_run_time
                    logger.info(
                        f"Programación agregada: {session.schedule_id} - "
                        f"Próxima ejecución: {session.next_run}"
                    )
                    
        except Exception as e:
            logger.error(f"Error agregando trabajo {session.schedule_id}: {e}")
    
    def _execute_scheduled_session(self, schedule_id: str):
        """Ejecuta una sesión programada."""
        with self._lock:
            session = self._scheduled_sessions.get(schedule_id)
            if not session or not session.enabled:
                return
            
            # Verificar ventana de tiempo
            if not self._is_within_time_window(session):
                logger.info(
                    f"Sesión {schedule_id} fuera de ventana de tiempo, omitiendo"
                )
                return
            
            # Actualizar estado
            session.last_run = datetime.now()
            session.run_count += 1
            
            # Calcular próxima ejecución
            job = self._scheduler.get_job(schedule_id)
            if job:
                session.next_run = job.next_run_time
        
        # Ejecutar callback
        if self.on_session_due:
            try:
                self.on_session_due(session.session_id, session.session_config)
            except Exception as e:
                logger.error(f"Error ejecutando sesión programada {schedule_id}: {e}")
        
        self._save_schedules()
    
    def _is_within_time_window(self, session: ScheduledSession) -> bool:
        """Verifica si la hora actual está dentro de la ventana permitida."""
        now = datetime.now()
        
        # Verificar día de la semana
        day_names = [
            "lunes", "martes", "miércoles", "jueves", "viernes",
            "sábado", "domingo"
        ]
        current_day = day_names[now.weekday()]
        if current_day not in session.days_of_week:
            return False
        
        # Verificar hora
        if session.start_time and now.time() < session.start_time:
            return False
        if session.end_time and now.time() > session.end_time:
            return False
        
        return True
    
    def add_schedule(
        self,
        session_id: str,
        session_config: Dict[str, Any],
        cron_expression: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        days_of_week: Optional[List[str]] = None
    ) -> Optional[str]:
        """Agrega una nueva programación.
        
        Args:
            session_id: ID de la sesión.
            session_config: Configuración de la sesión.
            cron_expression: Expresión cron (ej: "0 * * * *" = cada hora).
            start_time: Hora de inicio (HH:MM).
            end_time: Hora de fin (HH:MM).
            days_of_week: Lista de días permitidos.
            
        Returns:
            ID de la programación o None si falló.
        """
        import uuid
        
        schedule_id = str(uuid.uuid4())[:8]
        
        session = ScheduledSession(
            session_id=session_id,
            session_config=session_config,
            schedule_id=schedule_id,
            cron_expression=cron_expression
        )
        
        # Parsear tiempos
        if start_time:
            try:
                parts = start_time.split(':')
                session.start_time = time(int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                pass
        
        if end_time:
            try:
                parts = end_time.split(':')
                session.end_time = time(int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                pass
        
        if days_of_week:
            session.days_of_week = days_of_week
        
        with self._lock:
            self._scheduled_sessions[schedule_id] = session
        
        # Agregar trabajo
        if self._scheduler and self._scheduler.running:
            self._add_job(session)
        
        self._save_schedules()
        logger.info(f"Programación agregada: {schedule_id} para sesión {session_id}")
        
        return schedule_id
    
    def remove_schedule(self, schedule_id: str) -> bool:
        """Elimina una programación.
        
        Args:
            schedule_id: ID de la programación.
            
        Returns:
            True si se eliminó exitosamente.
        """
        with self._lock:
            if schedule_id not in self._scheduled_sessions:
                return False
            
            del self._scheduled_sessions[schedule_id]
        
        # Eliminar trabajo
        if self._scheduler:
            try:
                self._scheduler.remove_job(schedule_id)
            except Exception:
                pass
        
        self._save_schedules()
        logger.info(f"Programación eliminada: {schedule_id}")
        
        return True
    
    def enable_schedule(self, schedule_id: str, enabled: bool = True) -> bool:
        """Habilita o deshabilita una programación.
        
        Args:
            schedule_id: ID de la programación.
            enabled: Si debe estar habilitada.
            
        Returns:
            True si se actualizó exitosamente.
        """
        with self._lock:
            if schedule_id not in self._scheduled_sessions:
                return False
            
            self._scheduled_sessions[schedule_id].enabled = enabled
        
        # Actualizar trabajo
        if self._scheduler:
            if enabled:
                self._add_job(self._scheduled_sessions[schedule_id])
            else:
                try:
                    self._scheduler.pause_job(schedule_id)
                except Exception:
                    pass
        
        self._save_schedules()
        return True
    
    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de una programación."""
        with self._lock:
            if schedule_id in self._scheduled_sessions:
                return self._scheduled_sessions[schedule_id].to_dict()
        return None
    
    def get_all_schedules(self) -> List[Dict[str, Any]]:
        """Obtiene todas las programaciones."""
        with self._lock:
            return [s.to_dict() for s in self._scheduled_sessions.values()]
    
    def get_pending_runs(self) -> List[Dict[str, Any]]:
        """Obtiene las próximas ejecuciones programadas."""
        with self._lock:
            schedules = [
                s for s in self._scheduled_sessions.values()
                if s.enabled and s.next_run
            ]
            schedules.sort(key=lambda s: s.next_run)
            return [s.to_dict() for s in schedules[:10]]


class SessionQueue:
    """Cola de sesiones para ejecución secuencial.
    
    Gestiona una cola de sesiones pendientes con prioridad
    y reintentos automáticos.
    """
    
    def __init__(
        self,
        max_size: int = 100,
        on_session_ready: Optional[Callable] = None
    ):
        """Inicializa la cola de sesiones.
        
        Args:
            max_size: Tamaño máximo de la cola.
            on_session_ready: Callback cuando una sesión está lista.
        """
        self.max_size = max_size
        self.on_session_ready = on_session_ready
        self._queue: List[QueuedSession] = []
        self._processing: Dict[str, QueuedSession] = {}
        self._lock = Lock()
        self._running = False
        self._process_task: Optional[asyncio.Task] = None
    
    def add(
        self,
        session_id: str,
        session_config: Dict[str, Any],
        priority: int = 5
    ) -> bool:
        """Agrega una sesión a la cola.
        
        Args:
            session_id: ID de la sesión.
            session_config: Configuración de la sesión.
            priority: Prioridad (1-10, menor = mayor prioridad).
            
        Returns:
            True si se agregó exitosamente.
        """
        with self._lock:
            if len(self._queue) >= self.max_size:
                logger.warning("Cola de sesiones llena")
                return False
            
            queued = QueuedSession(
                session_id=session_id,
                session_config=session_config,
                priority=max(1, min(10, priority))
            )
            
            self._queue.append(queued)
            self._queue.sort()  # Ordenar por prioridad
            
            logger.info(f"Sesión {session_id} agregada a cola (prioridad: {priority})")
            return True
    
    def remove(self, session_id: str) -> bool:
        """Elimina una sesión de la cola.
        
        Args:
            session_id: ID de la sesión.
            
        Returns:
            True si se eliminó exitosamente.
        """
        with self._lock:
            original_len = len(self._queue)
            self._queue = [s for s in self._queue if s.session_id != session_id]
            return len(self._queue) < original_len
    
    def get_next(self) -> Optional[QueuedSession]:
        """Obtiene la siguiente sesión de la cola.
        
        Returns:
            La siguiente sesión o None si la cola está vacía.
        """
        with self._lock:
            if not self._queue:
                return None
            
            session = self._queue.pop(0)
            self._processing[session.session_id] = session
            return session
    
    def mark_complete(self, session_id: str, success: bool):
        """Marca una sesión como completada.
        
        Args:
            session_id: ID de la sesión.
            success: Si se completó exitosamente.
        """
        with self._lock:
            if session_id in self._processing:
                session = self._processing.pop(session_id)
                
                if not success and session.retry_count < session.max_retries:
                    # Reintentar
                    session.retry_count += 1
                    session.priority = min(10, session.priority + 1)
                    self._queue.append(session)
                    self._queue.sort()
                    logger.info(
                        f"Sesión {session_id} reintentando "
                        f"({session.retry_count}/{session.max_retries})"
                    )
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Obtiene el estado de la cola.
        
        Returns:
            Diccionario con estado de la cola.
        """
        with self._lock:
            return {
                "queued": len(self._queue),
                "processing": len(self._processing),
                "max_size": self.max_size,
                "next_sessions": [
                    {"session_id": s.session_id, "priority": s.priority}
                    for s in self._queue[:5]
                ]
            }
    
    def clear(self):
        """Limpia la cola."""
        with self._lock:
            self._queue.clear()
            logger.info("Cola de sesiones limpiada")
    
    async def start_processing(self, interval_sec: float = 1.0):
        """Inicia el procesamiento de la cola.
        
        Args:
            interval_sec: Intervalo entre verificaciones.
        """
        self._running = True
        
        async def process_loop():
            while self._running:
                session = self.get_next()
                if session and self.on_session_ready:
                    try:
                        await asyncio.to_thread(
                            self.on_session_ready,
                            session.session_id,
                            session.session_config
                        )
                        self.mark_complete(session.session_id, True)
                    except Exception as e:
                        logger.error(f"Error procesando sesión {session.session_id}: {e}")
                        self.mark_complete(session.session_id, False)
                
                await asyncio.sleep(interval_sec)
        
        self._process_task = asyncio.create_task(process_loop())
        logger.info("Procesamiento de cola iniciado")
    
    def stop_processing(self):
        """Detiene el procesamiento de la cola."""
        self._running = False
        if self._process_task:
            self._process_task.cancel()
            self._process_task = None
        logger.info("Procesamiento de cola detenido")


class SchedulingManager:
    """Administrador principal de programación.
    
    Coordina el programador y la cola de sesiones.
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        on_session_ready: Optional[Callable] = None,
        max_queue_size: int = 100
    ):
        """Inicializa el administrador de programación.
        
        Args:
            data_dir: Directorio para persistencia.
            on_session_ready: Callback cuando una sesión debe ejecutarse.
            max_queue_size: Tamaño máximo de la cola.
        """
        self.on_session_ready = on_session_ready
        
        # Inicializar componentes
        self.scheduler = SessionScheduler(
            data_dir=data_dir,
            on_session_due=self._on_scheduled_session
        )
        
        self.queue = SessionQueue(
            max_size=max_queue_size,
            on_session_ready=on_session_ready
        )
    
    def _on_scheduled_session(self, session_id: str, session_config: Dict[str, Any]):
        """Callback cuando una sesión programada debe ejecutarse."""
        # Agregar a la cola con alta prioridad
        self.queue.add(session_id, session_config, priority=1)
    
    def start(self):
        """Inicia el administrador de programación."""
        self.scheduler.start()
        logger.info("Administrador de programación iniciado")
    
    def stop(self):
        """Detiene el administrador de programación."""
        self.scheduler.stop()
        self.queue.stop_processing()
        logger.info("Administrador de programación detenido")
    
    def add_scheduled_session(
        self,
        session_id: str,
        session_config: Dict[str, Any],
        cron_expression: str,
        **kwargs
    ) -> Optional[str]:
        """Agrega una sesión programada.
        
        Args:
            session_id: ID de la sesión.
            session_config: Configuración de la sesión.
            cron_expression: Expresión cron.
            **kwargs: Argumentos adicionales (start_time, end_time, days_of_week).
            
        Returns:
            ID de la programación o None.
        """
        return self.scheduler.add_schedule(
            session_id,
            session_config,
            cron_expression,
            **kwargs
        )
    
    def queue_session(
        self,
        session_id: str,
        session_config: Dict[str, Any],
        priority: int = 5
    ) -> bool:
        """Agrega una sesión a la cola.
        
        Args:
            session_id: ID de la sesión.
            session_config: Configuración de la sesión.
            priority: Prioridad (1-10).
            
        Returns:
            True si se agregó exitosamente.
        """
        return self.queue.add(session_id, session_config, priority)
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del administrador.
        
        Returns:
            Diccionario con estado.
        """
        return {
            "scheduler_available": self.scheduler.is_available,
            "scheduled_sessions": len(self.scheduler.get_all_schedules()),
            "pending_runs": self.scheduler.get_pending_runs(),
            "queue": self.queue.get_queue_status()
        }
