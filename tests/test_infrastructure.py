"""
Tests para el módulo de infraestructura.

Prueba las funcionalidades añadidas para:
- Retry Decorator Genérico.
- Graceful Shutdown.
- Context Managers.
- Pool de Conexiones HTTP.
- Dependency Injection Container.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys

# Importar módulos a probar
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure import (
    retry, retry_sync,
    GracefulShutdown, get_shutdown_manager,
    ConnectionPool, 
    Dependencies, DependencyProvider
)


class TestRetryDecorator:
    """Tests para el decorador de reintentos."""
    
    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """Test: Función exitosa no reintenta."""
        call_count = 0
        
        @retry(max_attempts=3)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_func()
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test: Función exitosa después de fallos."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Error simulado")
            return "success"
        
        result = await flaky_func()
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausts_attempts(self):
        """Test: Función falla después de agotar intentos."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Error permanente")
        
        with pytest.raises(ValueError, match="Error permanente"):
            await always_fails()
        
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_specific_exceptions(self):
        """Test: Solo reintenta excepciones específicas."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01, exceptions=(ConnectionError,))
        async def specific_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Error no reintentable")
        
        with pytest.raises(ValueError):
            await specific_error()
        
        # Solo debe ejecutarse una vez, no reintenta ValueError
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_with_on_retry_callback(self):
        """Test: Callback on_retry se ejecuta correctamente."""
        retry_calls = []
        
        def on_retry_callback(exc, attempt):
            retry_calls.append((str(exc), attempt))
        
        @retry(max_attempts=3, delay=0.01, on_retry=on_retry_callback)
        async def flaky_with_callback():
            if len(retry_calls) < 2:
                raise RuntimeError("Error")
            return "success"
        
        result = await flaky_with_callback()
        
        assert result == "success"
        assert len(retry_calls) == 2
        assert retry_calls[0][1] == 1
        assert retry_calls[1][1] == 2
    
    @pytest.mark.asyncio
    async def test_retry_backoff_factor(self):
        """Test: Factor de backoff se aplica correctamente."""
        import time
        
        call_times = []
        
        @retry(max_attempts=3, delay=0.05, backoff_factor=2.0)
        async def timed_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise RuntimeError("Error")
            return "success"
        
        await timed_func()
        
        # Verificar que los intervalos aumentan
        if len(call_times) >= 3:
            interval1 = call_times[1] - call_times[0]
            interval2 = call_times[2] - call_times[1]
            # El segundo intervalo debe ser aproximadamente el doble
            assert interval2 > interval1 * 1.5


class TestRetrySyncDecorator:
    """Tests para el decorador de reintentos síncrono."""
    
    def test_retry_sync_success(self):
        """Test: Función síncrona exitosa."""
        call_count = 0
        
        @retry_sync(max_attempts=3, delay=0.01)
        def sync_func():
            nonlocal call_count
            call_count += 1
            return "sync_success"
        
        result = sync_func()
        
        assert result == "sync_success"
        assert call_count == 1
    
    def test_retry_sync_with_failures(self):
        """Test: Función síncrona con fallos."""
        call_count = 0
        
        @retry_sync(max_attempts=3, delay=0.01)
        def flaky_sync():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise IOError("Sync error")
            return "recovered"
        
        result = flaky_sync()
        
        assert result == "recovered"
        assert call_count == 3


class TestGracefulShutdown:
    """Tests para el administrador de graceful shutdown."""
    
    def test_initial_state(self):
        """Test: Estado inicial del shutdown manager."""
        shutdown = GracefulShutdown()
        
        assert shutdown.should_stop is False
    
    def test_request_stop(self):
        """Test: Solicitar parada programática."""
        shutdown = GracefulShutdown()
        
        shutdown.request_stop()
        
        assert shutdown.should_stop is True
    
    def test_register_cleanup_handler(self):
        """Test: Registrar manejador de limpieza."""
        shutdown = GracefulShutdown()
        
        async def cleanup():
            pass
        
        shutdown.register_cleanup(cleanup)
        
        assert len(shutdown._cleanup_handlers) == 1
    
    def test_register_sync_cleanup_handler(self):
        """Test: Registrar manejador de limpieza síncrono."""
        shutdown = GracefulShutdown()
        
        def sync_cleanup():
            pass
        
        shutdown.register_sync_cleanup(sync_cleanup)
        
        assert len(shutdown._sync_cleanup_handlers) == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_executes_handlers(self):
        """Test: Cleanup ejecuta todos los manejadores."""
        shutdown = GracefulShutdown()
        cleanup_called = []
        
        async def handler1():
            cleanup_called.append("handler1")
        
        async def handler2():
            cleanup_called.append("handler2")
        
        shutdown.register_cleanup(handler1)
        shutdown.register_cleanup(handler2)
        
        await shutdown.cleanup()
        
        assert "handler1" in cleanup_called
        assert "handler2" in cleanup_called
    
    @pytest.mark.asyncio
    async def test_cleanup_continues_on_error(self):
        """Test: Cleanup continúa incluso si un handler falla."""
        shutdown = GracefulShutdown()
        cleanup_called = []
        
        async def failing_handler():
            raise RuntimeError("Handler error")
        
        async def working_handler():
            cleanup_called.append("working")
        
        shutdown.register_cleanup(failing_handler)
        shutdown.register_cleanup(working_handler)
        
        await shutdown.cleanup()  # No debe lanzar excepción
        
        assert "working" in cleanup_called
    
    def test_get_shutdown_manager_singleton(self):
        """Test: get_shutdown_manager retorna singleton."""
        manager1 = get_shutdown_manager()
        manager2 = get_shutdown_manager()
        
        assert manager1 is manager2


class TestConnectionPool:
    """Tests para el pool de conexiones HTTP."""
    
    def test_pool_initialization(self):
        """Test: Inicialización del pool."""
        pool = ConnectionPool(limit=50, ttl_dns_cache=600)
        
        assert pool.limit == 50
        assert pool.ttl_dns_cache == 600
        assert pool.is_active is False
    
    @pytest.mark.asyncio
    async def test_pool_context_manager(self):
        """Test: Pool como context manager."""
        # Mock aiohttp para evitar dependencia real
        with patch.dict('sys.modules', {'aiohttp': MagicMock()}):
            import sys
            mock_aiohttp = sys.modules['aiohttp']
            mock_session = AsyncMock()
            mock_session.close = AsyncMock()
            mock_aiohttp.ClientSession = MagicMock(return_value=mock_session)
            mock_aiohttp.TCPConnector = MagicMock(return_value=MagicMock())
            mock_aiohttp.ClientTimeout = MagicMock(return_value=MagicMock())
            
            pool = ConnectionPool()
            await pool.get_session()
            assert pool.is_active
            
            await pool.close()
            mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pool_get_session_creates_once(self):
        """Test: get_session solo crea la sesión una vez."""
        with patch.dict('sys.modules', {'aiohttp': MagicMock()}):
            import sys
            mock_aiohttp = sys.modules['aiohttp']
            mock_session = AsyncMock()
            mock_session.close = AsyncMock()
            mock_aiohttp.ClientSession = MagicMock(return_value=mock_session)
            mock_aiohttp.TCPConnector = MagicMock(return_value=MagicMock())
            mock_aiohttp.ClientTimeout = MagicMock(return_value=MagicMock())
            
            pool = ConnectionPool()
            
            session1 = await pool.get_session()
            session2 = await pool.get_session()
            
            assert session1 is session2
            # ClientSession solo debe haberse creado una vez
            assert mock_aiohttp.ClientSession.call_count == 1
            
            await pool.close()
    
    @pytest.mark.asyncio
    async def test_pool_closed_raises_error(self):
        """Test: Usar pool cerrado lanza error."""
        with patch.dict('sys.modules', {'aiohttp': MagicMock()}):
            import sys
            mock_aiohttp = sys.modules['aiohttp']
            mock_session = AsyncMock()
            mock_session.close = AsyncMock()
            mock_aiohttp.ClientSession = MagicMock(return_value=mock_session)
            mock_aiohttp.TCPConnector = MagicMock(return_value=MagicMock())
            mock_aiohttp.ClientTimeout = MagicMock(return_value=MagicMock())
            
            pool = ConnectionPool()
            await pool.get_session()
            await pool.close()
            
            with pytest.raises(RuntimeError, match="cerrado"):
                await pool.get_session()


class TestDependencies:
    """Tests para el contenedor de dependencias."""
    
    @pytest.fixture
    def temp_dir(self):
        """Directorio temporal para pruebas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_dependencies_dataclass(self):
        """Test: Dependencies es un dataclass válido."""
        mock_fp = Mock()
        mock_proxy = Mock()
        mock_analytics = Mock()
        
        deps = Dependencies(
            fingerprint_manager=mock_fp,
            proxy_manager=mock_proxy,
            analytics=mock_analytics
        )
        
        assert deps.fingerprint_manager is mock_fp
        assert deps.proxy_manager is mock_proxy
        assert deps.analytics is mock_analytics
        assert deps.connection_pool is None
        assert deps.shutdown_manager is None
    
    def test_dependencies_with_optional_fields(self):
        """Test: Dependencies con campos opcionales."""
        mock_fp = Mock()
        mock_proxy = Mock()
        mock_analytics = Mock()
        mock_pool = Mock()
        mock_shutdown = Mock()
        
        deps = Dependencies(
            fingerprint_manager=mock_fp,
            proxy_manager=mock_proxy,
            analytics=mock_analytics,
            connection_pool=mock_pool,
            shutdown_manager=mock_shutdown
        )
        
        assert deps.connection_pool is mock_pool
        assert deps.shutdown_manager is mock_shutdown
    
    @pytest.mark.asyncio
    async def test_dependencies_close(self):
        """Test: Cerrar dependencias libera recursos."""
        mock_pool = AsyncMock()
        mock_analytics = Mock()
        mock_analytics.cleanup = Mock()
        
        deps = Dependencies(
            fingerprint_manager=Mock(),
            proxy_manager=Mock(),
            analytics=mock_analytics,
            connection_pool=mock_pool
        )
        
        await deps.close()
        
        mock_pool.close.assert_called_once()
        mock_analytics.cleanup.assert_called_once()


class TestDependencyProvider:
    """Tests para el proveedor de dependencias singleton."""
    
    @pytest.fixture(autouse=True)
    def reset_provider(self):
        """Reset del provider antes y después de cada test."""
        DependencyProvider.reset()
        yield
        DependencyProvider.reset()
    
    def test_get_without_init_raises(self):
        """Test: Get sin inicializar lanza error."""
        with pytest.raises(RuntimeError, match="no inicializado"):
            DependencyProvider.get()
    
    def test_reset_clears_instance(self):
        """Test: Reset limpia la instancia."""
        # Simular inicialización directa
        mock_deps = Mock()
        DependencyProvider._instance = mock_deps
        
        assert DependencyProvider.get() is mock_deps
        
        DependencyProvider.reset()
        
        with pytest.raises(RuntimeError):
            DependencyProvider.get()
    
    def test_manual_instance_setting(self):
        """Test: Configurar instancia manualmente."""
        mock_deps = Mock()
        mock_deps.fingerprint_manager = Mock()
        
        DependencyProvider._instance = mock_deps
        
        result = DependencyProvider.get()
        
        assert result is mock_deps
        assert result.fingerprint_manager is mock_deps.fingerprint_manager


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
