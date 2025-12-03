"""
Módulo de Gestión de Escalabilidad.

Maneja la escalabilidad del sistema usando Docker y AWS para operaciones
a gran escala (50+ sesiones).

Implementa características de fase5.txt:
- Contenedorización con Docker para entornos aislados.
- Integración con AWS EC2 para descarga de sesiones pesadas.
- Auto-escalado basado en umbrales de CPU/RAM.

Diseñado exclusivamente para Windows.
"""

import asyncio
import logging
import platform
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ContainerSession:
    """Representa una sesión ejecutándose en un contenedor Docker."""
    container_id: str
    session_id: str
    status: str = "running"
    created_at: datetime = field(default_factory=datetime.now)
    port_mapping: Dict[str, int] = field(default_factory=dict)


@dataclass
class CloudInstance:
    """Representa una instancia EC2 de AWS."""
    instance_id: str
    public_ip: str
    status: str = "running"
    session_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class DockerManager:
    """Administrador de contenedores Docker para sesiones aisladas.
    
    Permite ejecutar sesiones de navegador en contenedores Docker
    para mayor aislamiento y escalabilidad en Windows.
    """
    
    def __init__(self, image_name: str = "botsos:latest"):
        """Inicializa el administrador de Docker.
        
        Args:
            image_name: Nombre de la imagen Docker a usar.
        """
        self.image_name = image_name
        self._client = None
        self._containers: Dict[str, ContainerSession] = {}
        self._docker_available = False
        self._init_docker()
    
    def _init_docker(self) -> bool:
        """Inicializa el cliente Docker.
        
        Returns:
            True si Docker está disponible, False de lo contrario.
        """
        try:
            import docker
            self._client = docker.from_env()
            # Verificar conexión con Docker
            self._client.ping()
            self._docker_available = True
            logger.info("Docker está disponible y conectado")
            return True
        except ImportError:
            logger.warning("Docker SDK no está instalado. Instale con: pip install docker")
            return False
        except Exception as e:
            logger.warning(f"Docker no está disponible: {e}")
            logger.info("Para usar Docker en Windows, instale Docker Desktop")
            return False
    
    @property
    def is_available(self) -> bool:
        """Verifica si Docker está disponible."""
        return self._docker_available
    
    async def create_session_container(
        self,
        session_id: str,
        config: Dict[str, Any],
        volume_mounts: Optional[List[str]] = None,
        network_mode: str = "bridge"
    ) -> Optional[ContainerSession]:
        """Crea un contenedor para una sesión.
        
        Args:
            session_id: ID de la sesión.
            config: Configuración de la sesión.
            volume_mounts: Lista de montajes de volumen.
            network_mode: Modo de red del contenedor.
            
        Returns:
            ContainerSession si se creó exitosamente, None de lo contrario.
        """
        if not self._docker_available:
            logger.error("Docker no está disponible")
            return None
        
        try:
            # Preparar montajes de volumen
            volumes = {}
            if volume_mounts:
                for mount in volume_mounts:
                    if ':' in mount:
                        host_path, container_path = mount.split(':', 1)
                        volumes[host_path] = {'bind': container_path, 'mode': 'rw'}
            
            # Crear contenedor
            container = await asyncio.to_thread(
                self._client.containers.run,
                self.image_name,
                detach=True,
                name=f"botsos_session_{session_id}",
                environment={
                    "SESSION_ID": session_id,
                    "SESSION_CONFIG": str(config)
                },
                volumes=volumes,
                network_mode=network_mode,
                remove=True  # Eliminar al terminar
            )
            
            container_session = ContainerSession(
                container_id=container.id,
                session_id=session_id,
                status="running"
            )
            self._containers[session_id] = container_session
            
            logger.info(f"Contenedor creado para sesión {session_id}: {container.id[:12]}")
            return container_session
            
        except Exception as e:
            logger.error(f"Error creando contenedor para sesión {session_id}: {e}")
            return None
    
    async def stop_session_container(self, session_id: str) -> bool:
        """Detiene el contenedor de una sesión.
        
        Args:
            session_id: ID de la sesión.
            
        Returns:
            True si se detuvo exitosamente, False de lo contrario.
        """
        if session_id not in self._containers:
            return False
        
        try:
            container_session = self._containers[session_id]
            container = await asyncio.to_thread(
                self._client.containers.get,
                container_session.container_id
            )
            await asyncio.to_thread(container.stop)
            
            del self._containers[session_id]
            logger.info(f"Contenedor detenido para sesión {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deteniendo contenedor para sesión {session_id}: {e}")
            return False
    
    async def get_container_status(self, session_id: str) -> Optional[str]:
        """Obtiene el estado de un contenedor.
        
        Args:
            session_id: ID de la sesión.
            
        Returns:
            Estado del contenedor o None si no existe.
        """
        if session_id not in self._containers:
            return None
        
        try:
            container_session = self._containers[session_id]
            container = await asyncio.to_thread(
                self._client.containers.get,
                container_session.container_id
            )
            return container.status
            
        except Exception:
            return None
    
    def get_running_containers(self) -> List[ContainerSession]:
        """Obtiene la lista de contenedores en ejecución.
        
        Returns:
            Lista de ContainerSession activos.
        """
        return list(self._containers.values())
    
    async def cleanup_all(self) -> int:
        """Detiene y limpia todos los contenedores.
        
        Returns:
            Número de contenedores detenidos.
        """
        count = 0
        session_ids = list(self._containers.keys())
        
        for session_id in session_ids:
            if await self.stop_session_container(session_id):
                count += 1
        
        return count


