"""
Advanced Features Module

Handles advanced anti-detection features including:
- CAPTCHA solving integration
- Advanced fingerprint spoofing (TLS, WebGPU, Audio)
- Behavioral simulation (mouse jitter, delays, scrolling)
- Proxy validation
- Secure credential storage
- Retry mechanisms
"""

import asyncio
import logging
import random
import os
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AdvancedSpoofingConfig:
    """Configuration for advanced fingerprint spoofing."""
    # TLS/JA3 Fingerprint
    tls_profile: str = "chrome_120"  # chrome_110, chrome_120, firefox_121, safari_17
    
    # WebGPU Settings
    webgpu_enabled: bool = True
    webgpu_vendor: str = "Google Inc."
    webgpu_architecture: str = "x86_64"
    
    # Canvas/WebGL Advanced
    canvas_noise_enabled: bool = True
    canvas_noise_level: int = 5  # 0-10
    webgl_noise_enabled: bool = True
    webgl_vendor_override: str = ""
    webgl_renderer_override: str = ""
    
    # Audio Context
    audio_context_noise: bool = True
    audio_noise_level: int = 3  # 0-10
    
    # Font Spoofing
    font_spoofing_enabled: bool = True
    custom_fonts: List[str] = field(default_factory=lambda: [
        "Arial", "Helvetica", "Times New Roman",
        "Georgia", "Verdana", "Courier New"
    ])
    
    # Client Hints
    client_hints_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tls_profile": self.tls_profile,
            "webgpu_enabled": self.webgpu_enabled,
            "webgpu_vendor": self.webgpu_vendor,
            "webgpu_architecture": self.webgpu_architecture,
            "canvas_noise_enabled": self.canvas_noise_enabled,
            "canvas_noise_level": self.canvas_noise_level,
            "webgl_noise_enabled": self.webgl_noise_enabled,
            "webgl_vendor_override": self.webgl_vendor_override,
            "webgl_renderer_override": self.webgl_renderer_override,
            "audio_context_noise": self.audio_context_noise,
            "audio_noise_level": self.audio_noise_level,
            "font_spoofing_enabled": self.font_spoofing_enabled,
            "custom_fonts": self.custom_fonts,
            "client_hints_enabled": self.client_hints_enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdvancedSpoofingConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def get_spoofing_scripts(self) -> List[str]:
        """Get JavaScript injection scripts for advanced spoofing."""
        scripts = []
        
        # WebGPU spoofing
        if self.webgpu_enabled:
            scripts.append(f"""
                if ('gpu' in navigator) {{
                    const originalGPU = navigator.gpu;
                    Object.defineProperty(navigator, 'gpu', {{
                        get: function() {{
                            const adapter = {{
                                requestDevice: () => Promise.resolve(null),
                                requestAdapterInfo: () => Promise.resolve({{
                                    vendor: '{self.webgpu_vendor}',
                                    architecture: '{self.webgpu_architecture}'
                                }})
                            }};
                            return {{
                                requestAdapter: () => Promise.resolve(adapter)
                            }};
                        }}
                    }});
                }}
            """)
        
        # Enhanced canvas noise injection
        if self.canvas_noise_enabled:
            scripts.append(f"""
                const noise = {self.canvas_noise_level};
                
                // Canvas 2D noise
                const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
                    const imageData = origGetImageData.apply(this, args);
                    for (let i = 0; i < imageData.data.length; i += 4) {{
                        imageData.data[i] = Math.max(0, Math.min(255, 
                            imageData.data[i] + Math.floor(Math.random() * noise * 2 - noise)));
                    }}
                    return imageData;
                }};
                
                // Canvas toBlob noise
                const origToBlob = HTMLCanvasElement.prototype.toBlob;
                HTMLCanvasElement.prototype.toBlob = function(callback, ...args) {{
                    const ctx = this.getContext('2d');
                    if (ctx) {{
                        const imageData = ctx.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            imageData.data[i] = Math.max(0, Math.min(255,
                                imageData.data[i] + Math.floor(Math.random() * noise * 2 - noise)));
                        }}
                        ctx.putImageData(imageData, 0, 0);
                    }}
                    return origToBlob.call(this, callback, ...args);
                }};
            """)
        
        # Font spoofing
        if self.font_spoofing_enabled and self.custom_fonts:
            fonts_json = str(self.custom_fonts).replace("'", '"')
            scripts.append(f"""
                const spoofedFonts = {fonts_json};
                
                // Override font detection methods
                Object.defineProperty(document, 'fonts', {{
                    get: function() {{
                        return {{
                            check: (font, text) => spoofedFonts.some(f => font.includes(f)),
                            ready: Promise.resolve(true),
                            forEach: function(callback) {{
                                spoofedFonts.forEach(f => callback({{family: f}}));
                            }}
                        }};
                    }}
                }});
            """)
        
        # Client Hints Override
        if self.client_hints_enabled:
            scripts.append("""
                Object.defineProperty(navigator, 'userAgentData', {
                    get: function() {
                        return {
                            brands: [
                                {brand: "Not_A Brand", version: "8"},
                                {brand: "Chromium", version: "120"},
                                {brand: "Google Chrome", version: "120"}
                            ],
                            mobile: false,
                            platform: "Windows",
                            getHighEntropyValues: function(hints) {
                                return Promise.resolve({
                                    architecture: "x86",
                                    bitness: "64",
                                    model: "",
                                    platformVersion: "15.0.0",
                                    uaFullVersion: "120.0.0.0",
                                    fullVersionList: this.brands
                                });
                            }
                        };
                    }
                });
            """)
        
        return scripts


