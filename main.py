#!/usr/bin/env python3
"""
BotSOS - Administrador de Sesiones Multi-Modelo

Punto de entrada principal para la aplicación.
Ejecute este archivo para iniciar la aplicación GUI.

Diseñado exclusivamente para Windows.

Uso:
    python main.py
"""

import sys
import logging
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent))


def setup_logging():
    """Configurar el registro de la aplicación."""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "botsos.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def check_dependencies():
    """Verificar si las dependencias requeridas están instaladas."""
    missing = []
    
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        missing.append("PyQt6")
    
    try:
        import playwright
    except ImportError:
        missing.append("playwright (ejecute: pip install playwright && playwright install)")
    
    if missing:
        print("Dependencias faltantes:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstale con: pip install -r requirements.txt")
        print("Luego ejecute: playwright install")
        return False
    
    return True


def main():
    """Punto de entrada principal de la aplicación."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Iniciando BotSOS - Administrador de Sesiones Multi-Modelo")
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Importar y ejecutar GUI
    try:
        from src.session_manager_gui import main as gui_main
        gui_main()
    except Exception as e:
        logger.exception(f"Error de aplicación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
