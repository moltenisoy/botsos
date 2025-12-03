"""
Session Manager GUI Module

Professional PyQt6-based graphical user interface for managing
multiple LLM-powered browser automation sessions.

Implements features from fase2.txt:
- Multi-session management with QThreadPool
- Advanced fingerprint spoofing configuration
- Behavior simulation settings
- CAPTCHA handling configuration
- Proxy validation and rotation
- Real-time logging and monitoring
"""

import sys
import json
import logging
import time
import asyncio
from pathlib import Path
from typing import Dict, Optional, List
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
from PyQt6.QtGui import QFont, QIcon, QColor

from .session_config import SessionConfig, SessionConfigManager, BehaviorConfig, CaptchaConfig
from .proxy_manager import ProxyManager, ProxyEntry
from .fingerprint_manager import FingerprintManager


logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """Signals for QRunnable worker communication (from fase2.txt)."""
    status_update = pyqtSignal(str, str)  # session_id, status
    log_message = pyqtSignal(str, str)    # session_id, message
    finished = pyqtSignal(str)             # session_id
    resource_update = pyqtSignal(float, float)  # CPU%, RAM%
    error = pyqtSignal(str, str)          # session_id, error_message


class SessionRunnable(QRunnable):
    """QRunnable worker for running browser sessions with QThreadPool (from fase2.txt)."""
    
    def __init__(self, session_config: SessionConfig):
        super().__init__()
        self.session_config = session_config
        self.signals = WorkerSignals()
        self._is_running = True
        self.setAutoDelete(True)
    
    def run(self):
        """Execute the session automation using asyncio."""
        session_id = self.session_config.session_id
        self.signals.status_update.emit(session_id, "running")
        self.signals.log_message.emit(session_id, f"Starting session: {self.session_config.name}")
        
        try:
            # Run the async session in a new event loop
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
            self.signals.status_update.emit(session_id, "idle")
            self.signals.finished.emit(session_id)
    
    async def _run_session(self):
        """Async session execution with retry logic."""
        session_id = self.session_config.session_id
        
        # Import advanced features
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
            
            self.signals.log_message.emit(session_id, "Advanced features loaded")
        except ImportError as e:
            self.signals.log_message.emit(session_id, f"Advanced features unavailable: {e}")
        
        # Session execution placeholder - integrate with browser_session.py
        self.signals.log_message.emit(session_id, "Session started - waiting for browser automation integration")
        
        while self._is_running:
            await asyncio.sleep(1)
    
    def stop(self):
        """Stop the session."""
        self._is_running = False


class SessionWorker(QThread):
    """Worker thread for running browser automation sessions."""
    
    status_update = pyqtSignal(str, str)  # session_id, status
    log_message = pyqtSignal(str, str)    # session_id, message
    finished = pyqtSignal(str)             # session_id
    
    def __init__(self, session_config: SessionConfig):
        super().__init__()
        self.session_config = session_config
        self._is_running = True
    
    def run(self):
        """Execute the session automation."""
        session_id = self.session_config.session_id
        self.status_update.emit(session_id, "running")
        self.log_message.emit(session_id, f"Starting session: {self.session_config.name}")
        
        try:
            # Run using asyncio for async browser operations
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
            self.status_update.emit(session_id, "idle")
            self.finished.emit(session_id)
    
    async def _run_async_session(self):
        """Async session with behavior simulation and retry logic."""
        session_id = self.session_config.session_id
        
        # Simulate session running with async support
        while self._is_running:
            await asyncio.sleep(1)
    
    def stop(self):
        """Stop the session."""
        self._is_running = False


