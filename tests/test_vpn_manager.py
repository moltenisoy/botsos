"""
Tests para el módulo de administración de VPN y puentes.

Prueba las funcionalidades de:
- VPNConfig y BridgeConfig
- VPNManager
- Proveedores VPN (OpenVPN, WireGuard)
- Proveedores de puentes (Tor, SOCKS Chain)
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vpn_manager import (
    VPNConfig, BridgeConfig, ConnectionStatus, ConnectionState,
    VPNProtocol, BridgeType, VPNManager, OpenVPNProvider, WireGuardProvider,
    TorBridgeProvider, SOCKSChainProvider
)


class TestVPNConfig:
    """Tests para la configuración VPN."""
    
    def test_vpn_config_defaults(self):
        """Test: Valores por defecto de VPNConfig."""
        config = VPNConfig()
        
        assert config.protocol == "openvpn"
        assert config.enabled is True
        assert config.port == 1194
        assert config.auto_connect is False
        assert config.reconnect_on_failure is True
        assert config.dns_leak_protection is True
    
    def test_vpn_config_custom_values(self):
        """Test: Valores personalizados de VPNConfig."""
        config = VPNConfig(
            config_id="test123",
            name="Mi VPN",
            protocol="wireguard",
            server="vpn.example.com",
            port=51820
        )
        
        assert config.config_id == "test123"
        assert config.name == "Mi VPN"
        assert config.protocol == "wireguard"
        assert config.server == "vpn.example.com"
        assert config.port == 51820
    
    def test_vpn_config_to_dict(self):
        """Test: Conversión a diccionario (sin datos sensibles)."""
        config = VPNConfig(
            name="Test VPN",
            username="user",
            password="secret123",
            wg_private_key="private_key_secret"
        )
        
        data = config.to_dict()
        
        assert data["name"] == "Test VPN"
        assert data["username"] == "user"
        assert "password" not in data
        assert "wg_private_key" not in data
    
    def test_vpn_config_from_dict(self):
        """Test: Creación desde diccionario."""
        data = {
            "config_id": "abc123",
            "name": "VPN Importado",
            "protocol": "openvpn",
            "server": "vpn.test.com",
            "port": 443,
            "ovpn_protocol": "tcp"
        }
        
        config = VPNConfig.from_dict(data)
        
        assert config.config_id == "abc123"
        assert config.name == "VPN Importado"
        assert config.port == 443
        assert config.ovpn_protocol == "tcp"


class TestBridgeConfig:
    """Tests para la configuración de puentes."""
    
    def test_bridge_config_defaults(self):
        """Test: Valores por defecto de BridgeConfig."""
        config = BridgeConfig()
        
        assert config.bridge_type == "tor"
        assert config.enabled is True
        assert config.tor_socks_port == 9050
        assert config.tor_control_port == 9051
    
    def test_bridge_config_socks_chain(self):
        """Test: Configuración de cadena SOCKS."""
        config = BridgeConfig(
            bridge_type="socks_chain",
            socks_chain=[
                {"host": "proxy1.com", "port": 1080},
                {"host": "proxy2.com", "port": 1080}
            ]
        )
        
        assert len(config.socks_chain) == 2
        assert config.socks_chain[0]["host"] == "proxy1.com"
    
    def test_bridge_config_to_dict(self):
        """Test: Conversión a diccionario."""
        config = BridgeConfig(
            name="Mi Puente Tor",
            bridge_type="tor",
            tor_bridges_enabled=True
        )
        
        data = config.to_dict()
        
        assert data["name"] == "Mi Puente Tor"
        assert data["bridge_type"] == "tor"
        assert data["tor_bridges_enabled"] is True


class TestConnectionState:
    """Tests para el estado de conexión."""
    
    def test_initial_state(self):
        """Test: Estado inicial."""
        state = ConnectionState()
        
        assert state.status == ConnectionStatus.DISCONNECTED
        assert state.connected_since is None
        assert state.assigned_ip == ""
    
    def test_state_with_values(self):
        """Test: Estado con valores."""
        from datetime import datetime
        
        state = ConnectionState(
            status=ConnectionStatus.CONNECTED,
            connected_since=datetime.now(),
            assigned_ip="10.0.0.2",
            bytes_sent=1024,
            bytes_received=2048
        )
        
        assert state.status == ConnectionStatus.CONNECTED
        assert state.assigned_ip == "10.0.0.2"
        assert state.bytes_sent == 1024


class TestVPNManager:
    """Tests para el administrador de VPN."""
    
    @pytest.fixture
    def temp_dir(self):
        """Directorio temporal para pruebas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_manager_initialization(self, temp_dir):
        """Test: Inicialización del administrador."""
        manager = VPNManager(temp_dir)
        
        assert len(manager.vpn_configs) == 0
        assert len(manager.bridge_configs) == 0
        assert manager._active_vpn is None
    
    def test_add_vpn_config(self, temp_dir):
        """Test: Agregar configuración VPN."""
        manager = VPNManager(temp_dir)
        
        config = VPNConfig(name="Test VPN")
        config_id = manager.add_vpn_config(config)
        
        assert config_id is not None
        assert config_id in manager.vpn_configs
        assert manager.vpn_configs[config_id].name == "Test VPN"
    
    def test_update_vpn_config(self, temp_dir):
        """Test: Actualizar configuración VPN."""
        manager = VPNManager(temp_dir)
        
        config = VPNConfig(name="Original")
        config_id = manager.add_vpn_config(config)
        
        config.name = "Actualizado"
        manager.update_vpn_config(config)
        
        assert manager.vpn_configs[config_id].name == "Actualizado"
    
    def test_remove_vpn_config(self, temp_dir):
        """Test: Eliminar configuración VPN."""
        manager = VPNManager(temp_dir)
        
        config = VPNConfig(name="A Eliminar")
        config_id = manager.add_vpn_config(config)
        
        assert manager.remove_vpn_config(config_id) is True
        assert config_id not in manager.vpn_configs
        assert manager.remove_vpn_config("no_existe") is False
    
    def test_add_bridge_config(self, temp_dir):
        """Test: Agregar configuración de puente."""
        manager = VPNManager(temp_dir)
        
        config = BridgeConfig(name="Puente Tor", bridge_type="tor")
        config_id = manager.add_bridge_config(config)
        
        assert config_id is not None
        assert config_id in manager.bridge_configs
    
    def test_persistence(self, temp_dir):
        """Test: Persistencia de configuraciones."""
        # Crear y guardar
        manager1 = VPNManager(temp_dir)
        config = VPNConfig(name="Persistente")
        config_id = manager1.add_vpn_config(config)
        
        # Cargar en nueva instancia
        manager2 = VPNManager(temp_dir)
        
        assert config_id in manager2.vpn_configs
        assert manager2.vpn_configs[config_id].name == "Persistente"
    
    def test_get_available_protocols(self, temp_dir):
        """Test: Obtener protocolos disponibles."""
        manager = VPNManager(temp_dir)
        
        # Mockear disponibilidad
        with patch.object(OpenVPNProvider, 'is_available', return_value=True):
            with patch.object(WireGuardProvider, 'is_available', return_value=False):
                protocols = manager.get_available_protocols()
                
                assert "openvpn" in protocols
                assert "wireguard" not in protocols


