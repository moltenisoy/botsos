"""
Módulo de patrones de resiliencia.

Implementa patrones como Circuit Breaker, Cache con TTL,
y Repository para mejorar la robustez del sistema.

Diseñado exclusivamente para Windows.
"""

import time
import hashlib
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TypeVar, Generic, Callable
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ===========================================
# Circuit Breaker Pattern (Sugerencia #6 del análisis)
# ===========================================

class CircuitOpenError(Exception):
    """Excepción lanzada cuando el circuito está abierto."""
    pass


@dataclass
class CircuitBreakerState:
    """Estado del circuit breaker."""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "closed"  # closed, open, half-open


class CircuitBreaker:
    """
    Implementación del patrón Circuit Breaker para proxies y servicios externos.
    
    Estados:
    - closed: Funcionamiento normal, se permiten todas las llamadas.
    - open: Se rechazan todas las llamadas inmediatamente.
    - half-open: Se permite una llamada de prueba para verificar recuperación.
    
    Usage:
        breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60)
        try:
            result = breaker.call(make_proxy_request, proxy_url)
        except CircuitOpenError:
            # Usar proxy alternativo
            pass
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 3,
        reset_timeout: int = 60
    ):
        """
        Inicializar el circuit breaker.
        
        Args:
            failure_threshold: Número de fallas para abrir el circuito.
            success_threshold: Número de éxitos en half-open para cerrar.
            reset_timeout: Segundos antes de intentar half-open.
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.reset_timeout = reset_timeout
        self._state = CircuitBreakerState()
        self._lock = threading.Lock()
    
    @property
    def state(self) -> str:
        """Obtener el estado actual del circuito."""
        return self._state.state
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecutar una función a través del circuit breaker.
        
        Args:
            func: Función a ejecutar.
            *args: Argumentos posicionales.
            **kwargs: Argumentos con nombre.
            
        Returns:
            Resultado de la función.
            
        Raises:
            CircuitOpenError: Si el circuito está abierto.
        """
        with self._lock:
            self._check_state_transition()
            
            if self._state.state == "open":
                raise CircuitOpenError(
                    f"Circuito abierto. Próximo intento en "
                    f"{self._time_until_retry():.0f} segundos"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecutar una función asíncrona a través del circuit breaker.
        
        Args:
            func: Función asíncrona a ejecutar.
            *args: Argumentos posicionales.
            **kwargs: Argumentos con nombre.
            
        Returns:
            Resultado de la función.
        """
        with self._lock:
            self._check_state_transition()
            
            if self._state.state == "open":
                raise CircuitOpenError(
                    f"Circuito abierto. Próximo intento en "
                    f"{self._time_until_retry():.0f} segundos"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _check_state_transition(self) -> None:
        """Verificar y realizar transiciones de estado."""
        if self._state.state == "open":
            if self._should_attempt_reset():
                self._state.state = "half-open"
                self._state.success_count = 0
                logger.info("Circuit breaker transicionando a half-open")
    
    def _should_attempt_reset(self) -> bool:
        """Verificar si se debe intentar resetear el circuito."""
        if self._state.last_failure_time is None:
            return True
        elapsed = (datetime.now() - self._state.last_failure_time).total_seconds()
        return elapsed >= self.reset_timeout
    
    def _time_until_retry(self) -> float:
        """Calcular tiempo hasta próximo intento."""
        if self._state.last_failure_time is None:
            return 0
        elapsed = (datetime.now() - self._state.last_failure_time).total_seconds()
        return max(0, self.reset_timeout - elapsed)
    
    def _on_success(self) -> None:
        """Manejar una llamada exitosa."""
        with self._lock:
            if self._state.state == "half-open":
                self._state.success_count += 1
                if self._state.success_count >= self.success_threshold:
                    self._state.state = "closed"
                    self._state.failure_count = 0
                    logger.info("Circuit breaker cerrado tras recuperación")
            else:
                self._state.failure_count = 0
    
    def _on_failure(self) -> None:
        """Manejar una llamada fallida."""
        with self._lock:
            self._state.failure_count += 1
            self._state.last_failure_time = datetime.now()
            
            if self._state.state == "half-open":
                self._state.state = "open"
                logger.warning("Circuit breaker abierto tras falla en half-open")
            elif self._state.failure_count >= self.failure_threshold:
                self._state.state = "open"
                logger.warning(
                    f"Circuit breaker abierto tras {self.failure_threshold} fallas"
                )
    
    def reset(self) -> None:
        """Resetear manualmente el circuit breaker."""
        with self._lock:
            self._state = CircuitBreakerState()


# ===========================================
# Cache con TTL (Sugerencia #10 del análisis)
# ===========================================

@dataclass
class CacheEntry(Generic[T]):
    """Entrada de caché con tiempo de expiración."""
    value: T
    expires_at: datetime
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() >= self.expires_at


class TTLCache(Generic[T]):
    """
    Caché con tiempo de vida (TTL).
    
    Implementa caché para respuestas de LLM y otros datos
    que pueden ser reutilizados.
    
    Usage:
        cache = TTLCache[str](max_size=100, ttl=3600)
        cache.set("prompt_hash", "response")
        response = cache.get("prompt_hash")
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        Inicializar el caché.
        
        Args:
            max_size: Número máximo de entradas.
            ttl: Tiempo de vida en segundos.
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[T]:
        """
        Obtener un valor del caché.
        
        Args:
            key: Clave del valor.
            
        Returns:
            Valor almacenado o None si no existe o expiró.
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired:
                del self._cache[key]
                return None
            
            return entry.value
    
    def set(self, key: str, value: T) -> None:
        """
        Almacenar un valor en el caché.
        
        Args:
            key: Clave del valor.
            value: Valor a almacenar.
        """
        with self._lock:
            # Limpiar entradas expiradas si estamos al límite
            if len(self._cache) >= self.max_size:
                self._evict_expired()
            
            # Si aún estamos al límite, eliminar la más antigua
            if len(self._cache) >= self.max_size:
                oldest_key = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].expires_at
                )
                del self._cache[oldest_key]
            
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=datetime.now() + timedelta(seconds=self.ttl)
            )
    
    def delete(self, key: str) -> bool:
        """
        Eliminar un valor del caché.
        
        Args:
            key: Clave del valor.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Limpiar todo el caché."""
        with self._lock:
            self._cache.clear()
    
    def _evict_expired(self) -> int:
        """
        Eliminar entradas expiradas.
        
        Returns:
            Número de entradas eliminadas.
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)
    
    def __contains__(self, key: str) -> bool:
        """Verificar si una clave existe y no ha expirado."""
        return self.get(key) is not None
    
    def __len__(self) -> int:
        """Obtener número de entradas (sin contar expiradas)."""
        with self._lock:
            self._evict_expired()
            return len(self._cache)


class CachedLLMClient:
    """
    Cliente LLM con caché para evitar llamadas repetidas.
    
    Usage:
        client = CachedLLMClient(max_size=100, ttl=3600)
        response = await client.generate("prompt")
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        Inicializar el cliente con caché.
        
        Args:
            max_size: Tamaño máximo del caché.
            ttl: Tiempo de vida de las entradas.
        """
        self._cache = TTLCache[str](max_size=max_size, ttl=ttl)
        self._client = None
    
    def _get_cache_key(self, prompt: str) -> str:
        """Generar clave de caché para un prompt usando SHA-256."""
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    async def generate(self, prompt: str, use_cache: bool = True) -> str:
        """
        Generar respuesta LLM con caché.
        
        Args:
            prompt: Prompt para el modelo.
            use_cache: Si se debe usar el caché.
            
        Returns:
            Respuesta del modelo.
        """
        if use_cache:
            cache_key = self._get_cache_key(prompt)
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Respuesta LLM obtenida del caché")
                return cached
        
        # Aquí iría la llamada real al cliente LLM
        # response = await self._client.generate(prompt)
        response = f"[Respuesta simulada para: {prompt[:50]}...]"
        
        if use_cache:
            self._cache.set(cache_key, response)
        
        return response


# ===========================================
# Repository Pattern (Sugerencia #2 del análisis)
# ===========================================

class SessionRepository(ABC):
    """
    Interfaz abstracta para repositorios de sesión.
    
    Implementa el patrón Repository para desacoplar
    la lógica de persistencia.
    """
    
    @abstractmethod
    def save(self, session_id: str, config: Dict[str, Any]) -> bool:
        """Guardar configuración de sesión."""
        pass
    
    @abstractmethod
    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Cargar configuración de sesión."""
        pass
    
    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """Eliminar configuración de sesión."""
        pass
    
    @abstractmethod
    def list_all(self) -> list:
        """Listar todas las sesiones."""
        pass