@dataclass
class BehaviorSimulationConfig:
    """Configuration for human-like behavior simulation."""
    # Timing
    min_action_delay_ms: int = 100
    max_action_delay_ms: int = 500
    idle_time_min_sec: float = 5.0
    idle_time_max_sec: float = 15.0
    
    # Mouse Simulation
    mouse_jitter_enabled: bool = True
    mouse_jitter_px: int = 5  # Maximum pixels of jitter
    mouse_speed_variation: float = 0.3  # 30% speed variation
    
    # Scrolling
    scroll_simulation_enabled: bool = True
    scroll_delta_min: int = 50
    scroll_delta_max: int = 300
    scroll_pause_min_ms: int = 100
    scroll_pause_max_ms: int = 500
    
    # Typing
    typing_speed_min_ms: int = 50  # Min delay between keystrokes
    typing_speed_max_ms: int = 200  # Max delay between keystrokes
    typing_mistake_rate: float = 0.02  # 2% chance of typo
    
    # Random Actions
    enable_random_hover: bool = True
    enable_random_scroll: bool = True
    random_action_probability: float = 0.1  # 10% chance per action
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "min_action_delay_ms": self.min_action_delay_ms,
            "max_action_delay_ms": self.max_action_delay_ms,
            "idle_time_min_sec": self.idle_time_min_sec,
            "idle_time_max_sec": self.idle_time_max_sec,
            "mouse_jitter_enabled": self.mouse_jitter_enabled,
            "mouse_jitter_px": self.mouse_jitter_px,
            "mouse_speed_variation": self.mouse_speed_variation,
            "scroll_simulation_enabled": self.scroll_simulation_enabled,
            "scroll_delta_min": self.scroll_delta_min,
            "scroll_delta_max": self.scroll_delta_max,
            "scroll_pause_min_ms": self.scroll_pause_min_ms,
            "scroll_pause_max_ms": self.scroll_pause_max_ms,
            "typing_speed_min_ms": self.typing_speed_min_ms,
            "typing_speed_max_ms": self.typing_speed_max_ms,
            "typing_mistake_rate": self.typing_mistake_rate,
            "enable_random_hover": self.enable_random_hover,
            "enable_random_scroll": self.enable_random_scroll,
            "random_action_probability": self.random_action_probability
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BehaviorSimulationConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CaptchaConfig:
    """Configuration for CAPTCHA handling."""
    enabled: bool = False
    api_key: str = ""  # Stored securely via keyring
    provider: str = "2captcha"  # 2captcha, anticaptcha, capsolver
    auto_solve: bool = True
    captcha_types: List[str] = field(default_factory=lambda: ["recaptcha_v2", "recaptcha_v3", "hcaptcha"])
    timeout_sec: int = 120
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding sensitive data)."""
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "auto_solve": self.auto_solve,
            "captcha_types": self.captcha_types,
            "timeout_sec": self.timeout_sec,
            "max_retries": self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CaptchaConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class CaptchaSolver:
    """CAPTCHA solving integration with 2Captcha and similar services."""
    
    def __init__(self, config: CaptchaConfig):
        """Initialize the CAPTCHA solver.
        
        Args:
            config: CAPTCHA configuration.
        """
        self.config = config
        self._solver = None
    
    def _init_solver(self) -> bool:
        """Initialize the solver client."""
        if not self.config.enabled or not self.config.api_key:
            return False
        
        if self.config.provider == "2captcha":
            try:
                from twocaptcha import TwoCaptcha
            except ImportError:
                logger.warning("2captcha-python not installed. Install with: pip install 2captcha-python")
                return False
            
            try:
                self._solver = TwoCaptcha(self.config.api_key)
                return True
            except Exception as e:
                logger.error(f"Failed to initialize 2captcha solver: {e}")
                return False
        else:
            logger.warning(f"Unsupported CAPTCHA provider: {self.config.provider}")
            return False
    
    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> Optional[str]:
        """Solve reCAPTCHA v2.
        
        Args:
            site_key: The reCAPTCHA site key.
            page_url: URL of the page containing the CAPTCHA.
            
        Returns:
            Solution token or None if failed.
        """
        if not self._solver and not self._init_solver():
            return None
        
        try:
            result = await asyncio.to_thread(
                self._solver.recaptcha,
                sitekey=site_key,
                url=page_url
            )
            return result.get('code')
        except Exception as e:
            logger.error(f"Failed to solve reCAPTCHA v2: {e}")
            return None
    
    async def solve_recaptcha_v3(
        self, 
        site_key: str, 
        page_url: str, 
        action: str = "verify",
        min_score: float = 0.7
    ) -> Optional[str]:
        """Solve reCAPTCHA v3.
        
        Args:
            site_key: The reCAPTCHA site key.
            page_url: URL of the page.
            action: reCAPTCHA action name.
            min_score: Minimum required score.
            
        Returns:
            Solution token or None if failed.
        """
        if not self._solver and not self._init_solver():
            return None
        
        try:
            result = await asyncio.to_thread(
                self._solver.recaptcha,
                sitekey=site_key,
                url=page_url,
                version='v3',
                action=action,
                score=min_score
            )
            return result.get('code')
        except Exception as e:
            logger.error(f"Failed to solve reCAPTCHA v3: {e}")
            return None
    
    async def solve_hcaptcha(self, site_key: str, page_url: str) -> Optional[str]:
        """Solve hCaptcha.
        
        Args:
            site_key: The hCaptcha site key.
            page_url: URL of the page.
            
        Returns:
            Solution token or None if failed.
        """
        if not self._solver and not self._init_solver():
            return None
        
        try:
            result = await asyncio.to_thread(
                self._solver.hcaptcha,
                sitekey=site_key,
                url=page_url
            )
            return result.get('code')
        except Exception as e:
            logger.error(f"Failed to solve hCaptcha: {e}")
            return None


class ProxyValidator:
    """Validates proxy connections before use."""
    
    def __init__(self, timeout_sec: int = 10):
        """Initialize the proxy validator.
        
        Args:
            timeout_sec: Timeout for proxy tests.
        """
        self.timeout_sec = timeout_sec
        self.test_urls = [
            "https://httpbin.org/ip",
            "https://api.ipify.org?format=json"
        ]
    
    async def validate_proxy(
        self, 
        proxy_url: str, 
        username: str = "", 
        password: str = ""
    ) -> Dict[str, Any]:
        """Validate a single proxy.
        
        Args:
            proxy_url: Proxy URL in format protocol://host:port
            username: Optional proxy username.
            password: Optional proxy password.
            
        Returns:
            Validation result with status, IP, and latency.
        """
        import aiohttp
        
        result = {
            "valid": False,
            "ip": None,
            "latency_ms": None,
            "error": None
        }
        
        # Build proxy auth if credentials provided
        proxy_auth = None
        if username and password:
            proxy_auth = aiohttp.BasicAuth(username, password)
        
        try:
            start_time = time.perf_counter()
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout_sec)
            ) as session:
                for test_url in self.test_urls:
                    try:
                        async with session.get(
                            test_url,
                            proxy=proxy_url,
                            proxy_auth=proxy_auth
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                result["valid"] = True
                                result["ip"] = data.get("origin") or data.get("ip")
                                result["latency_ms"] = (time.perf_counter() - start_time) * 1000
                                return result
                    except Exception:
                        continue
                        
        except asyncio.TimeoutError:
            result["error"] = "Timeout"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def validate_pool(
        self, 
        proxies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate multiple proxies concurrently.
        
        Args:
            proxies: List of proxy configurations.
            
        Returns:
            List of validation results.
        """
        tasks = []
        for proxy in proxies:
            proxy_url = f"{proxy.get('type', 'http')}://{proxy['server']}:{proxy['port']}"
            task = self.validate_proxy(
                proxy_url,
                proxy.get('username', ''),
                proxy.get('password', '')
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)


