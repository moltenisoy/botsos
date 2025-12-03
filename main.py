#!/usr/bin/env python3
"""
BotSOS - Multi-Model Session Manager

Main entry point for the application.
Run this file to start the GUI application.

Usage:
    python main.py
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def setup_logging():
    """Configure application logging."""
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
    """Check if required dependencies are installed."""
    missing = []
    
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        missing.append("PyQt6")
    
    try:
        import playwright
    except ImportError:
        missing.append("playwright (run: pip install playwright && playwright install)")
    
    if missing:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with: pip install -r requirements.txt")
        print("Then run: playwright install")
        return False
    
    return True


def main():
    """Main application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting BotSOS - Multi-Model Session Manager")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Import and run GUI
    try:
        from src.session_manager_gui import main as gui_main
        gui_main()
    except Exception as e:
        logger.exception(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