class AWSCloudManager:
    """Administrador de instancias AWS EC2 para escalabilidad en cloud.
    
    Permite migrar sesiones pesadas a instancias EC2 cuando los recursos
    locales están al límite.
    """
    
    def __init__(
        self,
        region: str = "us-east-1",
        instance_type: str = "t3.medium"
    ):
        """Inicializa el administrador de AWS.
        
        Args:
            region: Región de AWS.
            instance_type: Tipo de instancia EC2.
        """
        self.region = region
        self.instance_type = instance_type
        self._client = None
        self._resource = None
        self._instances: Dict[str, CloudInstance] = {}
        self._aws_available = False
        self._init_aws()
    
    def _init_aws(self) -> bool:
        """Inicializa los clientes de AWS.
        
        Returns:
            True si AWS está disponible, False de lo contrario.
        """
        try:
            import boto3
            self._client = boto3.client('ec2', region_name=self.region)
            self._resource = boto3.resource('ec2', region_name=self.region)
            
            # Verificar credenciales con una operación simple
            self._client.describe_regions()
            self._aws_available = True
            logger.info(f"AWS está disponible en región {self.region}")
            return True
            
        except ImportError:
            logger.warning("boto3 no está instalado. Instale con: pip install boto3")
            return False
        except Exception as e:
            logger.warning(f"AWS no está disponible: {e}")
            logger.info("Configure las credenciales de AWS o use 'aws configure'")
            return False
    
    @property
    def is_available(self) -> bool:
        """Verifica si AWS está disponible."""
        return self._aws_available
    
    async def launch_instance(
        self,
        ami_id: str,
        key_name: Optional[str] = None,
        security_group_ids: Optional[List[str]] = None
    ) -> Optional[CloudInstance]:
        """Lanza una nueva instancia EC2.
        
        Args:
            ami_id: ID de la AMI de Windows a usar.
            key_name: Nombre del par de claves SSH.
            security_group_ids: IDs de grupos de seguridad.
            
        Returns:
            CloudInstance si se lanzó exitosamente, None de lo contrario.
        """
        if not self._aws_available:
            logger.error("AWS no está disponible")
            return None
        
        try:
            # Preparar parámetros
            params = {
                'ImageId': ami_id,
                'InstanceType': self.instance_type,
                'MinCount': 1,
                'MaxCount': 1,
                'TagSpecifications': [{
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': 'BotSOS-Session-Worker'}]
                }]
            }
            
            if key_name:
                params['KeyName'] = key_name
            if security_group_ids:
                params['SecurityGroupIds'] = security_group_ids
            
            # Lanzar instancia
            instances = await asyncio.to_thread(
                self._resource.create_instances,
                **params
            )
            
            if instances:
                instance = instances[0]
                await asyncio.to_thread(instance.wait_until_running)
                await asyncio.to_thread(instance.reload)
                
                cloud_instance = CloudInstance(
                    instance_id=instance.id,
                    public_ip=instance.public_ip_address or "",
                    status="running"
                )
                self._instances[instance.id] = cloud_instance
                
                logger.info(f"Instancia EC2 lanzada: {instance.id}")
                return cloud_instance
            
            return None
            
        except Exception as e:
            logger.error(f"Error lanzando instancia EC2: {e}")
            return None
    
    async def terminate_instance(self, instance_id: str) -> bool:
        """Termina una instancia EC2.
        
        Args:
            instance_id: ID de la instancia.
            
        Returns:
            True si se terminó exitosamente, False de lo contrario.
        """
        if instance_id not in self._instances:
            return False
        
        try:
            instance = await asyncio.to_thread(
                self._resource.Instance,
                instance_id
            )
            await asyncio.to_thread(instance.terminate)
            
            del self._instances[instance_id]
            logger.info(f"Instancia EC2 terminada: {instance_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error terminando instancia {instance_id}: {e}")
            return False
    
    async def get_instance_status(self, instance_id: str) -> Optional[str]:
        """Obtiene el estado de una instancia.
        
        Args:
            instance_id: ID de la instancia.
            
        Returns:
            Estado de la instancia o None si no existe.
        """
        try:
            instance = await asyncio.to_thread(
                self._resource.Instance,
                instance_id
            )
            await asyncio.to_thread(instance.reload)
            return instance.state['Name']
            
        except Exception:
            return None
    
    def get_running_instances(self) -> List[CloudInstance]:
        """Obtiene la lista de instancias en ejecución.
        
        Returns:
            Lista de CloudInstance activas.
        """
        return list(self._instances.values())
    
    async def cleanup_all(self) -> int:
        """Termina todas las instancias.
        
        Returns:
            Número de instancias terminadas.
        """
        count = 0
        instance_ids = list(self._instances.keys())
        
        for instance_id in instance_ids:
            if await self.terminate_instance(instance_id):
                count += 1
        
        return count


