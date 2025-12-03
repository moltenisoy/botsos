"""
Session Configuration Module

Handles session configuration data model and persistence.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class BehaviorConfig:
    """Configuration for session behavior settings."""
    llm_model: str = "llama3.1:8b"
    ad_skip_delay_sec: int = 5
    view_time_min_sec: int = 30
    view_time_max_sec: int = 120
    action_delay_min_ms: int = 100
    action_delay_max_ms: int = 500
    enable_like: bool = True
    enable_comment: bool = True
    enable_subscribe: bool = False
    enable_skip_ads: bool = True
    comment_phrases: List[str] = field(default_factory=lambda: [
        "¡Excelente video!",
        "Muy buen contenido.",
        "Gracias por compartir."
    ])
    task_prompt: str = ""
    selected_routine: str = ""
    
    # Behavior Simulation (from fase2.txt)
    idle_time_min_sec: float = 5.0
    idle_time_max_sec: float = 15.0
    mouse_jitter_enabled: bool = True
    mouse_jitter_px: int = 5
    scroll_simulation_enabled: bool = True
    scroll_delta_min: int = 50
    scroll_delta_max: int = 300
    typing_speed_min_ms: int = 50
    typing_speed_max_ms: int = 200
    typing_mistake_rate: float = 0.02
    enable_random_hover: bool = True
    enable_random_scroll: bool = True
    random_action_probability: float = 0.1


@dataclass
class ProxyConfig:
    """Configuration for proxy settings."""
    server: str = ""
    port: int = 0
    username: str = ""
    password: str = ""
    proxy_type: str = "http"  # http, https, socks5
    enabled: bool = False
    
    # Proxy pool and rotation settings (from fase2.txt)
    rotation_interval: int = 10  # Rotate every N requests
    rotation_strategy: str = "round_robin"  # round_robin, random, best_performance
    validate_before_use: bool = True
    auto_deactivate_failed: bool = True
    failure_threshold: int = 5


@dataclass
class FingerprintConfig:
    """Configuration for device fingerprint settings."""
    device_preset: str = "windows_desktop"
    user_agent: str = ""
    viewport_width: int = 1920
    viewport_height: int = 1080
    hardware_concurrency: int = 8
    device_memory: int = 8
    platform: str = "Win32"
    timezone: str = "America/New_York"
    languages: List[str] = field(default_factory=lambda: ["en-US", "en"])
    canvas_noise_enabled: bool = True
    canvas_noise_level: int = 5
    webrtc_protection_enabled: bool = True
    webgl_spoofing_enabled: bool = True
    audio_context_spoofing_enabled: bool = True
    font_spoofing_enabled: bool = True
    
    # Advanced spoofing settings (from fase2.txt - second block)
    tls_profile: str = "chrome_120"  # chrome_110, chrome_120, firefox_121, safari_17
    webgpu_spoofing_enabled: bool = True
    webgpu_vendor: str = "Google Inc."
    webgpu_architecture: str = "x86_64"
    client_hints_enabled: bool = True
    custom_fonts: List[str] = field(default_factory=lambda: [
        "Arial", "Helvetica", "Times New Roman",
        "Georgia", "Verdana", "Courier New"
    ])


@dataclass
class CaptchaConfig:
    """Configuration for CAPTCHA handling (from fase2.txt - second block)."""
    enabled: bool = False
    provider: str = "2captcha"  # 2captcha, anticaptcha, capsolver
    auto_solve: bool = True
    captcha_types: List[str] = field(default_factory=lambda: ["recaptcha_v2", "recaptcha_v3", "hcaptcha"])
    timeout_sec: int = 120
    max_retries: int = 3


@dataclass
class SessionConfig:
    """Complete configuration for a single session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "New Session"
    enabled: bool = True
    headless: bool = False
    browser_type: str = "chromium"
    persistent_context: bool = True
    context_dir: str = "browser_context"
    
    behavior: BehaviorConfig = field(default_factory=BehaviorConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    fingerprint: FingerprintConfig = field(default_factory=FingerprintConfig)
    captcha: CaptchaConfig = field(default_factory=CaptchaConfig)
    
    # Retry settings (from fase2.txt - second block)
    max_retries: int = 3
    retry_delay_sec: float = 1.0
    exponential_backoff: bool = True
    
    # Runtime state (not persisted)
    status: str = field(default="idle", repr=False)  # idle, running, paused, error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for JSON serialization."""
        data = asdict(self)
        # Remove runtime state
        data.pop('status', None)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionConfig':
        """Create configuration from dictionary."""
        behavior_data = data.pop('behavior', {})
        proxy_data = data.pop('proxy', {})
        fingerprint_data = data.pop('fingerprint', {})
        captcha_data = data.pop('captcha', {})
        
        # Filter out unknown fields from nested configs to handle version changes
        behavior_fields = set(BehaviorConfig.__dataclass_fields__.keys())
        proxy_fields = set(ProxyConfig.__dataclass_fields__.keys())
        fingerprint_fields = set(FingerprintConfig.__dataclass_fields__.keys())
        captcha_fields = set(CaptchaConfig.__dataclass_fields__.keys())
        
        return cls(
            behavior=BehaviorConfig(**{k: v for k, v in behavior_data.items() if k in behavior_fields}),
            proxy=ProxyConfig(**{k: v for k, v in proxy_data.items() if k in proxy_fields}),
            fingerprint=FingerprintConfig(**{k: v for k, v in fingerprint_data.items() if k in fingerprint_fields}),
            captcha=CaptchaConfig(**{k: v for k, v in captcha_data.items() if k in captcha_fields}),
            **{k: v for k, v in data.items() if k not in ('status',) and k in cls.__dataclass_fields__}
        )
    
    def save(self, path: Path) -> None:
        """Save configuration to JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, path: Path) -> 'SessionConfig':
        """Load configuration from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


class SessionConfigManager:
    """Manages multiple session configurations with persistence."""
    
    def __init__(self, data_dir: Path):
        """Initialize the configuration manager.
        
        Args:
            data_dir: Directory for storing session configurations.
        """
        self.data_dir = Path(data_dir)
        self.sessions_file = self.data_dir / "sessions.json"
        self.sessions: Dict[str, SessionConfig] = {}
        self._ensure_data_dir()
        self._load_sessions()
    
    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_sessions(self) -> None:
        """Load all sessions from storage."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for session_data in data.get('sessions', []):
                    session = SessionConfig.from_dict(session_data)
                    self.sessions[session.session_id] = session
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading sessions: {e}")
    
    def _save_sessions(self) -> None:
        """Save all sessions to storage."""
        data = {
            'sessions': [s.to_dict() for s in self.sessions.values()]
        }
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_session(self, name: str = "New Session") -> SessionConfig:
        """Create a new session with default configuration.
        
        Args:
            name: Display name for the session.
            
        Returns:
            The newly created session configuration.
        """
        session = SessionConfig(name=name)
        self.sessions[session.session_id] = session
        self._save_sessions()
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionConfig]:
        """Get a session by ID.
        
        Args:
            session_id: The session identifier.
            
        Returns:
            The session configuration or None if not found.
        """
        return self.sessions.get(session_id)
    
    def update_session(self, session: SessionConfig) -> None:
        """Update a session configuration.
        
        Args:
            session: The session configuration to update.
        """
        self.sessions[session.session_id] = session
        self._save_sessions()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session.
        
        Args:
            session_id: The session identifier to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
            return True
        return False
    
    def get_all_sessions(self) -> List[SessionConfig]:
        """Get all session configurations.
        
        Returns:
            List of all session configurations.
        """
        return list(self.sessions.values())
