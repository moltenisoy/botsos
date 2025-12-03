"""
Módulo de Sistema de Plugins para Evasión

Implementa un sistema modular de plugins para agregar nuevas
técnicas de evasión mediante archivos YAML/JSON.

Implementa características de fase6.txt:
- Sistema modular de plugins cargados desde YAML/JSON
- Carga dinámica de módulos de evasión
- Bucle de retroalimentación RL básico
- Detección de cambios en UI

Diseñado exclusivamente para Windows.
"""

import asyncio
import importlib
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Type
from datetime import datetime

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

import json

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadatos de un plugin."""
    name: str
    version: str
    description: str
    author: str = ""
    category: str = "evasion"  # evasion, behavior, fingerprint, etc.
    enabled: bool = True
    priority: int = 5  # 1-10, menor = mayor prioridad
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)


class EvasionPlugin(ABC):
    """Clase base abstracta para plugins de evasión.
    
    Todos los plugins de evasión deben heredar de esta clase
    e implementar los métodos abstractos.
    """
    
    def __init__(self, metadata: PluginMetadata):
        """Inicializa el plugin.
        
        Args:
            metadata: Metadatos del plugin.
        """
        self.metadata = metadata
        self.is_active = False
        self.success_count = 0
        self.failure_count = 0
        self.last_used: Optional[datetime] = None
    
    @property
    def name(self) -> str:
        return self.metadata.name
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5
    
    @abstractmethod
    async def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica la técnica de evasión.
        
        Args:
            context: Contexto actual (página, sesión, etc.).
            
        Returns:
            Contexto modificado con la evasión aplicada.
        """
        pass
    
    @abstractmethod
    def get_scripts(self) -> List[str]:
        """Obtiene scripts JavaScript para inyección.
        
        Returns:
            Lista de scripts JavaScript.
        """
        pass
    
    def on_success(self):
        """Registra un uso exitoso."""
        self.success_count += 1
        self.last_used = datetime.now()
    
    def on_failure(self):
        """Registra un uso fallido."""
        self.failure_count += 1
        self.last_used = datetime.now()
    
    def reset_stats(self):
        """Reinicia estadísticas."""
        self.success_count = 0
        self.failure_count = 0


class JitterPlugin(EvasionPlugin):
    """Plugin de movimiento aleatorio adaptativo."""
    
    async def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica jitter adaptativo al movimiento."""
        import random
        
        jitter_px = self.metadata.config.get("jitter_px", 5)
        adaptive = self.metadata.config.get("adaptive", True)
        
        # Jitter adaptativo basado en tasa de éxito
        if adaptive and self.success_rate < 0.7:
            # Aumentar jitter si hay muchos fallos
            jitter_px = int(jitter_px * 1.5)
        
        context["jitter_px"] = jitter_px
        context["jitter_enabled"] = True
        
        return context
    
    def get_scripts(self) -> List[str]:
        jitter_px = self.metadata.config.get("jitter_px", 5)
        return [f"""
            // Plugin: {self.name} - Jitter adaptativo
            window.__botsosJitter = {{
                px: {jitter_px},
                apply: function(x, y) {{
                    return {{
                        x: x + (Math.random() * {jitter_px * 2} - {jitter_px}),
                        y: y + (Math.random() * {jitter_px * 2} - {jitter_px})
                    }};
                }}
            }};
        """]


class TimingPlugin(EvasionPlugin):
    """Plugin de variación de tiempos."""
    
    async def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica variación de tiempos."""
        import random
        
        base_delay = self.metadata.config.get("base_delay_ms", 100)
        variation = self.metadata.config.get("variation_percent", 30)
        
        # Calcular delay con variación
        min_delay = int(base_delay * (1 - variation / 100))
        max_delay = int(base_delay * (1 + variation / 100))
        
        context["action_delay_ms"] = random.randint(min_delay, max_delay)
        
        return context
    
    def get_scripts(self) -> List[str]:
        base_delay = self.metadata.config.get("base_delay_ms", 100)
        variation = self.metadata.config.get("variation_percent", 30)
        
        return [f"""
            // Plugin: {self.name} - Variación de tiempos
            window.__botsosTimings = {{
                baseDelay: {base_delay},
                variation: {variation},
                getDelay: function() {{
                    const v = this.variation / 100;
                    const min = this.baseDelay * (1 - v);
                    const max = this.baseDelay * (1 + v);
                    return Math.floor(Math.random() * (max - min) + min);
                }}
            }};
        """]


