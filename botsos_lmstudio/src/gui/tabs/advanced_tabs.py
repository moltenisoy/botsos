"""
Pestañas de configuración avanzada.

Incluye: suplantación avanzada, simulación de comportamiento,
CAPTCHA, contingencia, comportamiento avanzado, y ocultación del sistema.

Diseñado exclusivamente para Windows.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit, 
    QTextEdit, QSlider, QLabel
)
from PyQt6.QtCore import Qt


def create_advanced_spoof_tab(parent) -> QWidget:
    """Crear la pestaña de suplantación avanzada."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Configuración TLS/JA3
    tls_group = QGroupBox("Huella Digital TLS/JA3")
    tls_layout = QFormLayout(tls_group)
    
    parent.tls_profile = QComboBox()
    parent.tls_profile.addItems(["chrome_120", "chrome_110", "firefox_121", "safari_17", "edge_120"])
    tls_layout.addRow("Perfil TLS:", parent.tls_profile)
    
    parent.client_hints_enabled = QCheckBox("Habilitar Client Hints")
    parent.client_hints_enabled.setChecked(True)
    tls_layout.addRow(parent.client_hints_enabled)
    
    layout.addWidget(tls_group)
    
    # Configuración WebGPU
    webgpu_group = QGroupBox("Suplantación de WebGPU")
    webgpu_layout = QFormLayout(webgpu_group)
    
    parent.webgpu_enabled = QCheckBox("Habilitar Suplantación de WebGPU")
    parent.webgpu_enabled.setChecked(True)
    webgpu_layout.addRow(parent.webgpu_enabled)
    
    parent.webgpu_vendor = QLineEdit()
    parent.webgpu_vendor.setText("Google Inc.")
    webgpu_layout.addRow("Fabricante de GPU:", parent.webgpu_vendor)
    
    parent.webgpu_architecture = QComboBox()
    parent.webgpu_architecture.addItems(["x86_64", "arm64", "x86"])
    webgpu_layout.addRow("Arquitectura:", parent.webgpu_architecture)
    
    layout.addWidget(webgpu_group)
    
    # Canvas/WebGL Avanzado
    canvas_group = QGroupBox("Canvas y WebGL Avanzado")
    canvas_layout = QFormLayout(canvas_group)
    
    noise_layout = QHBoxLayout()
    noise_layout.addWidget(QLabel("Ruido de Canvas (0-10):"))
    parent.adv_canvas_noise = QSlider(Qt.Orientation.Horizontal)
    parent.adv_canvas_noise.setRange(0, 10)
    parent.adv_canvas_noise.setValue(5)
    parent.adv_canvas_noise_label = QLabel("5")
    parent.adv_canvas_noise.valueChanged.connect(
        lambda v: parent.adv_canvas_noise_label.setText(str(v))
    )
    noise_layout.addWidget(parent.adv_canvas_noise)
    noise_layout.addWidget(parent.adv_canvas_noise_label)
    canvas_layout.addRow(noise_layout)
    
    parent.webgl_vendor_override = QLineEdit()
    parent.webgl_vendor_override.setPlaceholderText("Dejar vacío para valor del preset")
    canvas_layout.addRow("Sobrescribir Fabricante WebGL:", parent.webgl_vendor_override)
    
    parent.webgl_renderer_override = QLineEdit()
    parent.webgl_renderer_override.setPlaceholderText("Dejar vacío para valor del preset")
    canvas_layout.addRow("Sobrescribir Renderizador WebGL:", parent.webgl_renderer_override)
    
    layout.addWidget(canvas_group)
    
    # Suplantación de Fuentes
    font_group = QGroupBox("Suplantación de Fuentes")
    font_layout = QVBoxLayout(font_group)
    
    parent.custom_fonts_edit = QTextEdit()
    parent.custom_fonts_edit.setMaximumHeight(100)
    parent.custom_fonts_edit.setPlaceholderText("Una fuente por línea")
    parent.custom_fonts_edit.setText("Arial\nHelvetica\nTimes New Roman\nGeorgia\nVerdana\nCourier New")
    font_layout.addWidget(parent.custom_fonts_edit)
    
    layout.addWidget(font_group)
    
    layout.addStretch()
    return tab