class RetryManager:
    """Manages retry logic for failed operations."""
    
    def __init__(
        self, 
        max_retries: int = 3, 
        base_delay_sec: float = 1.0,
        exponential_backoff: bool = True,
        max_delay_sec: float = 30.0
    ):
        """Initialize the retry manager.
        
        Args:
            max_retries: Maximum number of retry attempts.
            base_delay_sec: Base delay between retries.
            exponential_backoff: Whether to use exponential backoff.
            max_delay_sec: Maximum delay between retries.
        """
        self.max_retries = max_retries
        self.base_delay_sec = base_delay_sec
        self.exponential_backoff = exponential_backoff
        self.max_delay_sec = max_delay_sec
    
    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        on_retry: Optional[Callable] = None,
        retryable_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """Execute an operation with retry logic.
        
        Args:
            operation: The async operation to execute.
            *args: Arguments for the operation.
            on_retry: Optional callback on retry.
            retryable_exceptions: Tuple of exceptions to retry on.
            **kwargs: Keyword arguments for the operation.
            
        Returns:
            Result of the operation.
            
        Raises:
            The last exception if all retries fail.
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(operation):
                    return await operation(*args, **kwargs)
                else:
                    return await asyncio.to_thread(operation, *args, **kwargs)
                    
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calculate delay
                    if self.exponential_backoff:
                        delay = min(
                            self.base_delay_sec * (2 ** attempt),
                            self.max_delay_sec
                        )
                    else:
                        delay = self.base_delay_sec
                    
                    # Add jitter
                    delay *= (0.5 + random.random())
                    
                    logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    if on_retry:
                        on_retry(attempt, e)
                    
                    await asyncio.sleep(delay)
        
        raise last_exception


class SecureCredentialStore:
    """Secure storage for sensitive credentials using keyring."""
    
    SERVICE_NAME = "botsos"
    
    def __init__(self):
        """Initialize the credential store."""
        self._keyring_available = self._check_keyring()
    
    def _check_keyring(self) -> bool:
        """Check if keyring is available."""
        try:
            import keyring
            # Test if keyring is properly configured
            keyring.get_keyring()
            return True
        except (ImportError, Exception):
            return False
    
    def store_credential(self, key: str, value: str) -> bool:
        """Store a credential securely.
        
        Args:
            key: Credential key/name.
            value: Credential value.
            
        Returns:
            True if stored successfully, False otherwise.
        """
        if not value:
            return True
            
        if self._keyring_available:
            try:
                import keyring
                keyring.set_password(self.SERVICE_NAME, key, value)
                return True
            except Exception as e:
                logger.error(f"Failed to store credential in keyring: {e}")
        
        # Fallback: store in environment variable (less secure)
        os.environ[f"BOTSOS_{key.upper()}"] = value
        logger.warning(f"Stored credential in environment variable (keyring not available)")
        return True
    
    def get_credential(self, key: str) -> Optional[str]:
        """Retrieve a credential.
        
        Args:
            key: Credential key/name.
            
        Returns:
            Credential value or None if not found.
        """
        if self._keyring_available:
            try:
                import keyring
                value = keyring.get_password(self.SERVICE_NAME, key)
                if value:
                    return value
            except Exception as e:
                logger.error(f"Failed to retrieve credential from keyring: {e}")
        
        # Fallback: check environment variable
        return os.environ.get(f"BOTSOS_{key.upper()}")
    
    def delete_credential(self, key: str) -> bool:
        """Delete a credential.
        
        Args:
            key: Credential key/name.
            
        Returns:
            True if deleted successfully, False otherwise.
        """
        if self._keyring_available:
            try:
                import keyring
                keyring.delete_password(self.SERVICE_NAME, key)
                return True
            except Exception as e:
                logger.error(f"Failed to delete credential from keyring: {e}")
        
        # Fallback: remove from environment
        env_key = f"BOTSOS_{key.upper()}"
        if env_key in os.environ:
            del os.environ[env_key]
        return True


class BehaviorSimulator:
    """Simulates human-like browser behavior."""
    
    def __init__(self, config: BehaviorSimulationConfig):
        """Initialize the behavior simulator.
        
        Args:
            config: Behavior simulation configuration.
        """
        self.config = config
    
    async def random_delay(self) -> None:
        """Wait for a random action delay."""
        delay_ms = random.randint(
            self.config.min_action_delay_ms,
            self.config.max_action_delay_ms
        )
        await asyncio.sleep(delay_ms / 1000)
    
    async def idle_pause(self) -> None:
        """Simulate an idle pause like a real user."""
        idle_time = random.uniform(
            self.config.idle_time_min_sec,
            self.config.idle_time_max_sec
        )
        await asyncio.sleep(idle_time)
    
    def calculate_mouse_path(
        self, 
        start_x: float, 
        start_y: float, 
        end_x: float, 
        end_y: float,
        steps: int = 10
    ) -> List[tuple]:
        """Calculate a human-like mouse path with jitter.
        
        Args:
            start_x: Starting X coordinate.
            start_y: Starting Y coordinate.
            end_x: Ending X coordinate.
            end_y: Ending Y coordinate.
            steps: Number of movement steps.
            
        Returns:
            List of (x, y) coordinates.
        """
        path = []
        
        for i in range(steps + 1):
            progress = i / steps
            # Add some curve to the path (bezier-like)
            curve = random.uniform(-0.1, 0.1)
            
            x = start_x + (end_x - start_x) * progress
            y = start_y + (end_y - start_y) * progress
            
            # Add perpendicular offset for curve
            perpendicular_x = -(end_y - start_y) * curve
            perpendicular_y = (end_x - start_x) * curve
            
            x += perpendicular_x
            y += perpendicular_y
            
            # Add jitter
            if self.config.mouse_jitter_enabled and i < steps:
                x += random.randint(-self.config.mouse_jitter_px, self.config.mouse_jitter_px)
                y += random.randint(-self.config.mouse_jitter_px, self.config.mouse_jitter_px)
            
            path.append((x, y))
        
        return path
    
    async def type_with_variations(self, text: str) -> List[Dict[str, Any]]:
        """Generate typing actions with human-like variations.
        
        Args:
            text: Text to type.
            
        Returns:
            List of typing actions with delays and potential corrections.
        """
        actions = []
        
        for i, char in enumerate(text):
            # Random delay between keystrokes
            delay = random.randint(
                self.config.typing_speed_min_ms,
                self.config.typing_speed_max_ms
            )
            
            # Simulate potential typo
            if random.random() < self.config.typing_mistake_rate:
                # Add typo
                typo_char = self._get_nearby_key(char)
                actions.append({
                    "type": "key",
                    "char": typo_char,
                    "delay_ms": delay
                })
                # Add correction
                actions.append({
                    "type": "key",
                    "char": "Backspace",
                    "delay_ms": random.randint(100, 300)
                })
            
            actions.append({
                "type": "key",
                "char": char,
                "delay_ms": delay
            })
        
        return actions
    
    def _get_nearby_key(self, char: str) -> str:
        """Get a nearby key on keyboard for typo simulation."""
        keyboard_rows = [
            "qwertyuiop",
            "asdfghjkl",
            "zxcvbnm"
        ]
        
        char_lower = char.lower()
        for row in keyboard_rows:
            if char_lower in row:
                idx = row.index(char_lower)
                # Pick adjacent key
                offset = random.choice([-1, 1])
                new_idx = max(0, min(len(row) - 1, idx + offset))
                result = row[new_idx]
                return result.upper() if char.isupper() else result
        
        return char
    
    def should_perform_random_action(self) -> bool:
        """Determine if a random action should be performed."""
        return random.random() < self.config.random_action_probability
    
    def get_random_scroll_delta(self) -> int:
        """Get a random scroll amount."""
        return random.randint(
            self.config.scroll_delta_min,
            self.config.scroll_delta_max
        )


class AdvancedLogging:
    """Advanced logging with rotation and session-specific logs."""
    
    def __init__(
        self, 
        log_dir: Path,
        max_size_mb: int = 10,
        backup_count: int = 5
    ):
        """Initialize advanced logging.
        
        Args:
            log_dir: Directory for log files.
            max_size_mb: Maximum log file size in MB.
            backup_count: Number of backup files to keep.
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.backup_count = backup_count
        self.session_loggers: Dict[str, logging.Logger] = {}
    
    def get_session_logger(self, session_id: str) -> logging.Logger:
        """Get or create a logger for a specific session.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            Logger for the session.
        """
        if session_id in self.session_loggers:
            return self.session_loggers[session_id]
        
        from logging.handlers import RotatingFileHandler
        
        logger = logging.getLogger(f"botsos.session.{session_id}")
        logger.setLevel(logging.DEBUG)
        
        # File handler with rotation
        log_file = self.log_dir / f"session_{session_id}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_size_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        self.session_loggers[session_id] = logger
        
        return logger
    
    def cleanup_old_logs(self, max_age_days: int = 30) -> int:
        """Clean up old log files.
        
        Args:
            max_age_days: Maximum age of logs to keep.
            
        Returns:
            Number of files deleted.
        """
        import time
        
        deleted = 0
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                deleted += 1
        
        return deleted


