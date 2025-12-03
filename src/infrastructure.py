"""
Módulo de Infraestructura.

Proporciona componentes de infraestructura avanzados para el sistema:
- Retry Decorator Genérico con backoff exponencial.
- Graceful Shutdown para manejo de señales.
- Context Managers para recursos de navegador.
- Pool de Conexiones HTTP con aiohttp.
- Contenedor de Inyección de Dependencias.

Diseñado exclusivamente para Windows.
"""

import asyncio
import functools
import signal
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import (
    Optional, Callable, Type, Tuple, Any, TypeVar, 
    ParamSpec, Awaitable, List
)
from pathlib import Path

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


# ===========================================
# Retry Decorator Genérico (Sugerencia #6)
# ===========================================

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff_factor: float = 2.0,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Decorador de reintentos genérico para funciones asíncronas.
    
    Implementa backoff exponencial y permite configurar qué excepciones
    deben causar reintentos.
    
    Args:
        max_attempts: Número máximo de intentos.
        delay: Retraso inicial en segundos.
        exceptions: Tupla de excepciones que activan reintento.
        backoff_factor: Factor de multiplicación para el backoff.
        on_retry: Callback opcional llamado en cada reintento.
        
    Returns:
        Decorador configurado.
        
    Usage:
        @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError,))
        async def fetch_data():
            ...
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Función {func.__name__} falló tras "
                            f"{max_attempts} intentos: {e}"
                        )
                        raise
                    
                    wait_time = delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"Intento {attempt + 1}/{max_attempts} de "
                        f"{func.__name__} falló: {e}. "
                        f"Reintentando en {wait_time:.2f}s..."
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    await asyncio.sleep(wait_time)
            
            # This should not be reached but satisfies type checker
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry state")
            
        return wrapper
    return decorator


def retry_sync(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff_factor: float = 2.0,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorador de reintentos genérico para funciones síncronas.
    
    Args:
        max_attempts: Número máximo de intentos.
        delay: Retraso inicial en segundos.
        exceptions: Tupla de excepciones que activan reintento.
        backoff_factor: Factor de multiplicación para el backoff.
        on_retry: Callback opcional llamado en cada reintento.
        
    Returns:
        Decorador configurado.
    """
    import time
    
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Función {func.__name__} falló tras "
                            f"{max_attempts} intentos: {e}"
                        )
                        raise
                    
                    wait_time = delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"Intento {attempt + 1}/{max_attempts} de "
                        f"{func.__name__} falló: {e}. "
                        f"Reintentando en {wait_time:.2f}s..."
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    time.sleep(wait_time)
            
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry state")
            
        return wrapper
    return decorator


# ===========================================
# Graceful Shutdown (Sugerencia #7)
# ===========================================

class GracefulShutdown:
    """
    Administrador de apagado graceful para la aplicación.
    
    Maneja señales del sistema (SIGTERM, SIGINT) y coordina
    la limpieza de recursos antes de terminar.
    
    Usage:
        shutdown = GracefulShutdown()
        shutdown.register_cleanup(cleanup_sessions)
        shutdown.setup_signal_handlers()
        
        # En tu código principal:
        if shutdown.should_stop:
            break
    """
    
    def __init__(self):
        """Inicializa el administrador de shutdown."""
        self._should_stop = False
        self._cleanup_handlers: List[Callable[[], Awaitable[None]]] = []
        self._sync_cleanup_handlers: List[Callable[[], None]] = []
        self._is_shutting_down = False
    
    @property
    def should_stop(self) -> bool:
        """Indica si la aplicación debe detenerse."""
        return self._should_stop
    
    def register_cleanup(self, handler: Callable[[], Awaitable[None]]) -> None:
        """
        Registra un manejador de limpieza asíncrono.
        
        Args:
            handler: Función asíncrona de limpieza.
        """
        self._cleanup_handlers.append(handler)
    
    def register_sync_cleanup(self, handler: Callable[[], None]) -> None:
        """
        Registra un manejador de limpieza síncrono.
        
        Args:
            handler: Función síncrona de limpieza.
        """
        self._sync_cleanup_handlers.append(handler)
    
    def setup_signal_handlers(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """
        Configura los manejadores de señales del sistema.
        
        Args:
            loop: Event loop de asyncio (opcional).
        """
        import sys
        
        # Windows no soporta add_signal_handler, usar signal.signal
        if sys.platform == "win32":
            signal.signal(signal.SIGINT, self._sync_signal_handler)
            signal.signal(signal.SIGTERM, self._sync_signal_handler)
            logger.info("Manejadores de señales configurados (Windows)")
        else:
            if loop is None:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.get_event_loop()
            
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self._async_signal_handler(s))
                )
            logger.info("Manejadores de señales configurados (Unix)")
    
    def _sync_signal_handler(self, signum: int, frame: Any) -> None:
        """Manejador de señal síncrono."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Señal {sig_name} recibida")
        self._should_stop = True
        
        # Ejecutar limpieza síncrona
        for handler in self._sync_cleanup_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error en limpieza síncrona: {e}")
    
    async def _async_signal_handler(self, sig: signal.Signals) -> None:
        """Manejador de señal asíncrono."""
        if self._is_shutting_down:
            return
        
        self._is_shutting_down = True
        logger.info(f"Señal {sig.name} recibida, iniciando apagado graceful...")
        self._should_stop = True
        
        await self.cleanup()
    
    async def cleanup(self) -> None:
        """Ejecuta todos los manejadores de limpieza registrados."""
        logger.info(f"Ejecutando {len(self._cleanup_handlers)} manejadores de limpieza...")
        
        for handler in self._cleanup_handlers:
            try:
                await handler()
            except Exception as e:
                logger.error(f"Error en manejador de limpieza: {e}")
        
        for handler in self._sync_cleanup_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error en limpieza síncrona: {e}")
        
        logger.info("Limpieza completada")
    
    def request_stop(self) -> None:
        """Solicita una parada programática."""
        logger.info("Parada solicitada programáticamente")
        self._should_stop = True


