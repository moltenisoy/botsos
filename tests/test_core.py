"""
Suite de Pruebas para BotSOS

Implementa pruebas unitarias y de integración usando pytest.

Implementa características de fase6.txt:
- Tests unitarios para módulos críticos
- Fixtures para sesiones mock
- Tests de integración con Playwright

Diseñado exclusivamente para Windows.
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Generator, Dict, Any
import tempfile
import os
import sys

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """Crea un directorio temporal para datos de prueba."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_session_config() -> Dict[str, Any]:
    """Configuración de sesión de ejemplo."""
    return {
        "session_id": "test123",
        "name": "Sesión de Prueba",
        "enabled": True,
        "headless": True,
        "browser_type": "chromium",
        "behavior": {
            "llm_model": "llama3.1:8b",
            "ad_skip_delay_sec": 5,
            "view_time_min_sec": 30,
            "view_time_max_sec": 60,
            "action_delay_min_ms": 100,
            "action_delay_max_ms": 300
        },
        "proxy": {
            "enabled": False,
            "server": "",
            "port": 0
        },
        "fingerprint": {
            "device_preset": "windows_desktop",
            "canvas_noise_enabled": True,
            "webrtc_protection_enabled": True
        }
    }


@pytest.fixture
def sample_proxy_list() -> list:
    """Lista de proxies de ejemplo."""
    return [
        {"server": "proxy1.example.com", "port": 8080, "type": "http"},
        {"server": "proxy2.example.com", "port": 3128, "type": "http"},
        {"server": "proxy3.example.com", "port": 1080, "type": "socks5"}
    ]


@pytest.fixture
def mock_browser_page():
    """Mock de página de Playwright."""
    page = AsyncMock()
    page.goto = AsyncMock(return_value=None)
    page.click = AsyncMock(return_value=None)
    page.type = AsyncMock(return_value=None)
    page.wait_for_selector = AsyncMock(return_value=MagicMock())
    page.content = AsyncMock(return_value="<html></html>")
    page.title = AsyncMock(return_value="Test Page")
    page.screenshot = AsyncMock(return_value=None)
    page.close = AsyncMock(return_value=None)
    return page


@pytest.fixture
def mock_browser_context(mock_browser_page):
    """Mock de contexto de navegador."""
    context = AsyncMock()
    context.new_page = AsyncMock(return_value=mock_browser_page)
    context.add_init_script = AsyncMock(return_value=None)
    context.close = AsyncMock(return_value=None)
    return context


@pytest.fixture
def mock_browser(mock_browser_context):
    """Mock de navegador Playwright."""
    browser = AsyncMock()
    browser.new_context = AsyncMock(return_value=mock_browser_context)
    browser.close = AsyncMock(return_value=None)
    return browser


# ============================================================
# TESTS DE SESSION_CONFIG
# ============================================================

class TestSessionConfig:
    """Tests para el módulo de configuración de sesión."""
    
    def test_session_config_creation(self):
        """Test: Crear configuración de sesión por defecto."""
        from session_config import SessionConfig
        
        config = SessionConfig()
        
        assert config.session_id is not None
        assert config.name == "New Session"
        assert config.enabled is True
        assert config.browser_type == "chromium"
    
    def test_session_config_to_dict(self):
        """Test: Convertir configuración a diccionario."""
        from session_config import SessionConfig
        
        config = SessionConfig(name="Test Session")
        data = config.to_dict()
        
        assert isinstance(data, dict)
        assert data["name"] == "Test Session"
        assert "status" not in data  # Runtime state no debe incluirse
    
    def test_session_config_from_dict(self, sample_session_config):
        """Test: Crear configuración desde diccionario."""
        from session_config import SessionConfig
        
        config = SessionConfig.from_dict(sample_session_config)
        
        assert config.name == "Sesión de Prueba"
        assert config.headless is True
        assert config.behavior.llm_model == "llama3.1:8b"
    
    def test_session_config_save_load(self, temp_data_dir):
        """Test: Guardar y cargar configuración."""
        from session_config import SessionConfig
        
        config = SessionConfig(name="Sesión Guardada")
        file_path = temp_data_dir / "test_config.json"
        
        config.save(file_path)
        assert file_path.exists()
        
        loaded_config = SessionConfig.load(file_path)
        assert loaded_config.name == "Sesión Guardada"


class TestSessionConfigManager:
    """Tests para el administrador de configuraciones."""
    
    def test_create_session(self, temp_data_dir):
        """Test: Crear nueva sesión."""
        from session_config import SessionConfigManager
        
        manager = SessionConfigManager(temp_data_dir)
        session = manager.create_session("Nueva Sesión")
        
        assert session.name == "Nueva Sesión"
        assert session.session_id in [s.session_id for s in manager.get_all_sessions()]
    
    def test_delete_session(self, temp_data_dir):
        """Test: Eliminar sesión."""
        from session_config import SessionConfigManager
        
        manager = SessionConfigManager(temp_data_dir)
        session = manager.create_session("A Eliminar")
        session_id = session.session_id
        
        result = manager.delete_session(session_id)
        
        assert result is True
        assert manager.get_session(session_id) is None