@dataclass
class ContingencyState:
    """Tracks contingency-related state for a session (from fase3.txt)."""
    consecutive_failures: int = 0
    total_blocks: int = 0
    total_requests: int = 0
    cool_down_until: Optional[datetime] = None
    last_proxy_rotation: Optional[datetime] = None
    session_start_time: Optional[datetime] = None
    
    @property
    def block_rate(self) -> float:
        """Calculate current block rate."""
        if self.total_requests == 0:
            return 0.0
        return self.total_blocks / self.total_requests
    
    def record_success(self):
        """Record a successful request."""
        self.consecutive_failures = 0
        self.total_requests += 1
    
    def record_failure(self, is_block: bool = False):
        """Record a failed request."""
        self.consecutive_failures += 1
        self.total_requests += 1
        if is_block:
            self.total_blocks += 1
    
    def should_evict_proxy(self, block_threshold: float, failure_threshold: int) -> bool:
        """Check if current proxy should be evicted."""
        return (
            self.block_rate > block_threshold or 
            self.consecutive_failures >= failure_threshold
        )
    
    def is_in_cool_down(self) -> bool:
        """Check if session is in cool-down period."""
        if self.cool_down_until is None:
            return False
        return datetime.now() < self.cool_down_until
    
    def start_cool_down(self, duration_sec: int):
        """Start a cool-down period."""
        from datetime import timedelta
        self.cool_down_until = datetime.now() + timedelta(seconds=duration_sec)