# Instancia global del shutdown manager
_shutdown_manager: Optional[GracefulShutdown] = None


def get_shutdown_manager() -> GracefulShutdown:
    """Obtiene la instancia global del shutdown manager."""
    global _shutdown_manager
    if _shutdown_manager is None:
        _shutdown_manager = GracefulShutdown()
    return _shutdown_manager


# ===========================================
# Context Managers para Recursos (Sugerencia #8)
# ===========================================

@asynccontextmanager
async def browser_context(
    browser_type: str = "chromium",
    headless: bool = False,
    proxy_config: Optional[dict] = None,
    **launch_args: Any
):
    """
    Context manager asíncrono para sesiones de navegador.
    
    Garantiza que el navegador se cierre correctamente incluso
    si ocurre una excepción.
    
    Args:
        browser_type: Tipo de navegador (chromium, firefox, webkit).
        headless: Si ejecutar en modo headless.
        proxy_config: Configuración de proxy opcional.
        **launch_args: Argumentos adicionales de lanzamiento.
        
    Yields:
        Instancia del navegador.
        
    Usage:
        async with browser_context(headless=True) as browser:
            page = await browser.new_page()
            await page.goto("https://example.com")
    """
    browser = None
    playwright_instance = None
    
    try:
        from playwright.async_api import async_playwright
        
        playwright_instance = await async_playwright().start()
        browser_launcher = getattr(playwright_instance, browser_type)
        
        launch_options = {
            "headless": headless,
            **launch_args
        }
        
        browser = await browser_launcher.launch(**launch_options)
        logger.debug(f"Navegador {browser_type} iniciado")
        
        yield browser
        
    except ImportError:
        logger.error(
            "Playwright no está instalado. "
            "Instale con: pip install playwright && playwright install"
        )
        raise
    finally:
        if browser:
            await browser.close()
            logger.debug(f"Navegador {browser_type} cerrado")
        if playwright_instance:
            await playwright_instance.stop()


@asynccontextmanager
async def browser_page_context(
    browser_type: str = "chromium",
    headless: bool = False,
    context_options: Optional[dict] = None,
    **launch_args: Any
):
    """
    Context manager para obtener directamente una página de navegador.
    
    Útil cuando solo necesitas una página sin gestionar el navegador
    y contexto manualmente.
    
    Args:
        browser_type: Tipo de navegador.
        headless: Si ejecutar en modo headless.
        context_options: Opciones para el contexto del navegador.
        **launch_args: Argumentos adicionales de lanzamiento.
        
    Yields:
        Tupla de (browser, context, page).
        
    Usage:
        async with browser_page_context(headless=True) as (browser, context, page):
            await page.goto("https://example.com")
    """
    async with browser_context(browser_type, headless, **launch_args) as browser:
        context_opts = context_options or {}
        context = await browser.new_context(**context_opts)
        page = await context.new_page()
        
        try:
            yield browser, context, page
        finally:
            await page.close()
            await context.close()