def create_behavior_simulation_tab(parent) -> QWidget:
    """Crear la pestaña de simulación de comportamiento."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Simulación del Ratón
    mouse_group = QGroupBox("Simulación del Ratón")
    mouse_layout = QFormLayout(mouse_group)
    
    parent.mouse_jitter_enabled = QCheckBox("Habilitar Movimiento Aleatorio del Ratón")
    parent.mouse_jitter_enabled.setChecked(True)
    mouse_layout.addRow(parent.mouse_jitter_enabled)
    
    parent.mouse_jitter_px = QSpinBox()
    parent.mouse_jitter_px.setRange(1, 20)
    parent.mouse_jitter_px.setValue(5)
    parent.mouse_jitter_px.setSuffix(" px")
    mouse_layout.addRow("Cantidad de Movimiento:", parent.mouse_jitter_px)
    
    parent.enable_random_hover = QCheckBox("Habilitar Hover Aleatorio")
    parent.enable_random_hover.setChecked(True)
    mouse_layout.addRow(parent.enable_random_hover)
    
    layout.addWidget(mouse_group)
    
    # Simulación de Tiempos
    timing_group = QGroupBox("Simulación de Tiempos")
    timing_layout = QFormLayout(timing_group)
    
    parent.idle_time_min = QDoubleSpinBox()
    parent.idle_time_min.setRange(0.5, 60.0)
    parent.idle_time_min.setValue(5.0)
    parent.idle_time_min.setSuffix(" seg")
    timing_layout.addRow("Tiempo Inactivo Mínimo:", parent.idle_time_min)
    
    parent.idle_time_max = QDoubleSpinBox()
    parent.idle_time_max.setRange(1.0, 120.0)
    parent.idle_time_max.setValue(15.0)
    parent.idle_time_max.setSuffix(" seg")
    timing_layout.addRow("Tiempo Inactivo Máximo:", parent.idle_time_max)
    
    parent.random_action_prob = QSpinBox()
    parent.random_action_prob.setRange(0, 50)
    parent.random_action_prob.setValue(10)
    parent.random_action_prob.setSuffix(" %")
    timing_layout.addRow("Probabilidad de Acción Aleatoria:", parent.random_action_prob)
    
    layout.addWidget(timing_group)
    
    # Simulación de Desplazamiento
    scroll_group = QGroupBox("Simulación de Desplazamiento")
    scroll_layout = QFormLayout(scroll_group)
    
    parent.scroll_enabled = QCheckBox("Habilitar Simulación de Desplazamiento")
    parent.scroll_enabled.setChecked(True)
    scroll_layout.addRow(parent.scroll_enabled)
    
    parent.enable_random_scroll = QCheckBox("Habilitar Desplazamiento Aleatorio")
    parent.enable_random_scroll.setChecked(True)
    scroll_layout.addRow(parent.enable_random_scroll)
    
    parent.scroll_delta_min = QSpinBox()
    parent.scroll_delta_min.setRange(10, 500)
    parent.scroll_delta_min.setValue(50)
    parent.scroll_delta_min.setSuffix(" px")
    scroll_layout.addRow("Delta Mínimo:", parent.scroll_delta_min)
    
    parent.scroll_delta_max = QSpinBox()
    parent.scroll_delta_max.setRange(50, 1000)
    parent.scroll_delta_max.setValue(300)
    parent.scroll_delta_max.setSuffix(" px")
    scroll_layout.addRow("Delta Máximo:", parent.scroll_delta_max)
    
    layout.addWidget(scroll_group)
    
    # Simulación de Escritura
    typing_group = QGroupBox("Simulación de Escritura")
    typing_layout = QFormLayout(typing_group)
    
    parent.typing_speed_min = QSpinBox()
    parent.typing_speed_min.setRange(10, 300)
    parent.typing_speed_min.setValue(50)
    parent.typing_speed_min.setSuffix(" ms")
    typing_layout.addRow("Retraso Mínimo:", parent.typing_speed_min)
    
    parent.typing_speed_max = QSpinBox()
    parent.typing_speed_max.setRange(50, 500)
    parent.typing_speed_max.setValue(200)
    parent.typing_speed_max.setSuffix(" ms")
    typing_layout.addRow("Retraso Máximo:", parent.typing_speed_max)
    
    parent.typing_mistake_rate = QSpinBox()
    parent.typing_mistake_rate.setRange(0, 10)
    parent.typing_mistake_rate.setValue(2)
    parent.typing_mistake_rate.setSuffix(" %")
    typing_layout.addRow("Tasa de Errores:", parent.typing_mistake_rate)
    
    layout.addWidget(typing_group)
    
    layout.addStretch()
    return tab


def create_captcha_tab(parent) -> QWidget:
    """Crear la pestaña de configuración de CAPTCHA."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Configuración de CAPTCHA
    captcha_group = QGroupBox("Resolución de CAPTCHA")
    captcha_layout = QFormLayout(captcha_group)
    
    parent.captcha_enabled = QCheckBox("Habilitar Resolución Automática")
    captcha_layout.addRow(parent.captcha_enabled)
    
    parent.captcha_provider = QComboBox()
    parent.captcha_provider.addItems(["2captcha", "anticaptcha", "capsolver"])
    captcha_layout.addRow("Proveedor:", parent.captcha_provider)
    
    parent.captcha_api_key = QLineEdit()
    parent.captcha_api_key.setEchoMode(QLineEdit.EchoMode.Password)
    parent.captcha_api_key.setPlaceholderText("Clave API")
    captcha_layout.addRow("Clave API:", parent.captcha_api_key)
    
    layout.addWidget(captcha_group)
    
    # Tipos de CAPTCHA
    types_group = QGroupBox("Tipos Soportados")
    types_layout = QVBoxLayout(types_group)
    
    parent.captcha_recaptcha_v2 = QCheckBox("reCAPTCHA v2")
    parent.captcha_recaptcha_v2.setChecked(True)
    types_layout.addWidget(parent.captcha_recaptcha_v2)
    
    parent.captcha_recaptcha_v3 = QCheckBox("reCAPTCHA v3")
    parent.captcha_recaptcha_v3.setChecked(True)
    types_layout.addWidget(parent.captcha_recaptcha_v3)
    
    parent.captcha_hcaptcha = QCheckBox("hCaptcha")
    parent.captcha_hcaptcha.setChecked(True)
    types_layout.addWidget(parent.captcha_hcaptcha)
    
    layout.addWidget(types_group)
    
    # Opciones
    options_group = QGroupBox("Opciones")
    options_layout = QFormLayout(options_group)
    
    parent.captcha_timeout = QSpinBox()
    parent.captcha_timeout.setRange(30, 300)
    parent.captcha_timeout.setValue(120)
    parent.captcha_timeout.setSuffix(" seg")
    options_layout.addRow("Tiempo de Espera:", parent.captcha_timeout)
    
    parent.captcha_max_retries = QSpinBox()
    parent.captcha_max_retries.setRange(1, 10)
    parent.captcha_max_retries.setValue(3)
    options_layout.addRow("Máximo Reintentos:", parent.captcha_max_retries)
    
    layout.addWidget(options_group)
    
    # Reintentos
    retry_group = QGroupBox("Configuración de Reintentos")
    retry_layout = QFormLayout(retry_group)
    
    parent.max_retries = QSpinBox()
    parent.max_retries.setRange(0, 10)
    parent.max_retries.setValue(3)
    retry_layout.addRow("Máximo Reintentos:", parent.max_retries)
    
    parent.retry_delay = QDoubleSpinBox()
    parent.retry_delay.setRange(0.5, 30.0)
    parent.retry_delay.setValue(1.0)
    parent.retry_delay.setSuffix(" seg")
    retry_layout.addRow("Retraso Base:", parent.retry_delay)
    
    parent.exponential_backoff = QCheckBox("Retroceso Exponencial")
    parent.exponential_backoff.setChecked(True)
    retry_layout.addRow(parent.exponential_backoff)
    
    layout.addWidget(retry_group)
    
    # Modo Híbrido
    hybrid_group = QGroupBox("Solucionador Híbrido")
    hybrid_layout = QFormLayout(hybrid_group)
    
    parent.captcha_hybrid_mode = QCheckBox("Modo Híbrido (IA primero)")
    parent.captcha_hybrid_mode.setChecked(True)
    hybrid_layout.addRow(parent.captcha_hybrid_mode)
    
    parent.captcha_secondary_provider = QComboBox()
    parent.captcha_secondary_provider.addItems(["capsolver", "anticaptcha", "2captcha"])
    hybrid_layout.addRow("Proveedor de Respaldo:", parent.captcha_secondary_provider)
    
    layout.addWidget(hybrid_group)
    
    layout.addStretch()
    return tab


