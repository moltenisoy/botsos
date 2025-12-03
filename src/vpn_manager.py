"""
Módulo Administrador de VPN y Puentes.

Proporciona gestión completa de sistemas VPN y puentes de red:
- OpenVPN, WireGuard, IKEv2/IPsec
- Puentes Tor, I2P
- Cadenas de proxies SOCKS
- Conexión automática/manual desde GUI

Diseñado exclusivamente para Windows.
"""

import asyncio
import json
import logging
import os
import subprocess
import platform
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

logger = logging.getLogger(__name__)


class VPNProtocol(Enum):
    """Protocolos VPN soportados."""
    OPENVPN = "openvpn"
    WIREGUARD = "wireguard"
    IKEV2 = "ikev2"
    L2TP = "l2tp"
    PPTP = "pptp"
    CUSTOM = "custom"


class BridgeType(Enum):
    """Tipos de puentes de red soportados."""
    TOR = "tor"
    I2P = "i2p"
    SOCKS_CHAIN = "socks_chain"
    SSH_TUNNEL = "ssh_tunnel"
    CUSTOM_BRIDGE = "custom_bridge"


class ConnectionStatus(Enum):
    """Estados de conexión."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class VPNConfig:
    """Configuración de conexión VPN."""
    config_id: str = ""
    name: str = ""
    protocol: str = "openvpn"
    enabled: bool = True

    # Servidor
    server: str = ""
    port: int = 1194

    # Autenticación
    auth_type: str = "credentials"  # credentials, certificate, key
    username: str = ""
    password: str = ""  # Se almacena de forma segura
    certificate_path: str = ""
    private_key_path: str = ""

    # Configuración OpenVPN
    ovpn_config_path: str = ""
    ovpn_protocol: str = "udp"  # udp, tcp

    # Configuración WireGuard
    wg_private_key: str = ""
    wg_public_key: str = ""
    wg_preshared_key: str = ""
    wg_endpoint: str = ""
    wg_allowed_ips: str = "0.0.0.0/0, ::/0"
    wg_persistent_keepalive: int = 25
    wg_dns: str = "1.1.1.1"

    # Opciones avanzadas
    auto_connect: bool = False
    reconnect_on_failure: bool = True
    max_reconnect_attempts: int = 3
    reconnect_delay_sec: int = 10
    kill_switch_enabled: bool = False
    dns_leak_protection: bool = True
    ipv6_leak_protection: bool = True

    # Metadatos
    last_connected: Optional[str] = None
    total_uptime_sec: int = 0
    connection_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario (excluyendo datos sensibles)."""
        data = asdict(self)
        data.pop('password', None)
        data.pop('wg_private_key', None)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VPNConfig':
        """Crea desde diccionario."""
        fields = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in data.items() if k in fields})


@dataclass
class BridgeConfig:
    """Configuración de puente de red."""
    config_id: str = ""
    name: str = ""
    bridge_type: str = "tor"
    enabled: bool = True

    # Configuración Tor
    tor_socks_port: int = 9050
    tor_control_port: int = 9051
    tor_bridges_enabled: bool = False
    tor_bridge_addresses: List[str] = field(default_factory=list)
    tor_use_obfs4: bool = False

    # Configuración I2P
    i2p_proxy_port: int = 4444
    i2p_socks_port: int = 4447

    # Cadena de proxies SOCKS
    socks_chain: List[Dict[str, Any]] = field(default_factory=list)

    # Túnel SSH
    ssh_host: str = ""
    ssh_port: int = 22
    ssh_username: str = ""
    ssh_key_path: str = ""
    ssh_dynamic_port: int = 1080

    # Opciones generales
    auto_start: bool = False
    start_before_vpn: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BridgeConfig':
        """Crea desde diccionario."""
        fields = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in data.items() if k in fields})


@dataclass
class ConnectionState:
    """Estado actual de conexión VPN/Puente."""
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    connected_since: Optional[datetime] = None
    assigned_ip: str = ""
    server_ip: str = ""
    protocol: str = ""
    bytes_sent: int = 0
    bytes_received: int = 0
    current_latency_ms: float = 0.0
    last_error: str = ""
    reconnect_attempts: int = 0