class JsonSessionRepository(SessionRepository):
    """
    Implementación de repositorio de sesión usando JSON.
    """
    
    def __init__(self, data_dir: Path):
        """
        Inicializar el repositorio.
        
        Args:
            data_dir: Directorio para almacenar datos.
        """
        self.data_dir = Path(data_dir)
        self.sessions_file = self.data_dir / "sessions.json"
        self._ensure_dir()
    
    def _ensure_dir(self) -> None:
        """Asegurar que el directorio existe."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_all(self) -> Dict[str, Any]:
        """Cargar todas las sesiones del archivo."""
        if not self.sessions_file.exists():
            return {"sessions": {}}
        
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error cargando sesiones: {e}")
            return {"sessions": {}}
    
    def _save_all(self, data: Dict[str, Any]) -> bool:
        """Guardar todas las sesiones al archivo."""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            logger.error(f"Error guardando sesiones: {e}")
            return False
    
    def save(self, session_id: str, config: Dict[str, Any]) -> bool:
        """Guardar configuración de sesión."""
        data = self._load_all()
        data["sessions"][session_id] = config
        return self._save_all(data)
    
    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Cargar configuración de sesión."""
        data = self._load_all()
        return data["sessions"].get(session_id)
    
    def delete(self, session_id: str) -> bool:
        """Eliminar configuración de sesión."""
        data = self._load_all()
        if session_id in data["sessions"]:
            del data["sessions"][session_id]
            return self._save_all(data)
        return False
    
    def list_all(self) -> list:
        """Listar todas las sesiones."""
        data = self._load_all()
        return list(data["sessions"].values())


