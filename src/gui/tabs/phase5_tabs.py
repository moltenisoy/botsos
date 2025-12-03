"""
Pestañas de configuración de Fase 5.

Incluye: escalabilidad, rendimiento, evasión ML, programación,
analíticas, cuentas y registros.

Diseñado exclusivamente para Windows.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit, 
    QTextEdit, QPushButton, QListWidget, QLabel
)


def create_scaling_tab(parent) -> QWidget:
    """Crear la pestaña de escalabilidad/cloud."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Docker
    docker_group = QGroupBox("Docker")
    docker_layout = QFormLayout(docker_group)
    
    parent.docker_enabled = QCheckBox("Habilitar Docker")
    docker_layout.addRow(parent.docker_enabled)
    
    parent.docker_image = QLineEdit()
    parent.docker_image.setText("botsos:latest")
    docker_layout.addRow("Imagen:", parent.docker_image)
    
    parent.docker_network = QComboBox()
    parent.docker_network.addItems(["bridge", "host", "none"])
    docker_layout.addRow("Modo de Red:", parent.docker_network)
    
    layout.addWidget(docker_group)
    
    # AWS
    aws_group = QGroupBox("AWS Cloud")
    aws_layout = QFormLayout(aws_group)
    
    parent.aws_enabled = QCheckBox("Habilitar AWS")
    aws_layout.addRow(parent.aws_enabled)
    
    parent.aws_region = QComboBox()
    parent.aws_region.addItems(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"])
    aws_layout.addRow("Región:", parent.aws_region)
    
    parent.aws_instance_type = QComboBox()
    parent.aws_instance_type.addItems(["t3.medium", "t3.large", "t3.xlarge", "m5.large"])
    aws_layout.addRow("Tipo de Instancia:", parent.aws_instance_type)
    
    parent.aws_ami_id = QLineEdit()
    parent.aws_ami_id.setPlaceholderText("ID de AMI")
    aws_layout.addRow("AMI ID:", parent.aws_ami_id)
    
    layout.addWidget(aws_group)
    
    # Auto-escalado
    scale_group = QGroupBox("Auto-escalado")
    scale_layout = QFormLayout(scale_group)
    
    parent.auto_scale_enabled = QCheckBox("Habilitar Auto-escalado")
    scale_layout.addRow(parent.auto_scale_enabled)
    
    parent.ram_threshold = QSpinBox()
    parent.ram_threshold.setRange(50, 100)
    parent.ram_threshold.setValue(85)
    parent.ram_threshold.setSuffix(" %")
    scale_layout.addRow("Umbral RAM:", parent.ram_threshold)
    
    parent.cpu_threshold = QSpinBox()
    parent.cpu_threshold.setRange(50, 100)
    parent.cpu_threshold.setValue(80)
    parent.cpu_threshold.setSuffix(" %")
    scale_layout.addRow("Umbral CPU:", parent.cpu_threshold)
    
    parent.max_local_sessions = QSpinBox()
    parent.max_local_sessions.setRange(1, 20)
    parent.max_local_sessions.setValue(6)
    scale_layout.addRow("Máx. Sesiones Locales:", parent.max_local_sessions)
    
    parent.max_cloud_sessions = QSpinBox()
    parent.max_cloud_sessions.setRange(1, 100)
    parent.max_cloud_sessions.setValue(50)
    scale_layout.addRow("Máx. Sesiones Cloud:", parent.max_cloud_sessions)
    
    layout.addWidget(scale_group)
    
    layout.addStretch()
    return tab


def create_performance_tab(parent) -> QWidget:
    """Crear la pestaña de rendimiento."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Aceleración GPU
    gpu_group = QGroupBox("Aceleración GPU")
    gpu_layout = QFormLayout(gpu_group)
    
    parent.gpu_acceleration_enabled = QCheckBox("Habilitar")
    gpu_layout.addRow(parent.gpu_acceleration_enabled)
    
    parent.gpu_backend = QComboBox()
    parent.gpu_backend.addItems(["auto", "rocm", "directml"])
    gpu_layout.addRow("Backend:", parent.gpu_backend)
    
    layout.addWidget(gpu_group)
    
    # Procesamiento Async
    async_group = QGroupBox("Procesamiento Async")
    async_layout = QFormLayout(async_group)
    
    parent.async_batch_size = QSpinBox()
    parent.async_batch_size.setRange(1, 20)
    parent.async_batch_size.setValue(4)
    async_layout.addRow("Tamaño de Lote:", parent.async_batch_size)
    
    layout.addWidget(async_group)
    
    # Caché LLM
    cache_group = QGroupBox("Caché LLM")
    cache_layout = QFormLayout(cache_group)
    
    parent.llm_cache_enabled = QCheckBox("Habilitar")
    parent.llm_cache_enabled.setChecked(True)
    cache_layout.addRow(parent.llm_cache_enabled)
    
    parent.llm_cache_size = QSpinBox()
    parent.llm_cache_size.setRange(100, 10000)
    parent.llm_cache_size.setValue(1000)
    cache_layout.addRow("Tamaño Máximo:", parent.llm_cache_size)
    
    layout.addWidget(cache_group)
    
    # Optimización de Memoria
    memory_group = QGroupBox("Optimización de Memoria")
    memory_layout = QFormLayout(memory_group)
    
    parent.memory_optimization_enabled = QCheckBox("Habilitar")
    parent.memory_optimization_enabled.setChecked(True)
    memory_layout.addRow(parent.memory_optimization_enabled)
    
    parent.gc_interval = QSpinBox()
    parent.gc_interval.setRange(30, 300)
    parent.gc_interval.setValue(60)
    parent.gc_interval.setSuffix(" seg")
    memory_layout.addRow("Intervalo GC:", parent.gc_interval)
    
    layout.addWidget(memory_group)
    
    layout.addStretch()
    return tab


def create_ml_evasion_tab(parent) -> QWidget:
    """Crear la pestaña de evasión ML."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Modelo RL
    rl_group = QGroupBox("Aprendizaje por Refuerzo")
    rl_layout = QFormLayout(rl_group)
    
    parent.rl_enabled = QCheckBox("Habilitar RL")
    rl_layout.addRow(parent.rl_enabled)
    
    parent.rl_model_type = QComboBox()
    parent.rl_model_type.addItems(["simple_qlearning", "dqn"])
    rl_layout.addRow("Tipo de Modelo:", parent.rl_model_type)
    
    parent.rl_learning_rate = QDoubleSpinBox()
    parent.rl_learning_rate.setRange(0.001, 0.1)
    parent.rl_learning_rate.setValue(0.01)
    parent.rl_learning_rate.setSingleStep(0.001)
    parent.rl_learning_rate.setDecimals(3)
    rl_layout.addRow("Tasa de Aprendizaje:", parent.rl_learning_rate)
    
    layout.addWidget(rl_group)
    
    # Adaptación
    adapt_group = QGroupBox("Adaptación de Comportamiento")
    adapt_layout = QFormLayout(adapt_group)
    
    parent.adaptive_jitter_enabled = QCheckBox("Jitter Adaptativo")
    parent.adaptive_jitter_enabled.setChecked(True)
    adapt_layout.addRow(parent.adaptive_jitter_enabled)
    
    parent.adaptive_delay_enabled = QCheckBox("Retraso Adaptativo")
    parent.adaptive_delay_enabled.setChecked(True)
    adapt_layout.addRow(parent.adaptive_delay_enabled)
    
    parent.feedback_loop_enabled = QCheckBox("Bucle de Retroalimentación")
    parent.feedback_loop_enabled.setChecked(True)
    adapt_layout.addRow(parent.feedback_loop_enabled)
    
    layout.addWidget(adapt_group)
    
    # Biométrico
    bio_group = QGroupBox("Suplantación Biométrica")
    bio_layout = QFormLayout(bio_group)
    
    parent.biometric_spoof_enabled = QCheckBox("Habilitar")
    bio_layout.addRow(parent.biometric_spoof_enabled)
    
    parent.eye_track_simulation = QCheckBox("Simulación de Seguimiento Ocular")
    bio_layout.addRow(parent.eye_track_simulation)
    
    layout.addWidget(bio_group)
    
    # ML Proxy
    ml_proxy_group = QGroupBox("Selección de Proxy con ML")
    ml_proxy_layout = QFormLayout(ml_proxy_group)
    
    parent.ml_proxy_enabled = QCheckBox("Habilitar")
    ml_proxy_layout.addRow(parent.ml_proxy_enabled)
    
    parent.ml_proxy_model = QComboBox()
    parent.ml_proxy_model.addItems(["random_forest", "gradient_boosting"])
    ml_proxy_layout.addRow("Modelo:", parent.ml_proxy_model)
    
    parent.train_ml_proxy_btn = QPushButton("Entrenar Modelo")
    parent.train_ml_proxy_btn.clicked.connect(parent._train_ml_proxy_model)
    ml_proxy_layout.addRow(parent.train_ml_proxy_btn)
    
    layout.addWidget(ml_proxy_group)
    
    layout.addStretch()
    return tab


def create_scheduling_tab(parent) -> QWidget:
    """Crear la pestaña de programación."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Programación
    sched_group = QGroupBox("Programación de Tareas")
    sched_layout = QFormLayout(sched_group)
    
    parent.scheduling_enabled = QCheckBox("Habilitar Programación")
    sched_layout.addRow(parent.scheduling_enabled)
    
    parent.cron_expression = QLineEdit()
    parent.cron_expression.setPlaceholderText("0 * * * *")
    sched_layout.addRow("Expresión Cron:", parent.cron_expression)
    
    layout.addWidget(sched_group)
    
    # Ventana de Ejecución
    window_group = QGroupBox("Ventana de Ejecución")
    window_layout = QFormLayout(window_group)
    
    parent.schedule_start_time = QLineEdit()
    parent.schedule_start_time.setPlaceholderText("08:00")
    window_layout.addRow("Hora de Inicio:", parent.schedule_start_time)
    
    parent.schedule_end_time = QLineEdit()
    parent.schedule_end_time.setPlaceholderText("22:00")
    window_layout.addRow("Hora de Fin:", parent.schedule_end_time)
    
    layout.addWidget(window_group)
    
    # Cola de Sesiones
    queue_group = QGroupBox("Cola de Sesiones")
    queue_layout = QFormLayout(queue_group)
    
    parent.queue_enabled = QCheckBox("Habilitar Cola")
    parent.queue_enabled.setChecked(True)
    queue_layout.addRow(parent.queue_enabled)
    
    parent.max_queue_size = QSpinBox()
    parent.max_queue_size.setRange(10, 500)
    parent.max_queue_size.setValue(100)
    queue_layout.addRow("Tamaño Máximo:", parent.max_queue_size)
    
    layout.addWidget(queue_group)
    
    # Reinicio Automático
    restart_group = QGroupBox("Reinicio Automático")
    restart_layout = QFormLayout(restart_group)
    
    parent.auto_restart_enabled = QCheckBox("Reiniciar Sesiones Fallidas")
    parent.auto_restart_enabled.setChecked(True)
    restart_layout.addRow(parent.auto_restart_enabled)
    
    parent.restart_delay = QSpinBox()
    parent.restart_delay.setRange(10, 300)
    parent.restart_delay.setValue(60)
    parent.restart_delay.setSuffix(" seg")
    restart_layout.addRow("Retraso:", parent.restart_delay)
    
    layout.addWidget(restart_group)
    
    layout.addStretch()
    return tab


def create_analytics_tab(parent) -> QWidget:
    """Crear la pestaña de analíticas."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Prometheus
    prom_group = QGroupBox("Servidor Prometheus")
    prom_layout = QFormLayout(prom_group)
    
    parent.prometheus_enabled = QCheckBox("Habilitar")
    prom_layout.addRow(parent.prometheus_enabled)
    
    parent.prometheus_port = QSpinBox()
    parent.prometheus_port.setRange(1024, 65535)
    parent.prometheus_port.setValue(9090)
    prom_layout.addRow("Puerto:", parent.prometheus_port)
    
    parent.start_prometheus_btn = QPushButton("Iniciar Servidor")
    parent.start_prometheus_btn.clicked.connect(parent._start_prometheus_server)
    prom_layout.addRow(parent.start_prometheus_btn)
    
    layout.addWidget(prom_group)
    
    # Métricas
    metrics_group = QGroupBox("Métricas a Rastrear")
    metrics_layout = QVBoxLayout(metrics_group)
    
    parent.track_success_rate = QCheckBox("Tasa de Éxito")
    parent.track_success_rate.setChecked(True)
    metrics_layout.addWidget(parent.track_success_rate)
    
    parent.track_ban_count = QCheckBox("Conteo de Bloqueos")
    parent.track_ban_count.setChecked(True)
    metrics_layout.addWidget(parent.track_ban_count)
    
    parent.track_session_duration = QCheckBox("Duración de Sesiones")
    parent.track_session_duration.setChecked(True)
    metrics_layout.addWidget(parent.track_session_duration)
    
    parent.track_proxy_performance = QCheckBox("Rendimiento de Proxies")
    parent.track_proxy_performance.setChecked(True)
    metrics_layout.addWidget(parent.track_proxy_performance)
    
    layout.addWidget(metrics_group)
    
    # Exportación
    export_group = QGroupBox("Exportación")
    export_layout = QFormLayout(export_group)
    
    parent.export_csv_enabled = QCheckBox("Exportar CSV Automáticamente")
    export_layout.addRow(parent.export_csv_enabled)
    
    parent.export_interval = QSpinBox()
    parent.export_interval.setRange(10, 1440)
    parent.export_interval.setValue(60)
    parent.export_interval.setSuffix(" min")
    export_layout.addRow("Intervalo:", parent.export_interval)
    
    parent.export_now_btn = QPushButton("Exportar Ahora")
    parent.export_now_btn.clicked.connect(parent._export_analytics)
    export_layout.addRow(parent.export_now_btn)
    
    layout.addWidget(export_group)
    
    # Resumen
    summary_group = QGroupBox("Resumen de Métricas")
    summary_layout = QVBoxLayout(summary_group)
    
    parent.metrics_summary_text = QTextEdit()
    parent.metrics_summary_text.setReadOnly(True)
    parent.metrics_summary_text.setMaximumHeight(150)
    summary_layout.addWidget(parent.metrics_summary_text)
    
    refresh_btn = QPushButton("Actualizar")
    refresh_btn.clicked.connect(parent._refresh_metrics_summary)
    summary_layout.addWidget(refresh_btn)
    
    layout.addWidget(summary_group)
    
    layout.addStretch()
    return tab


def create_accounts_tab(parent) -> QWidget:
    """Crear la pestaña de gestión de cuentas."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Gestión
    mgmt_group = QGroupBox("Gestión de Cuentas")
    mgmt_layout = QFormLayout(mgmt_group)
    
    parent.accounts_enabled = QCheckBox("Habilitar")
    mgmt_layout.addRow(parent.accounts_enabled)
    
    parent.account_rotation_enabled = QCheckBox("Rotación Automática")
    parent.account_rotation_enabled.setChecked(True)
    mgmt_layout.addRow(parent.account_rotation_enabled)
    
    layout.addWidget(mgmt_group)
    
    # Importar/Exportar
    io_group = QGroupBox("Importar/Exportar")
    io_layout = QVBoxLayout(io_group)
    
    btn_layout = QHBoxLayout()
    
    import_btn = QPushButton("📥 Importar CSV")
    import_btn.clicked.connect(parent._import_accounts)
    btn_layout.addWidget(import_btn)
    
    export_btn = QPushButton("📤 Exportar CSV")
    export_btn.clicked.connect(parent._export_accounts)
    btn_layout.addWidget(export_btn)
    
    io_layout.addLayout(btn_layout)
    
    parent.encrypt_csv = QCheckBox("Encriptar archivos")
    parent.encrypt_csv.setChecked(True)
    io_layout.addWidget(parent.encrypt_csv)
    
    layout.addWidget(io_group)
    
    # Lista
    list_group = QGroupBox("Cuentas Registradas")
    list_layout = QVBoxLayout(list_group)
    
    parent.accounts_list = QListWidget()
    parent.accounts_list.setMaximumHeight(150)
    list_layout.addWidget(parent.accounts_list)
    
    list_btn_layout = QHBoxLayout()
    
    add_btn = QPushButton("➕ Agregar")
    add_btn.clicked.connect(parent._add_account)
    list_btn_layout.addWidget(add_btn)
    
    remove_btn = QPushButton("🗑️ Eliminar")
    remove_btn.clicked.connect(parent._remove_account)
    list_btn_layout.addWidget(remove_btn)
    
    list_layout.addLayout(list_btn_layout)
    
    layout.addWidget(list_group)
    
    # Estadísticas
    stats_group = QGroupBox("Estadísticas")
    stats_layout = QFormLayout(stats_group)
    
    parent.accounts_total_label = QLabel("0")
    stats_layout.addRow("Total:", parent.accounts_total_label)
    
    parent.accounts_active_label = QLabel("0")
    stats_layout.addRow("Activas:", parent.accounts_active_label)
    
    layout.addWidget(stats_group)
    
    layout.addStretch()
    return tab


def create_logging_tab(parent) -> QWidget:
    """Crear la pestaña de registros."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    log_group = QGroupBox("Registros de Sesión")
    log_layout = QVBoxLayout(log_group)
    
    parent.log_display = QTextEdit()
    parent.log_display.setReadOnly(True)
    parent.log_display.setStyleSheet("""
        QTextEdit {
            background-color: #1e1e1e;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 11px;
        }
    """)
    log_layout.addWidget(parent.log_display)
    
    log_btn_layout = QHBoxLayout()
    
    clear_btn = QPushButton("Limpiar")
    clear_btn.clicked.connect(parent._clear_logs)
    log_btn_layout.addWidget(clear_btn)
    
    export_btn = QPushButton("Exportar...")
    export_btn.clicked.connect(parent._export_logs)
    log_btn_layout.addWidget(export_btn)
    
    log_layout.addLayout(log_btn_layout)
    
    layout.addWidget(log_group)
    
    return tab
