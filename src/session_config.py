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
    
    # Hybrid CAPTCHA solver settings (from fase3.txt)
    hybrid_mode: bool = True  # AI first, human fallback
    secondary_provider: str = "capsolver"  # Fallback provider


@dataclass
class ContingencyConfig:
    """Configuration for contingency planning (from fase3.txt)."""
    # Eviction thresholds
    block_rate_threshold: float = 0.10  # 5-10% - evict proxy if block rate exceeds this
    consecutive_failure_threshold: int = 3  # 3-5 consecutive failures before eviction
    
    # Cool-down settings
    cool_down_min_sec: int = 300  # 5 minutes minimum cool-down
    cool_down_max_sec: int = 1200  # 20 minutes maximum cool-down
    
    # Ban recovery
    ban_recovery_strategy: str = "mobile_fallback"  # mobile_fallback, throttle, rotate_all
    enable_dynamic_throttling: bool = True
    
    # Session management
    sticky_session_duration_sec: int = 600  # 10 minutes sticky sessions
    enable_session_persistence: bool = True


@dataclass
class AdvancedBehaviorConfig:
    """Configuration for advanced behavioral simulation (from fase3.txt)."""
    # Polymorphic fingerprinting
    polymorphic_fingerprint_enabled: bool = True
    fingerprint_rotation_interval_sec: int = 3600  # Rotate every hour
    
    # OS-level input emulation
    os_level_input_enabled: bool = False  # Use nodriver-style emulation
    
    # Touch emulation for mobile
    touch_emulation_enabled: bool = False
    touch_pressure_variation: float = 0.2  # 20% pressure variation
    
    # Micro-jitters for touch patterns
    micro_jitter_enabled: bool = True
    micro_jitter_amplitude: int = 2  # Pixels
    
    # Typing pressure patterns
    typing_pressure_enabled: bool = False
    typing_rhythm_variation: float = 0.15  # 15% variation


@dataclass
class SystemHidingConfig:
    """Configuration for system/port hiding (from fase3.txt)."""
    # CDP port blocking
    block_cdp_ports: bool = True
    cdp_port_default: int = 9222
    
    # Loopback interface management
    disable_loopback_services: bool = False
    
    # Ephemeral port randomization
    randomize_ephemeral_ports: bool = True
    ephemeral_port_min: int = 49152
    ephemeral_port_max: int = 65535
    
    # Firewall rules (commands)
    custom_firewall_rules: List[str] = field(default_factory=list)
    
    # WebRTC leak prevention
    block_webrtc_completely: bool = False  # More aggressive than just spoofing


@dataclass
class MfaConfig:
    """Configuration for MFA contingency handling (from fase3.txt)."""
    mfa_simulation_enabled: bool = False
    mfa_method: str = "none"  # none, email, sms (for future integration)
    mfa_timeout_sec: int = 120
    show_ethical_warning: bool = True


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
    
    # Phase 3 configurations
    contingency: ContingencyConfig = field(default_factory=ContingencyConfig)
    advanced_behavior: AdvancedBehaviorConfig = field(default_factory=AdvancedBehaviorConfig)
    system_hiding: SystemHidingConfig = field(default_factory=SystemHidingConfig)
    mfa: MfaConfig = field(default_factory=MfaConfig)
    
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
        contingency_data = data.pop('contingency', {})
        advanced_behavior_data = data.pop('advanced_behavior', {})
        system_hiding_data = data.pop('system_hiding', {})
        mfa_data = data.pop('mfa', {})
        
        # Filter out unknown fields from nested configs to handle version changes
        behavior_fields = set(BehaviorConfig.__dataclass_fields__.keys())
        proxy_fields = set(ProxyConfig.__dataclass_fields__.keys())
        fingerprint_fields = set(FingerprintConfig.__dataclass_fields__.keys())
        captcha_fields = set(CaptchaConfig.__dataclass_fields__.keys())
        contingency_fields = set(ContingencyConfig.__dataclass_fields__.keys())
        advanced_behavior_fields = set(AdvancedBehaviorConfig.__dataclass_fields__.keys())
        system_hiding_fields = set(SystemHidingConfig.__dataclass_fields__.keys())
        mfa_fields = set(MfaConfig.__dataclass_fields__.keys())
        
        return cls(
            behavior=BehaviorConfig(**{k: v for k, v in behavior_data.items() if k in behavior_fields}),
            proxy=ProxyConfig(**{k: v for k, v in proxy_data.items() if k in proxy_fields}),
            fingerprint=FingerprintConfig(**{k: v for k, v in fingerprint_data.items() if k in fingerprint_fields}),
            captcha=CaptchaConfig(**{k: v for k, v in captcha_data.items() if k in captcha_fields}),
            contingency=ContingencyConfig(**{k: v for k, v in contingency_data.items() if k in contingency_fields}),
            advanced_behavior=AdvancedBehaviorConfig(**{k: v for k, v in advanced_behavior_data.items() if k in advanced_behavior_fields}),
            system_hiding=SystemHidingConfig(**{k: v for k, v in system_hiding_data.items() if k in system_hiding_fields}),
            mfa=MfaConfig(**{k: v for k, v in mfa_data.items() if k in mfa_fields}),
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
