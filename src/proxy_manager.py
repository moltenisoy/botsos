"""
Módulo Administrador de Proxies.

Maneja la gestión del pool de proxies, rotación y validación.
Diseñado para Windows.
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
    """Represents a single proxy in the pool."""
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
        """Get the full proxy URL."""
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        return f"{self.proxy_type}://{auth}{self.server}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of this proxy."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProxyEntry':
        """Create from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_url(cls, url: str) -> 'ProxyEntry':
        """Parse proxy from URL format.
        
        Supports formats:
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
    """Manages a pool of proxies with rotation and health tracking."""
    
    def __init__(self, data_dir: Path):
        """Initialize the proxy manager.
        
        Args:
            data_dir: Directory for storing proxy data.
        """
        self.data_dir = Path(data_dir)
        self.proxies_file = self.data_dir / "proxies.json"
        self.proxies: List[ProxyEntry] = []
        self._current_index = 0
        self._ensure_data_dir()
        self._load_proxies()
    
    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_proxies(self) -> None:
        """Load proxies from storage."""
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
        """Save proxies to storage."""
        data = {
            'proxies': [p.to_dict() for p in self.proxies],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.proxies_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_proxy(self, proxy: ProxyEntry) -> None:
        """Add a proxy to the pool.
        
        Args:
            proxy: The proxy entry to add.
        """
        self.proxies.append(proxy)
        self._save_proxies()
        logger.info(f"Added proxy: {proxy.server}:{proxy.port}")
    
    def add_proxy_from_url(self, url: str) -> ProxyEntry:
        """Add a proxy from URL string.
        
        Args:
            url: Proxy URL in format protocol://[user:pass@]host:port
            
        Returns:
            The created proxy entry.
        """
        proxy = ProxyEntry.from_url(url)
        self.add_proxy(proxy)
        return proxy
    
    def remove_proxy(self, index: int) -> bool:
        """Remove a proxy by index.
        
        Args:
            index: Index of the proxy to remove.
            
        Returns:
            True if removed, False if index out of range.
        """
        if 0 <= index < len(self.proxies):
            removed = self.proxies.pop(index)
            self._save_proxies()
            logger.info(f"Removed proxy: {removed.server}:{removed.port}")
            return True
        return False
    
    def get_next_proxy(self, strategy: str = "round_robin") -> Optional[ProxyEntry]:
        """Get the next proxy based on rotation strategy.
        
        Args:
            strategy: Rotation strategy - "round_robin", "random", "best"
            
        Returns:
            The next proxy or None if pool is empty.
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
        """Report successful use of a proxy.
        
        Args:
            proxy: The proxy that was used successfully.
        """
        for p in self.proxies:
            if p.server == proxy.server and p.port == proxy.port:
                p.success_count += 1
                break
        self._save_proxies()
    
    def report_failure(self, proxy: ProxyEntry, deactivate_threshold: int = 5) -> None:
        """Report failed use of a proxy.
        
        Args:
            proxy: The proxy that failed.
            deactivate_threshold: Number of consecutive failures before deactivation.
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
        """Import proxies from a text file (one URL per line).
        
        Args:
            file_path: Path to the file containing proxy URLs.
            
        Returns:
            Number of proxies imported.
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
        """Export proxies to a text file.
        
        Args:
            file_path: Path to the output file.
            
        Returns:
            Number of proxies exported.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            for proxy in self.proxies:
                f.write(f"{proxy.url}\n")
        return len(self.proxies)
    
    def get_all_proxies(self) -> List[ProxyEntry]:
        """Get all proxies in the pool.
        
        Returns:
            List of all proxy entries.
        """
        return self.proxies.copy()
    
    def get_active_count(self) -> int:
        """Get count of active proxies.
        
        Returns:
            Number of active proxies.
        """
        return sum(1 for p in self.proxies if p.is_active)
    
    def clear_all(self) -> None:
        """Remove all proxies from the pool."""
        self.proxies.clear()
        self._save_proxies()
        logger.info("Cleared all proxies from pool")