class ContingencyManager:
    """Manages contingency planning and recovery for sessions (from fase3.txt)."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the contingency manager.
        
        Args:
            config: Contingency configuration dictionary.
        """
        self.config = config or {}
        self.session_states: Dict[str, ContingencyState] = {}
    
    def get_session_state(self, session_id: str) -> ContingencyState:
        """Get or create state for a session."""
        if session_id not in self.session_states:
            self.session_states[session_id] = ContingencyState()
            self.session_states[session_id].session_start_time = datetime.now()
        return self.session_states[session_id]
    
    def record_success(self, session_id: str):
        """Record a successful action for a session."""
        state = self.get_session_state(session_id)
        state.record_success()
    
    def record_failure(self, session_id: str, is_block: bool = False):
        """Record a failed action for a session."""
        state = self.get_session_state(session_id)
        state.record_failure(is_block)
    
    def should_rotate_proxy(self, session_id: str) -> bool:
        """Check if proxy should be rotated for a session."""
        state = self.get_session_state(session_id)
        block_threshold = self.config.get('block_rate_threshold', 0.10)
        failure_threshold = self.config.get('consecutive_failure_threshold', 3)
        return state.should_evict_proxy(block_threshold, failure_threshold)
    
    def should_enter_cool_down(self, session_id: str) -> bool:
        """Check if session should enter cool-down."""
        state = self.get_session_state(session_id)
        # Enter cool-down after significant failures
        return state.consecutive_failures >= self.config.get('consecutive_failure_threshold', 3) * 2
    
    def get_cool_down_duration(self) -> int:
        """Get appropriate cool-down duration in seconds."""
        min_sec = self.config.get('cool_down_min_sec', 300)
        max_sec = self.config.get('cool_down_max_sec', 1200)
        return random.randint(min_sec, max_sec)
    
    def get_recovery_strategy(self) -> str:
        """Get the ban recovery strategy."""
        return self.config.get('ban_recovery_strategy', 'mobile_fallback')
    
    def reset_session_state(self, session_id: str):
        """Reset state for a session."""
        if session_id in self.session_states:
            del self.session_states[session_id]