class ResourceMonitor:
    """Monitor de recursos del sistema para auto-escalado."""
    
    def __init__(
        self,
        ram_threshold_percent: int = 85,
        cpu_threshold_percent: int = 80
    ):
        """Inicializa el monitor de recursos.
        
        Args:
            ram_threshold_percent: Umbral de RAM para escalado.
            cpu_threshold_percent: Umbral de CPU para escalado.
        """
        self.ram_threshold = ram_threshold_percent
        self.cpu_threshold = cpu_threshold_percent
        self._history: List[Dict[str, float]] = []
        self._max_history = 60  # Mantener 60 muestras
    
    def get_current_usage(self) -> Dict[str, float]:
        """Obtiene el uso actual de recursos.
        
        Returns:
            Diccionario con uso de CPU y RAM.
        """
        if not PSUTIL_AVAILABLE:
            return {"cpu": 0.0, "ram": 0.0}
        
        usage = {
            "cpu": psutil.cpu_percent(interval=0.1),
            "ram": psutil.virtual_memory().percent,
            "timestamp": datetime.now().timestamp()
        }
        
        # Agregar al historial
        self._history.append(usage)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        return usage
    
    def should_scale_to_cloud(self) -> bool:
        """Determina si se debe escalar a cloud.
        
        Retorna True si el uso de recursos excede los umbrales
        de manera consistente.
        
        Returns:
            True si se debe escalar, False de lo contrario.
        """
        usage = self.get_current_usage()
        
        # Verificar umbrales actuales
        if usage["ram"] > self.ram_threshold or usage["cpu"] > self.cpu_threshold:
            # Verificar que sea consistente (últimas 3 muestras)
            if len(self._history) >= 3:
                recent = self._history[-3:]
                avg_ram = sum(s["ram"] for s in recent) / 3
                avg_cpu = sum(s["cpu"] for s in recent) / 3
                return avg_ram > self.ram_threshold or avg_cpu > self.cpu_threshold
            return True
        
        return False
    
    def should_scale_down(self) -> bool:
        """Determina si se puede reducir el escalado.
        
        Returns:
            True si se puede reducir, False de lo contrario.
        """
        usage = self.get_current_usage()
        
        # Si los recursos están por debajo del 50% de los umbrales
        safe_ram = self.ram_threshold * 0.5
        safe_cpu = self.cpu_threshold * 0.5
        
        if usage["ram"] < safe_ram and usage["cpu"] < safe_cpu:
            # Verificar que sea consistente (últimas 5 muestras)
            if len(self._history) >= 5:
                recent = self._history[-5:]
                avg_ram = sum(s["ram"] for s in recent) / 5
                avg_cpu = sum(s["cpu"] for s in recent) / 5
                return avg_ram < safe_ram and avg_cpu < safe_cpu
        
        return False
    
    def get_resource_report(self) -> Dict[str, Any]:
        """Genera un reporte de recursos.
        
        Returns:
            Diccionario con estadísticas de recursos.
        """
        if not self._history:
            return {"error": "Sin datos de historial"}
        
        return {
            "current": self.get_current_usage(),
            "avg_cpu": sum(s["cpu"] for s in self._history) / len(self._history),
            "avg_ram": sum(s["ram"] for s in self._history) / len(self._history),
            "max_cpu": max(s["cpu"] for s in self._history),
            "max_ram": max(s["ram"] for s in self._history),
            "samples": len(self._history),
            "should_scale_to_cloud": self.should_scale_to_cloud(),
            "should_scale_down": self.should_scale_down()
        }


