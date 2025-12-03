"""
Módulo de Interfaz Gráfica del Administrador de Sesiones

Interfaz gráfica profesional basada en PyQt6 para gestionar
múltiples sesiones de automatización de navegador con LLM.

Diseñado exclusivamente para Windows.

Implementa características de fase2.txt:
- Gestión de múltiples sesiones con QThreadPool
- Configuración avanzada de suplantación de huella digital
- Ajustes de simulación de comportamiento
- Configuración de manejo de CAPTCHA
- Validación y rotación de proxies
- Registro y monitoreo en tiempo real
"""

import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional
from logging.handlers import RotatingFileHandler

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QListWidget, QListWidgetItem, QPushButton, QLabel,
    QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit,
    QCheckBox, QGroupBox, QSplitter, QStatusBar, QMessageBox,
    QFileDialog, QProgressBar, QSlider
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QThreadPool, QRunnable, QObject
from PyQt6.QtGui import QFont

from .session_config import SessionConfig, SessionConfigManager
from .proxy_manager import ProxyManager, ProxyEntry
from .fingerprint_manager import FingerprintManager


logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """Señales para comunicación de trabajadores QRunnable (de fase2.txt)."""
    status_update = pyqtSignal(str, str)  # session_id, estado
    log_message = pyqtSignal(str, str)    # session_id, mensaje
    finished = pyqtSignal(str)             # session_id
    resource_update = pyqtSignal(float, float)  # CPU%, RAM%
    error = pyqtSignal(str, str)          # session_id, mensaje_error


class SessionRunnable(QRunnable):
    """Trabajador QRunnable para ejecutar sesiones de navegador con QThreadPool (de fase2.txt)."""
    
    def __init__(self, session_config: SessionConfig):
        super().__init__()
        self.session_config = session_config
        self.signals = WorkerSignals()
        self._is_running = True
        self.setAutoDelete(True)
    
    def run(self):
        """Ejecutar la automatización de sesión usando asyncio."""
        session_id = self.session_config.session_id
        self.signals.status_update.emit(session_id, "ejecutando")
        self.signals.log_message.emit(session_id, f"Iniciando sesión: {self.session_config.name}")
        
        try:
            # Ejecutar la sesión async en un nuevo bucle de eventos
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._run_session())
            finally:
                loop.close()
                
        except Exception as e:
            self.signals.log_message.emit(session_id, f"Error: {str(e)}")
            self.signals.status_update.emit(session_id, "error")
            self.signals.error.emit(session_id, str(e))
        finally:
            self.signals.status_update.emit(session_id, "inactivo")
            self.signals.finished.emit(session_id)
    
    async def _run_session(self):
        """Ejecución de sesión async con lógica de reintentos."""
        session_id = self.session_config.session_id
        
        # Importar características avanzadas
        try:
            from .advanced_features import RetryManager, BehaviorSimulator, BehaviorSimulationConfig
            
            retry_manager = RetryManager(
                max_retries=self.session_config.max_retries,
                base_delay_sec=self.session_config.retry_delay_sec,
                exponential_backoff=self.session_config.exponential_backoff
            )
            
            behavior_sim = BehaviorSimulator(BehaviorSimulationConfig(
                min_action_delay_ms=self.session_config.behavior.action_delay_min_ms,
                max_action_delay_ms=self.session_config.behavior.action_delay_max_ms,
                idle_time_min_sec=self.session_config.behavior.idle_time_min_sec,
                idle_time_max_sec=self.session_config.behavior.idle_time_max_sec,
                mouse_jitter_enabled=self.session_config.behavior.mouse_jitter_enabled,
                mouse_jitter_px=self.session_config.behavior.mouse_jitter_px,
                scroll_simulation_enabled=self.session_config.behavior.scroll_simulation_enabled
            ))
            
            self.signals.log_message.emit(session_id, "Características avanzadas cargadas")
        except ImportError as e:
            self.signals.log_message.emit(session_id, f"Características avanzadas no disponibles: {e}")
        
        # Marcador de ejecución de sesión - integrar con browser_session.py
        self.signals.log_message.emit(session_id, "Sesión iniciada - esperando integración de automatización del navegador")
        
        while self._is_running:
            await asyncio.sleep(1)
    
    def stop(self):
        """Detener la sesión."""
        self._is_running = False


class SessionWorker(QThread):
    """Hilo de trabajo para ejecutar sesiones de automatización del navegador."""
    
    status_update = pyqtSignal(str, str)  # session_id, estado
    log_message = pyqtSignal(str, str)    # session_id, mensaje
    finished = pyqtSignal(str)             # session_id
    
    def __init__(self, session_config: SessionConfig):
        super().__init__()
        self.session_config = session_config
        self._is_running = True
    
    def run(self):
        """Ejecutar la automatización de sesión."""
        session_id = self.session_config.session_id
        self.status_update.emit(session_id, "ejecutando")
        self.log_message.emit(session_id, f"Iniciando sesión: {self.session_config.name}")
        
        try:
            # Ejecutar usando asyncio para operaciones async del navegador
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._run_async_session())
            finally:
                loop.close()
                
        except Exception as e:
            self.log_message.emit(session_id, f"Error: {str(e)}")
            self.status_update.emit(session_id, "error")
        finally:
            self.status_update.emit(session_id, "inactivo")
            self.finished.emit(session_id)
    
    async def _run_async_session(self):
        """Sesión async con simulación de comportamiento y lógica de reintentos."""
        session_id = self.session_config.session_id
        
        # Simular sesión ejecutándose con soporte async
        while self._is_running:
            await asyncio.sleep(1)
    
    def stop(self):
        """Detener la sesión."""
        self._is_running = False


