"""
Pestaña de configuración de proxy.

Diseñado exclusivamente para Windows.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QCheckBox, QLineEdit, QListWidget, QPushButton
)


def create_proxy_tab(parent) -> QWidget:
    """
    Crear la pestaña de configuración de proxy.
    
    Args:
        parent: Ventana padre para almacenar referencias a widgets.
        
    Returns:
        Widget de la pestaña configurado.
    """
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Configuración de Proxy Individual
    single_group = QGroupBox("Proxy de Sesión")
    single_layout = QFormLayout(single_group)
    
    parent.proxy_enabled = QCheckBox("Habilitar Proxy")
    single_layout.addRow(parent.proxy_enabled)
    
    parent.proxy_type = QComboBox()
    parent.proxy_type.addItems(["http", "https", "socks5"])
    single_layout.addRow("Tipo:", parent.proxy_type)
    
    parent.proxy_server = QLineEdit()
    parent.proxy_server.setPlaceholderText("proxy.ejemplo.com")
    single_layout.addRow("Servidor:", parent.proxy_server)
    
    parent.proxy_port = QSpinBox()
    parent.proxy_port.setRange(1, 65535)
    parent.proxy_port.setValue(8080)
    single_layout.addRow("Puerto:", parent.proxy_port)
    
    parent.proxy_user = QLineEdit()
    parent.proxy_user.setPlaceholderText("usuario (opcional)")
    single_layout.addRow("Usuario:", parent.proxy_user)
    
    parent.proxy_pass = QLineEdit()
    parent.proxy_pass.setPlaceholderText("contraseña (opcional)")
    parent.proxy_pass.setEchoMode(QLineEdit.EchoMode.Password)
    single_layout.addRow("Contraseña:", parent.proxy_pass)
    
    layout.addWidget(single_group)
    
    # Pool de Proxies
    pool_group = QGroupBox("Pool de Proxies")
    pool_layout = QVBoxLayout(pool_group)
    
    parent.proxy_pool_list = QListWidget()
    parent.proxy_pool_list.setMaximumHeight(150)
    pool_layout.addWidget(parent.proxy_pool_list)
    
    pool_btn_layout = QHBoxLayout()
    
    add_proxy_btn = QPushButton("Agregar")
    add_proxy_btn.clicked.connect(parent._add_proxy_to_pool)
    pool_btn_layout.addWidget(add_proxy_btn)
    
    remove_proxy_btn = QPushButton("Eliminar")
    remove_proxy_btn.clicked.connect(parent._remove_proxy_from_pool)
    pool_btn_layout.addWidget(remove_proxy_btn)
    
    import_proxy_btn = QPushButton("Importar...")
    import_proxy_btn.clicked.connect(parent._import_proxies)
    pool_btn_layout.addWidget(import_proxy_btn)
    
    validate_proxy_btn = QPushButton("Validar Todos")
    validate_proxy_btn.clicked.connect(parent._validate_proxy_pool)
    pool_btn_layout.addWidget(validate_proxy_btn)
    
    pool_layout.addLayout(pool_btn_layout)
    
    layout.addWidget(pool_group)
    
    # Configuración de Rotación
    rotation_group = QGroupBox("Configuración de Rotación")
    rotation_layout = QFormLayout(rotation_group)
    
    parent.rotation_interval = QSpinBox()
    parent.rotation_interval.setRange(1, 100)
    parent.rotation_interval.setValue(10)
    parent.rotation_interval.setSuffix(" solicitudes")
    rotation_layout.addRow("Rotar Cada:", parent.rotation_interval)
    
    parent.rotation_strategy = QComboBox()
    parent.rotation_strategy.addItems(["Round Robin", "Aleatorio", "Mejor Rendimiento"])
    rotation_layout.addRow("Estrategia:", parent.rotation_strategy)
    
    parent.validate_before_use = QCheckBox("Validar Proxy Antes de Usar")
    parent.validate_before_use.setChecked(True)
    rotation_layout.addRow(parent.validate_before_use)
    
    parent.auto_deactivate_failed = QCheckBox("Desactivar Automáticamente Proxies Fallidos")
    parent.auto_deactivate_failed.setChecked(True)
    rotation_layout.addRow(parent.auto_deactivate_failed)
    
    layout.addWidget(rotation_group)
    
    layout.addStretch()
    
    return tab