# ============================================================
# TESTS DE PROXY_MANAGER
# ============================================================

class TestProxyManager:
    """Tests para el administrador de proxies."""
    
    def test_add_proxy(self, temp_data_dir):
        """Test: Agregar proxy al pool."""
        from proxy_manager import ProxyManager, ProxyEntry
        
        manager = ProxyManager(temp_data_dir)
        proxy = ProxyEntry(
            server="test.proxy.com",
            port=8080,
            proxy_type="http"
        )
        
        manager.add_proxy(proxy)
        
        assert len(manager.get_all_proxies()) == 1
        assert manager.get_all_proxies()[0].server == "test.proxy.com"
    
    def test_proxy_from_url(self):
        """Test: Parsear proxy desde URL."""
        from proxy_manager import ProxyEntry
        
        # URL simple
        proxy1 = ProxyEntry.from_url("http://proxy.example.com:8080")
        assert proxy1.server == "proxy.example.com"
        assert proxy1.port == 8080
        assert proxy1.proxy_type == "http"
        
        # URL con autenticación
        proxy2 = ProxyEntry.from_url("socks5://user:pass@proxy.example.com:1080")
        assert proxy2.username == "user"
        assert proxy2.password == "pass"
        assert proxy2.proxy_type == "socks5"
    
    def test_proxy_rotation_round_robin(self, temp_data_dir, sample_proxy_list):
        """Test: Rotación round-robin de proxies."""
        from proxy_manager import ProxyManager, ProxyEntry
        
        manager = ProxyManager(temp_data_dir)
        for p in sample_proxy_list:
            manager.add_proxy(ProxyEntry(
                server=p["server"],
                port=p["port"],
                proxy_type=p["type"]
            ))
        
        # Obtener proxies en orden
        proxy1 = manager.get_next_proxy("round_robin")
        proxy2 = manager.get_next_proxy("round_robin")
        proxy3 = manager.get_next_proxy("round_robin")
        
        assert proxy1.server == "proxy1.example.com"
        assert proxy2.server == "proxy2.example.com"
        assert proxy3.server == "proxy3.example.com"
    
    def test_proxy_success_rate(self, temp_data_dir):
        """Test: Cálculo de tasa de éxito."""
        from proxy_manager import ProxyManager, ProxyEntry
        
        manager = ProxyManager(temp_data_dir)
        proxy = ProxyEntry(server="test.proxy.com", port=8080)
        manager.add_proxy(proxy)
        
        # Simular éxitos y fallos
        for _ in range(7):
            manager.report_success(proxy)
        for _ in range(3):
            manager.report_failure(proxy)
        
        updated_proxy = manager.get_all_proxies()[0]
        assert updated_proxy.success_rate == 0.7


# ============================================================
# TESTS DE FINGERPRINT_MANAGER
# ============================================================

class TestFingerprintManager:
    """Tests para el administrador de huellas digitales."""
    
    def test_generate_fingerprint(self, temp_data_dir):
        """Test: Generar huella digital."""
        from fingerprint_manager import FingerprintManager
        
        # Crear archivo de configuración de dispositivos
        devices_file = temp_data_dir / "devices.json"
        devices_data = {
            "presets": {
                "windows_desktop": {
                    "user_agents": ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)"],
                    "viewport": {"width": [1920], "height": [1080]},
                    "platform": "Win32"
                }
            },
            "spoofing_options": {}
        }
        with open(devices_file, 'w') as f:
            json.dump(devices_data, f)
        
        manager = FingerprintManager(temp_data_dir)
        fingerprint = manager.generate_fingerprint("windows_desktop")
        
        assert fingerprint.platform == "Win32"
        assert fingerprint.viewport_width == 1920
    
    def test_fingerprint_spoofing_scripts(self, temp_data_dir):
        """Test: Scripts de suplantación."""
        from fingerprint_manager import DeviceFingerprint
        
        fingerprint = DeviceFingerprint(
            user_agent="Mozilla/5.0",
            viewport_width=1920,
            viewport_height=1080,
            hardware_concurrency=8,
            device_memory=8,
            platform="Win32",
            timezone="America/Mexico_City",
            languages=["es-MX", "es"],
            webgl_vendor="Google Inc.",
            webgl_renderer="ANGLE",
            canvas_noise_level=5,
            webgl_spoofing=True,
            webrtc_protection=True
        )
        
        scripts = fingerprint.get_spoofing_scripts()
        
        assert len(scripts) > 0
        assert any("hardwareConcurrency" in s for s in scripts)


# ============================================================
# TESTS DE PLUGIN_SYSTEM
# ============================================================

