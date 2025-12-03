"""
Widget de lista de sesiones.

Diseñado exclusivamente para Windows.
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal


class SessionListWidget(QWidget):
    """
    Widget para mostrar y gestionar la lista de sesiones.
    
    Emite señales cuando se selecciona una sesión o se ejecutan acciones.
    """
    
    session_selected = pyqtSignal(str)  # session_id
    add_requested = pyqtSignal()
    remove_requested = pyqtSignal(str)  # session_id
    start_requested = pyqtSignal(str)   # session_id
    stop_requested = pyqtSignal(str)    # session_id
    start_all_requested = pyqtSignal()
    stop_all_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configurar la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Encabezado
        header = QLabel("Sesiones")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Lista de sesiones
        self.session_list = QListWidget()
        self.session_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.session_list, stretch=1)
        
        # Botones de control
        btn_layout = QVBoxLayout()
        
        add_btn = QPushButton("➕ Agregar Sesión")
        add_btn.clicked.connect(self.add_requested.emit)
        btn_layout.addWidget(add_btn)
        
        self.remove_btn = QPushButton("🗑️ Eliminar Sesión")
        self.remove_btn.setObjectName("dangerBtn")
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        btn_layout.addWidget(self.remove_btn)
        
        btn_layout.addSpacing(10)
        
        self.start_btn = QPushButton("▶️ Iniciar Seleccionada")
        self.start_btn.setObjectName("successBtn")
        self.start_btn.clicked.connect(self._on_start_clicked)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Detener Seleccionada")
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        btn_layout.addWidget(self.stop_btn)
        
        btn_layout.addSpacing(10)
        
        start_all_btn = QPushButton("▶️▶️ Iniciar Todas")
        start_all_btn.setObjectName("successBtn")
        start_all_btn.clicked.connect(self.start_all_requested.emit)
        btn_layout.addWidget(start_all_btn)
        
        stop_all_btn = QPushButton("⏹️⏹️ Detener Todas")
        stop_all_btn.setObjectName("dangerBtn")
        stop_all_btn.clicked.connect(self.stop_all_requested.emit)
        btn_layout.addWidget(stop_all_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """Manejar clic en un elemento de la lista."""
        session_id = item.data(Qt.ItemDataRole.UserRole)
        self.session_selected.emit(session_id)
    
    def _on_remove_clicked(self):
        """Manejar clic en botón eliminar."""
        session_id = self.get_selected_session_id()
        if session_id:
            self.remove_requested.emit(session_id)
    
    def _on_start_clicked(self):
        """Manejar clic en botón iniciar."""
        session_id = self.get_selected_session_id()
        if session_id:
            self.start_requested.emit(session_id)
    
    def _on_stop_clicked(self):
        """Manejar clic en botón detener."""
        session_id = self.get_selected_session_id()
        if session_id:
            self.stop_requested.emit(session_id)
    
    def get_selected_session_id(self) -> Optional[str]:
        """Obtener el ID de la sesión seleccionada."""
        current_item = self.session_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def add_session(self, session_id: str, name: str) -> None:
        """Agregar una sesión a la lista."""
        item = QListWidgetItem(f"📋 {name}")
        item.setData(Qt.ItemDataRole.UserRole, session_id)
        self.session_list.addItem(item)
    
    def remove_session(self, session_id: str) -> bool:
        """Eliminar una sesión de la lista."""
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == session_id:
                self.session_list.takeItem(i)
                return True
        return False
    
    def clear(self) -> None:
        """Limpiar la lista de sesiones."""
        self.session_list.clear()
    
    def select_session(self, session_id: str) -> bool:
        """Seleccionar una sesión por ID."""
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == session_id:
                self.session_list.setCurrentItem(item)
                return True
        return False