class SessionManagerGUI(QMainWindow):
    """Ventana principal de la GUI para el Administrador de Sesiones Multi-Modelo."""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar rutas
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        
        # Inicializar administradores
        self.config_manager = SessionConfigManager(self.data_dir)
        self.proxy_manager = ProxyManager(self.data_dir)
        self.fingerprint_manager = FingerprintManager(self.config_dir)
        
        # Inicializar QThreadPool para ejecución paralela de sesiones (de fase2.txt)
        self.threadpool = QThreadPool()
        # Usar conteo ideal de hilos basado en el sistema, limitado a 8 para gestión de recursos
        ideal_threads = min(QThread.idealThreadCount(), 8)
        self.threadpool.setMaxThreadCount(max(2, ideal_threads))
        
        # Trabajadores de sesión (seguimiento de QThread y QRunnable)
        self.workers: Dict[str, SessionWorker] = {}
        self.runnables: Dict[str, SessionRunnable] = {}
        
        # Sesión actual siendo editada
        self.current_session: Optional[SessionConfig] = None
        
        # Configurar UI
        self._setup_window()
        self._setup_ui()
        self._setup_status_bar()
        self._load_sessions_list()
        
        # Temporizador de monitoreo de recursos
        self.resource_timer = QTimer()
        self.resource_timer.timeout.connect(self._update_resource_usage)
        self.resource_timer.start(5000)  # Cada 5 segundos
        
        # Temporizador de detección de anomalías (de fase3.txt)
        self.anomaly_timer = QTimer()
        self.anomaly_timer.timeout.connect(self._check_anomalies)
        self.anomaly_timer.start(5000)  # Cada 5 segundos
        
        # Inicializar administradores de contingencia y anomalías (de fase3.txt)
        self._init_phase3_managers()
        
        # Configurar registro avanzado (de fase2.txt)
        self._setup_advanced_logging()
    
    def _init_phase3_managers(self):
        """Inicializar administradores de Fase 3 para contingencia y detección de anomalías."""
        try:
            from .advanced_features import ContingencyManager, AnomalyDetector, SystemHidingManager
            self.contingency_manager = ContingencyManager()
            self.anomaly_detector = AnomalyDetector()
            self.system_hiding_manager = SystemHidingManager()
        except ImportError as e:
            logger.warning(f"Administradores de Fase 3 no disponibles: {e}")
            self.contingency_manager = None
            self.anomaly_detector = None
            self.system_hiding_manager = None
    
    def _check_anomalies(self):
        """Verificar anomalías en sesiones activas (de fase3.txt)."""
        if not self.anomaly_detector:
            return
        
        for session_id, worker in self.workers.items():
            try:
                # Registrar CPU/RAM como métricas para detección de anomalías
                if PSUTIL_AVAILABLE:
                    cpu = psutil.cpu_percent()
                    ram = psutil.virtual_memory().percent
                    
                    self.anomaly_detector.record_metric(session_id, 'cpu_usage', cpu)
                    self.anomaly_detector.record_metric(session_id, 'ram_usage', ram)
                    
                    # Verificar anomalías de CPU/RAM
                    if self.anomaly_detector.check_anomaly(session_id, 'cpu_usage', cpu):
                        self._on_log_message(session_id, f"⚠️ Anomalía de CPU detectada: {cpu:.1f}%")
                    
                    if self.anomaly_detector.check_anomaly(session_id, 'ram_usage', ram):
                        self._on_log_message(session_id, f"⚠️ Anomalía de RAM detectada: {ram:.1f}%")
                    
                    # Alertar si los recursos están críticamente altos
                    if cpu > 80:
                        self._on_log_message(session_id, f"🔴 Uso alto de CPU: {cpu:.1f}%")
                    if ram > 80:
                        self._on_log_message(session_id, f"🔴 Uso alto de RAM: {ram:.1f}%")
            except Exception as e:
                logger.error(f"Error verificando anomalías para {session_id}: {e}")
    
    def _setup_advanced_logging(self):
        """Configurar registro avanzado con RotatingFileHandler (de fase2.txt)."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Logger principal de la aplicación
        app_log_file = self.logs_dir / "botsos_app.log"
        file_handler = RotatingFileHandler(
            app_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
    
    def _setup_window(self):
        """Configurar la ventana principal."""
        self.setWindowTitle("BotSOS - Administrador de Sesiones Multi-Modelo")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        
        # Apply stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QListWidget {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3c3c3c;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
            QPushButton {
                background-color: #0e639c;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
                color: #808080;
            }
            QPushButton#dangerBtn {
                background-color: #c42b1c;
            }
            QPushButton#dangerBtn:hover {
                background-color: #e03e2d;
            }
            QPushButton#successBtn {
                background-color: #16825d;
            }
            QPushButton#successBtn:hover {
                background-color: #1a9d6f;
            }
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #252526;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #094771;
            }
            QTabBar::tab:hover {
                background-color: #3c3c3c;
            }
            QLineEdit, QSpinBox, QComboBox, QTextEdit {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                padding: 6px;
                border-radius: 4px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
                border: 1px solid #0e639c;
            }
            QGroupBox {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #0e639c;
                border: 1px solid #0e639c;
                border-radius: 3px;
            }
            QProgressBar {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0e639c;
                border-radius: 3px;
            }
        """)
    
    def _setup_ui(self):
        """Configurar la interfaz de usuario principal."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Crear divisor para paneles redimensionables
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Barra lateral izquierda - Lista de Sesiones
        sidebar = self._create_sidebar()
        splitter.addWidget(sidebar)
        
        # Panel derecho - Pestañas de Configuración
        config_panel = self._create_config_panel()
        splitter.addWidget(config_panel)
        
        # Establecer tamaños iniciales (30% barra lateral, 70% configuración)
        splitter.setSizes([350, 850])
        
        main_layout.addWidget(splitter)
    
    def _create_sidebar(self) -> QWidget:
        """Crear la barra lateral izquierda con lista de sesiones."""
        sidebar = QWidget()
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(10)
        
        # Encabezado
        header = QLabel("Sesiones")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Lista de sesiones
        self.session_list = QListWidget()
        self.session_list.itemClicked.connect(self._on_session_selected)
        layout.addWidget(self.session_list, stretch=1)
        
        # Botones de control de sesión
        btn_layout = QVBoxLayout()
        
        add_btn = QPushButton("➕ Agregar Sesión")
        add_btn.clicked.connect(self._add_session)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("🗑️ Eliminar Sesión")
        remove_btn.setObjectName("dangerBtn")
        remove_btn.clicked.connect(self._remove_session)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addSpacing(10)
        
        start_btn = QPushButton("▶️ Iniciar Seleccionada")
        start_btn.setObjectName("successBtn")
        start_btn.clicked.connect(self._start_selected_session)
        btn_layout.addWidget(start_btn)
        
        stop_btn = QPushButton("⏹️ Detener Seleccionada")
        stop_btn.clicked.connect(self._stop_selected_session)
        btn_layout.addWidget(stop_btn)
        
        btn_layout.addSpacing(10)
        
        start_all_btn = QPushButton("▶️▶️ Iniciar Todas")
        start_all_btn.setObjectName("successBtn")
        start_all_btn.clicked.connect(self._start_all_sessions)
        btn_layout.addWidget(start_all_btn)
        
        stop_all_btn = QPushButton("⏹️⏹️ Detener Todas")
        stop_all_btn.setObjectName("dangerBtn")
        stop_all_btn.clicked.connect(self._stop_all_sessions)
        btn_layout.addWidget(stop_all_btn)
        
        layout.addLayout(btn_layout)
        
        # Uso de recursos
        resource_group = QGroupBox("Recursos del Sistema")
        resource_layout = QVBoxLayout(resource_group)
        
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        resource_layout.addWidget(self.cpu_label)
        resource_layout.addWidget(self.cpu_bar)
        
        self.ram_label = QLabel("RAM: 0%")
        self.ram_bar = QProgressBar()
        self.ram_bar.setMaximum(100)
        resource_layout.addWidget(self.ram_label)
        resource_layout.addWidget(self.ram_bar)
        
        layout.addWidget(resource_group)
        
        return sidebar
    
    def _create_config_panel(self) -> QWidget:
        """Crear el panel de configuración derecho con pestañas."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Encabezado del nombre de sesión
        name_layout = QHBoxLayout()
        name_label = QLabel("Sesión:")
        name_label.setFont(QFont("Segoe UI", 12))
        self.session_name_edit = QLineEdit()
        self.session_name_edit.setPlaceholderText("Seleccione una sesión...")
        self.session_name_edit.textChanged.connect(self._on_session_name_changed)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.session_name_edit, stretch=1)
        layout.addLayout(name_layout)
        
        # Pestañas de configuración
        self.config_tabs = QTabWidget()
        self.config_tabs.addTab(self._create_behavior_tab(), "🎮 Comportamientos")
        self.config_tabs.addTab(self._create_proxy_tab(), "🌐 Proxy/IP")
        self.config_tabs.addTab(self._create_fingerprint_tab(), "🖥️ Huella Digital")
        self.config_tabs.addTab(self._create_advanced_spoof_tab(), "🔒 Suplantación Avanzada")
        self.config_tabs.addTab(self._create_behavior_simulation_tab(), "🤖 Simulación de Comportamiento")
        self.config_tabs.addTab(self._create_captcha_tab(), "🔑 CAPTCHA")
        # Pestañas de Fase 3
        self.config_tabs.addTab(self._create_contingency_tab(), "🛡️ Contingencia")
        self.config_tabs.addTab(self._create_advanced_behavior_tab(), "⚡ Comportamiento Avanzado")
        self.config_tabs.addTab(self._create_system_hiding_tab(), "🔐 Ocultación del Sistema")
        self.config_tabs.addTab(self._create_logging_tab(), "📝 Registros")
        layout.addWidget(self.config_tabs)
        
        # Botón de guardar
        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.setObjectName("successBtn")
        save_btn.clicked.connect(self._save_current_session)
        layout.addWidget(save_btn)
        
        return panel
    
    def _create_behavior_tab(self) -> QWidget:
        """Crear la pestaña de configuración de comportamiento."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configuración de LLM
        llm_group = QGroupBox("Configuración del Modelo LLM")
        llm_layout = QFormLayout(llm_group)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "llama3.1:8b",
            "qwen2.5:7b", 
            "mistral-nemo:12b",
            "phi3.5:3.8b",
            "gemma2:9b"
        ])
        llm_layout.addRow("Modelo:", self.model_combo)
        
        self.headless_check = QCheckBox("Ejecutar en modo oculto")
        llm_layout.addRow(self.headless_check)
        
        layout.addWidget(llm_group)
        
        # Configuración de Tiempos
        timing_group = QGroupBox("Configuración de Tiempos")
        timing_layout = QFormLayout(timing_group)
        
        self.ad_skip_delay = QSpinBox()
        self.ad_skip_delay.setRange(1, 30)
        self.ad_skip_delay.setValue(5)
        self.ad_skip_delay.setSuffix(" seg")
        timing_layout.addRow("Retraso para Saltar Anuncio:", self.ad_skip_delay)
        
        self.view_time_min = QSpinBox()
        self.view_time_min.setRange(10, 300)
        self.view_time_min.setValue(30)
        self.view_time_min.setSuffix(" seg")
        timing_layout.addRow("Tiempo Mínimo de Vista:", self.view_time_min)
        
        self.view_time_max = QSpinBox()
        self.view_time_max.setRange(30, 600)
        self.view_time_max.setValue(120)
        self.view_time_max.setSuffix(" seg")
        timing_layout.addRow("Tiempo Máximo de Vista:", self.view_time_max)
        
        self.action_delay_min = QSpinBox()
        self.action_delay_min.setRange(50, 1000)
        self.action_delay_min.setValue(100)
        self.action_delay_min.setSuffix(" ms")
        timing_layout.addRow("Retraso Mínimo de Acción:", self.action_delay_min)
        
        self.action_delay_max = QSpinBox()
        self.action_delay_max.setRange(100, 2000)
        self.action_delay_max.setValue(500)
        self.action_delay_max.setSuffix(" ms")
        timing_layout.addRow("Retraso Máximo de Acción:", self.action_delay_max)
        
        layout.addWidget(timing_group)
        
        # Configuración de Acciones
        actions_group = QGroupBox("Acciones Habilitadas")
        actions_layout = QVBoxLayout(actions_group)
        
        self.enable_like = QCheckBox("Habilitar Me Gusta")
        self.enable_like.setChecked(True)
        actions_layout.addWidget(self.enable_like)
        
        self.enable_comment = QCheckBox("Habilitar Comentarios")
        self.enable_comment.setChecked(True)
        actions_layout.addWidget(self.enable_comment)
        
        self.enable_subscribe = QCheckBox("Habilitar Suscripción")
        actions_layout.addWidget(self.enable_subscribe)
        
        self.enable_skip_ads = QCheckBox("Habilitar Saltar Anuncios")
        self.enable_skip_ads.setChecked(True)
        actions_layout.addWidget(self.enable_skip_ads)
        
        layout.addWidget(actions_group)
        
        # Prompt de Tarea
        prompt_group = QGroupBox("Prompt de Tarea (YAML/JSON)")
        prompt_layout = QVBoxLayout(prompt_group)
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Ingrese su prompt de tarea aquí...")
        self.prompt_edit.setMinimumHeight(150)
        prompt_layout.addWidget(self.prompt_edit)
        
        layout.addWidget(prompt_group)
        
        layout.addStretch()
        return tab
    
    def _create_proxy_tab(self) -> QWidget:
        """Crear la pestaña de configuración de proxy."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configuración de Proxy Individual
        single_group = QGroupBox("Proxy de Sesión")
        single_layout = QFormLayout(single_group)
        
        self.proxy_enabled = QCheckBox("Habilitar Proxy")
        single_layout.addRow(self.proxy_enabled)
        
        self.proxy_type = QComboBox()
        self.proxy_type.addItems(["http", "https", "socks5"])
        single_layout.addRow("Tipo:", self.proxy_type)
        
        self.proxy_server = QLineEdit()
        self.proxy_server.setPlaceholderText("proxy.ejemplo.com")
        single_layout.addRow("Servidor:", self.proxy_server)
        
        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(8080)
        single_layout.addRow("Puerto:", self.proxy_port)
        
        self.proxy_user = QLineEdit()
        self.proxy_user.setPlaceholderText("usuario (opcional)")
        single_layout.addRow("Usuario:", self.proxy_user)
        
        self.proxy_pass = QLineEdit()
        self.proxy_pass.setPlaceholderText("contraseña (opcional)")
        self.proxy_pass.setEchoMode(QLineEdit.EchoMode.Password)
        single_layout.addRow("Contraseña:", self.proxy_pass)
        
        layout.addWidget(single_group)
        
        # Pool de Proxies
        pool_group = QGroupBox("Pool de Proxies")
        pool_layout = QVBoxLayout(pool_group)
        
        self.proxy_pool_list = QListWidget()
        self.proxy_pool_list.setMaximumHeight(150)
        pool_layout.addWidget(self.proxy_pool_list)
        
        pool_btn_layout = QHBoxLayout()
        
        add_proxy_btn = QPushButton("Agregar")
        add_proxy_btn.clicked.connect(self._add_proxy_to_pool)
        pool_btn_layout.addWidget(add_proxy_btn)
        
        remove_proxy_btn = QPushButton("Eliminar")
        remove_proxy_btn.clicked.connect(self._remove_proxy_from_pool)
        pool_btn_layout.addWidget(remove_proxy_btn)
        
        import_proxy_btn = QPushButton("Importar...")
        import_proxy_btn.clicked.connect(self._import_proxies)
        pool_btn_layout.addWidget(import_proxy_btn)
        
        validate_proxy_btn = QPushButton("Validar Todos")
        validate_proxy_btn.clicked.connect(self._validate_proxy_pool)
        pool_btn_layout.addWidget(validate_proxy_btn)
        
        pool_layout.addLayout(pool_btn_layout)
        
        layout.addWidget(pool_group)
        
        # Configuración de Rotación
        rotation_group = QGroupBox("Configuración de Rotación")
        rotation_layout = QFormLayout(rotation_group)
        
        self.rotation_interval = QSpinBox()
        self.rotation_interval.setRange(1, 100)
        self.rotation_interval.setValue(10)
        self.rotation_interval.setSuffix(" solicitudes")
        rotation_layout.addRow("Rotar Cada:", self.rotation_interval)
        
        self.rotation_strategy = QComboBox()
        self.rotation_strategy.addItems(["Round Robin", "Aleatorio", "Mejor Rendimiento"])
        rotation_layout.addRow("Estrategia:", self.rotation_strategy)
        
        self.validate_before_use = QCheckBox("Validar Proxy Antes de Usar")
        self.validate_before_use.setChecked(True)
        rotation_layout.addRow(self.validate_before_use)
        
        self.auto_deactivate_failed = QCheckBox("Desactivar Automáticamente Proxies Fallidos")
        self.auto_deactivate_failed.setChecked(True)
        rotation_layout.addRow(self.auto_deactivate_failed)
        
        layout.addWidget(rotation_group)
        
        layout.addStretch()
        
        # Cargar pool de proxies
        self._load_proxy_pool()
        
        return tab
    
    def _create_fingerprint_tab(self) -> QWidget:
        """Crear la pestaña de configuración de huella digital/dispositivo."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Preset de Dispositivo
        preset_group = QGroupBox("Preset de Dispositivo")
        preset_layout = QFormLayout(preset_group)
        
        self.device_preset = QComboBox()
        preset_names = self.fingerprint_manager.get_preset_names()
        for name in preset_names:
            preset = self.fingerprint_manager.get_preset(name)
            display_name = preset.get("name", name) if preset else name
            self.device_preset.addItem(display_name, name)
        self.device_preset.currentIndexChanged.connect(self._on_device_preset_changed)
        preset_layout.addRow("Preset:", self.device_preset)
        
        self.randomize_on_start = QCheckBox("Aleatorizar al iniciar sesión")
        self.randomize_on_start.setChecked(True)
        preset_layout.addRow(self.randomize_on_start)
        
        layout.addWidget(preset_group)
        
        # Configuración Personalizada
        custom_group = QGroupBox("Configuración Personalizada")
        custom_layout = QFormLayout(custom_group)
        
        self.user_agent_edit = QLineEdit()
        self.user_agent_edit.setPlaceholderText("Auto-generado desde preset")
        custom_layout.addRow("User-Agent:", self.user_agent_edit)
        
        viewport_layout = QHBoxLayout()
        self.viewport_width = QSpinBox()
        self.viewport_width.setRange(320, 3840)
        self.viewport_width.setValue(1920)
        viewport_layout.addWidget(self.viewport_width)
        viewport_layout.addWidget(QLabel("x"))
        self.viewport_height = QSpinBox()
        self.viewport_height.setRange(240, 2160)
        self.viewport_height.setValue(1080)
        viewport_layout.addWidget(self.viewport_height)
        custom_layout.addRow("Viewport:", viewport_layout)
        
        self.hardware_concurrency = QSpinBox()
        self.hardware_concurrency.setRange(1, 64)
        self.hardware_concurrency.setValue(8)
        custom_layout.addRow("Núcleos de CPU:", self.hardware_concurrency)
        
        self.device_memory = QSpinBox()
        self.device_memory.setRange(1, 128)
        self.device_memory.setValue(8)
        self.device_memory.setSuffix(" GB")
        custom_layout.addRow("Memoria del Dispositivo:", self.device_memory)
        
        self.timezone_combo = QComboBox()
        self.timezone_combo.addItems([
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
        custom_layout.addRow("Zona Horaria:", self.timezone_combo)
        
        layout.addWidget(custom_group)
        
        # Opciones de Suplantación
        spoof_group = QGroupBox("Opciones de Suplantación")
        spoof_layout = QVBoxLayout(spoof_group)
        
        self.canvas_noise = QCheckBox("Inyección de Ruido en Canvas")
        self.canvas_noise.setChecked(True)
        spoof_layout.addWidget(self.canvas_noise)
        
        noise_layout = QHBoxLayout()
        noise_layout.addWidget(QLabel("Nivel de Ruido:"))
        self.canvas_noise_level = QSpinBox()
        self.canvas_noise_level.setRange(0, 10)
        self.canvas_noise_level.setValue(5)
        noise_layout.addWidget(self.canvas_noise_level)
        noise_layout.addStretch()
        spoof_layout.addLayout(noise_layout)
        
        self.webrtc_protection = QCheckBox("Protección WebRTC")
        self.webrtc_protection.setChecked(True)
        spoof_layout.addWidget(self.webrtc_protection)
        
        self.webgl_spoofing = QCheckBox("Suplantación de WebGL")
        self.webgl_spoofing.setChecked(True)
        spoof_layout.addWidget(self.webgl_spoofing)
        
        self.audio_spoofing = QCheckBox("Suplantación de Contexto de Audio")
        self.audio_spoofing.setChecked(True)
        spoof_layout.addWidget(self.audio_spoofing)
        
        self.font_spoofing = QCheckBox("Suplantación de Fuentes")
        self.font_spoofing.setChecked(True)
        spoof_layout.addWidget(self.font_spoofing)
        
        layout.addWidget(spoof_group)
        
        layout.addStretch()
        return tab
    
    def _create_advanced_spoof_tab(self) -> QWidget:
        """Crear la pestaña de configuración de suplantación avanzada (de fase2.txt - segundo bloque)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configuración TLS/JA3
        tls_group = QGroupBox("Huella Digital TLS/JA3")
        tls_layout = QFormLayout(tls_group)
        
        self.tls_profile = QComboBox()
        self.tls_profile.addItems([
            "chrome_120",
            "chrome_110", 
            "firefox_121",
            "safari_17",
            "edge_120"
        ])
        tls_layout.addRow("Perfil TLS:", self.tls_profile)
        
        self.client_hints_enabled = QCheckBox("Habilitar Client Hints")
        self.client_hints_enabled.setChecked(True)
        tls_layout.addRow(self.client_hints_enabled)
        
        layout.addWidget(tls_group)
        
        # Configuración WebGPU
        webgpu_group = QGroupBox("Suplantación de WebGPU")
        webgpu_layout = QFormLayout(webgpu_group)
        
        self.webgpu_enabled = QCheckBox("Habilitar Suplantación de WebGPU")
        self.webgpu_enabled.setChecked(True)
        webgpu_layout.addRow(self.webgpu_enabled)
        
        self.webgpu_vendor = QLineEdit()
        self.webgpu_vendor.setText("Google Inc.")
        webgpu_layout.addRow("Fabricante de GPU:", self.webgpu_vendor)
        
        self.webgpu_architecture = QComboBox()
        self.webgpu_architecture.addItems(["x86_64", "arm64", "x86"])
        webgpu_layout.addRow("Arquitectura:", self.webgpu_architecture)
        
        layout.addWidget(webgpu_group)
        
        # Canvas/WebGL Avanzado
        canvas_group = QGroupBox("Canvas y WebGL Avanzado")
        canvas_layout = QFormLayout(canvas_group)
        
        noise_layout = QHBoxLayout()
        noise_layout.addWidget(QLabel("Ruido de Canvas (0-10):"))
        self.adv_canvas_noise = QSlider(Qt.Orientation.Horizontal)
        self.adv_canvas_noise.setRange(0, 10)
        self.adv_canvas_noise.setValue(5)
        self.adv_canvas_noise_label = QLabel("5")
        self.adv_canvas_noise.valueChanged.connect(
            lambda v: self.adv_canvas_noise_label.setText(str(v))
        )
        noise_layout.addWidget(self.adv_canvas_noise)
        noise_layout.addWidget(self.adv_canvas_noise_label)
        canvas_layout.addRow(noise_layout)
        
        self.webgl_vendor_override = QLineEdit()
        self.webgl_vendor_override.setPlaceholderText("Dejar vacío para valor del preset")
        canvas_layout.addRow("Sobrescribir Fabricante WebGL:", self.webgl_vendor_override)
        
        self.webgl_renderer_override = QLineEdit()
        self.webgl_renderer_override.setPlaceholderText("Dejar vacío para valor del preset")
        canvas_layout.addRow("Sobrescribir Renderizador WebGL:", self.webgl_renderer_override)
        
        layout.addWidget(canvas_group)
        
        # Suplantación de Fuentes
        font_group = QGroupBox("Suplantación de Fuentes")
        font_layout = QVBoxLayout(font_group)
        
        self.custom_fonts_edit = QTextEdit()
        self.custom_fonts_edit.setMaximumHeight(100)
        self.custom_fonts_edit.setPlaceholderText("Una fuente por línea:\nArial\nHelvetica\nTimes New Roman")
        self.custom_fonts_edit.setText("Arial\nHelvetica\nTimes New Roman\nGeorgia\nVerdana\nCourier New")
        font_layout.addWidget(self.custom_fonts_edit)
        
        layout.addWidget(font_group)
        
        layout.addStretch()
        return tab
    
    def _create_behavior_simulation_tab(self) -> QWidget:
        """Crear la pestaña de configuración de simulación de comportamiento (de fase2.txt - segundo bloque)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Simulación del Ratón
        mouse_group = QGroupBox("Simulación del Ratón")
        mouse_layout = QFormLayout(mouse_group)
        
        self.mouse_jitter_enabled = QCheckBox("Habilitar Movimiento Aleatorio del Ratón")
        self.mouse_jitter_enabled.setChecked(True)
        mouse_layout.addRow(self.mouse_jitter_enabled)
        
        self.mouse_jitter_px = QSpinBox()
        self.mouse_jitter_px.setRange(1, 20)
        self.mouse_jitter_px.setValue(5)
        self.mouse_jitter_px.setSuffix(" px")
        mouse_layout.addRow("Cantidad de Movimiento:", self.mouse_jitter_px)
        
        self.enable_random_hover = QCheckBox("Habilitar Hover Aleatorio")
        self.enable_random_hover.setChecked(True)
        mouse_layout.addRow(self.enable_random_hover)
        
        layout.addWidget(mouse_group)
        
        # Simulación de Tiempos
        timing_group = QGroupBox("Simulación de Tiempos")
        timing_layout = QFormLayout(timing_group)
        
        self.idle_time_min = QDoubleSpinBox()
        self.idle_time_min.setRange(0.5, 60.0)
        self.idle_time_min.setValue(5.0)
        self.idle_time_min.setSuffix(" seg")
        timing_layout.addRow("Tiempo Inactivo Mínimo:", self.idle_time_min)
        
        self.idle_time_max = QDoubleSpinBox()
        self.idle_time_max.setRange(1.0, 120.0)
        self.idle_time_max.setValue(15.0)
        self.idle_time_max.setSuffix(" seg")
        timing_layout.addRow("Tiempo Inactivo Máximo:", self.idle_time_max)
        
        self.random_action_prob = QSpinBox()
        self.random_action_prob.setRange(0, 50)
        self.random_action_prob.setValue(10)
        self.random_action_prob.setSuffix(" %")
        timing_layout.addRow("Probabilidad de Acción Aleatoria:", self.random_action_prob)
        
        layout.addWidget(timing_group)
        
        # Simulación de Desplazamiento
        scroll_group = QGroupBox("Simulación de Desplazamiento")
        scroll_layout = QFormLayout(scroll_group)
        
        self.scroll_enabled = QCheckBox("Habilitar Simulación de Desplazamiento")
        self.scroll_enabled.setChecked(True)
        scroll_layout.addRow(self.scroll_enabled)
        
        self.enable_random_scroll = QCheckBox("Habilitar Desplazamiento Aleatorio")
        self.enable_random_scroll.setChecked(True)
        scroll_layout.addRow(self.enable_random_scroll)
        
        self.scroll_delta_min = QSpinBox()
        self.scroll_delta_min.setRange(10, 500)
        self.scroll_delta_min.setValue(50)
        self.scroll_delta_min.setSuffix(" px")
        scroll_layout.addRow("Delta de Desplazamiento Mínimo:", self.scroll_delta_min)
        
        self.scroll_delta_max = QSpinBox()
        self.scroll_delta_max.setRange(50, 1000)
        self.scroll_delta_max.setValue(300)
        self.scroll_delta_max.setSuffix(" px")
        scroll_layout.addRow("Delta de Desplazamiento Máximo:", self.scroll_delta_max)
        
        layout.addWidget(scroll_group)
        
        # Simulación de Escritura
        typing_group = QGroupBox("Simulación de Escritura")
        typing_layout = QFormLayout(typing_group)
        
        self.typing_speed_min = QSpinBox()
        self.typing_speed_min.setRange(10, 300)
        self.typing_speed_min.setValue(50)
        self.typing_speed_min.setSuffix(" ms")
        typing_layout.addRow("Retraso Mínimo entre Teclas:", self.typing_speed_min)
        
        self.typing_speed_max = QSpinBox()
        self.typing_speed_max.setRange(50, 500)
        self.typing_speed_max.setValue(200)
        self.typing_speed_max.setSuffix(" ms")
        typing_layout.addRow("Retraso Máximo entre Teclas:", self.typing_speed_max)
        
        self.typing_mistake_rate = QSpinBox()
        self.typing_mistake_rate.setRange(0, 10)
        self.typing_mistake_rate.setValue(2)
        self.typing_mistake_rate.setSuffix(" %")
        typing_layout.addRow("Tasa de Errores de Escritura:", self.typing_mistake_rate)
        
        layout.addWidget(typing_group)
        
        layout.addStretch()
        return tab
    
    def _create_captcha_tab(self) -> QWidget:
        """Crear la pestaña de configuración de manejo de CAPTCHA (de fase2.txt - segundo bloque)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configuración de CAPTCHA
        captcha_group = QGroupBox("Resolución de CAPTCHA")
        captcha_layout = QFormLayout(captcha_group)
        
        self.captcha_enabled = QCheckBox("Habilitar Resolución Automática de CAPTCHA")
        self.captcha_enabled.setChecked(False)
        captcha_layout.addRow(self.captcha_enabled)
        
        self.captcha_provider = QComboBox()
        self.captcha_provider.addItems(["2captcha", "anticaptcha", "capsolver"])
        captcha_layout.addRow("Proveedor:", self.captcha_provider)
        
        self.captcha_api_key = QLineEdit()
        self.captcha_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.captcha_api_key.setPlaceholderText("Ingrese clave API (almacenada de forma segura)")
        captcha_layout.addRow("Clave API:", self.captcha_api_key)
        
        layout.addWidget(captcha_group)
        
        # Tipos de CAPTCHA
        types_group = QGroupBox("Tipos de CAPTCHA Soportados")
        types_layout = QVBoxLayout(types_group)
        
        self.captcha_recaptcha_v2 = QCheckBox("reCAPTCHA v2")
        self.captcha_recaptcha_v2.setChecked(True)
        types_layout.addWidget(self.captcha_recaptcha_v2)
        
        self.captcha_recaptcha_v3 = QCheckBox("reCAPTCHA v3")
        self.captcha_recaptcha_v3.setChecked(True)
        types_layout.addWidget(self.captcha_recaptcha_v3)
        
        self.captcha_hcaptcha = QCheckBox("hCaptcha")
        self.captcha_hcaptcha.setChecked(True)
        types_layout.addWidget(self.captcha_hcaptcha)
        
        layout.addWidget(types_group)
        
        # Opciones de CAPTCHA
        options_group = QGroupBox("Opciones")
        options_layout = QFormLayout(options_group)
        
        self.captcha_timeout = QSpinBox()
        self.captcha_timeout.setRange(30, 300)
        self.captcha_timeout.setValue(120)
        self.captcha_timeout.setSuffix(" seg")
        options_layout.addRow("Tiempo de Espera para Resolver:", self.captcha_timeout)
        
        self.captcha_max_retries = QSpinBox()
        self.captcha_max_retries.setRange(1, 10)
        self.captcha_max_retries.setValue(3)
        options_layout.addRow("Máximo de Reintentos:", self.captcha_max_retries)
        
        layout.addWidget(options_group)
        
        # Configuración de Reintentos (de fase2.txt)
        retry_group = QGroupBox("Configuración de Reintentos")
        retry_layout = QFormLayout(retry_group)
        
        self.max_retries = QSpinBox()
        self.max_retries.setRange(0, 10)
        self.max_retries.setValue(3)
        retry_layout.addRow("Máximo de Reintentos de Acción:", self.max_retries)
        
        self.retry_delay = QDoubleSpinBox()
        self.retry_delay.setRange(0.5, 30.0)
        self.retry_delay.setValue(1.0)
        self.retry_delay.setSuffix(" seg")
        retry_layout.addRow("Retraso Base de Reintento:", self.retry_delay)
        
        self.exponential_backoff = QCheckBox("Usar Retroceso Exponencial")
        self.exponential_backoff.setChecked(True)
        retry_layout.addRow(self.exponential_backoff)
        
        layout.addWidget(retry_group)
        
        # Información de Almacenamiento Seguro
        info_label = QLabel(
            "ℹ️ Las claves API se almacenan de forma segura usando el llavero del sistema cuando está disponible.\n"
            "Si el llavero no está disponible, se utilizan variables de entorno como respaldo."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #808080; font-size: 10px;")
        layout.addWidget(info_label)
        
        # Configuración híbrida de CAPTCHA (de fase3.txt)
        hybrid_group = QGroupBox("Solucionador Híbrido (fase3)")
        hybrid_layout = QFormLayout(hybrid_group)
        
        self.captcha_hybrid_mode = QCheckBox("Habilitar Modo Híbrido (IA primero, humano como respaldo)")
        self.captcha_hybrid_mode.setChecked(True)
        hybrid_layout.addRow(self.captcha_hybrid_mode)
        
        self.captcha_secondary_provider = QComboBox()
        self.captcha_secondary_provider.addItems(["capsolver", "anticaptcha", "2captcha"])
        hybrid_layout.addRow("Proveedor de Respaldo:", self.captcha_secondary_provider)
        
        layout.addWidget(hybrid_group)
        
        layout.addStretch()
        return tab
    
    def _create_contingency_tab(self) -> QWidget:
        """Crear la pestaña de planificación de contingencia (de fase3.txt)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Umbrales de Evicción
        eviction_group = QGroupBox("Umbrales de Evicción")
        eviction_layout = QFormLayout(eviction_group)
        
        self.block_rate_threshold = QDoubleSpinBox()
        self.block_rate_threshold.setRange(0.01, 0.50)
        self.block_rate_threshold.setValue(0.10)
        self.block_rate_threshold.setSingleStep(0.01)
        self.block_rate_threshold.setSuffix(" (5-10%)")
        eviction_layout.addRow("Umbral de Tasa de Bloqueo:", self.block_rate_threshold)
        
        self.consecutive_failure_threshold = QSpinBox()
        self.consecutive_failure_threshold.setRange(1, 10)
        self.consecutive_failure_threshold.setValue(3)
        eviction_layout.addRow("Fallas Consecutivas:", self.consecutive_failure_threshold)
        
        layout.addWidget(eviction_group)
        
        # Configuración de Enfriamiento
        cooldown_group = QGroupBox("Configuración de Enfriamiento")
        cooldown_layout = QFormLayout(cooldown_group)
        
        self.cool_down_min = QSpinBox()
        self.cool_down_min.setRange(60, 1800)
        self.cool_down_min.setValue(300)
        self.cool_down_min.setSuffix(" seg (5 min)")
        cooldown_layout.addRow("Enfriamiento Mínimo:", self.cool_down_min)
        
        self.cool_down_max = QSpinBox()
        self.cool_down_max.setRange(300, 3600)
        self.cool_down_max.setValue(1200)
        self.cool_down_max.setSuffix(" seg (20 min)")
        cooldown_layout.addRow("Enfriamiento Máximo:", self.cool_down_max)
        
        layout.addWidget(cooldown_group)
        
        # Recuperación de Bloqueo
        recovery_group = QGroupBox("Estrategia de Recuperación de Bloqueo")
        recovery_layout = QFormLayout(recovery_group)
        
        self.ban_recovery_strategy = QComboBox()
        self.ban_recovery_strategy.addItems(["mobile_fallback", "throttle", "rotate_all"])
        recovery_layout.addRow("Estrategia de Recuperación:", self.ban_recovery_strategy)
        
        self.enable_dynamic_throttling = QCheckBox("Habilitar Limitación Dinámica")
        self.enable_dynamic_throttling.setChecked(True)
        recovery_layout.addRow(self.enable_dynamic_throttling)
        
        layout.addWidget(recovery_group)
        
        # Sesiones Persistentes
        sticky_group = QGroupBox("Sesiones Persistentes")
        sticky_layout = QFormLayout(sticky_group)
        
        self.sticky_session_duration = QSpinBox()
        self.sticky_session_duration.setRange(60, 3600)
        self.sticky_session_duration.setValue(600)
        self.sticky_session_duration.setSuffix(" seg (10 min)")
        sticky_layout.addRow("Duración de Sesión:", self.sticky_session_duration)
        
        self.enable_session_persistence = QCheckBox("Habilitar Persistencia de Sesión")
        self.enable_session_persistence.setChecked(True)
        sticky_layout.addRow(self.enable_session_persistence)
        
        layout.addWidget(sticky_group)
        
        layout.addStretch()
        return tab
    
    def _create_advanced_behavior_tab(self) -> QWidget:
        """Crear la pestaña de configuración de comportamiento avanzado (de fase3.txt)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Huella Digital Polimórfica
        poly_group = QGroupBox("Huella Digital Polimórfica")
        poly_layout = QFormLayout(poly_group)
        
        self.polymorphic_enabled = QCheckBox("Habilitar Huella Digital Polimórfica")
        self.polymorphic_enabled.setChecked(True)
        poly_layout.addRow(self.polymorphic_enabled)
        
        self.fingerprint_rotation_interval = QSpinBox()
        self.fingerprint_rotation_interval.setRange(300, 7200)
        self.fingerprint_rotation_interval.setValue(3600)
        self.fingerprint_rotation_interval.setSuffix(" seg (1 hr)")
        poly_layout.addRow("Intervalo de Rotación:", self.fingerprint_rotation_interval)
        
        layout.addWidget(poly_group)
        
        # Entrada a Nivel de SO
        os_group = QGroupBox("Emulación de Entrada a Nivel de SO")
        os_layout = QFormLayout(os_group)
        
        self.os_level_input_enabled = QCheckBox("Habilitar Entradas a Nivel de SO (estilo nodriver)")
        os_layout.addRow(self.os_level_input_enabled)
        
        layout.addWidget(os_group)
        
        # Emulación Táctil
        touch_group = QGroupBox("Emulación Táctil (Móvil)")
        touch_layout = QFormLayout(touch_group)
        
        self.touch_emulation_enabled = QCheckBox("Habilitar Emulación Táctil")
        touch_layout.addRow(self.touch_emulation_enabled)
        
        self.touch_pressure_variation = QDoubleSpinBox()
        self.touch_pressure_variation.setRange(0.0, 0.5)
        self.touch_pressure_variation.setValue(0.2)
        self.touch_pressure_variation.setSingleStep(0.05)
        self.touch_pressure_variation.setSuffix(" (20%)")
        touch_layout.addRow("Variación de Presión:", self.touch_pressure_variation)
        
        layout.addWidget(touch_group)
        
        # Micro-movimientos
        jitter_group = QGroupBox("Micro-movimientos")
        jitter_layout = QFormLayout(jitter_group)
        
        self.micro_jitter_enabled = QCheckBox("Habilitar Micro-movimientos")
        self.micro_jitter_enabled.setChecked(True)
        jitter_layout.addRow(self.micro_jitter_enabled)
        
        self.micro_jitter_amplitude = QSpinBox()
        self.micro_jitter_amplitude.setRange(1, 10)
        self.micro_jitter_amplitude.setValue(2)
        self.micro_jitter_amplitude.setSuffix(" px")
        jitter_layout.addRow("Amplitud del Movimiento:", self.micro_jitter_amplitude)
        
        layout.addWidget(jitter_group)
        
        # Patrones de Escritura
        typing_group = QGroupBox("Patrones de Escritura Avanzados")
        typing_layout = QFormLayout(typing_group)
        
        self.typing_pressure_enabled = QCheckBox("Habilitar Simulación de Presión de Teclas")
        typing_layout.addRow(self.typing_pressure_enabled)
        
        self.typing_rhythm_variation = QDoubleSpinBox()
        self.typing_rhythm_variation.setRange(0.0, 0.5)
        self.typing_rhythm_variation.setValue(0.15)
        self.typing_rhythm_variation.setSingleStep(0.05)
        self.typing_rhythm_variation.setSuffix(" (15%)")
        typing_layout.addRow("Variación de Ritmo:", self.typing_rhythm_variation)
        
        layout.addWidget(typing_group)
        
        layout.addStretch()
        return tab
    
    def _create_system_hiding_tab(self) -> QWidget:
        """Crear la pestaña de configuración de ocultación del sistema (de fase3.txt)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Bloqueo de Puerto CDP
        cdp_group = QGroupBox("Bloqueo de Puerto CDP")
        cdp_layout = QFormLayout(cdp_group)
        
        self.block_cdp_ports = QCheckBox("Bloquear Puertos de Depuración CDP")
        self.block_cdp_ports.setChecked(True)
        cdp_layout.addRow(self.block_cdp_ports)
        
        self.cdp_port_default = QSpinBox()
        self.cdp_port_default.setRange(1, 65535)
        self.cdp_port_default.setValue(9222)
        cdp_layout.addRow("Puerto CDP:", self.cdp_port_default)
        
        layout.addWidget(cdp_group)
        
        # Gestión de Interfaz de Red/Loopback
        loopback_group = QGroupBox("Gestión de Interfaz de Red")
        loopback_layout = QFormLayout(loopback_group)
        
        self.disable_loopback_services = QCheckBox("Deshabilitar Servicios de Loopback")
        loopback_layout.addRow(self.disable_loopback_services)
        
        layout.addWidget(loopback_group)
        
        # Aleatorización de Puertos Efímeros
        port_group = QGroupBox("Aleatorización de Puertos Efímeros")
        port_layout = QFormLayout(port_group)
        
        self.randomize_ephemeral_ports = QCheckBox("Aleatorizar Puertos Efímeros")
        self.randomize_ephemeral_ports.setChecked(True)
        port_layout.addRow(self.randomize_ephemeral_ports)
        
        self.ephemeral_port_min = QSpinBox()
        self.ephemeral_port_min.setRange(49152, 60000)
        self.ephemeral_port_min.setValue(49152)
        port_layout.addRow("Puerto Mínimo:", self.ephemeral_port_min)
        
        self.ephemeral_port_max = QSpinBox()
        self.ephemeral_port_max.setRange(55000, 65535)
        self.ephemeral_port_max.setValue(65535)
        port_layout.addRow("Puerto Máximo:", self.ephemeral_port_max)
        
        layout.addWidget(port_group)
        
        # Bloqueo Completo de WebRTC
        webrtc_group = QGroupBox("Protección WebRTC")
        webrtc_layout = QFormLayout(webrtc_group)
        
        self.block_webrtc_completely = QCheckBox("Bloquear WebRTC Completamente (agresivo)")
        webrtc_layout.addRow(self.block_webrtc_completely)
        
        webrtc_info = QLabel(
            "⚠️ El bloqueo completo de WebRTC es más agresivo que la suplantación.\n"
            "Puede afectar algunas funciones de video/audio."
        )
        webrtc_info.setWordWrap(True)
        webrtc_info.setStyleSheet("color: #ffa500; font-size: 10px;")
        webrtc_layout.addRow(webrtc_info)
        
        layout.addWidget(webrtc_group)
        
        # Contingencia MFA (de fase3.txt)
        mfa_group = QGroupBox("Contingencia MFA")
        mfa_layout = QFormLayout(mfa_group)
        
        self.mfa_simulation_enabled = QCheckBox("Habilitar Simulación MFA")
        mfa_layout.addRow(self.mfa_simulation_enabled)
        
        self.mfa_method = QComboBox()
        self.mfa_method.addItems(["ninguno", "email", "sms"])
        mfa_layout.addRow("Método MFA:", self.mfa_method)
        
        self.mfa_timeout = QSpinBox()
        self.mfa_timeout.setRange(30, 300)
        self.mfa_timeout.setValue(120)
        self.mfa_timeout.setSuffix(" seg")
        mfa_layout.addRow("Tiempo de Espera MFA:", self.mfa_timeout)
        
        mfa_warning = QLabel(
            "⚠️ La simulación MFA es solo para fines de prueba.\n"
            "Úsela de manera ética y cumpla con los términos de servicio de las plataformas."
        )
        mfa_warning.setWordWrap(True)
        mfa_warning.setStyleSheet("color: #ff6b6b; font-size: 10px;")
        mfa_layout.addRow(mfa_warning)
        
        layout.addWidget(mfa_group)
        
        layout.addStretch()
        return tab
    
    def _create_logging_tab(self) -> QWidget:
        """Crear la pestaña de registros/monitoreo."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Visualización de Registros
        log_group = QGroupBox("Registros de Sesión")
        log_layout = QVBoxLayout(log_group)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self.log_display)
        
        log_btn_layout = QHBoxLayout()
        
        clear_log_btn = QPushButton("Limpiar Registros")
        clear_log_btn.clicked.connect(self._clear_logs)
        log_btn_layout.addWidget(clear_log_btn)
        
        export_log_btn = QPushButton("Exportar Registros...")
        export_log_btn.clicked.connect(self._export_logs)
        log_btn_layout.addWidget(export_log_btn)
        
        log_layout.addLayout(log_btn_layout)
        
        layout.addWidget(log_group)
        
        return tab
    
    def _setup_status_bar(self):
        """Configurar la barra de estado."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo")
    
    def _load_sessions_list(self):
        """Cargar sesiones en el widget de lista."""
        self.session_list.clear()
        for session in self.config_manager.get_all_sessions():
            item = QListWidgetItem(f"📋 {session.name}")
            item.setData(Qt.ItemDataRole.UserRole, session.session_id)
            self.session_list.addItem(item)
    
    def _load_proxy_pool(self):
        """Cargar proxies en la lista del pool."""
        self.proxy_pool_list.clear()
        for proxy in self.proxy_manager.get_all_proxies():
            status = "✅" if proxy.is_active else "❌"
            self.proxy_pool_list.addItem(f"{status} {proxy.server}:{proxy.port}")
    
    def _on_session_selected(self, item: QListWidgetItem):
        """Manejar selección de sesión."""
        session_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_session = self.config_manager.get_session(session_id)
        
        if self.current_session:
            self._populate_form(self.current_session)
            self.status_bar.showMessage(f"Sesión cargada: {self.current_session.name}")
    
    def _populate_form(self, session: SessionConfig):
        """Llenar el formulario con datos de sesión."""
        # Información básica
        self.session_name_edit.setText(session.name)
        
        # Behavior
        behavior = session.behavior
        index = self.model_combo.findText(behavior.llm_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        self.headless_check.setChecked(session.headless)
        self.ad_skip_delay.setValue(behavior.ad_skip_delay_sec)
        self.view_time_min.setValue(behavior.view_time_min_sec)
        self.view_time_max.setValue(behavior.view_time_max_sec)
        self.action_delay_min.setValue(behavior.action_delay_min_ms)
        self.action_delay_max.setValue(behavior.action_delay_max_ms)
        self.enable_like.setChecked(behavior.enable_like)
        self.enable_comment.setChecked(behavior.enable_comment)
        self.enable_subscribe.setChecked(behavior.enable_subscribe)
        self.enable_skip_ads.setChecked(behavior.enable_skip_ads)
        self.prompt_edit.setText(behavior.task_prompt)
        
        # Proxy
        proxy = session.proxy
        self.proxy_enabled.setChecked(proxy.enabled)
        index = self.proxy_type.findText(proxy.proxy_type)
        if index >= 0:
            self.proxy_type.setCurrentIndex(index)
        self.proxy_server.setText(proxy.server)
        self.proxy_port.setValue(proxy.port if proxy.port > 0 else 8080)
        self.proxy_user.setText(proxy.username)
        self.proxy_pass.setText(proxy.password)
        
        # Fingerprint
        fp = session.fingerprint
        for i in range(self.device_preset.count()):
            if self.device_preset.itemData(i) == fp.device_preset:
                self.device_preset.setCurrentIndex(i)
                break
        self.user_agent_edit.setText(fp.user_agent)
        self.viewport_width.setValue(fp.viewport_width)
        self.viewport_height.setValue(fp.viewport_height)
        self.hardware_concurrency.setValue(fp.hardware_concurrency)
        self.device_memory.setValue(fp.device_memory)
        index = self.timezone_combo.findText(fp.timezone)
        if index >= 0:
            self.timezone_combo.setCurrentIndex(index)
        self.canvas_noise.setChecked(fp.canvas_noise_enabled)
        # Sync both canvas noise controls
        self.canvas_noise_level.setValue(fp.canvas_noise_level)
        self.adv_canvas_noise.setValue(fp.canvas_noise_level)
        self.adv_canvas_noise_label.setText(str(fp.canvas_noise_level))
        self.webrtc_protection.setChecked(fp.webrtc_protection_enabled)
        self.webgl_spoofing.setChecked(fp.webgl_spoofing_enabled)
        self.audio_spoofing.setChecked(fp.audio_context_spoofing_enabled)
        self.font_spoofing.setChecked(fp.font_spoofing_enabled)
        
        # Advanced Spoofing (from fase2.txt)
        index = self.tls_profile.findText(fp.tls_profile)
        if index >= 0:
            self.tls_profile.setCurrentIndex(index)
        self.client_hints_enabled.setChecked(fp.client_hints_enabled)
        self.webgpu_enabled.setChecked(fp.webgpu_spoofing_enabled)
        self.webgpu_vendor.setText(fp.webgpu_vendor)
        index = self.webgpu_architecture.findText(fp.webgpu_architecture)
        if index >= 0:
            self.webgpu_architecture.setCurrentIndex(index)
        # Canvas noise already set above in fingerprint section
        self.custom_fonts_edit.setText("\n".join(fp.custom_fonts))
        
        # Behavior Simulation (from fase2.txt)
        self.mouse_jitter_enabled.setChecked(behavior.mouse_jitter_enabled)
        self.mouse_jitter_px.setValue(behavior.mouse_jitter_px)
        self.enable_random_hover.setChecked(behavior.enable_random_hover)
        self.idle_time_min.setValue(behavior.idle_time_min_sec)
        self.idle_time_max.setValue(behavior.idle_time_max_sec)
        self.random_action_prob.setValue(int(behavior.random_action_probability * 100))
        self.scroll_enabled.setChecked(behavior.scroll_simulation_enabled)
        self.enable_random_scroll.setChecked(behavior.enable_random_scroll)
        self.scroll_delta_min.setValue(behavior.scroll_delta_min)
        self.scroll_delta_max.setValue(behavior.scroll_delta_max)
        self.typing_speed_min.setValue(behavior.typing_speed_min_ms)
        self.typing_speed_max.setValue(behavior.typing_speed_max_ms)
        self.typing_mistake_rate.setValue(int(behavior.typing_mistake_rate * 100))
        
        # CAPTCHA (from fase2.txt)
        captcha = session.captcha
        self.captcha_enabled.setChecked(captcha.enabled)
        index = self.captcha_provider.findText(captcha.provider)
        if index >= 0:
            self.captcha_provider.setCurrentIndex(index)
        self.captcha_recaptcha_v2.setChecked("recaptcha_v2" in captcha.captcha_types)
        self.captcha_recaptcha_v3.setChecked("recaptcha_v3" in captcha.captcha_types)
        self.captcha_hcaptcha.setChecked("hcaptcha" in captcha.captcha_types)
        self.captcha_timeout.setValue(captcha.timeout_sec)
        self.captcha_max_retries.setValue(captcha.max_retries)
        
        # CAPTCHA Hybrid settings (from fase3.txt)
        self.captcha_hybrid_mode.setChecked(captcha.hybrid_mode)
        index = self.captcha_secondary_provider.findText(captcha.secondary_provider)
        if index >= 0:
            self.captcha_secondary_provider.setCurrentIndex(index)
        
        # Retry settings
        self.max_retries.setValue(session.max_retries)
        self.retry_delay.setValue(session.retry_delay_sec)
        self.exponential_backoff.setChecked(session.exponential_backoff)
        
        # Contingency settings (from fase3.txt)
        contingency = session.contingency
        self.block_rate_threshold.setValue(contingency.block_rate_threshold)
        self.consecutive_failure_threshold.setValue(contingency.consecutive_failure_threshold)
        self.cool_down_min.setValue(contingency.cool_down_min_sec)
        self.cool_down_max.setValue(contingency.cool_down_max_sec)
        index = self.ban_recovery_strategy.findText(contingency.ban_recovery_strategy)
        if index >= 0:
            self.ban_recovery_strategy.setCurrentIndex(index)
        self.enable_dynamic_throttling.setChecked(contingency.enable_dynamic_throttling)
        self.sticky_session_duration.setValue(contingency.sticky_session_duration_sec)
        self.enable_session_persistence.setChecked(contingency.enable_session_persistence)
        
        # Advanced Behavior settings (from fase3.txt)
        adv_behavior = session.advanced_behavior
        self.polymorphic_enabled.setChecked(adv_behavior.polymorphic_fingerprint_enabled)
        self.fingerprint_rotation_interval.setValue(adv_behavior.fingerprint_rotation_interval_sec)
        self.os_level_input_enabled.setChecked(adv_behavior.os_level_input_enabled)
        self.touch_emulation_enabled.setChecked(adv_behavior.touch_emulation_enabled)
        self.touch_pressure_variation.setValue(adv_behavior.touch_pressure_variation)
        self.micro_jitter_enabled.setChecked(adv_behavior.micro_jitter_enabled)
        self.micro_jitter_amplitude.setValue(adv_behavior.micro_jitter_amplitude)
        self.typing_pressure_enabled.setChecked(adv_behavior.typing_pressure_enabled)
        self.typing_rhythm_variation.setValue(adv_behavior.typing_rhythm_variation)
        
        # System Hiding settings (from fase3.txt)
        system_hiding = session.system_hiding
        self.block_cdp_ports.setChecked(system_hiding.block_cdp_ports)
        self.cdp_port_default.setValue(system_hiding.cdp_port_default)
        self.disable_loopback_services.setChecked(system_hiding.disable_loopback_services)
        self.randomize_ephemeral_ports.setChecked(system_hiding.randomize_ephemeral_ports)
        self.ephemeral_port_min.setValue(system_hiding.ephemeral_port_min)
        self.ephemeral_port_max.setValue(system_hiding.ephemeral_port_max)
        self.block_webrtc_completely.setChecked(system_hiding.block_webrtc_completely)
        
        # MFA settings (from fase3.txt)
        mfa = session.mfa
        self.mfa_simulation_enabled.setChecked(mfa.mfa_simulation_enabled)
        index = self.mfa_method.findText(mfa.mfa_method)
        if index >= 0:
            self.mfa_method.setCurrentIndex(index)
        self.mfa_timeout.setValue(mfa.mfa_timeout_sec)
    
    def _on_session_name_changed(self, text: str):
        """Manejar cambio de nombre de sesión."""
        if self.current_session:
            self.current_session.name = text
    
    def _on_device_preset_changed(self, index: int):
        """Manejar cambio de preset de dispositivo."""
        preset_key = self.device_preset.itemData(index)
        fingerprint = self.fingerprint_manager.generate_fingerprint(preset_key)
        
        self.user_agent_edit.setText(fingerprint.user_agent)
        self.viewport_width.setValue(fingerprint.viewport_width)
        self.viewport_height.setValue(fingerprint.viewport_height)
        self.hardware_concurrency.setValue(fingerprint.hardware_concurrency)
        self.device_memory.setValue(fingerprint.device_memory)
    
    def _add_session(self):
        """Agregar una nueva sesión."""
        session = self.config_manager.create_session(f"Sesión {len(self.config_manager.get_all_sessions()) + 1}")
        self._load_sessions_list()
        
        # Seleccionar la nueva sesión
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == session.session_id:
                self.session_list.setCurrentItem(item)
                self._on_session_selected(item)
                break
        
        self.status_bar.showMessage(f"Nueva sesión creada: {session.name}")
    
    def _remove_session(self):
        """Eliminar la sesión seleccionada."""
        current_item = self.session_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione una sesión para eliminar.")
            return
        
        session_id = current_item.data(Qt.ItemDataRole.UserRole)
        session = self.config_manager.get_session(session_id)
        
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar '{session.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Detener si está ejecutándose
            if session_id in self.workers:
                self.workers[session_id].stop()
                self.workers[session_id].wait()
                del self.workers[session_id]
            
            self.config_manager.delete_session(session_id)
            self._load_sessions_list()
            self.current_session = None
            self.session_name_edit.clear()
            self.status_bar.showMessage(f"Sesión eliminada: {session.name}")
    
    def _save_current_session(self):
        """Guardar la configuración de la sesión actual."""
        if not self.current_session:
            QMessageBox.warning(self, "Advertencia", "No hay sesión seleccionada.")
            return
        
        session = self.current_session
        
        # Update behavior
        session.behavior.llm_model = self.model_combo.currentText()
        session.headless = self.headless_check.isChecked()
        session.behavior.ad_skip_delay_sec = self.ad_skip_delay.value()
        session.behavior.view_time_min_sec = self.view_time_min.value()
        session.behavior.view_time_max_sec = self.view_time_max.value()
        session.behavior.action_delay_min_ms = self.action_delay_min.value()
        session.behavior.action_delay_max_ms = self.action_delay_max.value()
        session.behavior.enable_like = self.enable_like.isChecked()
        session.behavior.enable_comment = self.enable_comment.isChecked()
        session.behavior.enable_subscribe = self.enable_subscribe.isChecked()
        session.behavior.enable_skip_ads = self.enable_skip_ads.isChecked()
        session.behavior.task_prompt = self.prompt_edit.toPlainText()
        
        # Update behavior simulation (from fase2.txt)
        session.behavior.idle_time_min_sec = self.idle_time_min.value()
        session.behavior.idle_time_max_sec = self.idle_time_max.value()
        session.behavior.mouse_jitter_enabled = self.mouse_jitter_enabled.isChecked()
        session.behavior.mouse_jitter_px = self.mouse_jitter_px.value()
        session.behavior.scroll_simulation_enabled = self.scroll_enabled.isChecked()
        session.behavior.scroll_delta_min = self.scroll_delta_min.value()
        session.behavior.scroll_delta_max = self.scroll_delta_max.value()
        session.behavior.typing_speed_min_ms = self.typing_speed_min.value()
        session.behavior.typing_speed_max_ms = self.typing_speed_max.value()
        session.behavior.typing_mistake_rate = self.typing_mistake_rate.value() / 100.0
        session.behavior.enable_random_hover = self.enable_random_hover.isChecked()
        session.behavior.enable_random_scroll = self.enable_random_scroll.isChecked()
        session.behavior.random_action_probability = self.random_action_prob.value() / 100.0
        
        # Update proxy
        session.proxy.enabled = self.proxy_enabled.isChecked()
        session.proxy.proxy_type = self.proxy_type.currentText()
        session.proxy.server = self.proxy_server.text()
        session.proxy.port = self.proxy_port.value()
        session.proxy.username = self.proxy_user.text()
        session.proxy.password = self.proxy_pass.text()
        
        # Update fingerprint
        session.fingerprint.device_preset = self.device_preset.currentData()
        session.fingerprint.user_agent = self.user_agent_edit.text()
        session.fingerprint.viewport_width = self.viewport_width.value()
        session.fingerprint.viewport_height = self.viewport_height.value()
        session.fingerprint.hardware_concurrency = self.hardware_concurrency.value()
        session.fingerprint.device_memory = self.device_memory.value()
        session.fingerprint.timezone = self.timezone_combo.currentText()
        session.fingerprint.canvas_noise_enabled = self.canvas_noise.isChecked()
        # Use the advanced canvas noise slider value as the primary source
        session.fingerprint.canvas_noise_level = self.adv_canvas_noise.value()
        session.fingerprint.webrtc_protection_enabled = self.webrtc_protection.isChecked()
        session.fingerprint.webgl_spoofing_enabled = self.webgl_spoofing.isChecked()
        session.fingerprint.audio_context_spoofing_enabled = self.audio_spoofing.isChecked()
        session.fingerprint.font_spoofing_enabled = self.font_spoofing.isChecked()
        
        # Update advanced spoofing (from fase2.txt)
        session.fingerprint.tls_profile = self.tls_profile.currentText()
        session.fingerprint.client_hints_enabled = self.client_hints_enabled.isChecked()
        session.fingerprint.webgpu_spoofing_enabled = self.webgpu_enabled.isChecked()
        session.fingerprint.webgpu_vendor = self.webgpu_vendor.text()
        session.fingerprint.webgpu_architecture = self.webgpu_architecture.currentText()
        session.fingerprint.custom_fonts = [f.strip() for f in self.custom_fonts_edit.toPlainText().split('\n') if f.strip()]
        
        # Update CAPTCHA settings (from fase2.txt)
        session.captcha.enabled = self.captcha_enabled.isChecked()
        session.captcha.provider = self.captcha_provider.currentText()
        captcha_types = []
        if self.captcha_recaptcha_v2.isChecked():
            captcha_types.append("recaptcha_v2")
        if self.captcha_recaptcha_v3.isChecked():
            captcha_types.append("recaptcha_v3")
        if self.captcha_hcaptcha.isChecked():
            captcha_types.append("hcaptcha")
        session.captcha.captcha_types = captcha_types
        session.captcha.timeout_sec = self.captcha_timeout.value()
        session.captcha.max_retries = self.captcha_max_retries.value()
        
        # Update CAPTCHA Hybrid settings (from fase3.txt)
        session.captcha.hybrid_mode = self.captcha_hybrid_mode.isChecked()
        session.captcha.secondary_provider = self.captcha_secondary_provider.currentText()
        
        # Update retry settings
        session.max_retries = self.max_retries.value()
        session.retry_delay_sec = self.retry_delay.value()
        session.exponential_backoff = self.exponential_backoff.isChecked()
        
        # Update Contingency settings (from fase3.txt)
        session.contingency.block_rate_threshold = self.block_rate_threshold.value()
        session.contingency.consecutive_failure_threshold = self.consecutive_failure_threshold.value()
        session.contingency.cool_down_min_sec = self.cool_down_min.value()
        session.contingency.cool_down_max_sec = self.cool_down_max.value()
        session.contingency.ban_recovery_strategy = self.ban_recovery_strategy.currentText()
        session.contingency.enable_dynamic_throttling = self.enable_dynamic_throttling.isChecked()
        session.contingency.sticky_session_duration_sec = self.sticky_session_duration.value()
        session.contingency.enable_session_persistence = self.enable_session_persistence.isChecked()
        
        # Update Advanced Behavior settings (from fase3.txt)
        session.advanced_behavior.polymorphic_fingerprint_enabled = self.polymorphic_enabled.isChecked()
        session.advanced_behavior.fingerprint_rotation_interval_sec = self.fingerprint_rotation_interval.value()
        session.advanced_behavior.os_level_input_enabled = self.os_level_input_enabled.isChecked()
        session.advanced_behavior.touch_emulation_enabled = self.touch_emulation_enabled.isChecked()
        session.advanced_behavior.touch_pressure_variation = self.touch_pressure_variation.value()
        session.advanced_behavior.micro_jitter_enabled = self.micro_jitter_enabled.isChecked()
        session.advanced_behavior.micro_jitter_amplitude = self.micro_jitter_amplitude.value()
        session.advanced_behavior.typing_pressure_enabled = self.typing_pressure_enabled.isChecked()
        session.advanced_behavior.typing_rhythm_variation = self.typing_rhythm_variation.value()
        
        # Update System Hiding settings (from fase3.txt)
        session.system_hiding.block_cdp_ports = self.block_cdp_ports.isChecked()
        session.system_hiding.cdp_port_default = self.cdp_port_default.value()
        session.system_hiding.disable_loopback_services = self.disable_loopback_services.isChecked()
        session.system_hiding.randomize_ephemeral_ports = self.randomize_ephemeral_ports.isChecked()
        session.system_hiding.ephemeral_port_min = self.ephemeral_port_min.value()
        session.system_hiding.ephemeral_port_max = self.ephemeral_port_max.value()
        session.system_hiding.block_webrtc_completely = self.block_webrtc_completely.isChecked()
        
        # Update MFA settings (from fase3.txt)
        session.mfa.mfa_simulation_enabled = self.mfa_simulation_enabled.isChecked()
        session.mfa.mfa_method = self.mfa_method.currentText()
        session.mfa.mfa_timeout_sec = self.mfa_timeout.value()
        
        # Almacenar clave API de CAPTCHA de forma segura (de fase2.txt)
        api_key = self.captcha_api_key.text()
        if api_key:
            try:
                from .advanced_features import SecureCredentialStore
                store = SecureCredentialStore()
                store.store_credential(f"captcha_api_key_{session.session_id}", api_key)
            except Exception as e:
                logger.warning(f"Error al almacenar clave API de forma segura: {e}")
        
        self.config_manager.update_session(session)
        self._load_sessions_list()
        self.status_bar.showMessage(f"Sesión guardada: {session.name}")
    
    def _start_selected_session(self):
        """Iniciar la sesión seleccionada."""
        if not self.current_session:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione una sesión para iniciar.")
            return
        
        session_id = self.current_session.session_id
        
        if session_id in self.workers:
            QMessageBox.warning(self, "Advertencia", "La sesión ya está en ejecución.")
            return
        
        worker = SessionWorker(self.current_session)
        worker.status_update.connect(self._on_session_status_update)
        worker.log_message.connect(self._on_log_message)
        worker.finished.connect(self._on_session_finished)
        
        self.workers[session_id] = worker
        worker.start()
        
        self.status_bar.showMessage(f"Sesión iniciada: {self.current_session.name}")
    
    def _stop_selected_session(self):
        """Detener la sesión seleccionada."""
        if not self.current_session:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione una sesión para detener.")
            return
        
        session_id = self.current_session.session_id
        
        if session_id not in self.workers:
            QMessageBox.warning(self, "Advertencia", "La sesión no está en ejecución.")
            return
        
        self.workers[session_id].stop()
        self.status_bar.showMessage(f"Deteniendo sesión: {self.current_session.name}")
    
    def _start_all_sessions(self):
        """Iniciar todas las sesiones."""
        for session in self.config_manager.get_all_sessions():
            if session.session_id not in self.workers:
                worker = SessionWorker(session)
                worker.status_update.connect(self._on_session_status_update)
                worker.log_message.connect(self._on_log_message)
                worker.finished.connect(self._on_session_finished)
                
                self.workers[session.session_id] = worker
                worker.start()
        
        self.status_bar.showMessage("Todas las sesiones iniciadas")
    
    def _stop_all_sessions(self):
        """Detener todas las sesiones en ejecución."""
        for session_id, worker in self.workers.items():
            worker.stop()
        
        self.status_bar.showMessage("Deteniendo todas las sesiones")
    
    def _on_session_status_update(self, session_id: str, status: str):
        """Manejar actualización de estado de sesión."""
        session = self.config_manager.get_session(session_id)
        if session:
            session.status = status
    
    def _on_log_message(self, session_id: str, message: str):
        """Manejar mensaje de registro de sesión."""
        session = self.config_manager.get_session(session_id)
        name = session.name if session else session_id
        self.log_display.append(f"[{name}] {message}")
    
    def _on_session_finished(self, session_id: str):
        """Manejar finalización de sesión."""
        if session_id in self.workers:
            del self.workers[session_id]
    
    def _add_proxy_to_pool(self):
        """Agregar un proxy al pool."""
        server = self.proxy_server.text()
        port = self.proxy_port.value()
        
        if not server:
            QMessageBox.warning(self, "Advertencia", "Por favor ingrese un servidor proxy.")
            return
        
        proxy = ProxyEntry(
            server=server,
            port=port,
            username=self.proxy_user.text(),
            password=self.proxy_pass.text(),
            proxy_type=self.proxy_type.currentText()
        )
        
        self.proxy_manager.add_proxy(proxy)
        self._load_proxy_pool()
        self.status_bar.showMessage(f"Proxy agregado: {server}:{port}")
    
    def _remove_proxy_from_pool(self):
        """Eliminar proxy seleccionado del pool."""
        current_row = self.proxy_pool_list.currentRow()
        if current_row >= 0:
            self.proxy_manager.remove_proxy(current_row)
            self._load_proxy_pool()
    
    def _import_proxies(self):
        """Importar proxies desde archivo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Proxies",
            "", "Archivos de Texto (*.txt);;Todos los Archivos (*)"
        )
        
        if file_path:
            count = self.proxy_manager.import_from_file(Path(file_path))
            self._load_proxy_pool()
            QMessageBox.information(
                self, "Importación Completa",
                f"Se importaron {count} proxies exitosamente."
            )
    
    def _validate_proxy_pool(self):
        """Validar todos los proxies en el pool (de fase2.txt)."""
        proxies = self.proxy_manager.get_all_proxies()
        if not proxies:
            QMessageBox.information(self, "Información", "No hay proxies para validar.")
            return
        
        self.status_bar.showMessage("Validando proxies...")
        
        # Ejecutar validación en un hilo para evitar bloquear la UI
        class ValidatorWorker(QThread):
            finished = pyqtSignal(list)
            
            def __init__(self, proxies):
                super().__init__()
                self.proxies = proxies
            
            def run(self):
                import asyncio
                try:
                    from .advanced_features import ProxyValidator
                    validator = ProxyValidator(timeout_sec=10)
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        proxy_configs = [
                            {
                                "server": p.server,
                                "port": p.port,
                                "type": p.proxy_type,
                                "username": p.username,
                                "password": p.password
                            }
                            for p in self.proxies
                        ]
                        results = loop.run_until_complete(validator.validate_pool(proxy_configs))
                        self.finished.emit(results)
                    finally:
                        loop.close()
                except Exception as e:
                    self.finished.emit([{"error": str(e)}])
        
        def on_validation_complete(results):
            valid_count = sum(1 for r in results if r.get("valid", False))
            invalid_count = len(results) - valid_count
            
            # Actualizar estado del proxy
            for i, result in enumerate(results):
                if i < len(proxies):
                    proxies[i].is_active = result.get("valid", False)
            
            self.proxy_manager._save_proxies()
            self._load_proxy_pool()
            
            QMessageBox.information(
                self, "Validación Completa",
                f"Válidos: {valid_count}\nInválidos: {invalid_count}"
            )
            self.status_bar.showMessage(f"Se validaron {len(results)} proxies")
        
        self._validator_worker = ValidatorWorker(proxies)
        self._validator_worker.finished.connect(on_validation_complete)
        self._validator_worker.start()
    
    def _clear_logs(self):
        """Limpiar la visualización de registros."""
        self.log_display.clear()
    
    def _export_logs(self):
        """Exportar registros a archivo."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Registros",
            "registros_sesion.txt", "Archivos de Texto (*.txt)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_display.toPlainText())
            self.status_bar.showMessage(f"Registros exportados a: {file_path}")
    
    def _update_resource_usage(self):
        """Actualizar visualización de uso de recursos."""
        if not PSUTIL_AVAILABLE:
            self.cpu_label.setText("CPU: N/D")
            self.ram_label.setText("RAM: N/D")
            return
        
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            
            self.cpu_label.setText(f"CPU: {cpu:.1f}%")
            self.cpu_bar.setValue(int(cpu))
            
            self.ram_label.setText(f"RAM: {ram:.1f}%")
            self.ram_bar.setValue(int(ram))
            
            # Código de colores basado en uso
            if cpu > 80:
                self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #c42b1c; }")
            elif cpu > 60:
                self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #ffa500; }")
            else:
                self.cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #16825d; }")
                
            if ram > 80:
                self.ram_bar.setStyleSheet("QProgressBar::chunk { background-color: #c42b1c; }")
            elif ram > 60:
                self.ram_bar.setStyleSheet("QProgressBar::chunk { background-color: #ffa500; }")
            else:
                self.ram_bar.setStyleSheet("QProgressBar::chunk { background-color: #16825d; }")
                
        except Exception:
            # Error obteniendo uso de recursos
            self.cpu_label.setText("CPU: N/D")
            self.ram_label.setText("RAM: N/D")
    
    def closeEvent(self, event):
        """Manejar evento de cierre de ventana."""
        # Detener todas las sesiones en ejecución
        if self.workers:
            reply = QMessageBox.question(
                self, "Confirmar Salida",
                "Hay sesiones en ejecución. ¿Detener todas y salir?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            for worker in self.workers.values():
                worker.stop()
            
            for worker in self.workers.values():
                worker.wait()
        
        event.accept()


def main():
    """Punto de entrada principal para la aplicación GUI."""
    app = QApplication(sys.argv)
    
    # Establecer metadatos de la aplicación
    app.setApplicationName("BotSOS")
    app.setApplicationVersion("1.2.0")
    app.setOrganizationName("BotSOS")
    
    window = SessionManagerGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
