"""
Widget de monitoreo de recursos del sistema.

Diseñado exclusivamente para Windows.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QGroupBox

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class ResourceMonitor(QWidget):
    """
    Widget para monitorear y mostrar el uso de recursos del sistema.
    
    Muestra barras de progreso para CPU y RAM con código de colores
    basado en el nivel de uso.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configurar la interfaz del widget."""
        group = QGroupBox("Recursos del Sistema")
        layout = QVBoxLayout(group)
        
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.cpu_bar)
        
        self.ram_label = QLabel("RAM: 0%")
        self.ram_bar = QProgressBar()
        self.ram_bar.setMaximum(100)
        layout.addWidget(self.ram_label)
        layout.addWidget(self.ram_bar)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(group)
        main_layout.setContentsMargins(0, 0, 0, 0)
    
    def update_values(self) -> None:
        """Actualizar los valores de uso de recursos."""
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
            self._apply_color_to_bar(self.cpu_bar, cpu)
            self._apply_color_to_bar(self.ram_bar, ram)
                
        except Exception:
            self.cpu_label.setText("CPU: N/D")
            self.ram_label.setText("RAM: N/D")
    
    def _apply_color_to_bar(self, bar: QProgressBar, value: float) -> None:
        """Aplicar color a la barra de progreso según el valor."""
        if value > 80:
            color = "#c42b1c"  # Rojo
        elif value > 60:
            color = "#ffa500"  # Naranja
        else:
            color = "#16825d"  # Verde
        
        bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
    
    def get_cpu_percent(self) -> float:
        """Obtener el porcentaje de uso de CPU."""
        if PSUTIL_AVAILABLE:
            return psutil.cpu_percent()
        return 0.0
    
    def get_ram_percent(self) -> float:
        """Obtener el porcentaje de uso de RAM."""
        if PSUTIL_AVAILABLE:
            return psutil.virtual_memory().percent
        return 0.0