class SessionManagerGUI(QMainWindow):
    """Main GUI window for the Multi-Model Session Manager."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize paths
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        
        # Initialize managers
        self.config_manager = SessionConfigManager(self.data_dir)
        self.proxy_manager = ProxyManager(self.data_dir)
        self.fingerprint_manager = FingerprintManager(self.config_dir)
        
        # Initialize QThreadPool for parallel session execution (from fase2.txt)
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(6)  # Limit based on hardware
        
        # Session workers (both QThread and QRunnable tracking)
        self.workers: Dict[str, SessionWorker] = {}
        self.runnables: Dict[str, SessionRunnable] = {}
        
        # Current session being edited
        self.current_session: Optional[SessionConfig] = None
        
        # Setup UI
        self._setup_window()
        self._setup_ui()
        self._setup_status_bar()
        self._load_sessions_list()
        
        # Resource monitoring timer
        self.resource_timer = QTimer()
        self.resource_timer.timeout.connect(self._update_resource_usage)
        self.resource_timer.start(5000)  # Every 5 seconds
        
        # Setup advanced logging (from fase2.txt)
        self._setup_advanced_logging()
    
    def _setup_advanced_logging(self):
        """Setup advanced logging with RotatingFileHandler (from fase2.txt)."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Main application logger
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
        """Configure the main window."""
        self.setWindowTitle("BotSOS - Multi-Model Session Manager")
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
        """Setup the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left sidebar - Session List
        sidebar = self._create_sidebar()
        splitter.addWidget(sidebar)
        
        # Right panel - Configuration Tabs
        config_panel = self._create_config_panel()
        splitter.addWidget(config_panel)
        
        # Set initial sizes (30% sidebar, 70% config)
        splitter.setSizes([350, 850])
        
        main_layout.addWidget(splitter)
    
    def _create_sidebar(self) -> QWidget:
        """Create the left sidebar with session list."""
        sidebar = QWidget()
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Sessions")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Session list
        self.session_list = QListWidget()
        self.session_list.itemClicked.connect(self._on_session_selected)
        layout.addWidget(self.session_list, stretch=1)
        
        # Session control buttons
        btn_layout = QVBoxLayout()
        
        add_btn = QPushButton("➕ Add Session")
        add_btn.clicked.connect(self._add_session)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("🗑️ Remove Session")
        remove_btn.setObjectName("dangerBtn")
        remove_btn.clicked.connect(self._remove_session)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addSpacing(10)
        
        start_btn = QPushButton("▶️ Start Selected")
        start_btn.setObjectName("successBtn")
        start_btn.clicked.connect(self._start_selected_session)
        btn_layout.addWidget(start_btn)
        
        stop_btn = QPushButton("⏹️ Stop Selected")
        stop_btn.clicked.connect(self._stop_selected_session)
        btn_layout.addWidget(stop_btn)
        
        btn_layout.addSpacing(10)
        
        start_all_btn = QPushButton("▶️▶️ Start All")
        start_all_btn.setObjectName("successBtn")
        start_all_btn.clicked.connect(self._start_all_sessions)
        btn_layout.addWidget(start_all_btn)
        
        stop_all_btn = QPushButton("⏹️⏹️ Stop All")
        stop_all_btn.setObjectName("dangerBtn")
        stop_all_btn.clicked.connect(self._stop_all_sessions)
        btn_layout.addWidget(stop_all_btn)
        
        layout.addLayout(btn_layout)
        
        # Resource usage
        resource_group = QGroupBox("System Resources")
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
        """Create the right configuration panel with tabs."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Session name header
        name_layout = QHBoxLayout()
        name_label = QLabel("Session:")
        name_label.setFont(QFont("Segoe UI", 12))
        self.session_name_edit = QLineEdit()
        self.session_name_edit.setPlaceholderText("Select a session...")
        self.session_name_edit.textChanged.connect(self._on_session_name_changed)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.session_name_edit, stretch=1)
        layout.addLayout(name_layout)
        
        # Configuration tabs
        self.config_tabs = QTabWidget()
        self.config_tabs.addTab(self._create_behavior_tab(), "🎮 Behaviors")
        self.config_tabs.addTab(self._create_proxy_tab(), "🌐 Proxy/IP")
        self.config_tabs.addTab(self._create_fingerprint_tab(), "🖥️ Fingerprint")
        self.config_tabs.addTab(self._create_advanced_spoof_tab(), "🔒 Advanced Spoof")
        self.config_tabs.addTab(self._create_behavior_simulation_tab(), "🤖 Behavior Sim")
        self.config_tabs.addTab(self._create_captcha_tab(), "🔑 CAPTCHA")
        self.config_tabs.addTab(self._create_logging_tab(), "📝 Logs")
        layout.addWidget(self.config_tabs)
        
        # Save button
        save_btn = QPushButton("💾 Save Configuration")
        save_btn.setObjectName("successBtn")
        save_btn.clicked.connect(self._save_current_session)
        layout.addWidget(save_btn)
        
        return panel
    
    def _create_behavior_tab(self) -> QWidget:
        """Create the behavior configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # LLM Settings
        llm_group = QGroupBox("LLM Model Settings")
        llm_layout = QFormLayout(llm_group)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "llama3.1:8b",
            "qwen2.5:7b", 
            "mistral-nemo:12b",
            "phi3.5:3.8b",
            "gemma2:9b"
        ])
        llm_layout.addRow("Model:", self.model_combo)
        
        self.headless_check = QCheckBox("Run in headless mode")
        llm_layout.addRow(self.headless_check)
        
        layout.addWidget(llm_group)
        
        # Timing Settings
        timing_group = QGroupBox("Timing Settings")
        timing_layout = QFormLayout(timing_group)
        
        self.ad_skip_delay = QSpinBox()
        self.ad_skip_delay.setRange(1, 30)
        self.ad_skip_delay.setValue(5)
        self.ad_skip_delay.setSuffix(" sec")
        timing_layout.addRow("Ad Skip Delay:", self.ad_skip_delay)
        
        self.view_time_min = QSpinBox()
        self.view_time_min.setRange(10, 300)
        self.view_time_min.setValue(30)
        self.view_time_min.setSuffix(" sec")
        timing_layout.addRow("Min View Time:", self.view_time_min)
        
        self.view_time_max = QSpinBox()
        self.view_time_max.setRange(30, 600)
        self.view_time_max.setValue(120)
        self.view_time_max.setSuffix(" sec")
        timing_layout.addRow("Max View Time:", self.view_time_max)
        
        self.action_delay_min = QSpinBox()
        self.action_delay_min.setRange(50, 1000)
        self.action_delay_min.setValue(100)
        self.action_delay_min.setSuffix(" ms")
        timing_layout.addRow("Min Action Delay:", self.action_delay_min)
        
        self.action_delay_max = QSpinBox()
        self.action_delay_max.setRange(100, 2000)
        self.action_delay_max.setValue(500)
        self.action_delay_max.setSuffix(" ms")
        timing_layout.addRow("Max Action Delay:", self.action_delay_max)
        
        layout.addWidget(timing_group)
        
        # Actions Settings
        actions_group = QGroupBox("Enabled Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.enable_like = QCheckBox("Enable Like")
        self.enable_like.setChecked(True)
        actions_layout.addWidget(self.enable_like)
        
        self.enable_comment = QCheckBox("Enable Comment")
        self.enable_comment.setChecked(True)
        actions_layout.addWidget(self.enable_comment)
        
        self.enable_subscribe = QCheckBox("Enable Subscribe")
        actions_layout.addWidget(self.enable_subscribe)
        
        self.enable_skip_ads = QCheckBox("Enable Skip Ads")
        self.enable_skip_ads.setChecked(True)
        actions_layout.addWidget(self.enable_skip_ads)
        
        layout.addWidget(actions_group)
        
        # Task Prompt
        prompt_group = QGroupBox("Task Prompt (YAML/JSON)")
        prompt_layout = QVBoxLayout(prompt_group)
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Enter your task prompt here...")
        self.prompt_edit.setMinimumHeight(150)
        prompt_layout.addWidget(self.prompt_edit)
        
        layout.addWidget(prompt_group)
        
        layout.addStretch()
        return tab
    
    def _create_proxy_tab(self) -> QWidget:
        """Create the proxy configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Single Proxy Settings
        single_group = QGroupBox("Session Proxy")
        single_layout = QFormLayout(single_group)
        
        self.proxy_enabled = QCheckBox("Enable Proxy")
        single_layout.addRow(self.proxy_enabled)
        
        self.proxy_type = QComboBox()
        self.proxy_type.addItems(["http", "https", "socks5"])
        single_layout.addRow("Type:", self.proxy_type)
        
        self.proxy_server = QLineEdit()
        self.proxy_server.setPlaceholderText("proxy.example.com")
        single_layout.addRow("Server:", self.proxy_server)
        
        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(8080)
        single_layout.addRow("Port:", self.proxy_port)
        
        self.proxy_user = QLineEdit()
        self.proxy_user.setPlaceholderText("username (optional)")
        single_layout.addRow("Username:", self.proxy_user)
        
        self.proxy_pass = QLineEdit()
        self.proxy_pass.setPlaceholderText("password (optional)")
        self.proxy_pass.setEchoMode(QLineEdit.EchoMode.Password)
        single_layout.addRow("Password:", self.proxy_pass)
        
        layout.addWidget(single_group)
        
        # Proxy Pool
        pool_group = QGroupBox("Proxy Pool")
        pool_layout = QVBoxLayout(pool_group)
        
        self.proxy_pool_list = QListWidget()
        self.proxy_pool_list.setMaximumHeight(150)
        pool_layout.addWidget(self.proxy_pool_list)
        
        pool_btn_layout = QHBoxLayout()
        
        add_proxy_btn = QPushButton("Add")
        add_proxy_btn.clicked.connect(self._add_proxy_to_pool)
        pool_btn_layout.addWidget(add_proxy_btn)
        
        remove_proxy_btn = QPushButton("Remove")
        remove_proxy_btn.clicked.connect(self._remove_proxy_from_pool)
        pool_btn_layout.addWidget(remove_proxy_btn)
        
        import_proxy_btn = QPushButton("Import...")
        import_proxy_btn.clicked.connect(self._import_proxies)
        pool_btn_layout.addWidget(import_proxy_btn)
        
        validate_proxy_btn = QPushButton("Validate All")
        validate_proxy_btn.clicked.connect(self._validate_proxy_pool)
        pool_btn_layout.addWidget(validate_proxy_btn)
        
        pool_layout.addLayout(pool_btn_layout)
        
        layout.addWidget(pool_group)
        
        # Rotation Settings
        rotation_group = QGroupBox("Rotation Settings")
        rotation_layout = QFormLayout(rotation_group)
        
        self.rotation_interval = QSpinBox()
        self.rotation_interval.setRange(1, 100)
        self.rotation_interval.setValue(10)
        self.rotation_interval.setSuffix(" requests")
        rotation_layout.addRow("Rotate Every:", self.rotation_interval)
        
        self.rotation_strategy = QComboBox()
        self.rotation_strategy.addItems(["Round Robin", "Random", "Best Performance"])
        rotation_layout.addRow("Strategy:", self.rotation_strategy)
        
        self.validate_before_use = QCheckBox("Validate Proxy Before Use")
        self.validate_before_use.setChecked(True)
        rotation_layout.addRow(self.validate_before_use)
        
        self.auto_deactivate_failed = QCheckBox("Auto-deactivate Failed Proxies")
        self.auto_deactivate_failed.setChecked(True)
        rotation_layout.addRow(self.auto_deactivate_failed)
        
        layout.addWidget(rotation_group)
        
        layout.addStretch()
        
        # Load proxy pool
        self._load_proxy_pool()
        
        return tab
    
    def _create_fingerprint_tab(self) -> QWidget:
        """Create the fingerprint/device configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Device Preset
        preset_group = QGroupBox("Device Preset")
        preset_layout = QFormLayout(preset_group)
        
        self.device_preset = QComboBox()
        preset_names = self.fingerprint_manager.get_preset_names()
        for name in preset_names:
            preset = self.fingerprint_manager.get_preset(name)
            display_name = preset.get("name", name) if preset else name
            self.device_preset.addItem(display_name, name)
        self.device_preset.currentIndexChanged.connect(self._on_device_preset_changed)
        preset_layout.addRow("Preset:", self.device_preset)
        
        self.randomize_on_start = QCheckBox("Randomize on session start")
        self.randomize_on_start.setChecked(True)
        preset_layout.addRow(self.randomize_on_start)
        
        layout.addWidget(preset_group)
        
        # Custom Settings
        custom_group = QGroupBox("Custom Settings")
        custom_layout = QFormLayout(custom_group)
        
        self.user_agent_edit = QLineEdit()
        self.user_agent_edit.setPlaceholderText("Auto-generated from preset")
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
        custom_layout.addRow("CPU Cores:", self.hardware_concurrency)
        
        self.device_memory = QSpinBox()
        self.device_memory.setRange(1, 128)
        self.device_memory.setValue(8)
        self.device_memory.setSuffix(" GB")
        custom_layout.addRow("Device Memory:", self.device_memory)
        
        self.timezone_combo = QComboBox()
        self.timezone_combo.addItems([
            "America/New_York",
            "America/Los_Angeles", 
            "America/Chicago",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo",
            "UTC"
        ])
        custom_layout.addRow("Timezone:", self.timezone_combo)
        
        layout.addWidget(custom_group)
        
        # Spoofing Options
        spoof_group = QGroupBox("Spoofing Options")
        spoof_layout = QVBoxLayout(spoof_group)
        
        self.canvas_noise = QCheckBox("Canvas Noise Injection")
        self.canvas_noise.setChecked(True)
        spoof_layout.addWidget(self.canvas_noise)
        
        noise_layout = QHBoxLayout()
        noise_layout.addWidget(QLabel("Noise Level:"))
        self.canvas_noise_level = QSpinBox()
        self.canvas_noise_level.setRange(0, 10)
        self.canvas_noise_level.setValue(5)
        noise_layout.addWidget(self.canvas_noise_level)
        noise_layout.addStretch()
        spoof_layout.addLayout(noise_layout)
        
        self.webrtc_protection = QCheckBox("WebRTC Protection")
        self.webrtc_protection.setChecked(True)
        spoof_layout.addWidget(self.webrtc_protection)
        
        self.webgl_spoofing = QCheckBox("WebGL Spoofing")
        self.webgl_spoofing.setChecked(True)
        spoof_layout.addWidget(self.webgl_spoofing)
        
        self.audio_spoofing = QCheckBox("Audio Context Spoofing")
        self.audio_spoofing.setChecked(True)
        spoof_layout.addWidget(self.audio_spoofing)
        
        self.font_spoofing = QCheckBox("Font Spoofing")
        self.font_spoofing.setChecked(True)
        spoof_layout.addWidget(self.font_spoofing)
        
        layout.addWidget(spoof_group)
        
        layout.addStretch()
        return tab
    
    def _create_advanced_spoof_tab(self) -> QWidget:
        """Create the advanced spoofing configuration tab (from fase2.txt - second block)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # TLS/JA3 Settings
        tls_group = QGroupBox("TLS/JA3 Fingerprint")
        tls_layout = QFormLayout(tls_group)
        
        self.tls_profile = QComboBox()
        self.tls_profile.addItems([
            "chrome_120",
            "chrome_110", 
            "firefox_121",
            "safari_17",
            "edge_120"
        ])
        tls_layout.addRow("TLS Profile:", self.tls_profile)
        
        self.client_hints_enabled = QCheckBox("Enable Client Hints")
        self.client_hints_enabled.setChecked(True)
        tls_layout.addRow(self.client_hints_enabled)
        
        layout.addWidget(tls_group)
        
        # WebGPU Settings
        webgpu_group = QGroupBox("WebGPU Spoofing")
        webgpu_layout = QFormLayout(webgpu_group)
        
        self.webgpu_enabled = QCheckBox("Enable WebGPU Spoofing")
        self.webgpu_enabled.setChecked(True)
        webgpu_layout.addRow(self.webgpu_enabled)
        
        self.webgpu_vendor = QLineEdit()
        self.webgpu_vendor.setText("Google Inc.")
        webgpu_layout.addRow("GPU Vendor:", self.webgpu_vendor)
        
        self.webgpu_architecture = QComboBox()
        self.webgpu_architecture.addItems(["x86_64", "arm64", "x86"])
        webgpu_layout.addRow("Architecture:", self.webgpu_architecture)
        
        layout.addWidget(webgpu_group)
        
        # Canvas/WebGL Advanced
        canvas_group = QGroupBox("Canvas & WebGL Advanced")
        canvas_layout = QFormLayout(canvas_group)
        
        noise_layout = QHBoxLayout()
        noise_layout.addWidget(QLabel("Canvas Noise (0-10):"))
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
        self.webgl_vendor_override.setPlaceholderText("Leave empty for preset value")
        canvas_layout.addRow("WebGL Vendor Override:", self.webgl_vendor_override)
        
        self.webgl_renderer_override = QLineEdit()
        self.webgl_renderer_override.setPlaceholderText("Leave empty for preset value")
        canvas_layout.addRow("WebGL Renderer Override:", self.webgl_renderer_override)
        
        layout.addWidget(canvas_group)
        
        # Font Spoofing
        font_group = QGroupBox("Font Spoofing")
        font_layout = QVBoxLayout(font_group)
        
        self.custom_fonts_edit = QTextEdit()
        self.custom_fonts_edit.setMaximumHeight(100)
        self.custom_fonts_edit.setPlaceholderText("One font per line:\nArial\nHelvetica\nTimes New Roman")
        self.custom_fonts_edit.setText("Arial\nHelvetica\nTimes New Roman\nGeorgia\nVerdana\nCourier New")
        font_layout.addWidget(self.custom_fonts_edit)
        
        layout.addWidget(font_group)
        
        layout.addStretch()
        return tab
    
    def _create_behavior_simulation_tab(self) -> QWidget:
        """Create the behavior simulation configuration tab (from fase2.txt - second block)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Mouse Simulation
        mouse_group = QGroupBox("Mouse Simulation")
        mouse_layout = QFormLayout(mouse_group)
        
        self.mouse_jitter_enabled = QCheckBox("Enable Mouse Jitter")
        self.mouse_jitter_enabled.setChecked(True)
        mouse_layout.addRow(self.mouse_jitter_enabled)
        
        self.mouse_jitter_px = QSpinBox()
        self.mouse_jitter_px.setRange(1, 20)
        self.mouse_jitter_px.setValue(5)
        self.mouse_jitter_px.setSuffix(" px")
        mouse_layout.addRow("Jitter Amount:", self.mouse_jitter_px)
        
        self.enable_random_hover = QCheckBox("Enable Random Hover")
        self.enable_random_hover.setChecked(True)
        mouse_layout.addRow(self.enable_random_hover)
        
        layout.addWidget(mouse_group)
        
        # Timing Simulation
        timing_group = QGroupBox("Timing Simulation")
        timing_layout = QFormLayout(timing_group)
        
        self.idle_time_min = QDoubleSpinBox()
        self.idle_time_min.setRange(0.5, 60.0)
        self.idle_time_min.setValue(5.0)
        self.idle_time_min.setSuffix(" sec")
        timing_layout.addRow("Min Idle Time:", self.idle_time_min)
        
        self.idle_time_max = QDoubleSpinBox()
        self.idle_time_max.setRange(1.0, 120.0)
        self.idle_time_max.setValue(15.0)
        self.idle_time_max.setSuffix(" sec")
        timing_layout.addRow("Max Idle Time:", self.idle_time_max)
        
        self.random_action_prob = QSpinBox()
        self.random_action_prob.setRange(0, 50)
        self.random_action_prob.setValue(10)
        self.random_action_prob.setSuffix(" %")
        timing_layout.addRow("Random Action Probability:", self.random_action_prob)
        
        layout.addWidget(timing_group)
        
        # Scroll Simulation
        scroll_group = QGroupBox("Scroll Simulation")
        scroll_layout = QFormLayout(scroll_group)
        
        self.scroll_enabled = QCheckBox("Enable Scroll Simulation")
        self.scroll_enabled.setChecked(True)
        scroll_layout.addRow(self.scroll_enabled)
        
        self.enable_random_scroll = QCheckBox("Enable Random Scroll")
        self.enable_random_scroll.setChecked(True)
        scroll_layout.addRow(self.enable_random_scroll)
        
        self.scroll_delta_min = QSpinBox()
        self.scroll_delta_min.setRange(10, 500)
        self.scroll_delta_min.setValue(50)
        self.scroll_delta_min.setSuffix(" px")
        scroll_layout.addRow("Min Scroll Delta:", self.scroll_delta_min)
        
        self.scroll_delta_max = QSpinBox()
        self.scroll_delta_max.setRange(50, 1000)
        self.scroll_delta_max.setValue(300)
        self.scroll_delta_max.setSuffix(" px")
        scroll_layout.addRow("Max Scroll Delta:", self.scroll_delta_max)
        
        layout.addWidget(scroll_group)
        
        # Typing Simulation
        typing_group = QGroupBox("Typing Simulation")
        typing_layout = QFormLayout(typing_group)
        
        self.typing_speed_min = QSpinBox()
        self.typing_speed_min.setRange(10, 300)
        self.typing_speed_min.setValue(50)
        self.typing_speed_min.setSuffix(" ms")
        typing_layout.addRow("Min Keystroke Delay:", self.typing_speed_min)
        
        self.typing_speed_max = QSpinBox()
        self.typing_speed_max.setRange(50, 500)
        self.typing_speed_max.setValue(200)
        self.typing_speed_max.setSuffix(" ms")
        typing_layout.addRow("Max Keystroke Delay:", self.typing_speed_max)
        
        self.typing_mistake_rate = QSpinBox()
        self.typing_mistake_rate.setRange(0, 10)
        self.typing_mistake_rate.setValue(2)
        self.typing_mistake_rate.setSuffix(" %")
        typing_layout.addRow("Typo Rate:", self.typing_mistake_rate)
        
        layout.addWidget(typing_group)
        
        layout.addStretch()
        return tab
    
    def _create_captcha_tab(self) -> QWidget:
        """Create the CAPTCHA handling configuration tab (from fase2.txt - second block)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # CAPTCHA Settings
        captcha_group = QGroupBox("CAPTCHA Solving")
        captcha_layout = QFormLayout(captcha_group)
        
        self.captcha_enabled = QCheckBox("Enable Auto CAPTCHA Solving")
        self.captcha_enabled.setChecked(False)
        captcha_layout.addRow(self.captcha_enabled)
        
        self.captcha_provider = QComboBox()
        self.captcha_provider.addItems(["2captcha", "anticaptcha", "capsolver"])
        captcha_layout.addRow("Provider:", self.captcha_provider)
        
        self.captcha_api_key = QLineEdit()
        self.captcha_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.captcha_api_key.setPlaceholderText("Enter API key (stored securely)")
        captcha_layout.addRow("API Key:", self.captcha_api_key)
        
        layout.addWidget(captcha_group)
        
        # CAPTCHA Types
        types_group = QGroupBox("Supported CAPTCHA Types")
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
        
        # CAPTCHA Options
        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)
        
        self.captcha_timeout = QSpinBox()
        self.captcha_timeout.setRange(30, 300)
        self.captcha_timeout.setValue(120)
        self.captcha_timeout.setSuffix(" sec")
        options_layout.addRow("Solve Timeout:", self.captcha_timeout)
        
        self.captcha_max_retries = QSpinBox()
        self.captcha_max_retries.setRange(1, 10)
        self.captcha_max_retries.setValue(3)
        options_layout.addRow("Max Retries:", self.captcha_max_retries)
        
        layout.addWidget(options_group)
        
        # Retry Settings (from fase2.txt)
        retry_group = QGroupBox("Retry Settings")
        retry_layout = QFormLayout(retry_group)
        
        self.max_retries = QSpinBox()
        self.max_retries.setRange(0, 10)
        self.max_retries.setValue(3)
        retry_layout.addRow("Max Action Retries:", self.max_retries)
        
        self.retry_delay = QDoubleSpinBox()
        self.retry_delay.setRange(0.5, 30.0)
        self.retry_delay.setValue(1.0)
        self.retry_delay.setSuffix(" sec")
        retry_layout.addRow("Retry Base Delay:", self.retry_delay)
        
        self.exponential_backoff = QCheckBox("Use Exponential Backoff")
        self.exponential_backoff.setChecked(True)
        retry_layout.addRow(self.exponential_backoff)
        
        layout.addWidget(retry_group)
        
        # Secure Storage Info
        info_label = QLabel(
            "ℹ️ API keys are stored securely using system keyring when available.\n"
            "Falls back to environment variables if keyring is unavailable."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #808080; font-size: 10px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        return tab
    
    def _create_logging_tab(self) -> QWidget:
        """Create the logging/monitoring tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Log Display
        log_group = QGroupBox("Session Logs")
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
        
        clear_log_btn = QPushButton("Clear Logs")
        clear_log_btn.clicked.connect(self._clear_logs)
        log_btn_layout.addWidget(clear_log_btn)
        
        export_log_btn = QPushButton("Export Logs...")
        export_log_btn.clicked.connect(self._export_logs)
        log_btn_layout.addWidget(export_log_btn)
        
        log_layout.addLayout(log_btn_layout)
        
        layout.addWidget(log_group)
        
        return tab
    
    def _setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _load_sessions_list(self):
        """Load sessions into the list widget."""
        self.session_list.clear()
        for session in self.config_manager.get_all_sessions():
            item = QListWidgetItem(f"📋 {session.name}")
            item.setData(Qt.ItemDataRole.UserRole, session.session_id)
            self.session_list.addItem(item)
    
    def _load_proxy_pool(self):
        """Load proxies into the pool list."""
        self.proxy_pool_list.clear()
        for proxy in self.proxy_manager.get_all_proxies():
            status = "✅" if proxy.is_active else "❌"
            self.proxy_pool_list.addItem(f"{status} {proxy.server}:{proxy.port}")
    
    def _on_session_selected(self, item: QListWidgetItem):
        """Handle session selection."""
        session_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_session = self.config_manager.get_session(session_id)
        
        if self.current_session:
            self._populate_form(self.current_session)
            self.status_bar.showMessage(f"Loaded session: {self.current_session.name}")
    
    def _populate_form(self, session: SessionConfig):
        """Populate the form with session data."""
        # Basic info
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
        self.canvas_noise_level.setValue(fp.canvas_noise_level)
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
        self.adv_canvas_noise.setValue(fp.canvas_noise_level)
        self.adv_canvas_noise_label.setText(str(fp.canvas_noise_level))
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
        
        # Retry settings
        self.max_retries.setValue(session.max_retries)
        self.retry_delay.setValue(session.retry_delay_sec)
        self.exponential_backoff.setChecked(session.exponential_backoff)
    
    def _on_session_name_changed(self, text: str):
        """Handle session name change."""
        if self.current_session:
            self.current_session.name = text
    
    def _on_device_preset_changed(self, index: int):
        """Handle device preset change."""
        preset_key = self.device_preset.itemData(index)
        fingerprint = self.fingerprint_manager.generate_fingerprint(preset_key)
        
        self.user_agent_edit.setText(fingerprint.user_agent)
        self.viewport_width.setValue(fingerprint.viewport_width)
        self.viewport_height.setValue(fingerprint.viewport_height)
        self.hardware_concurrency.setValue(fingerprint.hardware_concurrency)
        self.device_memory.setValue(fingerprint.device_memory)
    
    def _add_session(self):
        """Add a new session."""
        session = self.config_manager.create_session(f"Session {len(self.config_manager.get_all_sessions()) + 1}")
        self._load_sessions_list()
        
        # Select the new session
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == session.session_id:
                self.session_list.setCurrentItem(item)
                self._on_session_selected(item)
                break
        
        self.status_bar.showMessage(f"Created new session: {session.name}")
    
    def _remove_session(self):
        """Remove the selected session."""
        current_item = self.session_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a session to remove.")
            return
        
        session_id = current_item.data(Qt.ItemDataRole.UserRole)
        session = self.config_manager.get_session(session_id)
        
        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Are you sure you want to remove '{session.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Stop if running
            if session_id in self.workers:
                self.workers[session_id].stop()
                self.workers[session_id].wait()
                del self.workers[session_id]
            
            self.config_manager.delete_session(session_id)
            self._load_sessions_list()
            self.current_session = None
            self.session_name_edit.clear()
            self.status_bar.showMessage(f"Removed session: {session.name}")
    
    def _save_current_session(self):
        """Save the current session configuration."""
        if not self.current_session:
            QMessageBox.warning(self, "Warning", "No session selected.")
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
        session.fingerprint.canvas_noise_level = self.canvas_noise_level.value()
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
        
        # Update retry settings
        session.max_retries = self.max_retries.value()
        session.retry_delay_sec = self.retry_delay.value()
        session.exponential_backoff = self.exponential_backoff.isChecked()
        
        # Store CAPTCHA API key securely (from fase2.txt)
        api_key = self.captcha_api_key.text()
        if api_key:
            try:
                from .advanced_features import SecureCredentialStore
                store = SecureCredentialStore()
                store.store_credential(f"captcha_api_key_{session.session_id}", api_key)
            except Exception as e:
                logger.warning(f"Failed to store API key securely: {e}")
        
        self.config_manager.update_session(session)
        self._load_sessions_list()
        self.status_bar.showMessage(f"Saved session: {session.name}")
    
    def _start_selected_session(self):
        """Start the selected session."""
        if not self.current_session:
            QMessageBox.warning(self, "Warning", "Please select a session to start.")
            return
        
        session_id = self.current_session.session_id
        
        if session_id in self.workers:
            QMessageBox.warning(self, "Warning", "Session is already running.")
            return
        
        worker = SessionWorker(self.current_session)
        worker.status_update.connect(self._on_session_status_update)
        worker.log_message.connect(self._on_log_message)
        worker.finished.connect(self._on_session_finished)
        
        self.workers[session_id] = worker
        worker.start()
        
        self.status_bar.showMessage(f"Started session: {self.current_session.name}")
    
    def _stop_selected_session(self):
        """Stop the selected session."""
        if not self.current_session:
            QMessageBox.warning(self, "Warning", "Please select a session to stop.")
            return
        
        session_id = self.current_session.session_id
        
        if session_id not in self.workers:
            QMessageBox.warning(self, "Warning", "Session is not running.")
            return
        
        self.workers[session_id].stop()
        self.status_bar.showMessage(f"Stopping session: {self.current_session.name}")
    
    def _start_all_sessions(self):
        """Start all sessions."""
        for session in self.config_manager.get_all_sessions():
            if session.session_id not in self.workers:
                worker = SessionWorker(session)
                worker.status_update.connect(self._on_session_status_update)
                worker.log_message.connect(self._on_log_message)
                worker.finished.connect(self._on_session_finished)
                
                self.workers[session.session_id] = worker
                worker.start()
        
        self.status_bar.showMessage("Started all sessions")
    
    def _stop_all_sessions(self):
        """Stop all running sessions."""
        for session_id, worker in self.workers.items():
            worker.stop()
        
        self.status_bar.showMessage("Stopping all sessions")
    
    def _on_session_status_update(self, session_id: str, status: str):
        """Handle session status update."""
        session = self.config_manager.get_session(session_id)
        if session:
            session.status = status
    
    def _on_log_message(self, session_id: str, message: str):
        """Handle log message from session."""
        session = self.config_manager.get_session(session_id)
        name = session.name if session else session_id
        self.log_display.append(f"[{name}] {message}")
    
    def _on_session_finished(self, session_id: str):
        """Handle session completion."""
        if session_id in self.workers:
            del self.workers[session_id]
    
    def _add_proxy_to_pool(self):
        """Add a proxy to the pool."""
        server = self.proxy_server.text()
        port = self.proxy_port.value()
        
        if not server:
            QMessageBox.warning(self, "Warning", "Please enter a proxy server.")
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
        self.status_bar.showMessage(f"Added proxy: {server}:{port}")
    
    def _remove_proxy_from_pool(self):
        """Remove selected proxy from pool."""
        current_row = self.proxy_pool_list.currentRow()
        if current_row >= 0:
            self.proxy_manager.remove_proxy(current_row)
            self._load_proxy_pool()
    
    def _import_proxies(self):
        """Import proxies from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Proxies",
            "", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            count = self.proxy_manager.import_from_file(Path(file_path))
            self._load_proxy_pool()
            QMessageBox.information(
                self, "Import Complete",
                f"Successfully imported {count} proxies."
            )
    
    def _validate_proxy_pool(self):
        """Validate all proxies in the pool (from fase2.txt)."""
        proxies = self.proxy_manager.get_all_proxies()
        if not proxies:
            QMessageBox.information(self, "Info", "No proxies to validate.")
            return
        
        self.status_bar.showMessage("Validating proxies...")
        
        # Run validation in a thread to avoid blocking UI
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
            
            # Update proxy status
            for i, result in enumerate(results):
                if i < len(proxies):
                    proxies[i].is_active = result.get("valid", False)
            
            self.proxy_manager._save_proxies()
            self._load_proxy_pool()
            
            QMessageBox.information(
                self, "Validation Complete",
                f"Valid: {valid_count}\nInvalid: {invalid_count}"
            )
            self.status_bar.showMessage(f"Validated {len(results)} proxies")
        
        self._validator_worker = ValidatorWorker(proxies)
        self._validator_worker.finished.connect(on_validation_complete)
        self._validator_worker.start()
    
    def _clear_logs(self):
        """Clear the log display."""
        self.log_display.clear()
    
    def _export_logs(self):
        """Export logs to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs",
            "session_logs.txt", "Text Files (*.txt)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_display.toPlainText())
            self.status_bar.showMessage(f"Logs exported to: {file_path}")
    
    def _update_resource_usage(self):
        """Update resource usage display."""
        if not PSUTIL_AVAILABLE:
            self.cpu_label.setText("CPU: N/A")
            self.ram_label.setText("RAM: N/A")
            return
        
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            
            self.cpu_label.setText(f"CPU: {cpu:.1f}%")
            self.cpu_bar.setValue(int(cpu))
            
            self.ram_label.setText(f"RAM: {ram:.1f}%")
            self.ram_bar.setValue(int(ram))
            
            # Color coding based on usage
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
            # Error getting resource usage
            self.cpu_label.setText("CPU: N/A")
            self.ram_label.setText("RAM: N/A")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop all running sessions
        if self.workers:
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "There are running sessions. Stop all and exit?",
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
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("BotSOS")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("BotSOS")
    
    window = SessionManagerGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
