"""
Módulo de Empaquetado y Distribución

Implementa empaquetado para distribución en Windows usando PyInstaller.

Implementa características de fase6.txt:
- Configuración PyInstaller para ejecutable Windows
- Bundling de dependencias y recursos
- Verificación de requisitos antes de build

Diseñado exclusivamente para Windows.
"""

import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class BuildConfig:
    """Configuración de build para PyInstaller."""
    app_name: str = "BotSOS"
    version: str = "1.0.0"
    icon_path: str = "assets/icon.ico"
    one_file: bool = True  # --onefile
    windowed: bool = True  # --windowed (sin consola)
    console: bool = False  # Para debug
    upx_enabled: bool = True  # Compresión UPX
    clean_build: bool = True
    
    # Archivos adicionales
    data_files: List[str] = field(default_factory=lambda: [
        "config/*.json",
        "assets/*.png",
        "assets/*.ico",
        "plugins/*.yaml",
        "plugins/*.json",
    ])
    
    # Módulos ocultos que PyInstaller no detecta automáticamente
    hidden_imports: List[str] = field(default_factory=lambda: [
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "playwright",
        "playwright.async_api",
        "cryptography",
        "cryptography.fernet",
        "aiohttp",
        "yaml",
        "keyring",
        "keyring.backends",
        "psutil",
        "ollama",
    ])
    
    # Módulos a excluir
    exclude_modules: List[str] = field(default_factory=lambda: [
        "tkinter",
        "matplotlib",
        "numpy.distutils",
        "scipy",
        "pytest",
    ])