class TestOpenVPNProvider:
    """Tests para el proveedor OpenVPN."""
    
    def test_provider_initialization(self):
        """Test: Inicialización del proveedor."""
        config = VPNConfig(
            name="Test OpenVPN",
            protocol="openvpn",
            ovpn_config_path="/path/to/config.ovpn"
        )
        
        provider = OpenVPNProvider(config)
        
        assert provider.config == config
        assert provider.state.status == ConnectionStatus.DISCONNECTED
    
    @pytest.mark.asyncio
    async def test_connect_without_config(self):
        """Test: Conectar sin archivo de configuración."""
        config = VPNConfig(
            name="Sin Config",
            protocol="openvpn",
            ovpn_config_path=""
        )
        
        provider = OpenVPNProvider(config)
        
        with patch.object(provider, 'is_available', return_value=True):
            result = await provider.connect()
            
            assert result is False
            assert provider.state.status == ConnectionStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test: Desconectar VPN."""
        config = VPNConfig(name="Test")
        provider = OpenVPNProvider(config)
        
        result = await provider.disconnect()
        
        assert result is True
        assert provider.state.status == ConnectionStatus.DISCONNECTED
    
    def test_is_available_not_installed(self):
        """Test: Verificar disponibilidad cuando no está instalado."""
        config = VPNConfig()
        provider = OpenVPNProvider(config)
        
        with patch('subprocess.run', side_effect=FileNotFoundError):
            assert provider.is_available() is False


class TestWireGuardProvider:
    """Tests para el proveedor WireGuard."""
    
    def test_provider_initialization(self):
        """Test: Inicialización del proveedor."""
        config = VPNConfig(
            name="Test WireGuard",
            protocol="wireguard",
            wg_public_key="test_public_key",
            wg_endpoint="vpn.example.com:51820"
        )
        
        provider = WireGuardProvider(config)
        
        assert provider.config == config
    
    def test_generate_config_file(self):
        """Test: Generación de archivo de configuración."""
        config = VPNConfig(
            name="WG Test",
            wg_private_key="test_private_key",
            wg_public_key="test_public_key",
            wg_endpoint="vpn.example.com:51820",
            wg_allowed_ips="0.0.0.0/0",
            wg_dns="1.1.1.1"
        )
        
        provider = WireGuardProvider(config)
        config_path = provider._generate_config_file()
        
        if config_path:
            assert Path(config_path).exists()
            with open(config_path, 'r') as f:
                content = f.read()
            assert "PrivateKey" in content
            assert "test_public_key" in content
            # Limpiar
            Path(config_path).unlink()


class TestTorBridgeProvider:
    """Tests para el proveedor de puente Tor."""
    
    def test_provider_initialization(self):
        """Test: Inicialización del proveedor."""
        config = BridgeConfig(
            name="Tor Bridge",
            bridge_type="tor",
            tor_socks_port=9050
        )
        
        provider = TorBridgeProvider(config)
        
        assert provider.config == config
        assert provider.state.status == ConnectionStatus.DISCONNECTED
    
    def test_get_proxy_config_disconnected(self):
        """Test: Obtener configuración de proxy cuando desconectado."""
        config = BridgeConfig()
        provider = TorBridgeProvider(config)
        
        proxy_config = provider.get_proxy_config()
        
        assert proxy_config == {}
    
    def test_get_proxy_config_connected(self):
        """Test: Obtener configuración de proxy cuando conectado."""
        config = BridgeConfig(tor_socks_port=9050)
        provider = TorBridgeProvider(config)
        provider.state.status = ConnectionStatus.CONNECTED
        
        proxy_config = provider.get_proxy_config()
        
        assert "server" in proxy_config
        assert "9050" in proxy_config["server"]


class TestSOCKSChainProvider:
    """Tests para el proveedor de cadena SOCKS."""
    
    def test_provider_initialization(self):
        """Test: Inicialización del proveedor."""
        config = BridgeConfig(
            bridge_type="socks_chain",
            socks_chain=[
                {"host": "proxy1.com", "port": 1080},
                {"host": "proxy2.com", "port": 1080}
            ]
        )
        
        provider = SOCKSChainProvider(config)
        
        assert len(provider.config.socks_chain) == 2
    
    def test_get_proxy_chain_disconnected(self):
        """Test: Obtener cadena de proxies cuando desconectado."""
        config = BridgeConfig(
            socks_chain=[{"host": "test.com", "port": 1080}]
        )
        provider = SOCKSChainProvider(config)
        
        chain = provider.get_proxy_chain()
        
        assert chain == []
    
    def test_get_proxy_chain_connected(self):
        """Test: Obtener cadena de proxies cuando conectado."""
        config = BridgeConfig(
            socks_chain=[{"host": "test.com", "port": 1080}]
        )
        provider = SOCKSChainProvider(config)
        provider.state.status = ConnectionStatus.CONNECTED
        provider._active_proxies = config.socks_chain.copy()
        
        chain = provider.get_proxy_chain()
        
        assert len(chain) == 1
        assert chain[0]["host"] == "test.com"


class TestVPNManagerIntegration:
    """Tests de integración para el administrador VPN."""
    
    @pytest.fixture
    def temp_dir(self):
        """Directorio temporal para pruebas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_vpn_and_bridge_configs_together(self, temp_dir):
        """Test: Gestión de VPN y puentes juntos."""
        manager = VPNManager(temp_dir)
        
        # Agregar VPN
        vpn = VPNConfig(name="VPN Principal")
        vpn_id = manager.add_vpn_config(vpn)
        
        # Agregar Puente
        bridge = BridgeConfig(name="Tor Fallback", bridge_type="tor")
        bridge_id = manager.add_bridge_config(bridge)
        
        # Verificar ambos
        assert len(manager.get_all_vpn_configs()) == 1
        assert len(manager.get_all_bridge_configs()) == 1
        
        # Eliminar uno no afecta al otro
        manager.remove_vpn_config(vpn_id)
        assert len(manager.get_all_vpn_configs()) == 0
        assert len(manager.get_all_bridge_configs()) == 1
    
    def test_export_configs(self, temp_dir):
        """Test: Exportar configuraciones."""
        manager = VPNManager(temp_dir)
        
        # Agregar configuraciones
        manager.add_vpn_config(VPNConfig(name="VPN Export Test"))
        manager.add_bridge_config(BridgeConfig(name="Bridge Export Test"))
        
        # Exportar
        export_path = temp_dir / "export.json"
        result = manager.export_configs(export_path)
        
        assert result is True
        assert export_path.exists()
        
        # Verificar contenido
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        assert "vpn_configs" in data
        assert "bridge_configs" in data
        assert len(data["vpn_configs"]) == 1
        assert len(data["bridge_configs"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
