"""
Módulo Administrador de Huellas Digitales

Maneja la generación, aleatorización y aplicación de huellas digitales de dispositivo.
Diseñado para Windows.
"""

import json
import random
import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass
class DeviceFingerprint:
    """Represents a complete device fingerprint configuration."""
    user_agent: str
    viewport_width: int
    viewport_height: int
    hardware_concurrency: int
    device_memory: int
    platform: str
    timezone: str
    languages: List[str]
    webgl_vendor: str
    webgl_renderer: str
    is_mobile: bool = False
    has_touch: bool = False
    
    # Spoofing settings
    canvas_noise_level: int = 5
    audio_noise_level: int = 3
    webrtc_protection: bool = True
    webgl_spoofing: bool = True
    font_list: List[str] = None
    
    def __post_init__(self):
        if self.font_list is None:
            self.font_list = [
                "Arial", "Helvetica", "Times New Roman",
                "Georgia", "Verdana", "Courier New"
            ]
    
    def to_playwright_context(self) -> Dict[str, Any]:
        """Convert to Playwright browser context options."""
        return {
            "viewport": {
                "width": self.viewport_width,
                "height": self.viewport_height
            },
            "user_agent": self.user_agent,
            "locale": self.languages[0] if self.languages else "en-US",
            "timezone_id": self.timezone,
            "is_mobile": self.is_mobile,
            "has_touch": self.has_touch,
            "device_scale_factor": 1.0
        }
    
    def get_spoofing_scripts(self) -> List[str]:
        """Get JavaScript injection scripts for fingerprint spoofing."""
        scripts = []
        
        # Navigator overrides
        scripts.append(f"""
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {self.hardware_concurrency}
            }});
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {self.device_memory}
            }});
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{self.platform}'
            }});
            Object.defineProperty(navigator, 'languages', {{
                get: () => {json.dumps(self.languages)}
            }});
        """)
        
        # WebGL spoofing
        if self.webgl_spoofing:
            scripts.append(f"""
                const getParameterOriginal = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) return '{self.webgl_vendor}';
                    if (parameter === 37446) return '{self.webgl_renderer}';
                    return getParameterOriginal.call(this, parameter);
                }};
            """)
        
        # Canvas noise injection
        if self.canvas_noise_level > 0:
            scripts.append(f"""
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type) {{
                    const context = this.getContext('2d');
                    if (context) {{
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        const noise = {self.canvas_noise_level};
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            imageData.data[i] = Math.max(0, Math.min(255, 
                                imageData.data[i] + Math.floor(Math.random() * noise * 2 - noise)));
                        }}
                        context.putImageData(imageData, 0, 0);
                    }}
                    return originalToDataURL.apply(this, arguments);
                }};
            """)
        
        # WebRTC protection
        if self.webrtc_protection:
            scripts.append("""
                if (typeof RTCPeerConnection !== 'undefined') {
                    const originalRTCPeerConnection = RTCPeerConnection;
                    RTCPeerConnection = function(config) {
                        if (config && config.iceServers) {
                            config.iceServers = [];
                        }
                        return new originalRTCPeerConnection(config);
                    };
                    RTCPeerConnection.prototype = originalRTCPeerConnection.prototype;
                }
            """)
        
        # Audio context noise
        if self.audio_noise_level > 0:
            scripts.append(f"""
                const originalGetChannelData = AudioBuffer.prototype.getChannelData;
                AudioBuffer.prototype.getChannelData = function(channel) {{
                    const data = originalGetChannelData.call(this, channel);
                    const noise = {self.audio_noise_level / 1000};
                    for (let i = 0; i < data.length; i++) {{
                        data[i] += (Math.random() * 2 - 1) * noise;
                    }}
                    return data;
                }};
            """)
        
        return scripts