class CanvasNoisePlugin(EvasionPlugin):
    """Plugin de ruido en Canvas avanzado."""
    
    async def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica ruido adaptativo a Canvas."""
        noise_level = self.metadata.config.get("noise_level", 5)
        
        # Ajustar ruido basado en éxitos
        if self.success_rate < 0.6:
            noise_level = min(10, noise_level + 2)
        
        context["canvas_noise_level"] = noise_level
        return context
    
    def get_scripts(self) -> List[str]:
        noise = self.metadata.config.get("noise_level", 5)
        return [f"""
            // Plugin: {self.name} - Ruido de Canvas avanzado
            (function() {{
                const noise = {noise};
                const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
                    const imageData = origGetImageData.apply(this, args);
                    for (let i = 0; i < imageData.data.length; i += 4) {{
                        // Solo modificar pixels RGB, no alpha
                        for (let j = 0; j < 3; j++) {{
                            imageData.data[i + j] = Math.max(0, Math.min(255,
                                imageData.data[i + j] + Math.floor(Math.random() * noise * 2 - noise)
                            ));
                        }}
                    }}
                    return imageData;
                }};
            }})();
        """]


class WebGLFingerprintPlugin(EvasionPlugin):
    """Plugin de suplantación de WebGL."""
    
    async def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica suplantación de WebGL."""
        context["webgl_vendor"] = self.metadata.config.get("vendor", "Google Inc.")
        context["webgl_renderer"] = self.metadata.config.get("renderer", "ANGLE")
        return context
    
    def get_scripts(self) -> List[str]:
        vendor = self.metadata.config.get("vendor", "Google Inc.")
        renderer = self.metadata.config.get("renderer", "ANGLE (Intel, Intel HD Graphics)")
        
        return [f"""
            // Plugin: {self.name} - Suplantación WebGL
            (function() {{
                const getParameterOrig = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(param) {{
                    if (param === 37445) return '{vendor}';  // UNMASKED_VENDOR_WEBGL
                    if (param === 37446) return '{renderer}';  // UNMASKED_RENDERER_WEBGL
                    return getParameterOrig.call(this, param);
                }};
                
                // También para WebGL2
                if (typeof WebGL2RenderingContext !== 'undefined') {{
                    const getParam2Orig = WebGL2RenderingContext.prototype.getParameter;
                    WebGL2RenderingContext.prototype.getParameter = function(param) {{
                        if (param === 37445) return '{vendor}';
                        if (param === 37446) return '{renderer}';
                        return getParam2Orig.call(this, param);
                    }};
                }}
            }})();
        """]


