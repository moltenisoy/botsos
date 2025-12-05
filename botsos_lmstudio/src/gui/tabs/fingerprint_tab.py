"""
Pestaña de configuración de huella digital.

Diseñado exclusivamente para Windows.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QCheckBox, QLineEdit, QLabel
)


def create_fingerprint_tab(parent, fingerprint_manager) -> QWidget:
    """
    Crear la pestaña de configuración de huella digital/dispositivo.
    
    Args:
        parent: Ventana padre para almacenar referencias a widgets.
        fingerprint_manager: Administrador de huellas digitales.
        
    Returns:
        Widget de la pestaña configurado.
    """
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Preset de Dispositivo
    preset_group = QGroupBox("Preset de Dispositivo")
    preset_layout = QFormLayout(preset_group)
    
    parent.device_preset = QComboBox()
    preset_names = fingerprint_manager.get_preset_names()
    for name in preset_names:
        preset = fingerprint_manager.get_preset(name)
        display_name = preset.get("name", name) if preset else name
        parent.device_preset.addItem(display_name, name)
    parent.device_preset.currentIndexChanged.connect(parent._on_device_preset_changed)
    preset_layout.addRow("Preset:", parent.device_preset)
    
    parent.randomize_on_start = QCheckBox("Aleatorizar al iniciar sesión")
    parent.randomize_on_start.setChecked(True)
    preset_layout.addRow(parent.randomize_on_start)
    
    layout.addWidget(preset_group)
    
    # Configuración Personalizada
    custom_group = QGroupBox("Configuración Personalizada")
    custom_layout = QFormLayout(custom_group)
    
    parent.user_agent_edit = QLineEdit()
    parent.user_agent_edit.setPlaceholderText("Auto-generado desde preset")
    custom_layout.addRow("User-Agent:", parent.user_agent_edit)
    
    viewport_layout = QHBoxLayout()
    parent.viewport_width = QSpinBox()
    parent.viewport_width.setRange(320, 3840)
    parent.viewport_width.setValue(1920)
    viewport_layout.addWidget(parent.viewport_width)
    viewport_layout.addWidget(QLabel("x"))
    parent.viewport_height = QSpinBox()
    parent.viewport_height.setRange(240, 2160)
    parent.viewport_height.setValue(1080)
    viewport_layout.addWidget(parent.viewport_height)
    custom_layout.addRow("Viewport:", viewport_layout)
    
    parent.hardware_concurrency = QSpinBox()
    parent.hardware_concurrency.setRange(1, 64)
    parent.hardware_concurrency.setValue(8)
    custom_layout.addRow("Núcleos de CPU:", parent.hardware_concurrency)
    
    parent.device_memory = QSpinBox()
    parent.device_memory.setRange(1, 128)
    parent.device_memory.setValue(8)
    parent.device_memory.setSuffix(" GB")
    custom_layout.addRow("Memoria del Dispositivo:", parent.device_memory)
    
    parent.timezone_combo = QComboBox()
    parent.timezone_combo.addItems([
        "America/Mexico_City",
        "America/Bogota",
        "America/Lima",
        "America/Santiago",
        "America/Buenos_Aires",
        "America/New_York",
        "America/Los_Angeles",
        "Europe/Madrid",
        "UTC"
    ])
    custom_layout.addRow("Zona Horaria:", parent.timezone_combo)
    
    layout.addWidget(custom_group)
    
    # Opciones de Suplantación
    spoof_group = QGroupBox("Opciones de Suplantación")
    spoof_layout = QVBoxLayout(spoof_group)
    
    parent.canvas_noise = QCheckBox("Inyección de Ruido en Canvas")
    parent.canvas_noise.setChecked(True)
    spoof_layout.addWidget(parent.canvas_noise)
    
    noise_layout = QHBoxLayout()
    noise_layout.addWidget(QLabel("Nivel de Ruido:"))
    parent.canvas_noise_level = QSpinBox()
    parent.canvas_noise_level.setRange(0, 10)
    parent.canvas_noise_level.setValue(5)
    noise_layout.addWidget(parent.canvas_noise_level)
    noise_layout.addStretch()
    spoof_layout.addLayout(noise_layout)
    
    parent.webrtc_protection = QCheckBox("Protección WebRTC")
    parent.webrtc_protection.setChecked(True)
    spoof_layout.addWidget(parent.webrtc_protection)
    
    parent.webgl_spoofing = QCheckBox("Suplantación de WebGL")
    parent.webgl_spoofing.setChecked(True)
    spoof_layout.addWidget(parent.webgl_spoofing)
    
    parent.audio_spoofing = QCheckBox("Suplantación de Contexto de Audio")
    parent.audio_spoofing.setChecked(True)
    spoof_layout.addWidget(parent.audio_spoofing)
    
    parent.font_spoofing = QCheckBox("Suplantación de Fuentes")
    parent.font_spoofing.setChecked(True)
    spoof_layout.addWidget(parent.font_spoofing)
    
    layout.addWidget(spoof_group)
    
    layout.addStretch()
    return tab