class FingerprintManager:
    """Manages device fingerprint presets and generation."""
    
    def __init__(self, config_dir: Path):
        """Initialize the fingerprint manager.
        
        Args:
            config_dir: Directory containing device configuration files.
        """
        self.config_dir = Path(config_dir)
        self.devices_file = self.config_dir / "devices.json"
        self.presets: Dict[str, Dict[str, Any]] = {}
        self.spoofing_options: Dict[str, Any] = {}
        self._load_presets()
    
    def _load_presets(self) -> None:
        """Load device presets from configuration file."""
        if self.devices_file.exists():
            try:
                with open(self.devices_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.presets = data.get('presets', {})
                self.spoofing_options = data.get('spoofing_options', {})
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error loading device presets: {e}")
    
    def get_preset_names(self) -> List[str]:
        """Get list of available preset names.
        
        Returns:
            List of preset names.
        """
        return list(self.presets.keys())
    
    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific preset by name.
        
        Args:
            name: Name of the preset.
            
        Returns:
            Preset data or None if not found.
        """
        return self.presets.get(name)
    
    def generate_fingerprint(
        self, 
        preset_name: str = "windows_desktop",
        randomize: bool = True
    ) -> DeviceFingerprint:
        """Generate a device fingerprint from a preset.
        
        Args:
            preset_name: Name of the preset to use.
            randomize: Whether to randomize values within ranges.
            
        Returns:
            A complete device fingerprint configuration.
        """
        preset = self.presets.get(preset_name, self.presets.get("windows_desktop", {}))
        
        # Select values (random from options if randomize=True)
        def pick(options, default):
            if isinstance(options, list) and options:
                return random.choice(options) if randomize else options[0]
            return options if options else default
        
        viewport = preset.get("viewport", {})
        spoofing = self.spoofing_options
        
        fingerprint = DeviceFingerprint(
            user_agent=pick(preset.get("user_agents", []), "Mozilla/5.0"),
            viewport_width=pick(viewport.get("width", [1920]), 1920),
            viewport_height=pick(viewport.get("height", [1080]), 1080),
            hardware_concurrency=pick(preset.get("hardware_concurrency", [8]), 8),
            device_memory=pick(preset.get("device_memory", [8]), 8),
            platform=preset.get("platform", "Win32"),
            timezone=preset.get("timezone", "America/New_York"),
            languages=preset.get("languages", ["en-US", "en"]),
            webgl_vendor=preset.get("webgl_vendor", "Google Inc."),
            webgl_renderer=preset.get("webgl_renderer", "ANGLE"),
            is_mobile=preset.get("is_mobile", False),
            has_touch=preset.get("has_touch", False),
            canvas_noise_level=spoofing.get("canvas_noise", {}).get("noise_level", 5),
            audio_noise_level=spoofing.get("audio_context_spoofing", {}).get("noise_level", 3),
            webrtc_protection=spoofing.get("webrtc_protection", {}).get("enabled", True),
            webgl_spoofing=spoofing.get("webgl_spoofing", {}).get("enabled", True),
            font_list=spoofing.get("font_spoofing", {}).get("fonts", [])
        )
        
        return fingerprint
    
    def apply_variations(
        self, 
        fingerprint: DeviceFingerprint,
        variation_percent: int = 10
    ) -> DeviceFingerprint:
        """Apply small random variations to a fingerprint.
        
        Args:
            fingerprint: The base fingerprint.
            variation_percent: Maximum percentage of variation.
            
        Returns:
            Modified fingerprint with variations.
        """
        def vary(value: int, percent: int) -> int:
            delta = int(value * percent / 100)
            return value + random.randint(-delta, delta)
        
        # Apply variations to numeric values
        fingerprint.viewport_width = vary(fingerprint.viewport_width, variation_percent)
        fingerprint.viewport_height = vary(fingerprint.viewport_height, variation_percent)
        
        return fingerprint
    
    def create_custom_fingerprint(
        self,
        user_agent: str,
        viewport_width: int,
        viewport_height: int,
        **kwargs
    ) -> DeviceFingerprint:
        """Create a custom fingerprint with specific values.
        
        Args:
            user_agent: The user agent string.
            viewport_width: Browser viewport width.
            viewport_height: Browser viewport height.
            **kwargs: Additional fingerprint parameters.
            
        Returns:
            Custom device fingerprint.
        """
        return DeviceFingerprint(
            user_agent=user_agent,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            hardware_concurrency=kwargs.get("hardware_concurrency", 8),
            device_memory=kwargs.get("device_memory", 8),
            platform=kwargs.get("platform", "Win32"),
            timezone=kwargs.get("timezone", "America/New_York"),
            languages=kwargs.get("languages", ["en-US", "en"]),
            webgl_vendor=kwargs.get("webgl_vendor", "Google Inc."),
            webgl_renderer=kwargs.get("webgl_renderer", "ANGLE"),
            is_mobile=kwargs.get("is_mobile", False),
            has_touch=kwargs.get("has_touch", False),
            canvas_noise_level=kwargs.get("canvas_noise_level", 5),
            audio_noise_level=kwargs.get("audio_noise_level", 3),
            webrtc_protection=kwargs.get("webrtc_protection", True),
            webgl_spoofing=kwargs.get("webgl_spoofing", True)
        )