class UIChangeDetectorPlugin(EvasionPlugin):
    """Plugin de detección de cambios en UI."""
    
    async def apply(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta cambios en la UI de YouTube."""
        selectors = self.metadata.config.get("selectors", {})
        
        # Almacenar selectores para verificación
        context["ui_selectors"] = selectors
        context["ui_change_detection"] = True
        
        return context
    
    def get_scripts(self) -> List[str]:
        selectors = self.metadata.config.get("selectors", {})
        selectors_json = json.dumps(selectors)
        
        return [f"""
            // Plugin: {self.name} - Detección de cambios UI
            window.__botsosUIDetector = {{
                selectors: {selectors_json},
                
                checkSelector: function(name) {{
                    const selector = this.selectors[name];
                    if (!selector) return false;
                    return document.querySelector(selector) !== null;
                }},
                
                findAlternative: function(name) {{
                    // Buscar alternativas comunes
                    const alternatives = {{
                        'skip_ad': [
                            'button.ytp-ad-skip-button',
                            'button.ytp-ad-skip-button-modern',
                            '[class*="skip"]',
                            '[class*="Skip"]'
                        ],
                        'like_button': [
                            'button[aria-label*="like"]',
                            'button[aria-label*="Like"]',
                            'ytd-toggle-button-renderer button'
                        ]
                    }};
                    
                    const alts = alternatives[name] || [];
                    for (const alt of alts) {{
                        if (document.querySelector(alt)) {{
                            return alt;
                        }}
                    }}
                    return null;
                }},
                
                reportMissing: function(name) {{
                    console.log('[BotSOS] Selector faltante:', name);
                    const alt = this.findAlternative(name);
                    if (alt) {{
                        console.log('[BotSOS] Alternativa encontrada:', alt);
                    }}
                    return alt;
                }}
            }};
        """]


# Registro de plugins incorporados
BUILTIN_PLUGINS: Dict[str, Type[EvasionPlugin]] = {
    "jitter": JitterPlugin,
    "timing": TimingPlugin,
    "canvas_noise": CanvasNoisePlugin,
    "webgl_fingerprint": WebGLFingerprintPlugin,
    "ui_change_detector": UIChangeDetectorPlugin
}


class PluginManager:
    """Administrador de plugins de evasión.
    
    Carga, gestiona y ejecuta plugins desde archivos YAML/JSON.
    """
    
    def __init__(self, plugins_dir: Optional[Path] = None):
        """Inicializa el administrador de plugins.
        
        Args:
            plugins_dir: Directorio de plugins.
        """
        self.plugins_dir = Path(plugins_dir) if plugins_dir else Path("plugins")
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self._plugins: Dict[str, EvasionPlugin] = {}
        self._load_builtin_plugins()
        self._load_custom_plugins()
    
    def _load_builtin_plugins(self):
        """Carga los plugins incorporados."""
        # Plugin de jitter por defecto
        self.register_plugin("jitter", PluginMetadata(
            name="Jitter Adaptativo",
            version="1.0.0",
            description="Añade movimiento aleatorio adaptativo",
            category="evasion",
            priority=3,
            config={"jitter_px": 5, "adaptive": True}
        ))
        
        # Plugin de timing
        self.register_plugin("timing", PluginMetadata(
            name="Variación de Tiempos",
            version="1.0.0",
            description="Varía los tiempos entre acciones",
            category="evasion",
            priority=2,
            config={"base_delay_ms": 150, "variation_percent": 30}
        ))
        
        # Plugin de canvas
        self.register_plugin("canvas_noise", PluginMetadata(
            name="Ruido de Canvas",
            version="1.0.0",
            description="Inyecta ruido en el fingerprint de canvas",
            category="fingerprint",
            priority=4,
            config={"noise_level": 5}
        ))
        
        # Plugin de WebGL
        self.register_plugin("webgl_fingerprint", PluginMetadata(
            name="Suplantación WebGL",
            version="1.0.0",
            description="Modifica información de GPU/WebGL",
            category="fingerprint",
            priority=4,
            config={
                "vendor": "Google Inc.",
                "renderer": "ANGLE (Intel, Intel HD Graphics 630)"
            }
        ))
        
        # Plugin de detección UI
        self.register_plugin("ui_change_detector", PluginMetadata(
            name="Detector de Cambios UI",
            version="1.0.0",
            description="Detecta cambios en selectores de YouTube",
            category="detection",
            priority=1,
            config={
                "selectors": {
                    "skip_ad": "button.ytp-ad-skip-button",
                    "like_button": "button[aria-label*='like']",
                    "subscribe": "ytd-subscribe-button-renderer button"
                }
            }
        ))
        
        logger.info(f"Cargados {len(self._plugins)} plugins incorporados")
    
    def _load_custom_plugins(self):
        """Carga plugins personalizados desde archivos."""
        if not self.plugins_dir.exists():
            return
        
        # Cargar archivos YAML
        if YAML_AVAILABLE:
            for yaml_file in self.plugins_dir.glob("*.yaml"):
                self._load_plugin_file(yaml_file, "yaml")
            for yml_file in self.plugins_dir.glob("*.yml"):
                self._load_plugin_file(yml_file, "yaml")
        
        # Cargar archivos JSON
        for json_file in self.plugins_dir.glob("*.json"):
            self._load_plugin_file(json_file, "json")
        
        logger.info(f"Total de plugins: {len(self._plugins)}")
    
    def _load_plugin_file(self, file_path: Path, format: str):
        """Carga un plugin desde archivo.
        
        Args:
            file_path: Ruta al archivo.
            format: Formato del archivo (yaml/json).
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if format == "yaml" and YAML_AVAILABLE:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            if not data or not isinstance(data, dict):
                return
            
            # Crear metadatos
            metadata = PluginMetadata(
                name=data.get("name", file_path.stem),
                version=data.get("version", "1.0.0"),
                description=data.get("description", ""),
                author=data.get("author", ""),
                category=data.get("category", "evasion"),
                enabled=data.get("enabled", True),
                priority=data.get("priority", 5),
                dependencies=data.get("dependencies", []),
                config=data.get("config", {})
            )
            
            # Determinar tipo de plugin
            plugin_type = data.get("type", "jitter")
            if plugin_type in BUILTIN_PLUGINS:
                plugin_class = BUILTIN_PLUGINS[plugin_type]
                plugin = plugin_class(metadata)
                self._plugins[file_path.stem] = plugin
                logger.info(f"Plugin cargado: {metadata.name} ({file_path.name})")
            
        except Exception as e:
            logger.error(f"Error cargando plugin {file_path}: {e}")
    
    def register_plugin(self, plugin_id: str, metadata: PluginMetadata):
        """Registra un plugin incorporado.
        
        Args:
            plugin_id: ID del plugin.
            metadata: Metadatos del plugin.
        """
        if plugin_id in BUILTIN_PLUGINS:
            plugin_class = BUILTIN_PLUGINS[plugin_id]
            self._plugins[plugin_id] = plugin_class(metadata)
    
    def get_plugin(self, plugin_id: str) -> Optional[EvasionPlugin]:
        """Obtiene un plugin por ID."""
        return self._plugins.get(plugin_id)
    
    def get_all_plugins(self) -> List[EvasionPlugin]:
        """Obtiene todos los plugins."""
        return list(self._plugins.values())
    
    def get_enabled_plugins(self) -> List[EvasionPlugin]:
        """Obtiene plugins habilitados ordenados por prioridad."""
        plugins = [p for p in self._plugins.values() if p.metadata.enabled]
        plugins.sort(key=lambda p: p.metadata.priority)
        return plugins
    
    def get_plugins_by_category(self, category: str) -> List[EvasionPlugin]:
        """Obtiene plugins de una categoría."""
        return [
            p for p in self._plugins.values()
            if p.metadata.category == category and p.metadata.enabled
        ]
    
    async def apply_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica todos los plugins habilitados.
        
        Args:
            context: Contexto actual.
            
        Returns:
            Contexto modificado.
        """
        for plugin in self.get_enabled_plugins():
            try:
                context = await plugin.apply(context)
            except Exception as e:
                logger.error(f"Error aplicando plugin {plugin.name}: {e}")
                plugin.on_failure()
        
        return context
    
    def get_all_scripts(self) -> List[str]:
        """Obtiene todos los scripts de plugins habilitados."""
        scripts = []
        for plugin in self.get_enabled_plugins():
            try:
                scripts.extend(plugin.get_scripts())
            except Exception as e:
                logger.error(f"Error obteniendo scripts de {plugin.name}: {e}")
        return scripts
    
    def enable_plugin(self, plugin_id: str, enabled: bool = True) -> bool:
        """Habilita o deshabilita un plugin.
        
        Args:
            plugin_id: ID del plugin.
            enabled: Si debe estar habilitado.
            
        Returns:
            True si se actualizó exitosamente.
        """
        if plugin_id in self._plugins:
            self._plugins[plugin_id].metadata.enabled = enabled
            return True
        return False
    
    def update_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Actualiza la configuración de un plugin.
        
        Args:
            plugin_id: ID del plugin.
            config: Nueva configuración.
            
        Returns:
            True si se actualizó exitosamente.
        """
        if plugin_id in self._plugins:
            self._plugins[plugin_id].metadata.config.update(config)
            return True
        return False
    
    def report_success(self, plugin_id: str):
        """Reporta uso exitoso de un plugin."""
        if plugin_id in self._plugins:
            self._plugins[plugin_id].on_success()
    
    def report_failure(self, plugin_id: str):
        """Reporta fallo de un plugin."""
        if plugin_id in self._plugins:
            self._plugins[plugin_id].on_failure()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de todos los plugins."""
        return {
            "total": len(self._plugins),
            "enabled": len(self.get_enabled_plugins()),
            "plugins": [
                {
                    "id": pid,
                    "name": p.name,
                    "enabled": p.metadata.enabled,
                    "priority": p.metadata.priority,
                    "success_rate": p.success_rate,
                    "uses": p.success_count + p.failure_count
                }
                for pid, p in self._plugins.items()
            ]
        }
    
    def save_plugin(self, plugin_id: str, file_format: str = "yaml") -> bool:
        """Guarda la configuración de un plugin a archivo.
        
        Args:
            plugin_id: ID del plugin.
            file_format: Formato (yaml/json).
            
        Returns:
            True si se guardó exitosamente.
        """
        if plugin_id not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_id]
        data = {
            "name": plugin.metadata.name,
            "version": plugin.metadata.version,
            "description": plugin.metadata.description,
            "author": plugin.metadata.author,
            "category": plugin.metadata.category,
            "enabled": plugin.metadata.enabled,
            "priority": plugin.metadata.priority,
            "dependencies": plugin.metadata.dependencies,
            "config": plugin.metadata.config,
            "type": plugin_id.split("_")[0] if "_" in plugin_id else plugin_id
        }
        
        try:
            if file_format == "yaml" and YAML_AVAILABLE:
                file_path = self.plugins_dir / f"{plugin_id}.yaml"
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            else:
                file_path = self.plugins_dir / f"{plugin_id}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Plugin guardado: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando plugin: {e}")
            return False


class RLFeedbackLoop:
    """Bucle de retroalimentación de aprendizaje reforzado simple.
    
    Ajusta parámetros de plugins basándose en resultados.
    """
    
    # Umbral mínimo de muestras para ajuste
    MIN_SAMPLES_FOR_ADJUSTMENT = 10
    
    def __init__(
        self,
        plugin_manager: PluginManager,
        learning_rate: float = 0.1,
        min_samples: int = 10
    ):
        """Inicializa el bucle de retroalimentación.
        
        Args:
            plugin_manager: Administrador de plugins.
            learning_rate: Tasa de aprendizaje.
            min_samples: Muestras mínimas antes de ajustar.
        """
        self.plugin_manager = plugin_manager
        self.learning_rate = learning_rate
        self.min_samples = min_samples
        self._history: List[Dict[str, Any]] = []
    
    def record_outcome(self, plugin_id: str, success: bool, context: Dict[str, Any]):
        """Registra el resultado de usar un plugin.
        
        Args:
            plugin_id: ID del plugin.
            success: Si fue exitoso.
            context: Contexto de la acción.
        """
        self._history.append({
            "plugin_id": plugin_id,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "context": context
        })
        
        # Actualizar estadísticas del plugin
        if success:
            self.plugin_manager.report_success(plugin_id)
        else:
            self.plugin_manager.report_failure(plugin_id)
        
        # Ajustar configuración si hay suficiente historial
        if len(self._history) >= self.min_samples:
            self._adjust_plugins()
    
    def _adjust_plugins(self):
        """Ajusta parámetros de plugins basándose en historial."""
        # Analizar últimas N muestras (configurable)
        sample_size = min(self.min_samples, len(self._history))
        recent = self._history[-sample_size:]
        
        # Agrupar por plugin
        plugin_results: Dict[str, List[bool]] = {}
        for entry in recent:
            pid = entry["plugin_id"]
            if pid not in plugin_results:
                plugin_results[pid] = []
            plugin_results[pid].append(entry["success"])
        
        # Ajustar plugins con bajo rendimiento
        for plugin_id, results in plugin_results.items():
            success_rate = sum(results) / len(results)
            
            if success_rate < 0.5:
                # Ajustar configuración
                plugin = self.plugin_manager.get_plugin(plugin_id)
                if plugin:
                    self._adjust_plugin_config(plugin, success_rate)
    
    def _adjust_plugin_config(self, plugin: EvasionPlugin, success_rate: float):
        """Ajusta la configuración de un plugin basándose en su rendimiento.
        
        Args:
            plugin: El plugin a ajustar.
            success_rate: Tasa de éxito actual.
        """
        config = plugin.metadata.config.copy()
        
        # Ajustes específicos por tipo de plugin
        if "jitter_px" in config:
            # Aumentar jitter si hay muchos fallos
            if success_rate < 0.5:
                config["jitter_px"] = min(15, int(config["jitter_px"] * 1.2))
            elif success_rate > 0.8:
                config["jitter_px"] = max(2, int(config["jitter_px"] * 0.9))
        
        if "noise_level" in config:
            if success_rate < 0.5:
                config["noise_level"] = min(10, config["noise_level"] + 1)
            elif success_rate > 0.8:
                config["noise_level"] = max(1, config["noise_level"] - 1)
        
        if "variation_percent" in config:
            if success_rate < 0.5:
                config["variation_percent"] = min(50, config["variation_percent"] + 5)
        
        plugin.metadata.config = config
        logger.debug(f"Plugin {plugin.name} ajustado: {config}")
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtiene recomendaciones basadas en el historial.
        
        Returns:
            Lista de recomendaciones.
        """
        recommendations = []
        
        for plugin in self.plugin_manager.get_enabled_plugins():
            if plugin.success_rate < 0.5 and (plugin.success_count + plugin.failure_count) >= 5:
                recommendations.append({
                    "plugin_id": plugin.name,
                    "current_rate": plugin.success_rate,
                    "suggestion": "Considere ajustar los parámetros o deshabilitarlo"
                })
        
        return recommendations
