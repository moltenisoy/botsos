"""
Tests para los nuevos módulos de validación y resiliencia.

Prueba las funcionalidades añadidas para:
- Validación de entrada
- Circuit Breaker
- Cache con TTL
- Repository Pattern
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Importar módulos a probar
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from validation import InputValidator, ValidationResult, validate_session_config
from resilience import (
    CircuitBreaker, CircuitOpenError, TTLCache, 
    JsonSessionRepository, assert_not_none, assert_in_range
)


class TestInputValidator:
    """Tests para el validador de entrada."""
    
    def test_validate_session_name_valid(self):
        """Test: Nombre de sesión válido."""
        result = InputValidator.validate_session_name("Mi Sesión")
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_session_name_empty(self):
        """Test: Nombre de sesión vacío."""
        result = InputValidator.validate_session_name("")
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validate_session_name_too_long(self):
        """Test: Nombre de sesión demasiado largo."""
        result = InputValidator.validate_session_name("x" * 150)
        assert result.is_valid is False
    
    def test_validate_proxy_config_valid(self):
        """Test: Configuración de proxy válida."""
        result = InputValidator.validate_proxy_config(
            server="proxy.example.com",
            port=8080,
            proxy_type="http"
        )
        assert result.is_valid is True
    
    def test_validate_proxy_config_invalid_server(self):
        """Test: Servidor proxy inválido."""
        result = InputValidator.validate_proxy_config(
            server="",
            port=8080,
            proxy_type="http"
        )
        assert result.is_valid is False
    
    def test_validate_proxy_config_invalid_port(self):
        """Test: Puerto proxy fuera de rango."""
        result = InputValidator.validate_proxy_config(
            server="proxy.example.com",
            port=70000,
            proxy_type="http"
        )
        assert result.is_valid is False
    
    def test_validate_proxy_config_invalid_type(self):
        """Test: Tipo de proxy inválido."""
        result = InputValidator.validate_proxy_config(
            server="proxy.example.com",
            port=8080,
            proxy_type="invalid"
        )
        assert result.is_valid is False
    
    def test_validate_range_valid(self):
        """Test: Rango válido."""
        result = InputValidator.validate_range(10, 100, "tiempo")
        assert result.is_valid is True
    
    def test_validate_range_invalid(self):
        """Test: Rango inválido (min > max)."""
        result = InputValidator.validate_range(100, 10, "tiempo")
        assert result.is_valid is False
    
    def test_validate_cron_valid(self):
        """Test: Expresión cron válida."""
        result = InputValidator.validate_cron_expression("0 * * * *")
        assert result.is_valid is True
    
    def test_validate_cron_invalid(self):
        """Test: Expresión cron inválida."""
        result = InputValidator.validate_cron_expression("invalid")
        assert result.is_valid is False
    
    def test_validate_time_valid(self):
        """Test: Formato de hora válido."""
        result = InputValidator.validate_time("09:30")
        assert result.is_valid is True
    
    def test_validate_time_invalid(self):
        """Test: Formato de hora inválido."""
        result = InputValidator.validate_time("25:00")
        assert result.is_valid is False
    
    def test_validate_email_valid(self):
        """Test: Email válido."""
        result = InputValidator.validate_email("user@example.com")
        assert result.is_valid is True
    
    def test_validate_email_invalid(self):
        """Test: Email inválido."""
        result = InputValidator.validate_email("invalid-email")
        assert result.is_valid is False


class TestCircuitBreaker:
    """Tests para el circuit breaker."""
    
    def test_circuit_starts_closed(self):
        """Test: El circuito inicia cerrado."""
        breaker = CircuitBreaker(failure_threshold=3)
        assert breaker.state == "closed"
    
    def test_circuit_opens_after_failures(self):
        """Test: El circuito se abre tras fallas."""
        breaker = CircuitBreaker(failure_threshold=3, reset_timeout=1)
        
        def failing_func():
            raise Exception("Error simulado")
        
        for _ in range(3):
            try:
                breaker.call(failing_func)
            except Exception:
                pass
        
        assert breaker.state == "open"
    
    def test_circuit_rejects_when_open(self):
        """Test: El circuito rechaza llamadas cuando está abierto."""
        breaker = CircuitBreaker(failure_threshold=1, reset_timeout=60)
        
        def failing_func():
            raise Exception("Error simulado")
        
        try:
            breaker.call(failing_func)
        except Exception:
            pass
        
        with pytest.raises(CircuitOpenError):
            breaker.call(lambda: "success")
    
    def test_circuit_successful_call(self):
        """Test: Llamada exitosa a través del circuito."""
        breaker = CircuitBreaker()
        
        result = breaker.call(lambda: "success")
        
        assert result == "success"
        assert breaker.state == "closed"
    
    def test_circuit_reset(self):
        """Test: Reset manual del circuito."""
        breaker = CircuitBreaker(failure_threshold=1)
        
        def failing_func():
            raise Exception("Error")
        
        try:
            breaker.call(failing_func)
        except Exception:
            pass
        
        breaker.reset()
        assert breaker.state == "closed"


class TestTTLCache:
    """Tests para el cache con TTL."""
    
    def test_cache_set_get(self):
        """Test: Guardar y obtener valor del cache."""
        cache = TTLCache[str](max_size=10, ttl=60)
        
        cache.set("key1", "value1")
        result = cache.get("key1")
        
        assert result == "value1"
    
    def test_cache_miss(self):
        """Test: Cache miss retorna None."""
        cache = TTLCache[str](max_size=10, ttl=60)
        
        result = cache.get("nonexistent")
        
        assert result is None
    
    def test_cache_contains(self):
        """Test: Operador 'in' funciona correctamente."""
        cache = TTLCache[str](max_size=10, ttl=60)
        
        cache.set("key1", "value1")
        
        assert "key1" in cache
        assert "key2" not in cache
    
    def test_cache_delete(self):
        """Test: Eliminar valor del cache."""
        cache = TTLCache[str](max_size=10, ttl=60)
        
        cache.set("key1", "value1")
        result = cache.delete("key1")
        
        assert result is True
        assert "key1" not in cache
    
    def test_cache_clear(self):
        """Test: Limpiar el cache."""
        cache = TTLCache[str](max_size=10, ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert len(cache) == 0
    
    def test_cache_max_size(self):
        """Test: Límite de tamaño del cache."""
        cache = TTLCache[str](max_size=3, ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Debe evictar una entrada
        
        assert len(cache) == 3


class TestJsonSessionRepository:
    """Tests para el repositorio de sesiones JSON."""
    
    @pytest.fixture
    def temp_dir(self):
        """Directorio temporal para pruebas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_save_and_load(self, temp_dir):
        """Test: Guardar y cargar sesión."""
        repo = JsonSessionRepository(temp_dir)
        
        config = {"name": "Test Session", "enabled": True}
        repo.save("session1", config)
        
        loaded = repo.load("session1")
        assert loaded == config
    
    def test_load_nonexistent(self, temp_dir):
        """Test: Cargar sesión inexistente."""
        repo = JsonSessionRepository(temp_dir)
        
        loaded = repo.load("nonexistent")
        assert loaded is None
    
    def test_delete(self, temp_dir):
        """Test: Eliminar sesión."""
        repo = JsonSessionRepository(temp_dir)
        
        repo.save("session1", {"name": "Test"})
        result = repo.delete("session1")
        
        assert result is True
        assert repo.load("session1") is None
    
    def test_list_all(self, temp_dir):
        """Test: Listar todas las sesiones."""
        repo = JsonSessionRepository(temp_dir)
        
        repo.save("session1", {"name": "Session 1"})
        repo.save("session2", {"name": "Session 2"})
        
        all_sessions = repo.list_all()
        assert len(all_sessions) == 2


class TestTypeGuards:
    """Tests para type guards y assertions."""
    
    def test_assert_not_none_valid(self):
        """Test: Valor no None pasa."""
        assert_not_none("value")  # No debe lanzar excepción
    
    def test_assert_not_none_invalid(self):
        """Test: Valor None falla."""
        with pytest.raises(AssertionError):
            assert_not_none(None)
    
    def test_assert_in_range_valid(self):
        """Test: Valor en rango pasa."""
        assert_in_range(50, 0, 100, "test")  # No debe lanzar excepción
    
    def test_assert_in_range_invalid(self):
        """Test: Valor fuera de rango falla."""
        with pytest.raises(AssertionError):
            assert_in_range(150, 0, 100, "test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