def create_contingency_tab(parent) -> QWidget:
    """Crear la pestaña de contingencia."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Umbrales de Evicción
    eviction_group = QGroupBox("Umbrales de Evicción")
    eviction_layout = QFormLayout(eviction_group)
    
    parent.block_rate_threshold = QDoubleSpinBox()
    parent.block_rate_threshold.setRange(0.01, 0.50)
    parent.block_rate_threshold.setValue(0.10)
    parent.block_rate_threshold.setSingleStep(0.01)
    eviction_layout.addRow("Umbral de Bloqueo:", parent.block_rate_threshold)
    
    parent.consecutive_failure_threshold = QSpinBox()
    parent.consecutive_failure_threshold.setRange(1, 10)
    parent.consecutive_failure_threshold.setValue(3)
    eviction_layout.addRow("Fallas Consecutivas:", parent.consecutive_failure_threshold)
    
    layout.addWidget(eviction_group)
    
    # Enfriamiento
    cooldown_group = QGroupBox("Configuración de Enfriamiento")
    cooldown_layout = QFormLayout(cooldown_group)
    
    parent.cool_down_min = QSpinBox()
    parent.cool_down_min.setRange(60, 1800)
    parent.cool_down_min.setValue(300)
    parent.cool_down_min.setSuffix(" seg")
    cooldown_layout.addRow("Mínimo:", parent.cool_down_min)
    
    parent.cool_down_max = QSpinBox()
    parent.cool_down_max.setRange(300, 3600)
    parent.cool_down_max.setValue(1200)
    parent.cool_down_max.setSuffix(" seg")
    cooldown_layout.addRow("Máximo:", parent.cool_down_max)
    
    layout.addWidget(cooldown_group)
    
    # Recuperación
    recovery_group = QGroupBox("Estrategia de Recuperación")
    recovery_layout = QFormLayout(recovery_group)
    
    parent.ban_recovery_strategy = QComboBox()
    parent.ban_recovery_strategy.addItems(["mobile_fallback", "throttle", "rotate_all"])
    recovery_layout.addRow("Estrategia:", parent.ban_recovery_strategy)
    
    parent.enable_dynamic_throttling = QCheckBox("Limitación Dinámica")
    parent.enable_dynamic_throttling.setChecked(True)
    recovery_layout.addRow(parent.enable_dynamic_throttling)
    
    layout.addWidget(recovery_group)
    
    # Sesiones Persistentes
    sticky_group = QGroupBox("Sesiones Persistentes")
    sticky_layout = QFormLayout(sticky_group)
    
    parent.sticky_session_duration = QSpinBox()
    parent.sticky_session_duration.setRange(60, 3600)
    parent.sticky_session_duration.setValue(600)
    parent.sticky_session_duration.setSuffix(" seg")
    sticky_layout.addRow("Duración:", parent.sticky_session_duration)
    
    parent.enable_session_persistence = QCheckBox("Habilitar Persistencia")
    parent.enable_session_persistence.setChecked(True)
    sticky_layout.addRow(parent.enable_session_persistence)
    
    layout.addWidget(sticky_group)
    
    layout.addStretch()
    return tab


def create_advanced_behavior_tab(parent) -> QWidget:
    """Crear la pestaña de comportamiento avanzado."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Huella Polimórfica
    poly_group = QGroupBox("Huella Digital Polimórfica")
    poly_layout = QFormLayout(poly_group)
    
    parent.polymorphic_enabled = QCheckBox("Habilitar")
    parent.polymorphic_enabled.setChecked(True)
    poly_layout.addRow(parent.polymorphic_enabled)
    
    parent.fingerprint_rotation_interval = QSpinBox()
    parent.fingerprint_rotation_interval.setRange(300, 7200)
    parent.fingerprint_rotation_interval.setValue(3600)
    parent.fingerprint_rotation_interval.setSuffix(" seg")
    poly_layout.addRow("Intervalo de Rotación:", parent.fingerprint_rotation_interval)
    
    layout.addWidget(poly_group)
    
    # Entrada a Nivel de SO
    os_group = QGroupBox("Emulación de Entrada")
    os_layout = QFormLayout(os_group)
    
    parent.os_level_input_enabled = QCheckBox("Entrada a Nivel de SO")
    os_layout.addRow(parent.os_level_input_enabled)
    
    layout.addWidget(os_group)
    
    # Emulación Táctil
    touch_group = QGroupBox("Emulación Táctil")
    touch_layout = QFormLayout(touch_group)
    
    parent.touch_emulation_enabled = QCheckBox("Habilitar")
    touch_layout.addRow(parent.touch_emulation_enabled)
    
    parent.touch_pressure_variation = QDoubleSpinBox()
    parent.touch_pressure_variation.setRange(0.0, 0.5)
    parent.touch_pressure_variation.setValue(0.2)
    parent.touch_pressure_variation.setSingleStep(0.05)
    touch_layout.addRow("Variación de Presión:", parent.touch_pressure_variation)
    
    layout.addWidget(touch_group)
    
    # Micro-movimientos
    jitter_group = QGroupBox("Micro-movimientos")
    jitter_layout = QFormLayout(jitter_group)
    
    parent.micro_jitter_enabled = QCheckBox("Habilitar")
    parent.micro_jitter_enabled.setChecked(True)
    jitter_layout.addRow(parent.micro_jitter_enabled)
    
    parent.micro_jitter_amplitude = QSpinBox()
    parent.micro_jitter_amplitude.setRange(1, 10)
    parent.micro_jitter_amplitude.setValue(2)
    parent.micro_jitter_amplitude.setSuffix(" px")
    jitter_layout.addRow("Amplitud:", parent.micro_jitter_amplitude)
    
    layout.addWidget(jitter_group)
    
    # Patrones de Escritura
    typing_group = QGroupBox("Patrones de Escritura")
    typing_layout = QFormLayout(typing_group)
    
    parent.typing_pressure_enabled = QCheckBox("Simulación de Presión")
    typing_layout.addRow(parent.typing_pressure_enabled)
    
    parent.typing_rhythm_variation = QDoubleSpinBox()
    parent.typing_rhythm_variation.setRange(0.0, 0.5)
    parent.typing_rhythm_variation.setValue(0.15)
    parent.typing_rhythm_variation.setSingleStep(0.05)
    typing_layout.addRow("Variación de Ritmo:", parent.typing_rhythm_variation)
    
    layout.addWidget(typing_group)
    
    layout.addStretch()
    return tab