@asynccontextmanager
async def aiohttp_session_context(
    connector_limit: int = 100,
    ttl_dns_cache: int = 300,
    timeout_total: float = 30.0,
    **session_kwargs: Any
):
    """
    Context manager para sesiones de aiohttp.
    
    Args:
        connector_limit: Límite de conexiones simultáneas.
        ttl_dns_cache: TTL del caché DNS en segundos.
        timeout_total: Timeout total para requests.
        **session_kwargs: Argumentos adicionales para ClientSession.
        
    Yields:
        ClientSession de aiohttp.
        
    Usage:
        async with aiohttp_session_context() as session:
            async with session.get(url) as response:
                data = await response.json()
    """
    try:
        import aiohttp
        
        connector = aiohttp.TCPConnector(
            limit=connector_limit,
            ttl_dns_cache=ttl_dns_cache
        )
        
        timeout = aiohttp.ClientTimeout(total=timeout_total)
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            **session_kwargs
        )
        
        try:
            yield session
        finally:
            await session.close()
            
    except ImportError:
        logger.error(
            "aiohttp no está instalado. "
            "Instale con: pip install aiohttp"
        )
        raise


# ===========================================
# Pool de Conexiones HTTP (Sugerencia #9)
# ===========================================

class ConnectionPool:
    """
    Pool de conexiones HTTP reutilizable.
    
    Implementa un pool de conexiones eficiente usando aiohttp
    para reducir la latencia de conexión.
    
    Usage:
        pool = ConnectionPool(limit=100)
        session = await pool.get_session()
        async with session.get(url) as response:
            data = await response.json()
        
        # Al finalizar:
        await pool.close()
    """
    
    def __init__(
        self,
        limit: int = 100,
        ttl_dns_cache: int = 300,
        timeout_total: float = 30.0,
        timeout_connect: float = 10.0
    ):
        """
        Inicializa el pool de conexiones.
        
        Args:
            limit: Número máximo de conexiones simultáneas.
            ttl_dns_cache: TTL del caché DNS en segundos.
            timeout_total: Timeout total para requests.
            timeout_connect: Timeout de conexión.
        """
        self.limit = limit
        self.ttl_dns_cache = ttl_dns_cache
        self.timeout_total = timeout_total
        self.timeout_connect = timeout_connect
        
        self._connector = None
        self._session = None
        self._is_closed = False
    
    async def get_session(self):
        """
        Obtiene la sesión HTTP del pool.
        
        Returns:
            ClientSession de aiohttp.
        """
        if self._is_closed:
            raise RuntimeError("El pool de conexiones está cerrado")
        
        if self._session is None:
            try:
                import aiohttp
                
                self._connector = aiohttp.TCPConnector(
                    limit=self.limit,
                    ttl_dns_cache=self.ttl_dns_cache
                )
                
                timeout = aiohttp.ClientTimeout(
                    total=self.timeout_total,
                    connect=self.timeout_connect
                )
                
                self._session = aiohttp.ClientSession(
                    connector=self._connector,
                    timeout=timeout
                )
                
                logger.debug(f"Pool de conexiones creado (límite={self.limit})")
                
            except ImportError:
                logger.error("aiohttp no está instalado")
                raise
        
        return self._session
    
    async def close(self) -> None:
        """Cierra el pool de conexiones y libera recursos."""
        if self._session and not self._is_closed:
            await self._session.close()
            self._session = None
            self._connector = None
            self._is_closed = True
            logger.debug("Pool de conexiones cerrado")
    
    @property
    def is_active(self) -> bool:
        """Indica si el pool está activo."""
        return self._session is not None and not self._is_closed
    
    async def __aenter__(self):
        """Entrada del context manager."""
        await self.get_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Salida del context manager."""
        await self.close()
        return False


# ===========================================
# Dependency Injection Container (Sugerencia #10)
# ===========================================

@dataclass
class Dependencies:
    """
    Contenedor de inyección de dependencias.
    
    Centraliza la creación y gestión de dependencias del sistema,
    facilitando testing y configuración.
    
    Attributes:
        fingerprint_manager: Administrador de huellas digitales.
        proxy_manager: Administrador de proxies.
        analytics: Administrador de analíticas.
        connection_pool: Pool de conexiones HTTP.
        shutdown_manager: Administrador de shutdown.
    
    Usage:
        deps = Dependencies.create_default(Path("./data"))
        session = BrowserSession(config, deps.fingerprint_manager, deps.proxy_manager)
    """
    fingerprint_manager: Any  # FingerprintManager
    proxy_manager: Any  # ProxyManager
    analytics: Any  # AnalyticsManager
    connection_pool: Optional[ConnectionPool] = None
    shutdown_manager: Optional[GracefulShutdown] = None
    
    @classmethod
    def create_default(cls, data_dir: Path) -> 'Dependencies':
        """
        Crea un contenedor con las dependencias por defecto.
        
        Args:
            data_dir: Directorio base para datos.
            
        Returns:
            Instancia de Dependencies configurada.
        """
        # Importaciones diferidas para evitar dependencias circulares
        from .fingerprint_manager import FingerprintManager
        from .proxy_manager import ProxyManager
        from .analytics_manager import AnalyticsManager
        
        return cls(
            fingerprint_manager=FingerprintManager(data_dir / "config"),
            proxy_manager=ProxyManager(data_dir),
            analytics=AnalyticsManager(data_dir / "analytics"),
            connection_pool=ConnectionPool(),
            shutdown_manager=get_shutdown_manager()
        )
    
    @classmethod
    def create_for_testing(cls, data_dir: Path) -> 'Dependencies':
        """
        Crea un contenedor configurado para testing.
        
        Args:
            data_dir: Directorio temporal para datos de prueba.
            
        Returns:
            Instancia de Dependencies para testing.
        """
        from .fingerprint_manager import FingerprintManager
        from .proxy_manager import ProxyManager
        from .analytics_manager import AnalyticsManager
        
        return cls(
            fingerprint_manager=FingerprintManager(data_dir / "config"),
            proxy_manager=ProxyManager(data_dir),
            analytics=AnalyticsManager(
                data_dir / "analytics",
                enable_prometheus=False  # Deshabilitar Prometheus en tests
            ),
            connection_pool=None,  # No usar pool en tests
            shutdown_manager=GracefulShutdown()
        )
    
    async def initialize(self) -> None:
        """Inicializa todos los componentes del contenedor."""
        logger.info("Inicializando dependencias...")
        
        if self.connection_pool:
            await self.connection_pool.get_session()
        
        if self.shutdown_manager:
            self.shutdown_manager.register_cleanup(self._cleanup)
        
        logger.info("Dependencias inicializadas")
    
    async def _cleanup(self) -> None:
        """Limpia todos los recursos del contenedor."""
        logger.info("Limpiando dependencias...")
        
        if self.connection_pool:
            await self.connection_pool.close()
        
        if self.analytics:
            self.analytics.cleanup()
        
        logger.info("Dependencias limpiadas")
    
    async def close(self) -> None:
        """Cierra el contenedor y libera recursos."""
        await self._cleanup()


class DependencyProvider:
    """
    Proveedor singleton de dependencias para la aplicación.
    
    Permite acceder a las dependencias desde cualquier parte
    de la aplicación sin pasar referencias explícitas.
    
    Usage:
        # En el inicio de la aplicación:
        DependencyProvider.initialize(Path("./data"))
        
        # En cualquier parte:
        deps = DependencyProvider.get()
        proxy = deps.proxy_manager.get_next_proxy()
    """
    
    _instance: Optional[Dependencies] = None
    
    @classmethod
    def initialize(cls, data_dir: Path, for_testing: bool = False) -> Dependencies:
        """
        Inicializa el proveedor de dependencias.
        
        Args:
            data_dir: Directorio base para datos.
            for_testing: Si es para ambiente de testing.
            
        Returns:
            Instancia de Dependencies.
        """
        if for_testing:
            cls._instance = Dependencies.create_for_testing(data_dir)
        else:
            cls._instance = Dependencies.create_default(data_dir)
        
        return cls._instance
    
    @classmethod
    def get(cls) -> Dependencies:
        """
        Obtiene la instancia de dependencias.
        
        Returns:
            Instancia de Dependencies.
            
        Raises:
            RuntimeError: Si no se ha inicializado.
        """
        if cls._instance is None:
            raise RuntimeError(
                "DependencyProvider no inicializado. "
                "Llame a DependencyProvider.initialize() primero."
            )
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Resetea el proveedor (útil para testing)."""
        cls._instance = None