class VPNProviderBase(ABC):
    """Clase base abstracta para proveedores VPN."""

    def __init__(self, config: VPNConfig):
        self.config = config
        self.state = ConnectionState()
        self._process: Optional[subprocess.Popen] = None
        self._on_status_change: Optional[Callable[[ConnectionStatus], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None

    def set_callbacks(
        self,
        on_status_change: Optional[Callable[[ConnectionStatus], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """Configura callbacks para eventos."""
        self._on_status_change = on_status_change
        self._on_error = on_error

    def _update_status(self, status: ConnectionStatus):
        """Actualiza el estado y notifica."""
        self.state.status = status
        if self._on_status_change:
            self._on_status_change(status)
        logger.info(f"VPN {self.config.name}: Estado cambiado a {status.value}")

    def _report_error(self, error: str):
        """Reporta un error."""
        self.state.last_error = error
        self.state.status = ConnectionStatus.ERROR
        if self._on_error:
            self._on_error(error)
        logger.error(f"VPN {self.config.name}: {error}")

    @abstractmethod
    async def connect(self) -> bool:
        """Conecta al VPN."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Desconecta del VPN."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el proveedor está disponible en el sistema."""
        pass

    async def reconnect(self) -> bool:
        """Reconecta al VPN."""
        self._update_status(ConnectionStatus.RECONNECTING)
        await self.disconnect()
        await asyncio.sleep(2)
        return await self.connect()

    def get_state(self) -> ConnectionState:
        """Obtiene el estado actual."""
        return self.state


class OpenVPNProvider(VPNProviderBase):
    """Proveedor de conexión OpenVPN."""

    def __init__(self, config: VPNConfig):
        super().__init__(config)
        self._openvpn_path = self._find_openvpn()

    def _find_openvpn(self) -> str:
        """Busca el ejecutable de OpenVPN."""
        if platform.system() == "Windows":
            possible_paths = [
                r"C:\Program Files\OpenVPN\bin\openvpn.exe",
                r"C:\Program Files (x86)\OpenVPN\bin\openvpn.exe",
                os.environ.get("OPENVPN_PATH", "")
            ]
            for path in possible_paths:
                if path and os.path.exists(path):
                    return path
            return "openvpn"
        return "openvpn"

    def is_available(self) -> bool:
        """Verifica si OpenVPN está instalado."""
        try:
            result = subprocess.run(
                [self._openvpn_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 or "OpenVPN" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    async def connect(self) -> bool:
        """Conecta usando OpenVPN."""
        if not self.is_available():
            self._report_error("OpenVPN no está instalado o no se encuentra")
            return False

        config_path = self.config.ovpn_config_path
        if not config_path or not os.path.exists(config_path):
            self._report_error(f"Archivo de configuración no encontrado: {config_path}")
            return False

        self._update_status(ConnectionStatus.CONNECTING)

        try:
            cmd = [self._openvpn_path, "--config", config_path]

            # Agregar credenciales si es necesario
            if self.config.auth_type == "credentials" and self.config.username:
                auth_file = self._create_auth_file()
                if auth_file:
                    cmd.extend(["--auth-user-pass", auth_file])

            # Agregar opciones de seguridad
            if self.config.dns_leak_protection:
                cmd.extend([
                    "--script-security", "2",
                    "--dhcp-option", "DNS", "1.1.1.1",
                    "--dhcp-option", "DNS", "8.8.8.8"
                ])

            if platform.system() == "Windows":
                # En Windows, usar creationflags para ocultar ventana
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo
                )
            else:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            # Esperar a que se conecte (verificar salida)
            await self._wait_for_connection(timeout=30)

            if self.state.status == ConnectionStatus.CONNECTED:
                self.state.connected_since = datetime.now()
                self.config.connection_count += 1
                self.config.last_connected = datetime.now().isoformat()
                return True

            return False

        except Exception as e:
            self._report_error(f"Error al conectar: {str(e)}")
            return False

    async def _wait_for_connection(self, timeout: int = 30):
        """Espera a que la conexión se establezca."""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            if not self._is_process_running():
                return

            if await self._check_connection_established():
                return

            await asyncio.sleep(1)

        self._report_error("Tiempo de espera agotado al conectar")

    def _is_process_running(self) -> bool:
        """Verifica si el proceso VPN sigue ejecutándose."""
        if self._process is None or self._process.poll() is not None:
            if self._process:
                stderr = self._process.stderr.read().decode() if self._process.stderr else ""
                self._report_error(f"OpenVPN terminó inesperadamente: {stderr}")
            return False
        return True

    async def _check_connection_established(self) -> bool:
        """Verifica si la conexión VPN se estableció exitosamente."""
        if platform.system() != "Windows":
            return False

        try:
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if "TAP-Windows" not in result.stdout and "OpenVPN" not in result.stdout:
                return False

            ip = self._extract_vpn_ip(result.stdout)
            if ip:
                self.state.assigned_ip = ip
                self._update_status(ConnectionStatus.CONNECTED)
                return True

        except Exception:
            pass

        return False

    def _extract_vpn_ip(self, ipconfig_output: str) -> Optional[str]:
        """Extrae la IP asignada por VPN del output de ipconfig."""
        lines = ipconfig_output.split('\n')
        for i, line in enumerate(lines):
            if "TAP" in line or "OpenVPN" in line:
                for j in range(i, min(i + 5, len(lines))):
                    if "IPv4" in lines[j]:
                        return lines[j].split(":")[-1].strip()
        return None

    def _create_auth_file(self) -> Optional[str]:
        """Crea archivo temporal con credenciales."""
        import tempfile
        try:
            fd, path = tempfile.mkstemp(prefix="ovpn_auth_", suffix=".txt")
            with os.fdopen(fd, 'w') as f:
                f.write(f"{self.config.username}\n{self.config.password}\n")
            return path
        except Exception as e:
            logger.error(f"Error creando archivo de autenticación: {e}")
            return None

    async def disconnect(self) -> bool:
        """Desconecta OpenVPN."""
        if self._process:
            try:
                self._process.terminate()
                await asyncio.sleep(2)
                if self._process.poll() is None:
                    self._process.kill()
                self._process = None
            except Exception as e:
                logger.error(f"Error al terminar proceso OpenVPN: {e}")

        self._update_status(ConnectionStatus.DISCONNECTED)
        self.state.connected_since = None
        return True


class WireGuardProvider(VPNProviderBase):
    """Proveedor de conexión WireGuard."""

    def __init__(self, config: VPNConfig):
        super().__init__(config)
        self._wg_path = self._find_wireguard()

    def _find_wireguard(self) -> str:
        """Busca el ejecutable de WireGuard."""
        if platform.system() == "Windows":
            possible_paths = [
                r"C:\Program Files\WireGuard\wireguard.exe",
                r"C:\Program Files (x86)\WireGuard\wireguard.exe",
                os.environ.get("WIREGUARD_PATH", "")
            ]
            for path in possible_paths:
                if path and os.path.exists(path):
                    return path
            return "wireguard"
        return "wg-quick"

    def is_available(self) -> bool:
        """Verifica si WireGuard está instalado."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    [self._wg_path, "--help"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return True
            else:
                result = subprocess.run(
                    ["wg", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def _generate_config_file(self) -> Optional[str]:
        """Genera archivo de configuración WireGuard."""
        import tempfile

        config_content = f"""[Interface]
PrivateKey = {self.config.wg_private_key}
Address = 10.0.0.2/32
DNS = {self.config.wg_dns}

[Peer]
PublicKey = {self.config.wg_public_key}
"""
        if self.config.wg_preshared_key:
            config_content += f"PresharedKey = {self.config.wg_preshared_key}\n"

        config_content += f"""Endpoint = {self.config.wg_endpoint}
AllowedIPs = {self.config.wg_allowed_ips}
PersistentKeepalive = {self.config.wg_persistent_keepalive}
"""

        try:
            fd, path = tempfile.mkstemp(prefix="wg_", suffix=".conf")
            with os.fdopen(fd, 'w') as f:
                f.write(config_content)
            return path
        except Exception as e:
            logger.error(f"Error creando configuración WireGuard: {e}")
            return None

    async def connect(self) -> bool:
        """Conecta usando WireGuard."""
        if not self.is_available():
            self._report_error("WireGuard no está instalado")
            return False

        self._update_status(ConnectionStatus.CONNECTING)

        config_path = self._generate_config_file()
        if not config_path:
            self._report_error("No se pudo generar configuración")
            return False

        try:
            if platform.system() == "Windows":
                # En Windows, usar wireguard.exe /installtunnelservice
                cmd = [self._wg_path, "/installtunnelservice", config_path]
            else:
                cmd = ["wg-quick", "up", config_path]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self._update_status(ConnectionStatus.CONNECTED)
                self.state.connected_since = datetime.now()
                self.config.connection_count += 1
                return True
            else:
                self._report_error(f"Error WireGuard: {result.stderr}")
                return False

        except Exception as e:
            self._report_error(f"Error al conectar WireGuard: {str(e)}")
            return False
        finally:
            # Limpiar archivo temporal
            if config_path and os.path.exists(config_path):
                try:
                    os.unlink(config_path)
                except Exception:
                    pass

    async def disconnect(self) -> bool:
        """Desconecta WireGuard."""
        try:
            if platform.system() == "Windows":
                cmd = [self._wg_path, "/uninstalltunnelservice", self.config.name]
            else:
                cmd = ["wg-quick", "down", self.config.name]

            subprocess.run(cmd, capture_output=True, timeout=10)

        except Exception as e:
            logger.error(f"Error desconectando WireGuard: {e}")

        self._update_status(ConnectionStatus.DISCONNECTED)
        self.state.connected_since = None
        return True


class TorBridgeProvider:
    """Proveedor de puente Tor."""

    def __init__(self, config: BridgeConfig):
        self.config = config
        self.state = ConnectionState()
        self._process: Optional[subprocess.Popen] = None
        self._on_status_change: Optional[Callable[[ConnectionStatus], None]] = None

    def is_available(self) -> bool:
        """Verifica si Tor está instalado."""
        try:
            result = subprocess.run(
                ["tor", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    async def start(self) -> bool:
        """Inicia el servicio Tor."""
        if not self.is_available():
            self.state.last_error = "Tor no está instalado"
            return False

        self.state.status = ConnectionStatus.CONNECTING

        try:
            # Generar torrc temporal
            torrc_content = f"""
SocksPort {self.config.tor_socks_port}
ControlPort {self.config.tor_control_port}
"""
            if self.config.tor_bridges_enabled:
                torrc_content += "UseBridges 1\n"
                for bridge in self.config.tor_bridge_addresses:
                    torrc_content += f"Bridge {bridge}\n"
                if self.config.tor_use_obfs4:
                    torrc_content += "ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy\n"

            import tempfile
            fd, torrc_path = tempfile.mkstemp(prefix="torrc_", suffix=".txt")
            with os.fdopen(fd, 'w') as f:
                f.write(torrc_content)

            self._process = subprocess.Popen(
                ["tor", "-f", torrc_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Esperar a que se conecte
            await asyncio.sleep(10)

            if self._process.poll() is None:
                self.state.status = ConnectionStatus.CONNECTED
                self.state.connected_since = datetime.now()
                return True
            else:
                self.state.status = ConnectionStatus.ERROR
                stderr = self._process.stderr.read().decode() if self._process.stderr else ""
                self.state.last_error = f"Tor terminó: {stderr}"
                return False

        except Exception as e:
            self.state.status = ConnectionStatus.ERROR
            self.state.last_error = str(e)
            return False

    async def stop(self) -> bool:
        """Detiene el servicio Tor."""
        if self._process:
            try:
                self._process.terminate()
                await asyncio.sleep(2)
                if self._process.poll() is None:
                    self._process.kill()
                self._process = None
            except Exception as e:
                logger.error(f"Error deteniendo Tor: {e}")

        self.state.status = ConnectionStatus.DISCONNECTED
        return True

    def get_proxy_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de proxy para usar con el navegador."""
        if self.state.status == ConnectionStatus.CONNECTED:
            return {
                "server": f"socks5://127.0.0.1:{self.config.tor_socks_port}"
            }
        return {}


class SOCKSChainProvider:
    """Proveedor de cadena de proxies SOCKS."""

    def __init__(self, config: BridgeConfig):
        self.config = config
        self.state = ConnectionState()
        self._active_proxies: List[Dict[str, Any]] = []

    async def validate_chain(self) -> bool:
        """Valida que todos los proxies de la cadena están disponibles."""
        if not self.config.socks_chain:
            return False

        for proxy in self.config.socks_chain:
            try:
                import aiohttp
                proxy_url = f"socks5://{proxy.get('host')}:{proxy.get('port')}"

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://httpbin.org/ip",
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status != 200:
                            return False
            except Exception:
                return False

        return True

    async def connect(self) -> bool:
        """Activa la cadena de proxies."""
        if await self.validate_chain():
            self._active_proxies = self.config.socks_chain.copy()
            self.state.status = ConnectionStatus.CONNECTED
            return True

        self.state.status = ConnectionStatus.ERROR
        self.state.last_error = "Uno o más proxies de la cadena no están disponibles"
        return False

    def get_proxy_chain(self) -> List[Dict[str, Any]]:
        """Obtiene la cadena de proxies activa."""
        if self.state.status == ConnectionStatus.CONNECTED:
            return self._active_proxies
        return []


class VPNManager:
    """Administrador central de conexiones VPN y puentes."""

    def __init__(self, data_dir: Path):
        """Inicializa el administrador de VPN.

        Args:
            data_dir: Directorio para almacenar configuraciones.
        """
        self.data_dir = Path(data_dir)
        self.vpn_configs_file = self.data_dir / "vpn_configs.json"
        self.bridge_configs_file = self.data_dir / "bridge_configs.json"

        self.vpn_configs: Dict[str, VPNConfig] = {}
        self.bridge_configs: Dict[str, BridgeConfig] = {}

        self._active_vpn: Optional[VPNProviderBase] = None
        self._active_bridge: Optional[Any] = None

        self._on_status_change: Optional[Callable[[str, ConnectionStatus], None]] = None
        self._on_error: Optional[Callable[[str, str], None]] = None

        self._ensure_data_dir()
        self._load_configs()

    def _ensure_data_dir(self):
        """Asegura que el directorio de datos existe."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load_configs(self):
        """Carga las configuraciones guardadas."""
        # Cargar VPN configs
        if self.vpn_configs_file.exists():
            try:
                with open(self.vpn_configs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for config_data in data.get('configs', []):
                    config = VPNConfig.from_dict(config_data)
                    self.vpn_configs[config.config_id] = config
            except Exception as e:
                logger.error(f"Error cargando configuraciones VPN: {e}")

        # Cargar Bridge configs
        if self.bridge_configs_file.exists():
            try:
                with open(self.bridge_configs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for config_data in data.get('configs', []):
                    config = BridgeConfig.from_dict(config_data)
                    self.bridge_configs[config.config_id] = config
            except Exception as e:
                logger.error(f"Error cargando configuraciones de puente: {e}")

    def _save_configs(self):
        """Guarda las configuraciones."""
        # Guardar VPN configs
        vpn_data = {
            'configs': [c.to_dict() for c in self.vpn_configs.values()],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.vpn_configs_file, 'w', encoding='utf-8') as f:
            json.dump(vpn_data, f, indent=2, ensure_ascii=False)

        # Guardar Bridge configs
        bridge_data = {
            'configs': [c.to_dict() for c in self.bridge_configs.values()],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.bridge_configs_file, 'w', encoding='utf-8') as f:
            json.dump(bridge_data, f, indent=2, ensure_ascii=False)

    def set_callbacks(
        self,
        on_status_change: Optional[Callable[[str, ConnectionStatus], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None
    ):
        """Configura callbacks para eventos."""
        self._on_status_change = on_status_change
        self._on_error = on_error

    # ==========================================
    # Gestión de configuraciones VPN
    # ==========================================

    def add_vpn_config(self, config: VPNConfig) -> str:
        """Agrega una configuración VPN.

        Args:
            config: Configuración VPN a agregar.

        Returns:
            ID de la configuración.
        """
        import uuid
        if not config.config_id:
            config.config_id = str(uuid.uuid4())[:8]

        self.vpn_configs[config.config_id] = config
        self._save_configs()
        logger.info(f"Configuración VPN agregada: {config.name}")
        return config.config_id

    def update_vpn_config(self, config: VPNConfig):
        """Actualiza una configuración VPN existente."""
        if config.config_id in self.vpn_configs:
            self.vpn_configs[config.config_id] = config
            self._save_configs()

    def remove_vpn_config(self, config_id: str) -> bool:
        """Elimina una configuración VPN.

        Args:
            config_id: ID de la configuración a eliminar.

        Returns:
            True si se eliminó, False si no existía.
        """
        if config_id in self.vpn_configs:
            del self.vpn_configs[config_id]
            self._save_configs()
            return True
        return False

    def get_vpn_config(self, config_id: str) -> Optional[VPNConfig]:
        """Obtiene una configuración VPN por ID."""
        return self.vpn_configs.get(config_id)

    def get_all_vpn_configs(self) -> List[VPNConfig]:
        """Obtiene todas las configuraciones VPN."""
        return list(self.vpn_configs.values())

    # ==========================================
    # Gestión de configuraciones de puente
    # ==========================================

    def add_bridge_config(self, config: BridgeConfig) -> str:
        """Agrega una configuración de puente."""
        import uuid
        if not config.config_id:
            config.config_id = str(uuid.uuid4())[:8]

        self.bridge_configs[config.config_id] = config
        self._save_configs()
        return config.config_id

    def update_bridge_config(self, config: BridgeConfig):
        """Actualiza una configuración de puente."""
        if config.config_id in self.bridge_configs:
            self.bridge_configs[config.config_id] = config
            self._save_configs()

    def remove_bridge_config(self, config_id: str) -> bool:
        """Elimina una configuración de puente."""
        if config_id in self.bridge_configs:
            del self.bridge_configs[config_id]
            self._save_configs()
            return True
        return False

    def get_all_bridge_configs(self) -> List[BridgeConfig]:
        """Obtiene todas las configuraciones de puente."""
        return list(self.bridge_configs.values())

    # ==========================================
    # Conexión VPN
    # ==========================================

    def _create_vpn_provider(self, config: VPNConfig) -> Optional[VPNProviderBase]:
        """Crea el proveedor VPN apropiado."""
        protocol = VPNProtocol(config.protocol)

        if protocol == VPNProtocol.OPENVPN:
            return OpenVPNProvider(config)
        elif protocol == VPNProtocol.WIREGUARD:
            return WireGuardProvider(config)
        else:
            logger.warning(f"Protocolo no soportado: {config.protocol}")
            return None

    async def connect_vpn(self, config_id: str) -> bool:
        """Conecta a un VPN.

        Args:
            config_id: ID de la configuración VPN a usar.

        Returns:
            True si la conexión fue exitosa.
        """
        config = self.vpn_configs.get(config_id)
        if not config:
            logger.error(f"Configuración VPN no encontrada: {config_id}")
            return False

        # Desconectar VPN activo si existe
        if self._active_vpn:
            await self.disconnect_vpn()

        provider = self._create_vpn_provider(config)
        if not provider:
            return False

        if not provider.is_available():
            error = f"Proveedor VPN no disponible: {config.protocol}"
            logger.error(error)
            if self._on_error:
                self._on_error(config_id, error)
            return False

        # Configurar callbacks
        def on_status(status: ConnectionStatus):
            if self._on_status_change:
                self._on_status_change(config_id, status)

        def on_error(error: str):
            if self._on_error:
                self._on_error(config_id, error)

        provider.set_callbacks(on_status, on_error)

        success = await provider.connect()
        if success:
            self._active_vpn = provider
            self._save_configs()  # Guardar estadísticas actualizadas

        return success

    async def disconnect_vpn(self) -> bool:
        """Desconecta el VPN activo."""
        if self._active_vpn:
            success = await self._active_vpn.disconnect()
            self._active_vpn = None
            return success
        return True

    def get_vpn_status(self) -> Optional[ConnectionState]:
        """Obtiene el estado del VPN activo."""
        if self._active_vpn:
            return self._active_vpn.get_state()
        return None

    def is_vpn_connected(self) -> bool:
        """Verifica si hay un VPN conectado."""
        if self._active_vpn:
            return self._active_vpn.state.status == ConnectionStatus.CONNECTED
        return False

    # ==========================================
    # Conexión de puentes
    # ==========================================

    async def start_bridge(self, config_id: str) -> bool:
        """Inicia un puente de red.

        Args:
            config_id: ID de la configuración de puente.

        Returns:
            True si se inició correctamente.
        """
        config = self.bridge_configs.get(config_id)
        if not config:
            return False

        bridge_type = BridgeType(config.bridge_type)

        if bridge_type == BridgeType.TOR:
            provider = TorBridgeProvider(config)
            success = await provider.start()
            if success:
                self._active_bridge = provider
            return success
        elif bridge_type == BridgeType.SOCKS_CHAIN:
            provider = SOCKSChainProvider(config)
            success = await provider.connect()
            if success:
                self._active_bridge = provider
            return success

        return False

    async def stop_bridge(self) -> bool:
        """Detiene el puente activo."""
        if self._active_bridge:
            if hasattr(self._active_bridge, 'stop'):
                await self._active_bridge.stop()
            self._active_bridge = None
        return True

    def get_active_proxy_config(self) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración de proxy del puente activo."""
        if self._active_bridge and hasattr(self._active_bridge, 'get_proxy_config'):
            return self._active_bridge.get_proxy_config()
        return None

    # ==========================================
    # Verificación de disponibilidad
    # ==========================================

    def get_available_protocols(self) -> List[str]:
        """Obtiene los protocolos VPN disponibles en el sistema."""
        available = []

        # Verificar OpenVPN
        openvpn_test = OpenVPNProvider(VPNConfig())
        if openvpn_test.is_available():
            available.append(VPNProtocol.OPENVPN.value)

        # Verificar WireGuard
        wireguard_test = WireGuardProvider(VPNConfig())
        if wireguard_test.is_available():
            available.append(VPNProtocol.WIREGUARD.value)

        return available

    def get_available_bridges(self) -> List[str]:
        """Obtiene los tipos de puente disponibles."""
        available = []

        # Tor
        tor_test = TorBridgeProvider(BridgeConfig())
        if tor_test.is_available():
            available.append(BridgeType.TOR.value)

        # SOCKS Chain siempre está disponible
        available.append(BridgeType.SOCKS_CHAIN.value)

        return available

    # ==========================================
    # Importación/Exportación
    # ==========================================

    def import_openvpn_config(self, ovpn_file_path: str, name: str = "") -> Optional[str]:
        """Importa una configuración desde archivo .ovpn.

        Args:
            ovpn_file_path: Ruta al archivo .ovpn.
            name: Nombre para la configuración (opcional).

        Returns:
            ID de la configuración creada o None si falló.
        """
        if not os.path.exists(ovpn_file_path):
            return None

        # Copiar archivo a directorio de datos
        import shutil
        dest_path = self.data_dir / "ovpn" / os.path.basename(ovpn_file_path)
        dest_path.parent.mkdir(exist_ok=True)
        shutil.copy2(ovpn_file_path, dest_path)

        config = VPNConfig(
            name=name or os.path.splitext(os.path.basename(ovpn_file_path))[0],
            protocol=VPNProtocol.OPENVPN.value,
            ovpn_config_path=str(dest_path)
        )

        return self.add_vpn_config(config)

    def export_configs(self, export_path: Path) -> bool:
        """Exporta todas las configuraciones a un archivo.

        Args:
            export_path: Ruta del archivo de exportación.

        Returns:
            True si se exportó correctamente.
        """
        try:
            data = {
                'vpn_configs': [c.to_dict() for c in self.vpn_configs.values()],
                'bridge_configs': [c.to_dict() for c in self.bridge_configs.values()],
                'exported_at': datetime.now().isoformat()
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            logger.error(f"Error exportando configuraciones: {e}")
            return False
