"""
Módulo de Analíticas y Métricas.

Maneja la recopilación de métricas y dashboard de analíticas
usando Prometheus para monitoreo en tiempo real.

Implementa características de fase5.txt:
- Integración con Prometheus para métricas.
- Dashboard de métricas de sesiones.
- Seguimiento de tasas de éxito, bloqueos y rendimiento.
- Selección de proxy basada en ML.

Diseñado exclusivamente para Windows.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
import json

logger = logging.getLogger(__name__)


@dataclass
class SessionMetrics:
    """Métricas de una sesión individual."""
    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Contadores
    actions_total: int = 0
    actions_success: int = 0
    actions_failed: int = 0
    
    # Específicos
    videos_watched: int = 0
    likes_given: int = 0
    comments_posted: int = 0
    ads_skipped: int = 0
    
    # Detección/Bloqueos
    captchas_encountered: int = 0
    captchas_solved: int = 0
    bans_detected: int = 0
    
    # Proxy
    proxies_used: int = 0
    proxy_rotations: int = 0
    proxy_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito."""
        if self.actions_total == 0:
            return 1.0
        return self.actions_success / self.actions_total
    
    @property
    def duration_seconds(self) -> float:
        """Duración de la sesión en segundos."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate,
            "actions_total": self.actions_total,
            "actions_success": self.actions_success,
            "actions_failed": self.actions_failed,
            "videos_watched": self.videos_watched,
            "likes_given": self.likes_given,
            "comments_posted": self.comments_posted,
            "ads_skipped": self.ads_skipped,
            "captchas_encountered": self.captchas_encountered,
            "captchas_solved": self.captchas_solved,
            "bans_detected": self.bans_detected,
            "proxies_used": self.proxies_used,
            "proxy_rotations": self.proxy_rotations,
            "proxy_failures": self.proxy_failures
        }


@dataclass
class ProxyMetrics:
    """Métricas de rendimiento de un proxy."""
    proxy_id: str
    server: str
    port: int
    
    # Uso
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Rendimiento
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    
    # Bloqueos
    bans_detected: int = 0
    last_used: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def avg_latency_ms(self) -> float:
        """Latencia promedio."""
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency_ms / self.successful_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "proxy_id": self.proxy_id,
            "server": self.server,
            "port": self.port,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "min_latency_ms": self.min_latency_ms if self.min_latency_ms != float('inf') else 0,
            "max_latency_ms": self.max_latency_ms,
            "bans_detected": self.bans_detected,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }


class PrometheusMetrics:
    """Integración con Prometheus para métricas.
    
    Expone métricas en formato Prometheus para recolección.
    """
    
    def __init__(self, port: int = 9090):
        """Inicializa las métricas de Prometheus.
        
        Args:
            port: Puerto para el servidor HTTP de métricas.
        """
        self.port = port
        self._prometheus_available = False
        self._metrics_initialized = False
        self._server = None
        
        self._init_prometheus()
    
    def _init_prometheus(self):
        """Inicializa la biblioteca de Prometheus."""
        try:
            from prometheus_client import (
                Counter, Gauge, Histogram, Summary,
                start_http_server, REGISTRY
            )
            
            self._prometheus_available = True
            
            # Definir métricas
            self.sessions_active = Gauge(
                'botsos_sessions_active',
                'Número de sesiones activas'
            )
            
            self.sessions_total = Counter(
                'botsos_sessions_total',
                'Total de sesiones iniciadas'
            )
            
            self.actions_total = Counter(
                'botsos_actions_total',
                'Total de acciones ejecutadas',
                ['session_id', 'action_type', 'result']
            )
            
            self.session_duration = Histogram(
                'botsos_session_duration_seconds',
                'Duración de sesiones',
                buckets=[60, 300, 600, 1800, 3600, 7200]
            )
            
            self.proxy_requests = Counter(
                'botsos_proxy_requests_total',
                'Total de solicitudes via proxy',
                ['proxy_id', 'result']
            )
            
            self.proxy_latency = Histogram(
                'botsos_proxy_latency_ms',
                'Latencia de proxy en milisegundos',
                ['proxy_id'],
                buckets=[50, 100, 250, 500, 1000, 2500, 5000]
            )
            
            self.bans_detected = Counter(
                'botsos_bans_detected_total',
                'Total de bloqueos detectados',
                ['session_id']
            )
            
            self.captchas_encountered = Counter(
                'botsos_captchas_encountered_total',
                'Total de CAPTCHAs encontrados',
                ['session_id', 'solved']
            )
            
            self.cpu_usage = Gauge(
                'botsos_cpu_usage_percent',
                'Uso de CPU del sistema'
            )
            
            self.ram_usage = Gauge(
                'botsos_ram_usage_percent',
                'Uso de RAM del sistema'
            )
            
            self._metrics_initialized = True
            logger.info("Métricas de Prometheus inicializadas")
            
        except ImportError:
            logger.warning(
                "prometheus_client no está instalado. "
                "Instale con: pip install prometheus-client"
            )
    
    @property
    def is_available(self) -> bool:
        """Verifica si Prometheus está disponible."""
        return self._prometheus_available and self._metrics_initialized
    
    def start_server(self) -> bool:
        """Inicia el servidor HTTP de métricas.
        
        Returns:
            True si se inició exitosamente.
        """
        if not self.is_available:
            return False
        
        try:
            from prometheus_client import start_http_server
            start_http_server(self.port)
            logger.info(f"Servidor de métricas iniciado en puerto {self.port}")
            return True
        except Exception as e:
            logger.error(f"Error iniciando servidor de métricas: {e}")
            return False
    
    def record_session_start(self, session_id: str):
        """Registra inicio de sesión."""
        if self.is_available:
            self.sessions_active.inc()
            self.sessions_total.inc()
    
    def record_session_end(self, session_id: str, duration_sec: float):
        """Registra fin de sesión."""
        if self.is_available:
            self.sessions_active.dec()
            self.session_duration.observe(duration_sec)
    
    def record_action(self, session_id: str, action_type: str, success: bool):
        """Registra una acción."""
        if self.is_available:
            result = "success" if success else "failure"
            self.actions_total.labels(
                session_id=session_id,
                action_type=action_type,
                result=result
            ).inc()
    
    def record_proxy_request(self, proxy_id: str, success: bool, latency_ms: float):
        """Registra una solicitud de proxy."""
        if self.is_available:
            result = "success" if success else "failure"
            self.proxy_requests.labels(proxy_id=proxy_id, result=result).inc()
            if success:
                self.proxy_latency.labels(proxy_id=proxy_id).observe(latency_ms)
    
    def record_ban(self, session_id: str):
        """Registra un bloqueo detectado."""
        if self.is_available:
            self.bans_detected.labels(session_id=session_id).inc()
    
    def record_captcha(self, session_id: str, solved: bool):
        """Registra un CAPTCHA."""
        if self.is_available:
            result = "true" if solved else "false"
            self.captchas_encountered.labels(session_id=session_id, solved=result).inc()
    
    def update_system_metrics(self, cpu_percent: float, ram_percent: float):
        """Actualiza métricas del sistema."""
        if self.is_available:
            self.cpu_usage.set(cpu_percent)
            self.ram_usage.set(ram_percent)


class AnalyticsManager:
    """Administrador principal de analíticas.
    
    Coordina la recopilación de métricas, almacenamiento
    y generación de reportes.
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        prometheus_port: int = 9090,
        enable_prometheus: bool = True
    ):
        """Inicializa el administrador de analíticas.
        
        Args:
            data_dir: Directorio para almacenar datos.
            prometheus_port: Puerto para Prometheus.
            enable_prometheus: Si se debe habilitar Prometheus.
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data/analytics")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Métricas
        self._session_metrics: Dict[str, SessionMetrics] = {}
        self._proxy_metrics: Dict[str, ProxyMetrics] = {}
        self._lock = Lock()
        
        # Prometheus
        self.prometheus = PrometheusMetrics(prometheus_port) if enable_prometheus else None
        
        # Historial
        self._history_file = self.data_dir / "metrics_history.json"
        self._load_history()
    
    def _load_history(self):
        """Carga el historial de métricas."""
        if self._history_file.exists():
            try:
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Cargar métricas de proxies
                    for proxy_data in data.get('proxies', []):
                        proxy = ProxyMetrics(
                            proxy_id=proxy_data['proxy_id'],
                            server=proxy_data['server'],
                            port=proxy_data['port']
                        )
                        proxy.total_requests = proxy_data.get('total_requests', 0)
                        proxy.successful_requests = proxy_data.get('successful_requests', 0)
                        proxy.failed_requests = proxy_data.get('failed_requests', 0)
                        proxy.total_latency_ms = proxy_data.get('total_latency_ms', 0.0)
                        self._proxy_metrics[proxy.proxy_id] = proxy
            except Exception as e:
                logger.error(f"Error cargando historial de métricas: {e}")
    
    def _save_history(self):
        """Guarda el historial de métricas."""
        try:
            data = {
                'proxies': [m.to_dict() for m in self._proxy_metrics.values()],
                'last_saved': datetime.now().isoformat()
            }
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando historial de métricas: {e}")
    
    def start_prometheus_server(self) -> bool:
        """Inicia el servidor de Prometheus.
        
        Returns:
            True si se inició exitosamente.
        """
        if self.prometheus:
            return self.prometheus.start_server()
        return False
    
    # ==================== Métricas de Sesión ====================
    
    def start_session(self, session_id: str):
        """Registra el inicio de una sesión."""
        with self._lock:
            self._session_metrics[session_id] = SessionMetrics(session_id=session_id)
        
        if self.prometheus:
            self.prometheus.record_session_start(session_id)
    
    def end_session(self, session_id: str):
        """Registra el fin de una sesión."""
        with self._lock:
            if session_id in self._session_metrics:
                metrics = self._session_metrics[session_id]
                metrics.end_time = datetime.now()
                
                if self.prometheus:
                    self.prometheus.record_session_end(session_id, metrics.duration_seconds)
    
    def record_action(
        self,
        session_id: str,
        action_type: str,
        success: bool
    ):
        """Registra una acción en una sesión."""
        with self._lock:
            if session_id in self._session_metrics:
                metrics = self._session_metrics[session_id]
                metrics.actions_total += 1
                if success:
                    metrics.actions_success += 1
                else:
                    metrics.actions_failed += 1
                
                # Actualizar contadores específicos
                if action_type == "watch_video" and success:
                    metrics.videos_watched += 1
                elif action_type == "like" and success:
                    metrics.likes_given += 1
                elif action_type == "comment" and success:
                    metrics.comments_posted += 1
                elif action_type == "skip_ad" and success:
                    metrics.ads_skipped += 1
        
        if self.prometheus:
            self.prometheus.record_action(session_id, action_type, success)
    
    def record_captcha(self, session_id: str, solved: bool):
        """Registra un CAPTCHA encontrado."""
        with self._lock:
            if session_id in self._session_metrics:
                metrics = self._session_metrics[session_id]
                metrics.captchas_encountered += 1
                if solved:
                    metrics.captchas_solved += 1
        
        if self.prometheus:
            self.prometheus.record_captcha(session_id, solved)
    
    def record_ban(self, session_id: str):
        """Registra un bloqueo detectado."""
        with self._lock:
            if session_id in self._session_metrics:
                self._session_metrics[session_id].bans_detected += 1
        
        if self.prometheus:
            self.prometheus.record_ban(session_id)
    
    # ==================== Métricas de Proxy ====================
    
    def record_proxy_request(
        self,
        proxy_id: str,
        server: str,
        port: int,
        success: bool,
        latency_ms: float
    ):
        """Registra una solicitud de proxy."""
        with self._lock:
            if proxy_id not in self._proxy_metrics:
                self._proxy_metrics[proxy_id] = ProxyMetrics(
                    proxy_id=proxy_id,
                    server=server,
                    port=port
                )
            
            metrics = self._proxy_metrics[proxy_id]
            metrics.total_requests += 1
            metrics.last_used = datetime.now()
            
            if success:
                metrics.successful_requests += 1
                metrics.total_latency_ms += latency_ms
                metrics.min_latency_ms = min(metrics.min_latency_ms, latency_ms)
                metrics.max_latency_ms = max(metrics.max_latency_ms, latency_ms)
            else:
                metrics.failed_requests += 1
        
        if self.prometheus:
            self.prometheus.record_proxy_request(proxy_id, success, latency_ms)
        
        # Guardar periódicamente
        if sum(m.total_requests for m in self._proxy_metrics.values()) % 100 == 0:
            self._save_history()
    
    def record_proxy_ban(self, proxy_id: str):
        """Registra un bloqueo detectado para un proxy."""
        with self._lock:
            if proxy_id in self._proxy_metrics:
                self._proxy_metrics[proxy_id].bans_detected += 1
    
    # ==================== Reportes ====================
    
    def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene las métricas de una sesión.
        
        Args:
            session_id: ID de la sesión.
            
        Returns:
            Diccionario con métricas o None.
        """
        with self._lock:
            if session_id in self._session_metrics:
                return self._session_metrics[session_id].to_dict()
        return None
    
    def get_all_session_metrics(self) -> List[Dict[str, Any]]:
        """Obtiene las métricas de todas las sesiones."""
        with self._lock:
            return [m.to_dict() for m in self._session_metrics.values()]
    
    def get_proxy_metrics(self, proxy_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene las métricas de un proxy."""
        with self._lock:
            if proxy_id in self._proxy_metrics:
                return self._proxy_metrics[proxy_id].to_dict()
        return None
    
    def get_all_proxy_metrics(self) -> List[Dict[str, Any]]:
        """Obtiene las métricas de todos los proxies."""
        with self._lock:
            return [m.to_dict() for m in self._proxy_metrics.values()]
    
    def get_summary_report(self) -> Dict[str, Any]:
        """Genera un reporte resumido de todas las métricas.
        
        Returns:
            Diccionario con resumen de métricas.
        """
        with self._lock:
            sessions = list(self._session_metrics.values())
            proxies = list(self._proxy_metrics.values())
        
        # Estadísticas de sesiones
        total_sessions = len(sessions)
        active_sessions = sum(1 for s in sessions if s.end_time is None)
        total_actions = sum(s.actions_total for s in sessions)
        successful_actions = sum(s.actions_success for s in sessions)
        failed_actions = sum(s.actions_failed for s in sessions)
        total_bans = sum(s.bans_detected for s in sessions)
        total_captchas = sum(s.captchas_encountered for s in sessions)
        solved_captchas = sum(s.captchas_solved for s in sessions)
        
        # Estadísticas de proxies
        total_proxies = len(proxies)
        active_proxies = sum(1 for p in proxies if p.success_rate > 0.5)
        total_proxy_requests = sum(p.total_requests for p in proxies)
        avg_proxy_success_rate = (
            sum(p.success_rate for p in proxies) / total_proxies
            if total_proxies > 0 else 0
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "sessions": {
                "total": total_sessions,
                "active": active_sessions,
                "completed": total_sessions - active_sessions
            },
            "actions": {
                "total": total_actions,
                "successful": successful_actions,
                "failed": failed_actions,
                "success_rate": successful_actions / total_actions if total_actions > 0 else 0
            },
            "security": {
                "bans_detected": total_bans,
                "captchas_encountered": total_captchas,
                "captchas_solved": solved_captchas,
                "captcha_solve_rate": solved_captchas / total_captchas if total_captchas > 0 else 0
            },
            "proxies": {
                "total": total_proxies,
                "active": active_proxies,
                "total_requests": total_proxy_requests,
                "avg_success_rate": avg_proxy_success_rate
            }
        }
    
    def export_to_csv(self, output_path: Path) -> bool:
        """Exporta las métricas a un archivo CSV.
        
        Args:
            output_path: Ruta del archivo de salida.
            
        Returns:
            True si se exportó exitosamente.
        """
        try:
            import csv
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Encabezados
                writer.writerow([
                    'Tipo', 'ID', 'Total Solicitudes', 'Éxitos', 'Fallos',
                    'Tasa de Éxito', 'Latencia Promedio (ms)', 'Bloqueos'
                ])
                
                # Métricas de proxies
                for proxy in self._proxy_metrics.values():
                    writer.writerow([
                        'Proxy',
                        f"{proxy.server}:{proxy.port}",
                        proxy.total_requests,
                        proxy.successful_requests,
                        proxy.failed_requests,
                        f"{proxy.success_rate:.2%}",
                        f"{proxy.avg_latency_ms:.1f}",
                        proxy.bans_detected
                    ])
                
                # Métricas de sesiones
                for session in self._session_metrics.values():
                    writer.writerow([
                        'Sesión',
                        session.session_id,
                        session.actions_total,
                        session.actions_success,
                        session.actions_failed,
                        f"{session.success_rate:.2%}",
                        '-',
                        session.bans_detected
                    ])
            
            logger.info(f"Métricas exportadas a {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando métricas: {e}")
            return False
    
    def update_system_metrics(self, cpu_percent: float, ram_percent: float):
        """Actualiza las métricas del sistema."""
        if self.prometheus:
            self.prometheus.update_system_metrics(cpu_percent, ram_percent)
    
    def get_best_proxies(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Obtiene los mejores proxies basado en rendimiento.
        
        Args:
            top_n: Número de proxies a retornar.
            
        Returns:
            Lista de los mejores proxies.
        """
        with self._lock:
            # Filtrar proxies con suficientes solicitudes
            valid_proxies = [
                p for p in self._proxy_metrics.values()
                if p.total_requests >= 10
            ]
            
            # Ordenar por tasa de éxito y latencia
            sorted_proxies = sorted(
                valid_proxies,
                key=lambda p: (p.success_rate, -p.avg_latency_ms),
                reverse=True
            )
            
            return [p.to_dict() for p in sorted_proxies[:top_n]]
    
    def cleanup(self):
        """Limpia recursos y guarda datos."""
        self._save_history()
        logger.info("Analíticas guardadas y limpiadas")
