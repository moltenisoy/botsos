"""
Módulo Administrador de Proxies.

Maneja la gestión del pool de proxies, rotación y validación.
Diseñado exclusivamente para Windows.
"""

import json
import random
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class ProxyEntry:
    """Representa un proxy individual en el pool."""
    server: str
    port: int
    username: str = ""
    password: str = ""
    proxy_type: str = "http"  # http, https, socks5
    country: str = ""
    is_active: bool = True
    last_used: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    
    @property
    def url(self) -> str:
        """Obtiene la URL completa del proxy."""
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        return f"{self.proxy_type}://{auth}{self.server}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito de este proxy."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProxyEntry':
        """Crea desde diccionario."""
        return cls(**data)
    
    @classmethod
    def from_url(cls, url: str) -> 'ProxyEntry':
        """Parsea proxy desde formato URL.
        
        Soporta formatos:
        - http://host:port
        - http://user:pass@host:port
        - socks5://host:port
        """
        proxy_type = "http"
        username = ""
        password = ""
        
        # Extract protocol
        if "://" in url:
            proxy_type, url = url.split("://", 1)
        
        # Extract auth
        if "@" in url:
            auth, url = url.rsplit("@", 1)
            if ":" in auth:
                username, password = auth.split(":", 1)
            else:
                username = auth
        
        # Extract host and port
        if ":" in url:
            server, port_str = url.rsplit(":", 1)
            port = int(port_str)
        else:
            server = url
            port = 8080  # Default port
        
        return cls(
            server=server,
            port=port,
            username=username,
            password=password,
            proxy_type=proxy_type
        )


class ProxyManager:
    """Administra un pool de proxies con rotación y seguimiento de salud."""
    
    def __init__(self, data_dir: Path):
        """Inicializa el administrador de proxies.
        
        Args:
            data_dir: Directorio para almacenar datos de proxies.
        """
        self.data_dir = Path(data_dir)
        self.proxies_file = self.data_dir / "proxies.json"
        self.proxies: List[ProxyEntry] = []
        self._current_index = 0
        self._ensure_data_dir()
        self._load_proxies()
    
    def _ensure_data_dir(self) -> None:
        """Asegura que el directorio de datos existe."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_proxies(self) -> None:
        """Carga proxies desde almacenamiento."""
        if self.proxies_file.exists():
            try:
                with open(self.proxies_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.proxies = [
                    ProxyEntry.from_dict(p) for p in data.get('proxies', [])
                ]
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error loading proxies: {e}")
    
    def _save_proxies(self) -> None:
        """Guarda proxies en almacenamiento."""
        data = {
            'proxies': [p.to_dict() for p in self.proxies],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.proxies_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_proxy(self, proxy: ProxyEntry) -> None:
        """Agrega un proxy al pool.
        
        Args:
            proxy: La entrada de proxy a agregar.
        """
        self.proxies.append(proxy)
        self._save_proxies()
        logger.info(f"Added proxy: {proxy.server}:{proxy.port}")
    
    def add_proxy_from_url(self, url: str) -> ProxyEntry:
        """Agrega un proxy desde string URL.
        
        Args:
            url: URL del proxy en formato protocol://[user:pass@]host:port
            
        Returns:
            La entrada de proxy creada.
        """
        proxy = ProxyEntry.from_url(url)
        self.add_proxy(proxy)
        return proxy
    
    def remove_proxy(self, index: int) -> bool:
        """Elimina un proxy por índice.
        
        Args:
            index: Índice del proxy a eliminar.
            
        Returns:
            True si se eliminó, False si el índice está fuera de rango.
        """
        if 0 <= index < len(self.proxies):
            removed = self.proxies.pop(index)
            self._save_proxies()
            logger.info(f"Removed proxy: {removed.server}:{removed.port}")
            return True
        return False
    
    def get_next_proxy(self, strategy: str = "round_robin") -> Optional[ProxyEntry]:
        """Obtiene el siguiente proxy basado en estrategia de rotación.
        
        Args:
            strategy: Estrategia de rotación - "round_robin", "random", "best"
            
        Returns:
            El siguiente proxy o None si el pool está vacío.
        """
        active_proxies = [p for p in self.proxies if p.is_active]
        
        if not active_proxies:
            return None
        
        if strategy == "random":
            proxy = random.choice(active_proxies)
        elif strategy == "best":
            # Select proxy with best success rate
            proxy = max(active_proxies, key=lambda p: p.success_rate)
        else:  # round_robin
            self._current_index = self._current_index % len(active_proxies)
            proxy = active_proxies[self._current_index]
            self._current_index += 1
        
        proxy.last_used = datetime.now().isoformat()
        self._save_proxies()
        return proxy
    
    def report_success(self, proxy: ProxyEntry) -> None:
        """Reporta uso exitoso de un proxy.
        
        Args:
            proxy: El proxy que se usó exitosamente.
        """
        for p in self.proxies:
            if p.server == proxy.server and p.port == proxy.port:
                p.success_count += 1
                break
        self._save_proxies()
    
    def report_failure(self, proxy: ProxyEntry, deactivate_threshold: int = 5) -> None:
        """Reporta uso fallido de un proxy.
        
        Args:
            proxy: El proxy que falló.
            deactivate_threshold: Número de fallos consecutivos antes de desactivación.
        """
        for p in self.proxies:
            if p.server == proxy.server and p.port == proxy.port:
                p.failure_count += 1
                if p.failure_count >= deactivate_threshold:
                    p.is_active = False
                    logger.warning(
                        f"Deactivated proxy {p.server}:{p.port} after "
                        f"{deactivate_threshold} failures"
                    )
                break
        self._save_proxies()
    
    def import_from_file(self, file_path: Path) -> int:
        """Importa proxies desde un archivo de texto (una URL por línea).
        
        Args:
            file_path: Ruta al archivo que contiene URLs de proxies.
            
        Returns:
            Número de proxies importados.
        """
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        self.add_proxy_from_url(line)
                        count += 1
                    except ValueError as e:
                        logger.warning(f"Failed to parse proxy: {line} - {e}")
        return count
    
    def export_to_file(self, file_path: Path) -> int:
        """Exporta proxies a un archivo de texto.
        
        Args:
            file_path: Ruta al archivo de salida.
            
        Returns:
            Número de proxies exportados.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            for proxy in self.proxies:
                f.write(f"{proxy.url}\n")
        return len(self.proxies)
    
    def get_all_proxies(self) -> List[ProxyEntry]:
        """Obtiene todos los proxies en el pool.
        
        Returns:
            Lista de todas las entradas de proxy.
        """
        return self.proxies.copy()
    
    def get_active_count(self) -> int:
        """Obtiene el conteo de proxies activos.
        
        Returns:
            Número de proxies activos.
        """
        return sum(1 for p in self.proxies if p.is_active)
    
    def clear_all(self) -> None:
        """Elimina todos los proxies del pool."""
        self.proxies.clear()
        self._save_proxies()
        logger.info("Cleared all proxies from pool")