def create_system_hiding_tab(parent) -> QWidget:
    """Crear la pestaña de ocultación del sistema."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Bloqueo CDP
    cdp_group = QGroupBox("Bloqueo de Puerto CDP")
    cdp_layout = QFormLayout(cdp_group)
    
    parent.block_cdp_ports = QCheckBox("Bloquear Puertos CDP")
    parent.block_cdp_ports.setChecked(True)
    cdp_layout.addRow(parent.block_cdp_ports)
    
    parent.cdp_port_default = QSpinBox()
    parent.cdp_port_default.setRange(1, 65535)
    parent.cdp_port_default.setValue(9222)
    cdp_layout.addRow("Puerto CDP:", parent.cdp_port_default)
    
    layout.addWidget(cdp_group)
    
    # Gestión de Red
    loopback_group = QGroupBox("Gestión de Interfaz de Red")
    loopback_layout = QFormLayout(loopback_group)
    
    parent.disable_loopback_services = QCheckBox("Deshabilitar Servicios Loopback")
    loopback_layout.addRow(parent.disable_loopback_services)
    
    layout.addWidget(loopback_group)
    
    # Puertos Efímeros
    port_group = QGroupBox("Aleatorización de Puertos")
    port_layout = QFormLayout(port_group)
    
    parent.randomize_ephemeral_ports = QCheckBox("Aleatorizar Puertos")
    parent.randomize_ephemeral_ports.setChecked(True)
    port_layout.addRow(parent.randomize_ephemeral_ports)
    
    parent.ephemeral_port_min = QSpinBox()
    parent.ephemeral_port_min.setRange(1024, 65535)
    parent.ephemeral_port_min.setValue(49152)
    port_layout.addRow("Puerto Mínimo:", parent.ephemeral_port_min)
    
    parent.ephemeral_port_max = QSpinBox()
    parent.ephemeral_port_max.setRange(1024, 65535)
    parent.ephemeral_port_max.setValue(65535)
    port_layout.addRow("Puerto Máximo:", parent.ephemeral_port_max)
    
    layout.addWidget(port_group)
    
    # WebRTC
    webrtc_group = QGroupBox("Protección WebRTC")
    webrtc_layout = QFormLayout(webrtc_group)
    
    parent.block_webrtc_completely = QCheckBox("Bloquear WebRTC Completamente")
    webrtc_layout.addRow(parent.block_webrtc_completely)
    
    layout.addWidget(webrtc_group)
    
    # MFA
    mfa_group = QGroupBox("Simulación MFA")
    mfa_layout = QFormLayout(mfa_group)
    
    parent.mfa_simulation_enabled = QCheckBox("Habilitar Simulación MFA")
    mfa_layout.addRow(parent.mfa_simulation_enabled)
    
    parent.mfa_method = QComboBox()
    parent.mfa_method.addItems(["none", "email", "sms"])
    mfa_layout.addRow("Método:", parent.mfa_method)
    
    parent.mfa_timeout = QSpinBox()
    parent.mfa_timeout.setRange(30, 300)
    parent.mfa_timeout.setValue(120)
    parent.mfa_timeout.setSuffix(" seg")
    mfa_layout.addRow("Timeout:", parent.mfa_timeout)
    
    layout.addWidget(mfa_group)
    
    layout.addStretch()
    return tab