class SystemHidingManager:
    """Manages system hiding features for anti-detection (from fase3.txt)."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the system hiding manager.
        
        Args:
            config: System hiding configuration dictionary.
        """
        self.config = config or {}
        self._blocked_ports: List[int] = []
    
    def get_random_ephemeral_port(self) -> int:
        """Get a random ephemeral port."""
        min_port = self.config.get('ephemeral_port_min', 49152)
        max_port = self.config.get('ephemeral_port_max', 65535)
        return random.randint(min_port, max_port)
    
    def block_cdp_port(self, port: int = 9222) -> bool:
        """Block CDP debugging port.
        
        Note: Actual firewall manipulation requires elevated privileges.
        This method returns the command that would be used.
        
        Args:
            port: CDP port to block.
            
        Returns:
            True if command was prepared successfully.
        """
        if not self.config.get('block_cdp_ports', True):
            return False
        
        import platform
        
        try:
            if platform.system() == 'Windows':
                # Windows netsh command
                cmd = f'netsh advfirewall firewall add rule name="Block CDP {port}" dir=in action=block protocol=tcp localport={port}'
                logger.info(f"CDP blocking command (Windows): {cmd}")
            else:
                # Linux iptables command
                cmd = f'iptables -A INPUT -p tcp --dport {port} -j DROP'
                logger.info(f"CDP blocking command (Linux): {cmd}")
            
            self._blocked_ports.append(port)
            return True
            
        except Exception as e:
            logger.error(f"Failed to prepare CDP port blocking: {e}")
            return False
    
    def get_webrtc_blocking_script(self) -> str:
        """Get JavaScript to completely block WebRTC.
        
        Returns:
            JavaScript code to inject.
        """
        if not self.config.get('block_webrtc_completely', False):
            return ""
        
        return """
            // Completely disable WebRTC
            if (typeof RTCPeerConnection !== 'undefined') {
                RTCPeerConnection = undefined;
            }
            if (typeof webkitRTCPeerConnection !== 'undefined') {
                webkitRTCPeerConnection = undefined;
            }
            if (typeof RTCDataChannel !== 'undefined') {
                RTCDataChannel = undefined;
            }
            if (typeof RTCSessionDescription !== 'undefined') {
                RTCSessionDescription = undefined;
            }
            if (navigator.mediaDevices) {
                navigator.mediaDevices.getUserMedia = () => Promise.reject(new Error('Not allowed'));
            }
        """
    
    def get_port_hiding_scripts(self) -> List[str]:
        """Get scripts to hide port information.
        
        Returns:
            List of JavaScript scripts.
        """
        scripts = []
        
        # Hide localhost connections
        scripts.append("""
            // Prevent detection of local connections
            const originalFetch = window.fetch;
            window.fetch = function(url, ...args) {
                if (typeof url === 'string' && (url.includes('localhost') || url.includes('127.0.0.1'))) {
                    return Promise.reject(new Error('Network error'));
                }
                return originalFetch.apply(this, [url, ...args]);
            };
        """)
        
        return scripts


