"""
Pestaña de Gestión de VPN y Puentes.

Proporciona interfaz gráfica para configurar y gestionar:
- Conexiones VPN (OpenVPN, WireGuard, etc.)
- Puentes de red (Tor, I2P, cadenas SOCKS)
- Modo automático y manual de conexión

Diseñado exclusivamente para Windows.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QGroupBox, QFormLayout, QLineEdit, QSpinBox,
    QComboBox, QCheckBox, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTextEdit,
    QFileDialog, QMessageBox, QSplitter, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VPNConnectWorker(QThread):
    """Worker para conectar VPN en segundo plano."""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def __init__(self, vpn_manager, config_id: str):
        super().__init__()
        self.vpn_manager = vpn_manager
        self.config_id = config_id

    def run(self):
        import asyncio

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            self.progress.emit("Conectando...")
            success = loop.run_until_complete(
                self.vpn_manager.connect_vpn(self.config_id)
            )

            if success:
                self.finished.emit(True, "Conexión establecida")
            else:
                status = self.vpn_manager.get_vpn_status()
                error = status.last_error if status else "Error desconocido"
                self.finished.emit(False, error)

            loop.close()
        except Exception as e:
            self.finished.emit(False, str(e))


class VPNBridgeTab(QWidget):
    """Pestaña de gestión de VPN y puentes de red."""

    # Señales
    vpn_connected = pyqtSignal(str)  # config_id
    vpn_disconnected = pyqtSignal()
    bridge_started = pyqtSignal(str)  # config_id
    bridge_stopped = pyqtSignal()

    def __init__(self, data_dir: Path, parent=None):
        super().__init__(parent)

        self.data_dir = data_dir
        self._vpn_manager = None
        self._current_vpn_config = None
        self._current_bridge_config = None
        self._connect_worker = None

        self._setup_ui()
        self._setup_timers()
        self._load_configs()

    def _get_vpn_manager(self):
        """Obtiene o crea el administrador de VPN."""
        if self._vpn_manager is None:
            try:
                from ..vpn_manager import VPNManager
            except ImportError:
                from vpn_manager import VPNManager

            self._vpn_manager = VPNManager(self.data_dir / "vpn")
            self._vpn_manager.set_callbacks(
                on_status_change=self._on_vpn_status_change,
                on_error=self._on_vpn_error
            )
        return self._vpn_manager

    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Pestañas internas
        self.inner_tabs = QTabWidget()
        self.inner_tabs.addTab(self._create_vpn_tab(), "🔐 VPN")
        self.inner_tabs.addTab(self._create_bridges_tab(), "🌉 Puentes")
        self.inner_tabs.addTab(self._create_status_tab(), "📊 Estado")
        self.inner_tabs.addTab(self._create_settings_tab(), "⚙️ Configuración")

        layout.addWidget(self.inner_tabs)

    def _create_vpn_tab(self) -> QWidget:
        """Crea la pestaña de configuración VPN."""
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Panel izquierdo - Lista de configuraciones
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        left_layout.addWidget(QLabel("Configuraciones VPN:"))

        self.vpn_list = QListWidget()
        self.vpn_list.itemClicked.connect(self._on_vpn_selected)
        left_layout.addWidget(self.vpn_list)

        # Botones de lista
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Nueva")
        add_btn.clicked.connect(self._add_vpn_config)
        btn_layout.addWidget(add_btn)

        import_btn = QPushButton("📥 Importar .ovpn")
        import_btn.clicked.connect(self._import_ovpn)
        btn_layout.addWidget(import_btn)

        remove_btn = QPushButton("🗑️")
        remove_btn.clicked.connect(self._remove_vpn_config)
        btn_layout.addWidget(remove_btn)

        left_layout.addLayout(btn_layout)

        # Panel derecho - Configuración
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Información básica
        basic_group = QGroupBox("Configuración Básica")
        basic_layout = QFormLayout(basic_group)

        self.vpn_name_edit = QLineEdit()
        self.vpn_name_edit.setPlaceholderText("Mi VPN")
        basic_layout.addRow("Nombre:", self.vpn_name_edit)

        self.vpn_protocol = QComboBox()
        self.vpn_protocol.addItems(["openvpn", "wireguard", "ikev2", "l2tp"])
        self.vpn_protocol.currentIndexChanged.connect(self._on_protocol_changed)
        basic_layout.addRow("Protocolo:", self.vpn_protocol)

        self.vpn_server = QLineEdit()
        self.vpn_server.setPlaceholderText("vpn.example.com")
        basic_layout.addRow("Servidor:", self.vpn_server)

        self.vpn_port = QSpinBox()
        self.vpn_port.setRange(1, 65535)
        self.vpn_port.setValue(1194)
        basic_layout.addRow("Puerto:", self.vpn_port)

        right_layout.addWidget(basic_group)

        # Autenticación
        auth_group = QGroupBox("Autenticación")
        auth_layout = QFormLayout(auth_group)

        self.vpn_auth_type = QComboBox()
        self.vpn_auth_type.addItems(["credentials", "certificate", "key"])
        auth_layout.addRow("Tipo:", self.vpn_auth_type)

        self.vpn_username = QLineEdit()
        auth_layout.addRow("Usuario:", self.vpn_username)

        self.vpn_password = QLineEdit()
        self.vpn_password.setEchoMode(QLineEdit.EchoMode.Password)
        auth_layout.addRow("Contraseña:", self.vpn_password)

        cert_layout = QHBoxLayout()
        self.vpn_cert_path = QLineEdit()
        self.vpn_cert_path.setPlaceholderText("Ruta al certificado...")
        cert_layout.addWidget(self.vpn_cert_path)
        cert_browse_btn = QPushButton("...")
        cert_browse_btn.setMaximumWidth(30)
        cert_browse_btn.clicked.connect(lambda: self._browse_file(self.vpn_cert_path, "Certificados (*.crt *.pem)"))
        cert_layout.addWidget(cert_browse_btn)
        auth_layout.addRow("Certificado:", cert_layout)

        right_layout.addWidget(auth_group)

        # OpenVPN específico
        self.openvpn_group = QGroupBox("Configuración OpenVPN")
        openvpn_layout = QFormLayout(self.openvpn_group)

        ovpn_path_layout = QHBoxLayout()
        self.ovpn_config_path = QLineEdit()
        self.ovpn_config_path.setPlaceholderText("Archivo .ovpn...")
        ovpn_path_layout.addWidget(self.ovpn_config_path)
        ovpn_browse_btn = QPushButton("...")
        ovpn_browse_btn.setMaximumWidth(30)
        ovpn_browse_btn.clicked.connect(lambda: self._browse_file(self.ovpn_config_path, "OpenVPN (*.ovpn)"))
        ovpn_path_layout.addWidget(ovpn_browse_btn)
        openvpn_layout.addRow("Config:", ovpn_path_layout)

        self.ovpn_protocol = QComboBox()
        self.ovpn_protocol.addItems(["udp", "tcp"])
        openvpn_layout.addRow("Protocolo:", self.ovpn_protocol)

        right_layout.addWidget(self.openvpn_group)

        # WireGuard específico
        self.wireguard_group = QGroupBox("Configuración WireGuard")
        wg_layout = QFormLayout(self.wireguard_group)

        self.wg_private_key = QLineEdit()
        self.wg_private_key.setEchoMode(QLineEdit.EchoMode.Password)
        wg_layout.addRow("Clave Privada:", self.wg_private_key)

        self.wg_public_key = QLineEdit()
        wg_layout.addRow("Clave Pública Peer:", self.wg_public_key)

        self.wg_endpoint = QLineEdit()
        self.wg_endpoint.setPlaceholderText("vpn.example.com:51820")
        wg_layout.addRow("Endpoint:", self.wg_endpoint)

        self.wg_allowed_ips = QLineEdit()
        self.wg_allowed_ips.setText("0.0.0.0/0, ::/0")
        wg_layout.addRow("IPs Permitidas:", self.wg_allowed_ips)

        self.wg_dns = QLineEdit()
        self.wg_dns.setText("1.1.1.1")
        wg_layout.addRow("DNS:", self.wg_dns)

        right_layout.addWidget(self.wireguard_group)
        self.wireguard_group.hide()

        # Opciones avanzadas
        advanced_group = QGroupBox("Opciones Avanzadas")
        advanced_layout = QFormLayout(advanced_group)

        self.vpn_auto_connect = QCheckBox("Conectar automáticamente")
        advanced_layout.addRow(self.vpn_auto_connect)

        self.vpn_reconnect = QCheckBox("Reconectar en caso de fallo")
        self.vpn_reconnect.setChecked(True)
        advanced_layout.addRow(self.vpn_reconnect)

        self.vpn_kill_switch = QCheckBox("Kill Switch (bloquear tráfico si se desconecta)")
        advanced_layout.addRow(self.vpn_kill_switch)

        self.vpn_dns_leak = QCheckBox("Protección contra fugas DNS")
        self.vpn_dns_leak.setChecked(True)
        advanced_layout.addRow(self.vpn_dns_leak)

        self.vpn_ipv6_leak = QCheckBox("Protección contra fugas IPv6")
        self.vpn_ipv6_leak.setChecked(True)
        advanced_layout.addRow(self.vpn_ipv6_leak)

        right_layout.addWidget(advanced_group)

        # Botones de acción
        action_layout = QHBoxLayout()

        self.vpn_save_btn = QPushButton("💾 Guardar")
        self.vpn_save_btn.clicked.connect(self._save_vpn_config)
        action_layout.addWidget(self.vpn_save_btn)

        self.vpn_connect_btn = QPushButton("🔌 Conectar")
        self.vpn_connect_btn.setObjectName("successBtn")
        self.vpn_connect_btn.clicked.connect(self._connect_vpn)
        action_layout.addWidget(self.vpn_connect_btn)

        self.vpn_disconnect_btn = QPushButton("❌ Desconectar")
        self.vpn_disconnect_btn.setObjectName("dangerBtn")
        self.vpn_disconnect_btn.clicked.connect(self._disconnect_vpn)
        self.vpn_disconnect_btn.setEnabled(False)
        action_layout.addWidget(self.vpn_disconnect_btn)

        right_layout.addLayout(action_layout)
        right_layout.addStretch()

        # Agregar paneles al splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 550])

        layout.addWidget(splitter)

        return tab

    def _create_bridges_tab(self) -> QWidget:
        """Crea la pestaña de configuración de puentes."""
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Panel izquierdo - Lista
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        left_layout.addWidget(QLabel("Puentes de Red:"))

        self.bridge_list = QListWidget()
        self.bridge_list.itemClicked.connect(self._on_bridge_selected)
        left_layout.addWidget(self.bridge_list)

        btn_layout = QHBoxLayout()
        add_bridge_btn = QPushButton("➕ Nuevo")
        add_bridge_btn.clicked.connect(self._add_bridge_config)
        btn_layout.addWidget(add_bridge_btn)

        remove_bridge_btn = QPushButton("🗑️")
        remove_bridge_btn.clicked.connect(self._remove_bridge_config)
        btn_layout.addWidget(remove_bridge_btn)

        left_layout.addLayout(btn_layout)

        # Panel derecho - Configuración
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Configuración básica
        basic_group = QGroupBox("Configuración de Puente")
        basic_layout = QFormLayout(basic_group)

        self.bridge_name = QLineEdit()
        basic_layout.addRow("Nombre:", self.bridge_name)

        self.bridge_type = QComboBox()
        self.bridge_type.addItems(["tor", "socks_chain", "ssh_tunnel", "i2p"])
        self.bridge_type.currentIndexChanged.connect(self._on_bridge_type_changed)
        basic_layout.addRow("Tipo:", self.bridge_type)

        right_layout.addWidget(basic_group)

        # Configuración Tor
        self.tor_group = QGroupBox("Configuración Tor")
        tor_layout = QFormLayout(self.tor_group)

        self.tor_socks_port = QSpinBox()
        self.tor_socks_port.setRange(1, 65535)
        self.tor_socks_port.setValue(9050)
        tor_layout.addRow("Puerto SOCKS:", self.tor_socks_port)

        self.tor_control_port = QSpinBox()
        self.tor_control_port.setRange(1, 65535)
        self.tor_control_port.setValue(9051)
        tor_layout.addRow("Puerto Control:", self.tor_control_port)

        self.tor_use_bridges = QCheckBox("Usar Puentes Tor (obfs4)")
        tor_layout.addRow(self.tor_use_bridges)

        self.tor_bridges_edit = QTextEdit()
        self.tor_bridges_edit.setMaximumHeight(80)
        self.tor_bridges_edit.setPlaceholderText("Direcciones de puentes (una por línea)...")
        tor_layout.addRow("Puentes:", self.tor_bridges_edit)

        right_layout.addWidget(self.tor_group)

        # Configuración Cadena SOCKS
        self.socks_group = QGroupBox("Cadena de Proxies SOCKS")
        socks_layout = QVBoxLayout(self.socks_group)

        self.socks_chain_list = QListWidget()
        self.socks_chain_list.setMaximumHeight(100)
        socks_layout.addWidget(self.socks_chain_list)

        socks_btn_layout = QHBoxLayout()

        add_socks_btn = QPushButton("➕ Agregar Proxy")
        add_socks_btn.clicked.connect(self._add_socks_proxy)
        socks_btn_layout.addWidget(add_socks_btn)

        remove_socks_btn = QPushButton("🗑️ Eliminar")
        remove_socks_btn.clicked.connect(self._remove_socks_proxy)
        socks_btn_layout.addWidget(remove_socks_btn)

        socks_layout.addLayout(socks_btn_layout)

        # Campos para agregar proxy
        socks_add_layout = QHBoxLayout()
        self.socks_host = QLineEdit()
        self.socks_host.setPlaceholderText("host")
        socks_add_layout.addWidget(self.socks_host)
        self.socks_port_input = QSpinBox()
        self.socks_port_input.setRange(1, 65535)
        self.socks_port_input.setValue(1080)
        socks_add_layout.addWidget(self.socks_port_input)
        socks_layout.addLayout(socks_add_layout)

        right_layout.addWidget(self.socks_group)
        self.socks_group.hide()

        # Configuración SSH Tunnel
        self.ssh_group = QGroupBox("Túnel SSH")
        ssh_layout = QFormLayout(self.ssh_group)

        self.ssh_host = QLineEdit()
        ssh_layout.addRow("Host:", self.ssh_host)

        self.ssh_port = QSpinBox()
        self.ssh_port.setRange(1, 65535)
        self.ssh_port.setValue(22)
        ssh_layout.addRow("Puerto:", self.ssh_port)

        self.ssh_username = QLineEdit()
        ssh_layout.addRow("Usuario:", self.ssh_username)

        ssh_key_layout = QHBoxLayout()
        self.ssh_key_path = QLineEdit()
        ssh_key_layout.addWidget(self.ssh_key_path)
        ssh_key_btn = QPushButton("...")
        ssh_key_btn.setMaximumWidth(30)
        ssh_key_btn.clicked.connect(lambda: self._browse_file(self.ssh_key_path, "Claves SSH (*.pem *.key)"))
        ssh_key_layout.addWidget(ssh_key_btn)
        ssh_layout.addRow("Clave SSH:", ssh_key_layout)

        self.ssh_dynamic_port = QSpinBox()
        self.ssh_dynamic_port.setRange(1, 65535)
        self.ssh_dynamic_port.setValue(1080)
        ssh_layout.addRow("Puerto Dinámico:", self.ssh_dynamic_port)

        right_layout.addWidget(self.ssh_group)
        self.ssh_group.hide()

        # Opciones
        options_group = QGroupBox("Opciones")
        options_layout = QFormLayout(options_group)

        self.bridge_auto_start = QCheckBox("Iniciar automáticamente")
        options_layout.addRow(self.bridge_auto_start)

        self.bridge_before_vpn = QCheckBox("Iniciar antes del VPN")
        self.bridge_before_vpn.setChecked(True)
        options_layout.addRow(self.bridge_before_vpn)

        right_layout.addWidget(options_group)

        # Botones de acción
        action_layout = QHBoxLayout()

        self.bridge_save_btn = QPushButton("💾 Guardar")
        self.bridge_save_btn.clicked.connect(self._save_bridge_config)
        action_layout.addWidget(self.bridge_save_btn)

        self.bridge_start_btn = QPushButton("▶️ Iniciar")
        self.bridge_start_btn.setObjectName("successBtn")
        self.bridge_start_btn.clicked.connect(self._start_bridge)
        action_layout.addWidget(self.bridge_start_btn)

        self.bridge_stop_btn = QPushButton("⏹️ Detener")
        self.bridge_stop_btn.setObjectName("dangerBtn")
        self.bridge_stop_btn.clicked.connect(self._stop_bridge)
        self.bridge_stop_btn.setEnabled(False)
        action_layout.addWidget(self.bridge_stop_btn)

        right_layout.addLayout(action_layout)
        right_layout.addStretch()

        # Agregar al splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 550])

        layout.addWidget(splitter)

        return tab

    def _create_status_tab(self) -> QWidget:
        """Crea la pestaña de estado de conexión."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Estado VPN
        vpn_status_group = QGroupBox("Estado VPN")
        vpn_status_layout = QFormLayout(vpn_status_group)

        self.vpn_status_label = QLabel("Desconectado")
        self.vpn_status_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        vpn_status_layout.addRow("Estado:", self.vpn_status_label)

        self.vpn_ip_label = QLabel("-")
        vpn_status_layout.addRow("IP Asignada:", self.vpn_ip_label)

        self.vpn_server_label = QLabel("-")
        vpn_status_layout.addRow("Servidor:", self.vpn_server_label)

        self.vpn_protocol_label = QLabel("-")
        vpn_status_layout.addRow("Protocolo:", self.vpn_protocol_label)

        self.vpn_uptime_label = QLabel("-")
        vpn_status_layout.addRow("Tiempo Activo:", self.vpn_uptime_label)

        self.vpn_latency_label = QLabel("-")
        vpn_status_layout.addRow("Latencia:", self.vpn_latency_label)

        layout.addWidget(vpn_status_group)

        # Estado Puente
        bridge_status_group = QGroupBox("Estado Puente")
        bridge_status_layout = QFormLayout(bridge_status_group)

        self.bridge_status_label = QLabel("Inactivo")
        self.bridge_status_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        bridge_status_layout.addRow("Estado:", self.bridge_status_label)

        self.bridge_type_label = QLabel("-")
        bridge_status_layout.addRow("Tipo:", self.bridge_type_label)

        self.bridge_proxy_label = QLabel("-")
        bridge_status_layout.addRow("Proxy:", self.bridge_proxy_label)

        layout.addWidget(bridge_status_group)

        # Tráfico
        traffic_group = QGroupBox("Estadísticas de Tráfico")
        traffic_layout = QFormLayout(traffic_group)

        self.bytes_sent_label = QLabel("0 B")
        traffic_layout.addRow("Enviados:", self.bytes_sent_label)

        self.bytes_received_label = QLabel("0 B")
        traffic_layout.addRow("Recibidos:", self.bytes_received_label)

        layout.addWidget(traffic_group)

        # Log de conexión
        log_group = QGroupBox("Log de Conexión")
        log_layout = QVBoxLayout(log_group)

        self.connection_log = QTextEdit()
        self.connection_log.setReadOnly(True)
        self.connection_log.setMaximumHeight(150)
        log_layout.addWidget(self.connection_log)

        clear_log_btn = QPushButton("Limpiar Log")
        clear_log_btn.clicked.connect(self.connection_log.clear)
        log_layout.addWidget(clear_log_btn)

        layout.addWidget(log_group)
        layout.addStretch()

        return tab

    def _create_settings_tab(self) -> QWidget:
        """Crea la pestaña de configuración general."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Modo de conexión
        mode_group = QGroupBox("Modo de Conexión")
        mode_layout = QFormLayout(mode_group)

        self.connection_mode = QComboBox()
        self.connection_mode.addItems([
            "Manual",
            "Automático (mejor disponible)",
            "Automático (rotación)",
            "Por demanda"
        ])
        mode_layout.addRow("Modo:", self.connection_mode)

        self.auto_start_on_launch = QCheckBox("Conectar al iniciar la aplicación")
        mode_layout.addRow(self.auto_start_on_launch)

        self.reconnect_on_session_start = QCheckBox("Reconectar al iniciar sesión de navegador")
        self.reconnect_on_session_start.setChecked(True)
        mode_layout.addRow(self.reconnect_on_session_start)

        layout.addWidget(mode_group)

        # Orden de preferencia
        priority_group = QGroupBox("Orden de Preferencia")
        priority_layout = QFormLayout(priority_group)

        self.prefer_bridge_first = QCheckBox("Iniciar puente antes de VPN")
        self.prefer_bridge_first.setChecked(True)
        priority_layout.addRow(self.prefer_bridge_first)

        self.fallback_enabled = QCheckBox("Habilitar fallback automático")
        self.fallback_enabled.setChecked(True)
        priority_layout.addRow(self.fallback_enabled)

        layout.addWidget(priority_group)

        # Verificación de IP
        ip_check_group = QGroupBox("Verificación de IP")
        ip_check_layout = QFormLayout(ip_check_group)

        self.verify_ip_change = QCheckBox("Verificar cambio de IP después de conectar")
        self.verify_ip_change.setChecked(True)
        ip_check_layout.addRow(self.verify_ip_change)

        self.check_ip_interval = QSpinBox()
        self.check_ip_interval.setRange(30, 600)
        self.check_ip_interval.setValue(60)
        self.check_ip_interval.setSuffix(" seg")
        ip_check_layout.addRow("Intervalo de verificación:", self.check_ip_interval)

        layout.addWidget(ip_check_group)

        # Disponibilidad del sistema
        system_group = QGroupBox("Disponibilidad del Sistema")
        system_layout = QVBoxLayout(system_group)

        self.available_protocols_label = QLabel("Detectando...")
        system_layout.addWidget(self.available_protocols_label)

        check_btn = QPushButton("🔍 Verificar Disponibilidad")
        check_btn.clicked.connect(self._check_system_availability)
        system_layout.addWidget(check_btn)

        layout.addWidget(system_group)

        # Importar/Exportar
        io_group = QGroupBox("Importar/Exportar Configuraciones")
        io_layout = QHBoxLayout(io_group)

        import_all_btn = QPushButton("📥 Importar Todo")
        import_all_btn.clicked.connect(self._import_all_configs)
        io_layout.addWidget(import_all_btn)

        export_all_btn = QPushButton("📤 Exportar Todo")
        export_all_btn.clicked.connect(self._export_all_configs)
        io_layout.addWidget(export_all_btn)

        layout.addWidget(io_group)

        layout.addStretch()
        return tab

    def _setup_timers(self):
        """Configura los timers para actualización de estado."""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status_display)
        self.status_timer.start(5000)  # Cada 5 segundos

    def _load_configs(self):
        """Carga las configuraciones desde el administrador."""
        try:
            manager = self._get_vpn_manager()

            # Cargar VPN configs
            self.vpn_list.clear()
            for config in manager.get_all_vpn_configs():
                item = QListWidgetItem(f"🔐 {config.name}")
                item.setData(Qt.ItemDataRole.UserRole, config.config_id)
                self.vpn_list.addItem(item)

            # Cargar Bridge configs
            self.bridge_list.clear()
            for config in manager.get_all_bridge_configs():
                item = QListWidgetItem(f"🌉 {config.name}")
                item.setData(Qt.ItemDataRole.UserRole, config.config_id)
                self.bridge_list.addItem(item)

        except Exception as e:
            logger.error(f"Error cargando configuraciones: {e}")

    # ==========================================
    # Eventos VPN
    # ==========================================

    def _on_vpn_selected(self, item: QListWidgetItem):
        """Maneja la selección de una configuración VPN."""
        config_id = item.data(Qt.ItemDataRole.UserRole)
        manager = self._get_vpn_manager()
        config = manager.get_vpn_config(config_id)

        if config:
            self._current_vpn_config = config
            self._populate_vpn_form(config)

    def _populate_vpn_form(self, config):
        """Llena el formulario con los datos de configuración VPN."""
        self.vpn_name_edit.setText(config.name)

        idx = self.vpn_protocol.findText(config.protocol)
        if idx >= 0:
            self.vpn_protocol.setCurrentIndex(idx)

        self.vpn_server.setText(config.server)
        self.vpn_port.setValue(config.port if config.port > 0 else 1194)

        idx = self.vpn_auth_type.findText(config.auth_type)
        if idx >= 0:
            self.vpn_auth_type.setCurrentIndex(idx)

        self.vpn_username.setText(config.username)
        self.vpn_cert_path.setText(config.certificate_path)

        # OpenVPN
        self.ovpn_config_path.setText(config.ovpn_config_path)
        idx = self.ovpn_protocol.findText(config.ovpn_protocol)
        if idx >= 0:
            self.ovpn_protocol.setCurrentIndex(idx)

        # WireGuard
        self.wg_public_key.setText(config.wg_public_key)
        self.wg_endpoint.setText(config.wg_endpoint)
        self.wg_allowed_ips.setText(config.wg_allowed_ips)
        self.wg_dns.setText(config.wg_dns)

        # Opciones
        self.vpn_auto_connect.setChecked(config.auto_connect)
        self.vpn_reconnect.setChecked(config.reconnect_on_failure)
        self.vpn_kill_switch.setChecked(config.kill_switch_enabled)
        self.vpn_dns_leak.setChecked(config.dns_leak_protection)
        self.vpn_ipv6_leak.setChecked(config.ipv6_leak_protection)

        self._on_protocol_changed(self.vpn_protocol.currentIndex())

    def _on_protocol_changed(self, index: int):
        """Maneja el cambio de protocolo VPN."""
        protocol = self.vpn_protocol.currentText()

        self.openvpn_group.setVisible(protocol == "openvpn")
        self.wireguard_group.setVisible(protocol == "wireguard")

    def _add_vpn_config(self):
        """Agrega una nueva configuración VPN."""
        try:
            from vpn_manager import VPNConfig
        except ImportError:
            from ..vpn_manager import VPNConfig

        import uuid
        config = VPNConfig(
            config_id=str(uuid.uuid4())[:8],
            name=f"VPN {self.vpn_list.count() + 1}"
        )

        manager = self._get_vpn_manager()
        manager.add_vpn_config(config)

        self._load_configs()

        # Seleccionar la nueva configuración
        for i in range(self.vpn_list.count()):
            item = self.vpn_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == config.config_id:
                self.vpn_list.setCurrentItem(item)
                self._on_vpn_selected(item)
                break

    def _remove_vpn_config(self):
        """Elimina la configuración VPN seleccionada."""
        current = self.vpn_list.currentItem()
        if not current:
            return

        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Eliminar esta configuración VPN?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            config_id = current.data(Qt.ItemDataRole.UserRole)
            manager = self._get_vpn_manager()
            manager.remove_vpn_config(config_id)
            self._load_configs()
            self._current_vpn_config = None

    def _import_ovpn(self):
        """Importa un archivo .ovpn."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar OpenVPN",
            "", "Archivos OpenVPN (*.ovpn)"
        )

        if file_path:
            manager = self._get_vpn_manager()
            config_id = manager.import_openvpn_config(file_path)

            if config_id:
                self._load_configs()
                QMessageBox.information(
                    self, "Éxito",
                    "Configuración importada correctamente."
                )
            else:
                QMessageBox.warning(
                    self, "Error",
                    "No se pudo importar el archivo."
                )

    def _save_vpn_config(self):
        """Guarda la configuración VPN actual."""
        if not self._current_vpn_config:
            QMessageBox.warning(self, "Advertencia", "No hay configuración seleccionada.")
            return

        config = self._current_vpn_config

        config.name = self.vpn_name_edit.text()
        config.protocol = self.vpn_protocol.currentText()
        config.server = self.vpn_server.text()
        config.port = self.vpn_port.value()

        config.auth_type = self.vpn_auth_type.currentText()
        config.username = self.vpn_username.text()
        config.password = self.vpn_password.text()
        config.certificate_path = self.vpn_cert_path.text()

        # OpenVPN
        config.ovpn_config_path = self.ovpn_config_path.text()
        config.ovpn_protocol = self.ovpn_protocol.currentText()

        # WireGuard
        config.wg_private_key = self.wg_private_key.text()
        config.wg_public_key = self.wg_public_key.text()
        config.wg_endpoint = self.wg_endpoint.text()
        config.wg_allowed_ips = self.wg_allowed_ips.text()
        config.wg_dns = self.wg_dns.text()

        # Opciones
        config.auto_connect = self.vpn_auto_connect.isChecked()
        config.reconnect_on_failure = self.vpn_reconnect.isChecked()
        config.kill_switch_enabled = self.vpn_kill_switch.isChecked()
        config.dns_leak_protection = self.vpn_dns_leak.isChecked()
        config.ipv6_leak_protection = self.vpn_ipv6_leak.isChecked()

        manager = self._get_vpn_manager()
        manager.update_vpn_config(config)

        self._load_configs()
        self._log_message("Configuración VPN guardada")

    def _connect_vpn(self):
        """Conecta al VPN seleccionado."""
        if not self._current_vpn_config:
            QMessageBox.warning(self, "Advertencia", "Seleccione una configuración VPN.")
            return

        self.vpn_connect_btn.setEnabled(False)
        self.vpn_connect_btn.setText("Conectando...")

        self._connect_worker = VPNConnectWorker(
            self._get_vpn_manager(),
            self._current_vpn_config.config_id
        )
        self._connect_worker.finished.connect(self._on_vpn_connect_finished)
        self._connect_worker.progress.connect(self._log_message)
        self._connect_worker.start()

    def _on_vpn_connect_finished(self, success: bool, message: str):
        """Maneja la finalización de la conexión VPN."""
        self.vpn_connect_btn.setText("🔌 Conectar")

        if success:
            self.vpn_connect_btn.setEnabled(False)
            self.vpn_disconnect_btn.setEnabled(True)
            self._log_message(f"✅ {message}")
            self.vpn_connected.emit(self._current_vpn_config.config_id)
        else:
            self.vpn_connect_btn.setEnabled(True)
            self._log_message(f"❌ {message}")
            QMessageBox.warning(self, "Error de Conexión", message)

    def _disconnect_vpn(self):
        """Desconecta el VPN."""
        import asyncio

        manager = self._get_vpn_manager()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(manager.disconnect_vpn())
        finally:
            loop.close()

        self.vpn_connect_btn.setEnabled(True)
        self.vpn_disconnect_btn.setEnabled(False)
        self._log_message("VPN desconectado")
        self.vpn_disconnected.emit()

    def _on_vpn_status_change(self, config_id: str, status):
        """Maneja cambios de estado del VPN."""
        self._update_status_display()
        self._log_message(f"VPN: {status.value}")

    def _on_vpn_error(self, config_id: str, error: str):
        """Maneja errores de VPN."""
        self._log_message(f"Error VPN: {error}")

    # ==========================================
    # Eventos Bridge
    # ==========================================

    def _on_bridge_selected(self, item: QListWidgetItem):
        """Maneja la selección de un puente."""
        config_id = item.data(Qt.ItemDataRole.UserRole)
        manager = self._get_vpn_manager()

        for config in manager.get_all_bridge_configs():
            if config.config_id == config_id:
                self._current_bridge_config = config
                self._populate_bridge_form(config)
                break

    def _populate_bridge_form(self, config):
        """Llena el formulario de puente."""
        self.bridge_name.setText(config.name)

        idx = self.bridge_type.findText(config.bridge_type)
        if idx >= 0:
            self.bridge_type.setCurrentIndex(idx)

        # Tor
        self.tor_socks_port.setValue(config.tor_socks_port)
        self.tor_control_port.setValue(config.tor_control_port)
        self.tor_use_bridges.setChecked(config.tor_bridges_enabled)
        self.tor_bridges_edit.setText("\n".join(config.tor_bridge_addresses))

        # SSH
        self.ssh_host.setText(config.ssh_host)
        self.ssh_port.setValue(config.ssh_port)
        self.ssh_username.setText(config.ssh_username)
        self.ssh_key_path.setText(config.ssh_key_path)
        self.ssh_dynamic_port.setValue(config.ssh_dynamic_port)

        # SOCKS Chain
        self.socks_chain_list.clear()
        for proxy in config.socks_chain:
            self.socks_chain_list.addItem(f"{proxy.get('host')}:{proxy.get('port')}")

        # Opciones
        self.bridge_auto_start.setChecked(config.auto_start)
        self.bridge_before_vpn.setChecked(config.start_before_vpn)

        self._on_bridge_type_changed(self.bridge_type.currentIndex())

    def _on_bridge_type_changed(self, index: int):
        """Maneja el cambio de tipo de puente."""
        bridge_type = self.bridge_type.currentText()

        self.tor_group.setVisible(bridge_type == "tor")
        self.socks_group.setVisible(bridge_type == "socks_chain")
        self.ssh_group.setVisible(bridge_type == "ssh_tunnel")

    def _add_bridge_config(self):
        """Agrega una nueva configuración de puente."""
        try:
            from vpn_manager import BridgeConfig
        except ImportError:
            from ..vpn_manager import BridgeConfig

        import uuid
        config = BridgeConfig(
            config_id=str(uuid.uuid4())[:8],
            name=f"Puente {self.bridge_list.count() + 1}"
        )

        manager = self._get_vpn_manager()
        manager.add_bridge_config(config)

        self._load_configs()

    def _remove_bridge_config(self):
        """Elimina la configuración de puente seleccionada."""
        current = self.bridge_list.currentItem()
        if not current:
            return

        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Eliminar esta configuración de puente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            config_id = current.data(Qt.ItemDataRole.UserRole)
            manager = self._get_vpn_manager()
            manager.remove_bridge_config(config_id)
            self._load_configs()

    def _add_socks_proxy(self):
        """Agrega un proxy a la cadena SOCKS."""
        host = self.socks_host.text().strip()
        port = self.socks_port_input.value()

        if host:
            self.socks_chain_list.addItem(f"{host}:{port}")
            self.socks_host.clear()

    def _remove_socks_proxy(self):
        """Elimina el proxy seleccionado de la cadena."""
        current = self.socks_chain_list.currentRow()
        if current >= 0:
            self.socks_chain_list.takeItem(current)

    def _save_bridge_config(self):
        """Guarda la configuración de puente actual."""
        if not self._current_bridge_config:
            QMessageBox.warning(self, "Advertencia", "No hay configuración seleccionada.")
            return

        config = self._current_bridge_config

        config.name = self.bridge_name.text()
        config.bridge_type = self.bridge_type.currentText()

        # Tor
        config.tor_socks_port = self.tor_socks_port.value()
        config.tor_control_port = self.tor_control_port.value()
        config.tor_bridges_enabled = self.tor_use_bridges.isChecked()
        config.tor_bridge_addresses = [
            addr.strip() for addr in self.tor_bridges_edit.toPlainText().split('\n')
            if addr.strip()
        ]

        # SSH
        config.ssh_host = self.ssh_host.text()
        config.ssh_port = self.ssh_port.value()
        config.ssh_username = self.ssh_username.text()
        config.ssh_key_path = self.ssh_key_path.text()
        config.ssh_dynamic_port = self.ssh_dynamic_port.value()

        # SOCKS Chain
        config.socks_chain = []
        for i in range(self.socks_chain_list.count()):
            item = self.socks_chain_list.item(i)
            parts = item.text().split(':')
            if len(parts) == 2:
                config.socks_chain.append({
                    'host': parts[0],
                    'port': int(parts[1])
                })

        # Opciones
        config.auto_start = self.bridge_auto_start.isChecked()
        config.start_before_vpn = self.bridge_before_vpn.isChecked()

        manager = self._get_vpn_manager()
        manager.update_bridge_config(config)

        self._load_configs()
        self._log_message("Configuración de puente guardada")

    def _start_bridge(self):
        """Inicia el puente seleccionado."""
        if not self._current_bridge_config:
            QMessageBox.warning(self, "Advertencia", "Seleccione una configuración de puente.")
            return

        import asyncio

        manager = self._get_vpn_manager()

        self.bridge_start_btn.setEnabled(False)
        self._log_message("Iniciando puente...")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(
                manager.start_bridge(self._current_bridge_config.config_id)
            )

            if success:
                self.bridge_start_btn.setEnabled(False)
                self.bridge_stop_btn.setEnabled(True)
                self._log_message("✅ Puente iniciado")
                self.bridge_started.emit(self._current_bridge_config.config_id)
            else:
                self.bridge_start_btn.setEnabled(True)
                self._log_message("❌ Error iniciando puente")
        finally:
            loop.close()

    def _stop_bridge(self):
        """Detiene el puente activo."""
        import asyncio

        manager = self._get_vpn_manager()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(manager.stop_bridge())
        finally:
            loop.close()

        self.bridge_start_btn.setEnabled(True)
        self.bridge_stop_btn.setEnabled(False)
        self._log_message("Puente detenido")
        self.bridge_stopped.emit()

    # ==========================================
    # Utilidades
    # ==========================================

    def _browse_file(self, line_edit: QLineEdit, filter_str: str):
        """Abre un diálogo para seleccionar archivo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo",
            "", filter_str
        )
        if file_path:
            line_edit.setText(file_path)

    def _update_status_display(self):
        """Actualiza la visualización de estado."""
        manager = self._get_vpn_manager()

        # Estado VPN
        vpn_status = manager.get_vpn_status()
        if vpn_status:
            self.vpn_status_label.setText(vpn_status.status.value.upper())
            self.vpn_ip_label.setText(vpn_status.assigned_ip or "-")
            self.vpn_server_label.setText(vpn_status.server_ip or "-")
            self.vpn_protocol_label.setText(vpn_status.protocol or "-")

            if vpn_status.connected_since:
                from datetime import datetime
                delta = datetime.now() - vpn_status.connected_since
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.vpn_uptime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            self.vpn_latency_label.setText(f"{vpn_status.current_latency_ms:.0f} ms")
            self.bytes_sent_label.setText(self._format_bytes(vpn_status.bytes_sent))
            self.bytes_received_label.setText(self._format_bytes(vpn_status.bytes_received))

            # Colores según estado
            if vpn_status.status.value == "connected":
                self.vpn_status_label.setStyleSheet("color: #16825d;")
            elif vpn_status.status.value == "error":
                self.vpn_status_label.setStyleSheet("color: #c42b1c;")
            else:
                self.vpn_status_label.setStyleSheet("")
        else:
            self.vpn_status_label.setText("Desconectado")
            self.vpn_status_label.setStyleSheet("")

        # Estado Puente
        proxy_config = manager.get_active_proxy_config()
        if proxy_config:
            self.bridge_status_label.setText("ACTIVO")
            self.bridge_status_label.setStyleSheet("color: #16825d;")
            self.bridge_proxy_label.setText(proxy_config.get('server', '-'))
        else:
            self.bridge_status_label.setText("Inactivo")
            self.bridge_status_label.setStyleSheet("")
            self.bridge_proxy_label.setText("-")

    def _format_bytes(self, bytes_val: int) -> str:
        """Formatea bytes a unidades legibles."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} TB"

    def _log_message(self, message: str):
        """Agrega un mensaje al log de conexión."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.connection_log.append(f"[{timestamp}] {message}")

    def _check_system_availability(self):
        """Verifica la disponibilidad de protocolos en el sistema."""
        manager = self._get_vpn_manager()

        vpn_protocols = manager.get_available_protocols()
        bridge_types = manager.get_available_bridges()

        text = "Protocolos VPN disponibles:\n"
        if vpn_protocols:
            for p in vpn_protocols:
                text += f"  ✅ {p}\n"
        else:
            text += "  ❌ Ninguno detectado\n"

        text += "\nTipos de puente disponibles:\n"
        for b in bridge_types:
            text += f"  ✅ {b}\n"

        self.available_protocols_label.setText(text)

    def _import_all_configs(self):
        """Importa todas las configuraciones desde un archivo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Configuraciones",
            "", "Archivos JSON (*.json)"
        )

        if file_path:
            # TODO: Implementar importación
            QMessageBox.information(self, "Info", "Funcionalidad en desarrollo.")

    def _export_all_configs(self):
        """Exporta todas las configuraciones a un archivo."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Configuraciones",
            "vpn_bridge_configs.json", "Archivos JSON (*.json)"
        )

        if file_path:
            manager = self._get_vpn_manager()
            if manager.export_configs(Path(file_path)):
                QMessageBox.information(self, "Éxito", "Configuraciones exportadas.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo exportar.")

    # ==========================================
    # API Pública
    # ==========================================

    def get_active_proxy_for_session(self) -> Optional[dict]:
        """Obtiene la configuración de proxy activa para usar en sesiones.

        Returns:
            Diccionario con configuración de proxy o None.
        """
        manager = self._get_vpn_manager()

        # Primero verificar puente (Tor, SOCKS chain)
        proxy_config = manager.get_active_proxy_config()
        if proxy_config:
            return proxy_config

        # Si hay VPN conectado, no se necesita proxy adicional
        # (el tráfico ya pasa por VPN)
        if manager.is_vpn_connected():
            return None

        return None

    def is_secure_connection_active(self) -> bool:
        """Verifica si hay una conexión segura activa (VPN o puente)."""
        manager = self._get_vpn_manager()
        return manager.is_vpn_connected() or manager.get_active_proxy_config() is not None