class PackagingManager:
    """Administrador de empaquetado para Windows.
    
    Genera ejecutables standalone usando PyInstaller.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Inicializa el administrador de empaquetado.
        
        Args:
            project_root: Raíz del proyecto.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        
        self._pyinstaller_available = self._check_pyinstaller()
    
    def _check_pyinstaller(self) -> bool:
        """Verifica si PyInstaller está disponible."""
        try:
            import PyInstaller
            return True
        except ImportError:
            logger.warning("PyInstaller no está instalado. Instale con: pip install pyinstaller")
            return False
    
    def check_requirements(self) -> List[Dict[str, Any]]:
        """Verifica requisitos para el empaquetado.
        
        Returns:
            Lista de verificaciones con estado.
        """
        checks = []
        
        # Python
        py_version = sys.version_info
        py_ok = py_version >= (3, 10)
        checks.append({
            "name": "Python 3.10+",
            "ok": py_ok,
            "message": f"Python {py_version.major}.{py_version.minor}"
        })
        
        # PyInstaller
        checks.append({
            "name": "PyInstaller",
            "ok": self._pyinstaller_available,
            "message": "Instalado" if self._pyinstaller_available else "No instalado"
        })
        
        # Archivo principal
        main_file = self.project_root / "main.py"
        main_ok = main_file.exists()
        checks.append({
            "name": "Archivo main.py",
            "ok": main_ok,
            "message": str(main_file) if main_ok else "No encontrado"
        })
        
        # Icono
        icon_file = self.project_root / "assets" / "icon.ico"
        icon_ok = icon_file.exists()
        checks.append({
            "name": "Icono de aplicación",
            "ok": icon_ok,
            "message": str(icon_file) if icon_ok else "Usando icono por defecto",
            "optional": True
        })
        
        # Dependencias críticas
        critical_deps = [
            ("PyQt6", "pyqt6"),
            ("playwright", "playwright"),
            ("cryptography", "cryptography"),
        ]
        
        for name, package in critical_deps:
            try:
                __import__(package)
                checks.append({
                    "name": f"Dependencia: {name}",
                    "ok": True,
                    "message": "Instalada"
                })
            except ImportError:
                checks.append({
                    "name": f"Dependencia: {name}",
                    "ok": False,
                    "message": "No instalada"
                })
        
        return checks
    
    def generate_spec_file(self, config: BuildConfig) -> str:
        """Genera archivo .spec para PyInstaller.
        
        Args:
            config: Configuración de build.
            
        Returns:
            Contenido del archivo .spec.
        """
        # Preparar lista de datos
        datas = []
        for pattern in config.data_files:
            src_pattern = self.project_root / pattern
            for path in src_pattern.parent.glob(src_pattern.name):
                if path.is_file():
                    dest = str(path.parent.relative_to(self.project_root))
                    datas.append(f"('{path}', '{dest}')")
        
        datas_str = ",\n             ".join(datas) if datas else ""
        
        # Hidden imports
        hidden_str = ",\n             ".join(f"'{h}'" for h in config.hidden_imports)
        
        # Excludes
        excludes_str = ",\n             ".join(f"'{e}'" for e in config.exclude_modules)
        
        # Icono
        icon_path = self.project_root / config.icon_path
        icon_str = f"'{icon_path}'" if icon_path.exists() else "None"
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Archivo generado automáticamente por BotSOS PackagingManager
# Versión: {config.version}

import sys
from pathlib import Path

block_cipher = None

# Directorio del proyecto
project_root = Path(SPECPATH)

a = Analysis(
    [str(project_root / 'main.py')],
    pathex=[str(project_root), str(project_root / 'src')],
    binaries=[],
    datas=[{datas_str}],
    hiddenimports=[
             {hidden_str}
         ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
             {excludes_str}
         ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

'''
        if config.one_file:
            spec_content += f'''
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{config.app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx={'True' if config.upx_enabled else 'False'},
    upx_exclude=[],
    runtime_tmpdir=None,
    console={str(config.console)},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={icon_str},
)
'''
        else:
            spec_content += f'''
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{config.app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx={'True' if config.upx_enabled else 'False'},
    console={str(config.console)},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={icon_str},
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx={'True' if config.upx_enabled else 'False'},
    upx_exclude=[],
    name='{config.app_name}',
)
'''
        
        return spec_content
    
    def build(self, config: Optional[BuildConfig] = None) -> Tuple[bool, str]:
        """Ejecuta el proceso de build.
        
        Args:
            config: Configuración de build.
            
        Returns:
            Tupla (éxito, mensaje).
        """
        if not self._pyinstaller_available:
            return False, "PyInstaller no está instalado"
        
        config = config or BuildConfig()
        
        # Verificar requisitos
        checks = self.check_requirements()
        failed = [c for c in checks if not c["ok"] and not c.get("optional")]
        if failed:
            return False, f"Requisitos faltantes: {', '.join(c['name'] for c in failed)}"
        
        # Limpiar builds anteriores
        if config.clean_build:
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
            if self.dist_dir.exists():
                shutil.rmtree(self.dist_dir)
        
        # Generar archivo .spec
        spec_content = self.generate_spec_file(config)
        spec_file = self.project_root / f"{config.app_name}.spec"
        
        try:
            with open(spec_file, 'w', encoding='utf-8') as f:
                f.write(spec_content)
            
            logger.info(f"Archivo .spec generado: {spec_file}")
            
            # Ejecutar PyInstaller
            cmd = [sys.executable, "-m", "PyInstaller", str(spec_file), "--noconfirm"]
            
            logger.info(f"Ejecutando: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos máximo
            )
            
            if result.returncode == 0:
                # Verificar que se creó el ejecutable
                if config.one_file:
                    exe_path = self.dist_dir / f"{config.app_name}.exe"
                else:
                    exe_path = self.dist_dir / config.app_name / f"{config.app_name}.exe"
                
                if exe_path.exists():
                    size_mb = exe_path.stat().st_size / (1024 * 1024)
                    return True, f"Build exitoso: {exe_path} ({size_mb:.1f} MB)"
                else:
                    return False, "Build terminó pero no se encontró el ejecutable"
            else:
                return False, f"Error de PyInstaller: {result.stderr[:500]}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout: el build tardó más de 10 minutos"
        except Exception as e:
            return False, f"Error durante build: {e}"
    
    def create_installer(self, config: Optional[BuildConfig] = None) -> Tuple[bool, str]:
        """Crea un instalador usando NSIS (si está disponible).
        
        Args:
            config: Configuración de build.
            
        Returns:
            Tupla (éxito, mensaje).
        """
        config = config or BuildConfig()
        
        # Verificar NSIS
        nsis_path = Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "NSIS" / "makensis.exe"
        
        if not nsis_path.exists():
            nsis_path = Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "NSIS" / "makensis.exe"
        
        if not nsis_path.exists():
            return False, "NSIS no está instalado. Descargue desde https://nsis.sourceforge.io/"
        
        # Verificar que el build existe
        if config.one_file:
            exe_path = self.dist_dir / f"{config.app_name}.exe"
        else:
            exe_path = self.dist_dir / config.app_name / f"{config.app_name}.exe"
        
        if not exe_path.exists():
            return False, "Ejecute build() primero para crear el ejecutable"
        
        # Generar script NSIS
        nsis_script = f'''
!include "MUI2.nsh"

Name "{config.app_name}"
OutFile "{self.dist_dir / f'{config.app_name}_Setup.exe'}"
InstallDir "$PROGRAMFILES\\{config.app_name}"
RequestExecutionLevel admin

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "Spanish"

Section "Instalar"
    SetOutPath $INSTDIR
    File /r "{exe_path.parent}\\*.*"
    
    ; Crear acceso directo
    CreateDirectory "$SMPROGRAMS\\{config.app_name}"
    CreateShortcut "$SMPROGRAMS\\{config.app_name}\\{config.app_name}.lnk" "$INSTDIR\\{config.app_name}.exe"
    CreateShortcut "$DESKTOP\\{config.app_name}.lnk" "$INSTDIR\\{config.app_name}.exe"
    
    ; Registrar desinstalador
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    RMDir /r "$SMPROGRAMS\\{config.app_name}"
    Delete "$DESKTOP\\{config.app_name}.lnk"
SectionEnd
'''
        
        nsis_file = self.project_root / "installer.nsi"
        
        try:
            with open(nsis_file, 'w', encoding='utf-8') as f:
                f.write(nsis_script)
            
            # Ejecutar NSIS
            result = subprocess.run(
                [str(nsis_path), str(nsis_file)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                installer_path = self.dist_dir / f"{config.app_name}_Setup.exe"
                if installer_path.exists():
                    size_mb = installer_path.stat().st_size / (1024 * 1024)
                    return True, f"Instalador creado: {installer_path} ({size_mb:.1f} MB)"
            
            return False, f"Error de NSIS: {result.stderr[:500]}"
            
        except subprocess.TimeoutExpired:
            return False, "Timeout creando instalador"
        except Exception as e:
            return False, f"Error creando instalador: {e}"


class VersionManager:
    """Administrador de versiones.
    
    Gestiona el versionado semántico de la aplicación.
    """
    
    VERSION_FILE = "VERSION"
    
    def __init__(self, project_root: Optional[Path] = None):
        """Inicializa el administrador de versiones.
        
        Args:
            project_root: Raíz del proyecto.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._version_file = self.project_root / self.VERSION_FILE
        self._version = self._load_version()
    
    def _load_version(self) -> str:
        """Carga la versión actual."""
        if self._version_file.exists():
            return self._version_file.read_text().strip()
        return "1.0.0"
    
    def _save_version(self, version: str):
        """Guarda la versión."""
        self._version_file.write_text(version)
    
    @property
    def version(self) -> str:
        return self._version
    
    def bump_major(self) -> str:
        """Incrementa versión mayor (X.0.0)."""
        parts = self._version.split(".")
        parts[0] = str(int(parts[0]) + 1)
        parts[1] = "0"
        parts[2] = "0"
        self._version = ".".join(parts)
        self._save_version(self._version)
        return self._version
    
    def bump_minor(self) -> str:
        """Incrementa versión menor (x.X.0)."""
        parts = self._version.split(".")
        parts[1] = str(int(parts[1]) + 1)
        parts[2] = "0"
        self._version = ".".join(parts)
        self._save_version(self._version)
        return self._version
    
    def bump_patch(self) -> str:
        """Incrementa versión de parche (x.x.X)."""
        parts = self._version.split(".")
        parts[2] = str(int(parts[2]) + 1)
        self._version = ".".join(parts)
        self._save_version(self._version)
        return self._version
    
    def set_version(self, version: str) -> str:
        """Establece una versión específica."""
        # Validar formato
        parts = version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"Versión inválida: {version}. Use formato X.Y.Z")
        
        self._version = version
        self._save_version(self._version)
        return self._version