class AnomalyDetector:
    """Detects anomalies in session behavior for contingency triggering (from fase3.txt)."""
    
    def __init__(self, baseline_period_sec: int = 300):
        """Initialize the anomaly detector.
        
        Args:
            baseline_period_sec: Period for establishing baseline metrics.
        """
        self.baseline_period_sec = baseline_period_sec
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.baselines: Dict[str, Dict[str, float]] = {}
        self.anomaly_threshold = 0.10  # 10% deviation triggers anomaly
    
    def record_metric(self, session_id: str, metric_name: str, value: float):
        """Record a metric value for a session.
        
        Args:
            session_id: Session identifier.
            metric_name: Name of the metric (e.g., 'bounce_rate', 'api_calls').
            value: Metric value.
        """
        key = f"{session_id}:{metric_name}"
        if key not in self.metrics:
            self.metrics[key] = []
        
        self.metrics[key].append({
            'timestamp': datetime.now(),
            'value': value
        })
        
        # Keep only recent metrics
        cutoff = datetime.now() - timedelta(seconds=self.baseline_period_sec * 2)
        self.metrics[key] = [m for m in self.metrics[key] if m['timestamp'] > cutoff]
    
    def calculate_baseline(self, session_id: str, metric_name: str) -> Optional[float]:
        """Calculate baseline for a metric.
        
        Args:
            session_id: Session identifier.
            metric_name: Name of the metric.
            
        Returns:
            Baseline value or None if insufficient data.
        """
        key = f"{session_id}:{metric_name}"
        if key not in self.metrics or len(self.metrics[key]) < 5:
            return None
        
        values = [m['value'] for m in self.metrics[key]]
        baseline = sum(values) / len(values)
        self.baselines[key] = {'mean': baseline, 'count': len(values)}
        return baseline
    
    def check_anomaly(self, session_id: str, metric_name: str, current_value: float) -> bool:
        """Check if current value is an anomaly.
        
        Args:
            session_id: Session identifier.
            metric_name: Name of the metric.
            current_value: Current metric value.
            
        Returns:
            True if anomaly detected, False otherwise.
        """
        key = f"{session_id}:{metric_name}"
        
        if key not in self.baselines:
            baseline = self.calculate_baseline(session_id, metric_name)
            if baseline is None:
                return False
        else:
            baseline = self.baselines[key]['mean']
        
        if baseline == 0:
            return current_value > 0
        
        deviation = abs(current_value - baseline) / baseline
        return deviation > self.anomaly_threshold
    
    def get_anomaly_report(self, session_id: str) -> Dict[str, Any]:
        """Get a report of anomalies for a session.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            Dictionary with anomaly information.
        """
        report = {
            'session_id': session_id,
            'anomalies': [],
            'baselines': {}
        }
        
        for key, baseline_data in self.baselines.items():
            if key.startswith(f"{session_id}:"):
                metric_name = key.split(':', 1)[1]
                report['baselines'][metric_name] = baseline_data['mean']
                
                if key in self.metrics and self.metrics[key]:
                    current = self.metrics[key][-1]['value']
                    if self.check_anomaly(session_id, metric_name, current):
                        report['anomalies'].append({
                            'metric': metric_name,
                            'current': current,
                            'baseline': baseline_data['mean']
                        })
        
        return report


