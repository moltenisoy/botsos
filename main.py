#!/usr/bin/env python3
"""
BotSOS - Administrador de Sesiones Multi-Modelo

Punto de entrada principal para la aplicación.
Ejecute este archivo para iniciar la aplicación GUI.

Versión: 1.0.0
Diseñado exclusivamente para Windows.

Uso:
    python main.py
    python main.py --version
    python main.py --check-system
"""

import sys
import logging
import argparse
import platform
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Versión de la aplicación
__version__ = "1.0.0"
__app_name__ = "BotSOS"


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


def check_platform():
    """Verificar que se ejecuta en Windows."""
    if platform.system() != "Windows":
        print("⚠️ ADVERTENCIA: BotSOS está diseñado exclusivamente para Windows.")
        print(f"   Sistema detectado: {platform.system()}")
        print("   Algunas funcionalidades pueden no estar disponibles.")
        return False
    return True


def check_dependencies():
    """Verificar si las dependencias requeridas están instaladas."""
    missing = []
    optional_missing = []
    
    # Dependencias requeridas
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        missing.append("PyQt6")
    
    try:
        import playwright
    except ImportError:
        missing.append("playwright (ejecute: pip install playwright && playwright install)")
    
    # Dependencias opcionales
    try:
        import cryptography
    except ImportError:
        optional_missing.append("cryptography (para encriptación de credenciales)")
    
    try:
        import keyring
    except ImportError:
        optional_missing.append("keyring (para almacenamiento seguro)")
    
    try:
        import psutil
    except ImportError:
        optional_missing.append("psutil (para monitoreo de recursos)")
    
    try:
        import yaml
    except ImportError:
        optional_missing.append("pyyaml (para plugins YAML)")
    
    if missing:
        print("❌ Dependencias requeridas faltantes:")
        for dep in missing:
            print(f"   - {dep}")
        print("\n   Instale con: pip install -r requirements.txt")
        print("   Luego ejecute: playwright install")
        return False
    
    if optional_missing:
        print("⚠️ Dependencias opcionales faltantes:")
        for dep in optional_missing:
            print(f"   - {dep}")
        print("   Estas funcionalidades estarán limitadas.\n")
    
    return True


def check_system():
    """Verificar requisitos del sistema."""
    print(f"\n{'=' * 60}")
    print(f"  {__app_name__} v{__version__} - Verificación del Sistema")
    print(f"{'=' * 60}\n")
    
    checks = []
    
    # Sistema operativo
    os_name = platform.system()
    os_version = platform.version()
    os_ok = os_name == "Windows"
    checks.append(("Sistema Operativo", os_ok, f"{os_name} {os_version}"))
    
    # Python
    py_version = sys.version_info
    py_ok = py_version >= (3, 10)
    checks.append(("Python 3.10+", py_ok, f"{py_version.major}.{py_version.minor}.{py_version.micro}"))
    
    # RAM (si psutil está disponible)
    try:
        import psutil
        ram = psutil.virtual_memory()
        ram_gb = ram.total / (1024 ** 3)
        ram_ok = ram_gb >= 4
        checks.append(("RAM (mínimo 4 GB)", ram_ok, f"{ram_gb:.1f} GB"))
    except ImportError:
        checks.append(("RAM", None, "psutil no instalado"))
    
    # Dependencias
    deps = [
        ("PyQt6", "PyQt6.QtWidgets"),
        ("Playwright", "playwright"),
        ("cryptography", "cryptography"),
        ("keyring", "keyring"),
        ("psutil", "psutil"),
        ("PyYAML", "yaml"),
    ]
    
    for name, module in deps:
        try:
            __import__(module)
            checks.append((name, True, "Instalado"))
        except ImportError:
            checks.append((name, False, "No instalado"))
    
    # Mostrar resultados
    all_ok = True
    for name, status, message in checks:
        if status is True:
            icon = "✓"
            color = ""
        elif status is False:
            icon = "✗"
            color = ""
            all_ok = False
        else:
            icon = "?"
            color = ""
        
        print(f"  {icon} {name}: {message}")
    
    print(f"\n{'=' * 60}")
    if all_ok:
        print("  ✓ Sistema listo para ejecutar BotSOS")
    else:
        print("  ✗ Hay requisitos faltantes. Revise la lista anterior.")
    print(f"{'=' * 60}\n")
    
    return all_ok


def show_ethical_consent():
    """Muestra el diálogo de consentimiento ético al inicio."""
    try:
        from src.help_system import EthicalConsentManager
        
        data_dir = Path(__file__).parent / "data"
        consent_manager = EthicalConsentManager(data_dir)
        
        if not consent_manager.has_consent:
            print(consent_manager.get_consent_text())
            print("\n¿Acepta los términos de uso? (s/n): ", end="")
            
            try:
                response = input().strip().lower()
                if response in ('s', 'si', 'sí', 'yes', 'y'):
                    consent_manager.give_consent()
                    print("\n✓ Consentimiento registrado. Iniciando aplicación...\n")
                    return True
                else:
                    print("\n✗ Debe aceptar los términos para usar esta aplicación.")
                    return False
            except (EOFError, KeyboardInterrupt):
                print("\n✗ Operación cancelada.")
                return False
        
        return True
        
    except ImportError:
        # Si no está disponible el módulo, continuar
        return True


def main():
    """Punto de entrada principal de la aplicación."""
    # Parsear argumentos
    parser = argparse.ArgumentParser(
        description=f"{__app_name__} - Administrador de Sesiones Multi-Modelo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py                 Iniciar la aplicación
  python main.py --version       Mostrar versión
  python main.py --check-system  Verificar requisitos del sistema
        """
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'{__app_name__} v{__version__}'
    )
    parser.add_argument(
        '--check-system', '-c',
        action='store_true',
        help='Verificar requisitos del sistema'
    )
    parser.add_argument(
        '--skip-consent',
        action='store_true',
        help='Omitir diálogo de consentimiento (solo para desarrollo)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Habilitar modo debug con logging detallado'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Solo verificar sistema
    if args.check_system:
        sys.exit(0 if check_system() else 1)
    
    # Banner de inicio
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║   {__app_name__} v{__version__} - Administrador de Sesiones Multi-Modelo   ║
║   Diseñado exclusivamente para Windows                        ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    logger.info(f"Iniciando {__app_name__} v{__version__}")
    
    # Verificar plataforma
    check_platform()
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Mostrar consentimiento ético
    if not args.skip_consent:
        if not show_ethical_consent():
            sys.exit(0)
    
    # Importar y ejecutar GUI
    try:
        from src.session_manager_gui import main as gui_main
        gui_main()
    except Exception as e:
        logger.exception(f"Error de aplicación: {e}")
        print(f"\n❌ Error fatal: {e}")
        print("   Revise los logs en la carpeta 'logs' para más detalles.")
        sys.exit(1)


if __name__ == "__main__":
    main()