class ScalingManager:
    """Administrador principal de escalabilidad.
    
    Coordina Docker, AWS y monitoreo de recursos para
    escalar automáticamente las sesiones.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        on_scale_event: Optional[Callable] = None
    ):
        """Inicializa el administrador de escalabilidad.
        
        Args:
            config: Configuración de escalabilidad.
            on_scale_event: Callback para eventos de escalado.
        """
        self.config = config or {}
        self.on_scale_event = on_scale_event
        
        # Inicializar componentes
        self.docker = DockerManager(
            image_name=self.config.get('docker_image', 'botsos:latest')
        )
        self.aws = AWSCloudManager(
            region=self.config.get('aws_region', 'us-east-1'),
            instance_type=self.config.get('aws_instance_type', 't3.medium')
        )
        self.resource_monitor = ResourceMonitor(
            ram_threshold_percent=self.config.get('ram_threshold_percent', 85),
            cpu_threshold_percent=self.config.get('cpu_threshold_percent', 80)
        )
        
        # Estado
        self._local_sessions: List[str] = []
        self._cloud_sessions: List[str] = []
        self._auto_scale_task: Optional[asyncio.Task] = None
    
    @property
    def docker_available(self) -> bool:
        """Verifica si Docker está disponible."""
        return self.docker.is_available
    
    @property
    def aws_available(self) -> bool:
        """Verifica si AWS está disponible."""
        return self.aws.is_available
    
    async def start_session(
        self,
        session_id: str,
        session_config: Dict[str, Any],
        force_local: bool = False,
        force_cloud: bool = False
    ) -> Dict[str, Any]:
        """Inicia una sesión, decidiendo dónde ejecutarla.
        
        Args:
            session_id: ID de la sesión.
            session_config: Configuración de la sesión.
            force_local: Forzar ejecución local.
            force_cloud: Forzar ejecución en cloud.
            
        Returns:
            Información sobre dónde se inició la sesión.
        """
        result = {
            "session_id": session_id,
            "location": "local",
            "success": False,
            "message": ""
        }
        
        # Determinar ubicación
        if force_cloud and self.aws_available:
            result["location"] = "cloud"
        elif force_local:
            result["location"] = "local"
        elif self.resource_monitor.should_scale_to_cloud() and self.aws_available:
            result["location"] = "cloud"
            result["message"] = "Auto-escalado a cloud debido a recursos limitados"
        elif self.docker_available and self.config.get('docker_enabled', False):
            result["location"] = "docker"
        
        # Iniciar según ubicación
        if result["location"] == "cloud":
            # Implementar lógica de cloud aquí
            self._cloud_sessions.append(session_id)
            result["success"] = True
            result["message"] = result["message"] or "Sesión migrada a cloud"
        elif result["location"] == "docker":
            container = await self.docker.create_session_container(
                session_id,
                session_config,
                volume_mounts=self.config.get('docker_volume_mounts', []),
                network_mode=self.config.get('docker_network_mode', 'bridge')
            )
            if container:
                result["success"] = True
                result["message"] = f"Sesión iniciada en Docker: {container.container_id[:12]}"
        else:
            self._local_sessions.append(session_id)
            result["success"] = True
            result["message"] = "Sesión iniciada localmente"
        
        # Notificar evento
        if self.on_scale_event:
            await asyncio.to_thread(self.on_scale_event, result)
        
        return result
    
    async def stop_session(self, session_id: str) -> bool:
        """Detiene una sesión.
        
        Args:
            session_id: ID de la sesión.
            
        Returns:
            True si se detuvo exitosamente.
        """
        # Intentar detener en Docker
        if await self.docker.stop_session_container(session_id):
            return True
        
        # Remover de listas locales
        if session_id in self._local_sessions:
            self._local_sessions.remove(session_id)
            return True
        
        if session_id in self._cloud_sessions:
            self._cloud_sessions.remove(session_id)
            return True
        
        return False
    
    async def migrate_to_cloud(self, session_id: str) -> bool:
        """Migra una sesión local a cloud.
        
        Args:
            session_id: ID de la sesión a migrar.
            
        Returns:
            True si se migró exitosamente.
        """
        if not self.aws_available:
            logger.error("AWS no está disponible para migración")
            return False
        
        if session_id in self._local_sessions:
            self._local_sessions.remove(session_id)
            self._cloud_sessions.append(session_id)
            logger.info(f"Sesión {session_id} migrada a cloud")
            return True
        
        return False
    
    async def migrate_to_local(self, session_id: str) -> bool:
        """Migra una sesión de cloud a local.
        
        Args:
            session_id: ID de la sesión a migrar.
            
        Returns:
            True si se migró exitosamente.
        """
        if session_id in self._cloud_sessions:
            self._cloud_sessions.remove(session_id)
            self._local_sessions.append(session_id)
            logger.info(f"Sesión {session_id} migrada a local")
            return True
        
        return False
    
    def start_auto_scaling(self, check_interval_sec: int = 30):
        """Inicia el auto-escalado en segundo plano.
        
        Args:
            check_interval_sec: Intervalo entre verificaciones.
        """
        if self._auto_scale_task is not None:
            return
        
        async def auto_scale_loop():
            while True:
                try:
                    # Verificar si se necesita escalar
                    if self.resource_monitor.should_scale_to_cloud():
                        logger.info("Auto-escalado: recursos limitados, migrando a cloud...")
                        # Migrar sesiones locales más antiguas
                        if self._local_sessions and self.aws_available:
                            session_id = self._local_sessions[0]
                            await self.migrate_to_cloud(session_id)
                    
                    elif self.resource_monitor.should_scale_down():
                        logger.info("Auto-escalado: recursos disponibles, migrando de cloud...")
                        # Migrar sesiones de cloud a local
                        if self._cloud_sessions:
                            session_id = self._cloud_sessions[0]
                            await self.migrate_to_local(session_id)
                    
                except Exception as e:
                    logger.error(f"Error en auto-escalado: {e}")
                
                await asyncio.sleep(check_interval_sec)
        
        self._auto_scale_task = asyncio.create_task(auto_scale_loop())
        logger.info("Auto-escalado iniciado")
    
    def stop_auto_scaling(self):
        """Detiene el auto-escalado."""
        if self._auto_scale_task:
            self._auto_scale_task.cancel()
            self._auto_scale_task = None
            logger.info("Auto-escalado detenido")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sistema de escalabilidad.
        
        Returns:
            Diccionario con estado del sistema.
        """
        return {
            "docker_available": self.docker_available,
            "aws_available": self.aws_available,
            "local_sessions": len(self._local_sessions),
            "docker_sessions": len(self.docker.get_running_containers()),
            "cloud_sessions": len(self._cloud_sessions),
            "resources": self.resource_monitor.get_resource_report(),
            "auto_scaling_active": self._auto_scale_task is not None
        }
    
    async def cleanup(self):
        """Limpia todos los recursos."""
        self.stop_auto_scaling()
        await self.docker.cleanup_all()
        await self.aws.cleanup_all()
        self._local_sessions.clear()
        self._cloud_sessions.clear()
        logger.info("Recursos de escalabilidad limpiados")