class PolymorphicFingerprint:
    """Generates polymorphic fingerprints that change over time (from fase3.txt)."""
    
    def __init__(self, base_fingerprint: Optional[Dict[str, Any]] = None):
        """Initialize with a base fingerprint.
        
        Args:
            base_fingerprint: Base fingerprint configuration.
        """
        self.base = base_fingerprint or {}
        self.current = self.base.copy()
        self.rotation_count = 0
    
    def apply_variation(self, variation_level: float = 0.1) -> Dict[str, Any]:
        """Apply random variations to fingerprint.
        
        Args:
            variation_level: Amount of variation (0.0 to 1.0).
            
        Returns:
            Modified fingerprint.
        """
        fingerprint = self.current.copy()
        
        # Vary numeric values
        numeric_fields = [
            'viewport_width', 'viewport_height', 
            'hardware_concurrency', 'device_memory'
        ]
        
        for field in numeric_fields:
            if field in fingerprint:
                value = fingerprint[field]
                variation = int(value * variation_level)
                fingerprint[field] = value + random.randint(-variation, variation)
        
        # Vary canvas noise level
        if 'canvas_noise_level' in fingerprint:
            level = fingerprint['canvas_noise_level']
            fingerprint['canvas_noise_level'] = max(0, min(10, level + random.randint(-1, 1)))
        
        # Vary audio noise level
        if 'audio_noise_level' in fingerprint:
            level = fingerprint['audio_noise_level']
            fingerprint['audio_noise_level'] = max(0, min(10, level + random.randint(-1, 1)))
        
        self.current = fingerprint
        self.rotation_count += 1
        
        return fingerprint
    
    def get_polymorphic_scripts(self) -> List[str]:
        """Get JavaScript scripts for polymorphic fingerprinting.
        
        Returns:
            List of JavaScript injection scripts.
        """
        scripts = []
        
        # Polymorphic navigator properties
        scripts.append(f"""
            // Polymorphic variations
            const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
            
            // Add slight variation to performance.now()
            const perfOffset = {random.uniform(-0.1, 0.1)};
            const originalNow = performance.now;
            performance.now = function() {{
                return originalNow.call(performance) + perfOffset;
            }};
            
            // Add variation to Date.now()
            const dateOffset = {random.randint(-100, 100)};
            const originalDateNow = Date.now;
            Date.now = function() {{
                return originalDateNow() + dateOffset;
            }};
        """)
        
        return scripts
    
    def reset_to_base(self):
        """Reset to base fingerprint."""
        self.current = self.base.copy()


# Import timedelta for AnomalyDetector
from datetime import timedelta
