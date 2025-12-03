"""
Pestaña de configuración de comportamiento.

Diseñado exclusivamente para Windows.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QCheckBox, QTextEdit
)


def create_behavior_tab(parent) -> QWidget:
    """
    Crear la pestaña de configuración de comportamiento.
    
    Args:
        parent: Ventana padre para almacenar referencias a widgets.
        
    Returns:
        Widget de la pestaña configurado.
    """
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # Configuración de LLM
    llm_group = QGroupBox("Configuración del Modelo LLM")
    llm_layout = QFormLayout(llm_group)
    
    parent.model_combo = QComboBox()
    parent.model_combo.addItems([
        "llama3.1:8b",
        "qwen2.5:7b", 
        "mistral-nemo:12b",
        "phi3.5:3.8b",
        "gemma2:9b"
    ])
    llm_layout.addRow("Modelo:", parent.model_combo)
    
    parent.headless_check = QCheckBox("Ejecutar en modo oculto")
    llm_layout.addRow(parent.headless_check)
    
    layout.addWidget(llm_group)
    
    # Configuración de Tiempos
    timing_group = QGroupBox("Configuración de Tiempos")
    timing_layout = QFormLayout(timing_group)
    
    parent.ad_skip_delay = QSpinBox()
    parent.ad_skip_delay.setRange(1, 30)
    parent.ad_skip_delay.setValue(5)
    parent.ad_skip_delay.setSuffix(" seg")
    timing_layout.addRow("Retraso para Saltar Anuncio:", parent.ad_skip_delay)
    
    parent.view_time_min = QSpinBox()
    parent.view_time_min.setRange(10, 300)
    parent.view_time_min.setValue(30)
    parent.view_time_min.setSuffix(" seg")
    timing_layout.addRow("Tiempo Mínimo de Vista:", parent.view_time_min)
    
    parent.view_time_max = QSpinBox()
    parent.view_time_max.setRange(30, 600)
    parent.view_time_max.setValue(120)
    parent.view_time_max.setSuffix(" seg")
    timing_layout.addRow("Tiempo Máximo de Vista:", parent.view_time_max)
    
    parent.action_delay_min = QSpinBox()
    parent.action_delay_min.setRange(50, 1000)
    parent.action_delay_min.setValue(100)
    parent.action_delay_min.setSuffix(" ms")
    timing_layout.addRow("Retraso Mínimo de Acción:", parent.action_delay_min)
    
    parent.action_delay_max = QSpinBox()
    parent.action_delay_max.setRange(100, 2000)
    parent.action_delay_max.setValue(500)
    parent.action_delay_max.setSuffix(" ms")
    timing_layout.addRow("Retraso Máximo de Acción:", parent.action_delay_max)
    
    layout.addWidget(timing_group)
    
    # Configuración de Acciones
    actions_group = QGroupBox("Acciones Habilitadas")
    actions_layout = QVBoxLayout(actions_group)
    
    parent.enable_like = QCheckBox("Habilitar Me Gusta")
    parent.enable_like.setChecked(True)
    actions_layout.addWidget(parent.enable_like)
    
    parent.enable_comment = QCheckBox("Habilitar Comentarios")
    parent.enable_comment.setChecked(True)
    actions_layout.addWidget(parent.enable_comment)
    
    parent.enable_subscribe = QCheckBox("Habilitar Suscripción")
    actions_layout.addWidget(parent.enable_subscribe)
    
    parent.enable_skip_ads = QCheckBox("Habilitar Saltar Anuncios")
    parent.enable_skip_ads.setChecked(True)
    actions_layout.addWidget(parent.enable_skip_ads)
    
    layout.addWidget(actions_group)
    
    # Prompt de Tarea
    prompt_group = QGroupBox("Prompt de Tarea (YAML/JSON)")
    prompt_layout = QVBoxLayout(prompt_group)
    
    parent.prompt_edit = QTextEdit()
    parent.prompt_edit.setPlaceholderText("Ingrese su prompt de tarea aquí...")
    parent.prompt_edit.setMinimumHeight(150)
    prompt_layout.addWidget(parent.prompt_edit)
    
    layout.addWidget(prompt_group)
    
    layout.addStretch()
    return tab