# ===========================================
# Type Guards y Assertions (Sugerencia #7 del análisis)
# ===========================================

def assert_not_none(value: Any, message: str = "Valor no puede ser None") -> None:
    """
    Verificar que un valor no sea None.
    
    Args:
        value: Valor a verificar.
        message: Mensaje de error.
        
    Raises:
        AssertionError: Si el valor es None.
    """
    assert value is not None, message


def assert_type(value: Any, expected_type: type, name: str = "valor") -> None:
    """
    Verificar que un valor sea del tipo esperado.
    
    Args:
        value: Valor a verificar.
        expected_type: Tipo esperado.
        name: Nombre del valor para el mensaje de error.
        
    Raises:
        AssertionError: Si el tipo no coincide.
    """
    assert isinstance(value, expected_type), \
        f"Se esperaba {expected_type.__name__} para {name}, se recibió {type(value).__name__}"


def assert_positive(value: float, name: str = "valor") -> None:
    """
    Verificar que un valor numérico sea positivo.
    
    Args:
        value: Valor a verificar.
        name: Nombre del valor.
        
    Raises:
        AssertionError: Si el valor no es positivo.
    """
    assert value > 0, f"{name} debe ser positivo, se recibió {value}"


def assert_in_range(
    value: float,
    min_val: float,
    max_val: float,
    name: str = "valor"
) -> None:
    """
    Verificar que un valor esté en un rango.
    
    Args:
        value: Valor a verificar.
        min_val: Valor mínimo.
        max_val: Valor máximo.
        name: Nombre del valor.
        
    Raises:
        AssertionError: Si el valor está fuera del rango.
    """
    assert min_val <= value <= max_val, \
        f"{name} debe estar entre {min_val} y {max_val}, se recibió {value}"
