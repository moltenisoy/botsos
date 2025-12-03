"""
Módulo de Gestión de Windows

Maneja problemas específicos de Windows incluyendo:
- Verificación y elevación UAC
- Detección de Docker Desktop
- Fallback a WSL2 si Docker nativo falla
- Detección de hardware (AMD/ROCm)

Implementa características de fase6.txt:
- Verificaciones UAC para Docker/ROCm
- Fallback a WSL2 si nativo falla
- Pruebas en hardware Ryzen 3

Diseñado exclusivamente para Windows.
"""

import ctypes
import logging
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class WindowsSystemInfo:
    """Información del sistema Windows."""
    os_version: str
    os_build: str
    is_64bit: bool
    username: str
    is_admin: bool
    cpu_name: str
    gpu_name: str
    ram_total_gb: float
    has_docker: bool
    has_wsl2: bool
    has_rocm: bool


class UACManager:
    """Administrador de Control de Cuentas de Usuario (UAC).
    
    Proporciona métodos para verificar y solicitar
    privilegios de administrador en Windows.
    """
    
    @staticmethod
    def is_admin() -> bool:
        """Verifica si el proceso actual tiene privilegios de administrador.
        
        Returns:
            True si es administrador, False de lo contrario.
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    
    @staticmethod
    def request_admin(reason: str = "operación privilegiada") -> bool:
        """Solicita elevación de privilegios UAC.
        
        Reinicia el script actual con privilegios de administrador.
        
        Args:
            reason: Razón para la solicitud (para logging).
            
        Returns:
            True si se solicitó exitosamente (el script se reiniciará),
            False si falló o ya es administrador.
        """
        if UACManager.is_admin():
            return True
        
        try:
            logger.info(f"Solicitando elevación UAC para: {reason}")
            
            # Reiniciar con privilegios elevados
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                " ".join(sys.argv),
                None,
                1  # SW_SHOWNORMAL
            )
            return True
            
        except Exception as e:
            logger.error(f"Error solicitando elevación UAC: {e}")
            return False
    
    @staticmethod
    def check_and_prompt(operation: str) -> bool:
        """Verifica privilegios y muestra prompt si es necesario.
        
        Args:
            operation: Nombre de la operación que requiere privilegios.
            
        Returns:
            True si tiene privilegios o si el usuario aceptó elevar.
        """
        if UACManager.is_admin():
            return True
        
        logger.warning(
            f"La operación '{operation}' requiere privilegios de administrador."
        )
        return False


class DockerManager:
    """Administrador de Docker para Windows.
    
    Detecta Docker Desktop, verifica estado y proporciona
    fallback a WSL2 si es necesario.
    """
    
    def __init__(self):
        """Inicializa el administrador de Docker."""
        self._docker_available = None
        self._wsl2_available = None
        self._docker_path = None
    
    def check_docker_desktop(self) -> Tuple[bool, str]:
        """Verifica si Docker Desktop está instalado y funcionando.
        
        Returns:
            Tupla (disponible, mensaje).
        """
        try:
            # Verificar instalación
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False, "Docker no está instalado o no está en PATH"
            
            version = result.stdout.strip()
            
            # Verificar que Docker está corriendo
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                # Docker instalado pero no corriendo
                if "Is the docker daemon running?" in result.stderr:
                    return False, "Docker Desktop no está corriendo. Inícielo manualmente."
                if "permission denied" in result.stderr.lower():
                    return False, "Se requieren privilegios para Docker. Ejecute como administrador."
                return False, f"Error de Docker: {result.stderr[:100]}"
            
            self._docker_available = True
            return True, f"Docker Desktop funcionando: {version}"
            
        except FileNotFoundError:
            return False, "Docker no está instalado"
        except subprocess.TimeoutExpired:
            return False, "Docker no responde (timeout)"
        except Exception as e:
            return False, f"Error verificando Docker: {e}"
    
    def check_wsl2(self) -> Tuple[bool, str]:
        """Verifica si WSL2 está disponible como fallback.
        
        Returns:
            Tupla (disponible, mensaje).
        """
        try:
            result = subprocess.run(
                ["wsl", "--list", "--verbose"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False, "WSL2 no está instalado"
            
            output = result.stdout
            if "VERSION" not in output:
                # Verificar formato alternativo
                result = subprocess.run(
                    ["wsl", "--status"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                output = result.stdout
            
            if "2" in output:
                self._wsl2_available = True
                return True, "WSL2 disponible"
            else:
                return False, "Solo WSL1 disponible. Se requiere WSL2."
                
        except FileNotFoundError:
            return False, "WSL no está instalado"
        except subprocess.TimeoutExpired:
            return False, "WSL no responde (timeout)"
        except Exception as e:
            return False, f"Error verificando WSL2: {e}"
    
    def setup_wsl2_docker(self) -> Tuple[bool, str]:
        """Configura Docker en WSL2 como fallback.
        
        Returns:
            Tupla (éxito, mensaje).
        """
        if not self._wsl2_available:
            wsl_ok, msg = self.check_wsl2()
            if not wsl_ok:
                return False, f"WSL2 no disponible: {msg}"
        
        try:
            # Verificar si Docker está instalado en WSL2
            result = subprocess.run(
                ["wsl", "-e", "docker", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, "Docker disponible en WSL2"
            
            # Docker no instalado en WSL2
            return False, (
                "Docker no está instalado en WSL2. "
                "Instale Docker dentro de su distribución WSL2."
            )
            
        except Exception as e:
            return False, f"Error configurando Docker en WSL2: {e}"
    
    def get_docker_fallback_path(self) -> Tuple[bool, str, str]:
        """Obtiene la mejor ruta disponible para Docker.
        
        Intenta Docker Desktop primero, luego WSL2.
        
        Returns:
            Tupla (disponible, tipo, mensaje).
        """
        # Intentar Docker Desktop primero
        docker_ok, docker_msg = self.check_docker_desktop()
        if docker_ok:
            return True, "native", docker_msg
        
        logger.info(f"Docker nativo no disponible: {docker_msg}")
        logger.info("Intentando fallback a WSL2...")
        
        # Intentar WSL2 como fallback
        wsl_ok, wsl_msg = self.setup_wsl2_docker()
        if wsl_ok:
            return True, "wsl2", wsl_msg
        
        return False, "none", f"Docker no disponible. Nativo: {docker_msg}. WSL2: {wsl_msg}"


class HardwareDetector:
    """Detector de hardware para optimización.
    
    Detecta CPU (especialmente AMD Ryzen), GPU y
    capacidades de aceleración.
    """
    
    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Obtiene información de la CPU.
        
        Returns:
            Diccionario con información de CPU.
        """
        info = {
            "name": "Desconocido",
            "cores": os.cpu_count() or 4,
            "is_amd": False,
            "is_ryzen": False,
            "model": ""
        }
        
        try:
            # Usar WMIC en Windows
            result = subprocess.run(
                ["wmic", "cpu", "get", "name"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = [l.strip() for l in result.stdout.split('\n') if l.strip() and l.strip() != "Name"]
                if lines:
                    cpu_name = lines[0]
                    info["name"] = cpu_name
                    info["is_amd"] = "AMD" in cpu_name.upper()
                    info["is_ryzen"] = "RYZEN" in cpu_name.upper()
                    
                    # Extraer modelo
                    if "Ryzen" in cpu_name:
                        parts = cpu_name.split("Ryzen")
                        if len(parts) > 1:
                            info["model"] = "Ryzen" + parts[1].split()[0]
                            
        except Exception as e:
            logger.debug(f"Error obteniendo info de CPU: {e}")
        
        return info
    
    @staticmethod
    def get_gpu_info() -> Dict[str, Any]:
        """Obtiene información de la GPU.
        
        Returns:
            Diccionario con información de GPU.
        """
        info = {
            "name": "Desconocido",
            "is_amd": False,
            "is_nvidia": False,
            "is_intel": False,
            "has_vega": False,
            "vram_mb": 0
        }
        
        try:
            result = subprocess.run(
                ["wmic", "path", "win32_videocontroller", "get", "name"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = [l.strip() for l in result.stdout.split('\n') if l.strip() and l.strip() != "Name"]
                if lines:
                    gpu_name = lines[0]
                    info["name"] = gpu_name
                    upper_name = gpu_name.upper()
                    info["is_amd"] = "AMD" in upper_name or "RADEON" in upper_name
                    info["is_nvidia"] = "NVIDIA" in upper_name or "GEFORCE" in upper_name
                    info["is_intel"] = "INTEL" in upper_name
                    info["has_vega"] = "VEGA" in upper_name
                    
        except Exception as e:
            logger.debug(f"Error obteniendo info de GPU: {e}")
        
        return info
    
    @staticmethod
    def get_ram_info() -> Dict[str, Any]:
        """Obtiene información de RAM.
        
        Returns:
            Diccionario con información de RAM.
        """
        info = {
            "total_gb": 0,
            "available_gb": 0
        }
        
        try:
            import psutil
            mem = psutil.virtual_memory()
            info["total_gb"] = round(mem.total / (1024 ** 3), 1)
            info["available_gb"] = round(mem.available / (1024 ** 3), 1)
        except ImportError:
            try:
                result = subprocess.run(
                    ["wmic", "os", "get", "totalvisiblememorysize"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = [l.strip() for l in result.stdout.split('\n') if l.strip().isdigit()]
                    if lines:
                        info["total_gb"] = round(int(lines[0]) / (1024 * 1024), 1)
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"Error obteniendo info de RAM: {e}")
        
        return info
    
    @staticmethod
    def check_rocm_support() -> Tuple[bool, str]:
        """Verifica soporte ROCm para GPU AMD.
        
        Returns:
            Tupla (disponible, mensaje).
        """
        gpu_info = HardwareDetector.get_gpu_info()
        
        if not gpu_info["is_amd"]:
            return False, "No se detectó GPU AMD"
        
        # ROCm tiene soporte limitado en Windows
        # Principalmente para GPUs discretas más nuevas
        if gpu_info["has_vega"]:
            return False, (
                "GPU Vega integrada detectada. ROCm tiene soporte limitado "
                "para iGPUs. Se recomienda usar CPU para procesamiento."
            )
        
        # Verificar DirectML a través de DirectX
        try:
            # Intentar importar directml para verificar disponibilidad
            result = subprocess.run(
                ["dxdiag", "/t", "directx_info.txt"],
                capture_output=True,
                timeout=5,
                cwd=os.environ.get("TEMP", ".")
            )
            # Limpiar archivo temporal si se creó
            temp_file = Path(os.environ.get("TEMP", ".")) / "directx_info.txt"
            if temp_file.exists():
                temp_file.unlink()
            return True, "DirectML disponible para aceleración GPU AMD"
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            return False, "Aceleración GPU no disponible"


class WindowsManager:
    """Administrador principal de Windows.
    
    Coordina todas las funcionalidades específicas de Windows.
    """
    
    def __init__(self):
        """Inicializa el administrador de Windows."""
        self.uac = UACManager()
        self.docker = DockerManager()
        self.hardware = HardwareDetector()
        self._system_info: Optional[WindowsSystemInfo] = None
    
    def get_system_info(self) -> WindowsSystemInfo:
        """Obtiene información completa del sistema.
        
        Returns:
            Información del sistema Windows.
        """
        if self._system_info:
            return self._system_info
        
        cpu_info = self.hardware.get_cpu_info()
        gpu_info = self.hardware.get_gpu_info()
        ram_info = self.hardware.get_ram_info()
        docker_ok, _ = self.docker.check_docker_desktop()
        wsl_ok, _ = self.docker.check_wsl2()
        rocm_ok, _ = self.hardware.check_rocm_support()
        
        self._system_info = WindowsSystemInfo(
            os_version=platform.version(),
            os_build=platform.win32_ver()[1],
            is_64bit=platform.machine().endswith('64'),
            username=os.getenv('USERNAME', 'Usuario'),
            is_admin=self.uac.is_admin(),
            cpu_name=cpu_info["name"],
            gpu_name=gpu_info["name"],
            ram_total_gb=ram_info["total_gb"],
            has_docker=docker_ok,
            has_wsl2=wsl_ok,
            has_rocm=rocm_ok
        )
        
        return self._system_info
    
    def check_requirements(self) -> List[Dict[str, Any]]:
        """Verifica todos los requisitos del sistema.
        
        Returns:
            Lista de verificaciones con estado.
        """
        checks = []
        
        # Verificar Windows 10+
        try:
            build = int(platform.win32_ver()[1].split('.')[0])
            win10_ok = build >= 10240
            checks.append({
                "name": "Windows 10+",
                "ok": win10_ok,
                "message": f"Build {platform.win32_ver()[1]}" if win10_ok else "Se requiere Windows 10 o superior"
            })
        except Exception:
            checks.append({
                "name": "Windows 10+",
                "ok": False,
                "message": "No se pudo verificar la versión de Windows"
            })
        
        # Verificar Python
        python_ok = sys.version_info >= (3, 10)
        checks.append({
            "name": "Python 3.10+",
            "ok": python_ok,
            "message": f"Python {sys.version.split()[0]}" if python_ok else "Se requiere Python 3.10+"
        })
        
        # Verificar RAM
        ram_info = self.hardware.get_ram_info()
        ram_ok = ram_info["total_gb"] >= 4
        checks.append({
            "name": "RAM (mínimo 4GB)",
            "ok": ram_ok,
            "message": f"{ram_info['total_gb']} GB" if ram_ok else f"Solo {ram_info['total_gb']} GB disponibles"
        })
        
        # Verificar Docker (opcional)
        docker_ok, docker_msg = self.docker.check_docker_desktop()
        checks.append({
            "name": "Docker Desktop (opcional)",
            "ok": docker_ok,
            "message": docker_msg,
            "optional": True
        })
        
        # Verificar WSL2 (opcional, fallback)
        if not docker_ok:
            wsl_ok, wsl_msg = self.docker.check_wsl2()
            checks.append({
                "name": "WSL2 (fallback Docker)",
                "ok": wsl_ok,
                "message": wsl_msg,
                "optional": True
            })
        
        # Verificar hardware para Ryzen 3
        cpu_info = self.hardware.get_cpu_info()
        if cpu_info["is_ryzen"]:
            checks.append({
                "name": "CPU AMD Ryzen",
                "ok": True,
                "message": f"{cpu_info['name']} - Optimizado para este hardware"
            })
        
        return checks
    
    def get_optimal_settings(self) -> Dict[str, Any]:
        """Obtiene configuración óptima basada en hardware.
        
        Returns:
            Diccionario con configuraciones recomendadas.
        """
        sys_info = self.get_system_info()
        cpu_info = self.hardware.get_cpu_info()
        
        # Calcular sesiones máximas basadas en RAM
        max_sessions = max(1, int(sys_info.ram_total_gb / 2))  # ~2GB por sesión
        if max_sessions > 8:
            max_sessions = 8  # Límite superior
        
        # Calcular threads basados en CPU
        threads = cpu_info["cores"]
        if cpu_info["is_ryzen"]:
            # Ryzen tiene buen rendimiento multi-hilo
            threads = min(threads, 8)
        else:
            threads = min(threads, 4)
        
        # Configuración GPU
        gpu_backend = "cpu"
        if sys_info.has_rocm:
            gpu_backend = "directml"  # DirectML para AMD en Windows
        
        return {
            "max_concurrent_sessions": max_sessions,
            "max_threads": threads,
            "gpu_backend": gpu_backend,
            "use_docker": sys_info.has_docker,
            "use_wsl2_fallback": sys_info.has_wsl2 and not sys_info.has_docker,
            "ram_threshold_percent": 80 if sys_info.ram_total_gb >= 8 else 70,
            "cpu_threshold_percent": 85 if cpu_info["is_ryzen"] else 75,
            "recommended_llm": self._get_recommended_llm(sys_info.ram_total_gb)
        }
    
    def _get_recommended_llm(self, ram_gb: float) -> str:
        """Obtiene el modelo LLM recomendado basado en RAM.
        
        Args:
            ram_gb: RAM total en GB.
            
        Returns:
            Nombre del modelo recomendado.
        """
        if ram_gb >= 16:
            return "mistral-nemo:12b"
        elif ram_gb >= 8:
            return "llama3.1:8b"
        elif ram_gb >= 6:
            return "qwen2.5:7b"
        else:
            return "phi3.5:3.8b"
    
    def create_firewall_rule(self, name: str, port: int, action: str = "block") -> Tuple[bool, str]:
        """Crea una regla de firewall (requiere privilegios).
        
        Args:
            name: Nombre de la regla.
            port: Puerto a bloquear/permitir.
            action: "block" o "allow".
            
        Returns:
            Tupla (éxito, mensaje).
        """
        if not self.uac.is_admin():
            return False, "Se requieren privilegios de administrador"
        
        try:
            cmd = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={name}",
                "dir=in",
                f"action={action}",
                "protocol=tcp",
                f"localport={port}"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, f"Regla '{name}' creada exitosamente"
            else:
                return False, f"Error: {result.stderr}"
                
        except Exception as e:
            return False, f"Error creando regla: {e}"