class TestPluginSystem:
    """Tests para el sistema de plugins."""
    
    def test_plugin_manager_init(self, temp_data_dir):
        """Test: Inicialización del administrador de plugins."""
        from plugin_system import PluginManager
        
        manager = PluginManager(temp_data_dir / "plugins")
        
        # Debe tener plugins incorporados
        assert len(manager.get_all_plugins()) > 0
    
    def test_get_enabled_plugins(self, temp_data_dir):
        """Test: Obtener plugins habilitados."""
        from plugin_system import PluginManager
        
        manager = PluginManager(temp_data_dir / "plugins")
        enabled = manager.get_enabled_plugins()
        
        # Todos los plugins incorporados están habilitados por defecto
        assert len(enabled) > 0
        assert all(p.metadata.enabled for p in enabled)
    
    def test_plugin_scripts(self, temp_data_dir):
        """Test: Obtener scripts de plugins."""
        from plugin_system import PluginManager
        
        manager = PluginManager(temp_data_dir / "plugins")
        scripts = manager.get_all_scripts()
        
        assert len(scripts) > 0
        assert all(isinstance(s, str) for s in scripts)
    
    @pytest.mark.asyncio
    async def test_apply_all_plugins(self, temp_data_dir):
        """Test: Aplicar todos los plugins."""
        from plugin_system import PluginManager
        
        manager = PluginManager(temp_data_dir / "plugins")
        context = {"test": True}
        
        result = await manager.apply_all(context)
        
        assert "test" in result  # Contexto original preservado
        # Plugins deben haber añadido propiedades
        assert "jitter_enabled" in result or "action_delay_ms" in result


# ============================================================
# TESTS DE WINDOWS_MANAGER
# ============================================================

class TestWindowsManager:
    """Tests para el administrador de Windows."""
    
    def test_hardware_detector_cpu(self):
        """Test: Detección de CPU."""
        from windows_manager import HardwareDetector
        
        cpu_info = HardwareDetector.get_cpu_info()
        
        assert "name" in cpu_info
        assert "cores" in cpu_info
        assert cpu_info["cores"] > 0
    
    def test_hardware_detector_ram(self):
        """Test: Detección de RAM."""
        from windows_manager import HardwareDetector
        
        ram_info = HardwareDetector.get_ram_info()
        
        assert "total_gb" in ram_info
        # En CI puede ser variable, pero debe ser > 0
        assert ram_info["total_gb"] >= 0


# ============================================================
# TESTS DE HELP_SYSTEM
# ============================================================

class TestHelpSystem:
    """Tests para el sistema de ayuda."""
    
    def test_tooltip_manager(self):
        """Test: Administrador de tooltips."""
        from help_system import TooltipManager
        
        manager = TooltipManager()
        
        # Verificar que existen tooltips
        tooltip = manager.get_tooltip("proxy_enabled")
        assert tooltip is not None
        assert tooltip.short_text != ""
    
    def test_tutorial_wizard(self):
        """Test: Asistente de tutorial."""
        from help_system import TutorialWizard
        
        wizard = TutorialWizard()
        
        assert wizard.total_steps > 0
        assert wizard.current_step == 0
        
        wizard.next_step()
        assert wizard.current_step == 1
        
        wizard.previous_step()
        assert wizard.current_step == 0
    
    def test_ethical_consent(self, temp_data_dir):
        """Test: Administrador de consentimiento ético."""
        from help_system import EthicalConsentManager
        
        manager = EthicalConsentManager(temp_data_dir)
        
        assert manager.has_consent is False
        
        manager.give_consent()
        assert manager.has_consent is True
        
        # Crear nueva instancia para verificar persistencia
        manager2 = EthicalConsentManager(temp_data_dir)
        assert manager2.has_consent is True


# ============================================================
# TESTS DE INTEGRACIÓN
# ============================================================

class TestIntegration:
    """Tests de integración entre módulos."""
    
    @pytest.mark.asyncio
    async def test_session_with_fingerprint(
        self, temp_data_dir, sample_session_config, mock_browser
    ):
        """Test: Sesión con huella digital aplicada."""
        from session_config import SessionConfig
        from fingerprint_manager import FingerprintManager
        
        # Crear configuración
        config = SessionConfig.from_dict(sample_session_config)
        
        # Crear archivo de dispositivos
        devices_file = temp_data_dir / "devices.json"
        with open(devices_file, 'w') as f:
            json.dump({"presets": {}, "spoofing_options": {}}, f)
        
        # Generar huella
        fm = FingerprintManager(temp_data_dir)
        fingerprint = fm.generate_fingerprint(
            preset_name=config.fingerprint.device_preset
        )
        
        # Verificar que la huella se puede convertir a opciones de Playwright
        context_options = fingerprint.to_playwright_context()
        
        assert "viewport" in context_options
        assert "user_agent" in context_options


# ============================================================
# TESTS DE EMPAQUETADO
# ============================================================

class TestPackaging:
    """Tests para el sistema de empaquetado."""
    
    def test_build_config_defaults(self):
        """Test: Configuración de build por defecto."""
        from packaging_manager import BuildConfig
        
        config = BuildConfig()
        
        assert config.app_name == "BotSOS"
        assert config.one_file is True
        assert config.windowed is True
    
    def test_version_manager(self, temp_data_dir):
        """Test: Administrador de versiones."""
        from packaging_manager import VersionManager
        
        manager = VersionManager(temp_data_dir)
        
        assert manager.version == "1.0.0"
        
        new_version = manager.bump_minor()
        assert new_version == "1.1.0"
        
        new_version = manager.bump_patch()
        assert new_version == "1.1.1"


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
