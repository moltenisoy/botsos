"""
Módulo de Documentación y Ayuda

Implementa sistema de documentación integrada incluyendo:
- Tooltips contextuales para todos los campos de la GUI
- Asistente de inicio para nuevos usuarios
- Sistema de ayuda en tiempo real

Implementa características de fase6.txt:
- Tooltips en cada campo de la GUI
- Asistente de bienvenida con tutorial paso a paso
- Generación de documentación desde docstrings

Diseñado exclusivamente para Windows.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class HelpCategory(Enum):
    """Categorías de ayuda."""
    GENERAL = "general"
    SESSION = "session"
    PROXY = "proxy"
    FINGERPRINT = "fingerprint"
    BEHAVIOR = "behavior"
    CAPTCHA = "captcha"
    SCALING = "scaling"
    SECURITY = "security"
    ADVANCED = "advanced"


@dataclass
class TooltipInfo:
    """Información de tooltip para un campo."""
    field_name: str
    short_text: str
    long_text: str = ""
    category: HelpCategory = HelpCategory.GENERAL
    example: str = ""
    warning: str = ""


# Base de datos de tooltips en español
TOOLTIPS_DATABASE: Dict[str, TooltipInfo] = {
    # === SESIÓN ===
    "session_name": TooltipInfo(
        field_name="Nombre de Sesión",
        short_text="Nombre identificador para esta sesión",
        long_text="Un nombre descriptivo para identificar esta sesión. "
                  "Use nombres que describan el propósito de la sesión.",
        category=HelpCategory.SESSION,
        example="Sesión YouTube - Canal Principal"
    ),
    "headless": TooltipInfo(
        field_name="Modo Oculto (Headless)",
        short_text="Ejecutar navegador sin interfaz visible",
        long_text="En modo oculto, el navegador funciona en segundo plano sin "
                  "mostrar ventana. Útil para ejecución desatendida pero puede "
                  "ser detectado por algunos sitios.",
        category=HelpCategory.SESSION,
        warning="Algunos sitios detectan modo headless. Use con precaución."
    ),
    
    # === LLM ===
    "llm_model": TooltipInfo(
        field_name="Modelo LLM",
        short_text="Modelo de lenguaje a utilizar",
        long_text="Seleccione el modelo de IA que controlará las decisiones. "
                  "Modelos más grandes son más precisos pero requieren más RAM.",
        category=HelpCategory.BEHAVIOR,
        example="llama3.1:8b requiere ~8GB RAM"
    ),
    
    # === PROXY ===
    "proxy_enabled": TooltipInfo(
        field_name="Habilitar Proxy",
        short_text="Usar proxy para ocultar IP real",
        long_text="Los proxies permiten ocultar su dirección IP real y simular "
                  "conexiones desde diferentes ubicaciones geográficas.",
        category=HelpCategory.PROXY,
        warning="Proxies gratuitos suelen ser lentos y poco fiables."
    ),
    "proxy_server": TooltipInfo(
        field_name="Servidor Proxy",
        short_text="Dirección del servidor proxy",
        long_text="Ingrese la dirección IP o nombre de dominio del servidor proxy.",
        category=HelpCategory.PROXY,
        example="proxy.ejemplo.com o 192.168.1.100"
    ),
    "proxy_port": TooltipInfo(
        field_name="Puerto Proxy",
        short_text="Puerto del servidor proxy",
        long_text="El puerto en el que escucha el servidor proxy. "
                  "Los puertos comunes son 8080, 3128, 1080 (SOCKS5).",
        category=HelpCategory.PROXY,
        example="8080"
    ),
    "proxy_type": TooltipInfo(
        field_name="Tipo de Proxy",
        short_text="Protocolo del proxy",
        long_text="HTTP: Más común, solo para tráfico web.\n"
                  "HTTPS: HTTP con encriptación.\n"
                  "SOCKS5: Más versátil, soporta cualquier protocolo.",
        category=HelpCategory.PROXY
    ),
    "rotation_interval": TooltipInfo(
        field_name="Intervalo de Rotación",
        short_text="Cada cuántas solicitudes cambiar proxy",
        long_text="Rotar proxies regularmente ayuda a evitar detección. "
                  "Un valor bajo (5-10) es más seguro pero más lento.",
        category=HelpCategory.PROXY,
        example="10 solicitudes"
    ),
    
    # === HUELLA DIGITAL ===
    "device_preset": TooltipInfo(
        field_name="Preset de Dispositivo",
        short_text="Perfil de dispositivo predefinido",
        long_text="Seleccione un perfil que simula un dispositivo real. "
                  "El perfil incluye user-agent, resolución, y otras características.",
        category=HelpCategory.FINGERPRINT
    ),
    "canvas_noise": TooltipInfo(
        field_name="Ruido de Canvas",
        short_text="Añadir ruido al fingerprint de canvas",
        long_text="Canvas fingerprinting es una técnica de rastreo. "
                  "Añadir ruido hace que cada sesión tenga un fingerprint único.",
        category=HelpCategory.FINGERPRINT,
        warning="Demasiado ruido puede ser sospechoso. Use nivel 3-7."
    ),
    "webrtc_protection": TooltipInfo(
        field_name="Protección WebRTC",
        short_text="Prevenir filtración de IP por WebRTC",
        long_text="WebRTC puede revelar su IP real incluso usando proxy. "
                  "Esta opción previene esa filtración.",
        category=HelpCategory.FINGERPRINT
    ),
    
    # === COMPORTAMIENTO ===
    "action_delay_min": TooltipInfo(
        field_name="Retraso Mínimo de Acción",
        short_text="Tiempo mínimo entre acciones",
        long_text="Tiempo mínimo de espera entre cada acción del navegador. "
                  "Valores muy bajos pueden parecer bots.",
        category=HelpCategory.BEHAVIOR,
        example="100-200 ms es natural"
    ),
    "action_delay_max": TooltipInfo(
        field_name="Retraso Máximo de Acción",
        short_text="Tiempo máximo entre acciones",
        long_text="El retraso real será un valor aleatorio entre mínimo y máximo. "
                  "Mayor variación parece más humano.",
        category=HelpCategory.BEHAVIOR
    ),
    "mouse_jitter": TooltipInfo(
        field_name="Movimiento Aleatorio del Ratón",
        short_text="Añadir pequeños movimientos al cursor",
        long_text="Los humanos no mueven el ratón en línea perfectamente recta. "
                  "El jitter simula esa imperfección natural.",
        category=HelpCategory.BEHAVIOR
    ),
    "typing_speed": TooltipInfo(
        field_name="Velocidad de Escritura",
        short_text="Velocidad al escribir texto",
        long_text="Simula la velocidad de escritura humana. "
                  "Incluye variaciones y ocasionales errores tipográficos.",
        category=HelpCategory.BEHAVIOR,
        example="50-200 ms por tecla"
    ),
    
    # === CAPTCHA ===
    "captcha_enabled": TooltipInfo(
        field_name="Resolución de CAPTCHA",
        short_text="Resolver CAPTCHAs automáticamente",
        long_text="Integra con servicios de resolución de CAPTCHA como 2captcha. "
                  "Requiere una clave API y tiene costo por uso.",
        category=HelpCategory.CAPTCHA,
        warning="Los servicios de CAPTCHA tienen costo por cada resolución."
    ),
    "captcha_provider": TooltipInfo(
        field_name="Proveedor de CAPTCHA",
        short_text="Servicio para resolver CAPTCHAs",
        long_text="2captcha: Más popular, buena relación precio/velocidad.\n"
                  "anticaptcha: Alternativa fiable.\n"
                  "capsolver: Más rápido pero más caro.",
        category=HelpCategory.CAPTCHA
    ),
    
    # === ESCALABILIDAD ===
    "docker_enabled": TooltipInfo(
        field_name="Habilitar Docker",
        short_text="Ejecutar sesiones en contenedores",
        long_text="Docker permite ejecutar cada sesión en un entorno aislado. "
                  "Requiere Docker Desktop instalado.",
        category=HelpCategory.SCALING,
        warning="Requiere Docker Desktop con al menos 4GB RAM asignados."
    ),
    "aws_enabled": TooltipInfo(
        field_name="Habilitar AWS",
        short_text="Escalar a la nube de Amazon",
        long_text="Cuando los recursos locales están al límite, las sesiones "
                  "pueden migrar automáticamente a instancias EC2 de AWS.",
        category=HelpCategory.SCALING,
        warning="AWS tiene costos por uso. Configure límites de gasto."
    ),
    "auto_scale": TooltipInfo(
        field_name="Auto-Escalado",
        short_text="Escalar automáticamente según carga",
        long_text="Monitorea CPU y RAM. Si superan los umbrales, migra "
                  "sesiones automáticamente a Docker o cloud.",
        category=HelpCategory.SCALING
    ),
    
    # === SEGURIDAD ===
    "block_cdp_ports": TooltipInfo(
        field_name="Bloquear Puertos CDP",
        short_text="Bloquear puertos de depuración",
        long_text="Los puertos CDP pueden revelar que el navegador está "
                  "siendo controlado. Bloquearlos aumenta la evasión.",
        category=HelpCategory.SECURITY
    ),
    "polymorphic_fingerprint": TooltipInfo(
        field_name="Huella Polimórfica",
        short_text="Variar huella digital periódicamente",
        long_text="Cambia ligeramente la huella digital cada cierto tiempo "
                  "para evitar correlación entre sesiones.",
        category=HelpCategory.SECURITY
    ),
    
    # === AVANZADO ===
    "ml_proxy_selection": TooltipInfo(
        field_name="Selección ML de Proxy",
        short_text="Usar IA para elegir el mejor proxy",
        long_text="Un modelo de machine learning analiza el historial de "
                  "rendimiento y selecciona el proxy con mayor probabilidad de éxito.",
        category=HelpCategory.ADVANCED
    ),
    "rl_evasion": TooltipInfo(
        field_name="Evasión con RL",
        short_text="Aprendizaje reforzado para evasión",
        long_text="El sistema aprende de sus éxitos y fracasos para "
                  "ajustar automáticamente los parámetros de evasión.",
        category=HelpCategory.ADVANCED
    ),
}


class TooltipManager:
    """Administrador de tooltips para la GUI.
    
    Proporciona tooltips contextuales en español para
    todos los campos de la interfaz.
    """
    
    def __init__(self):
        """Inicializa el administrador de tooltips."""
        self._tooltips = TOOLTIPS_DATABASE.copy()
        self._custom_tooltips: Dict[str, TooltipInfo] = {}
    
    def get_tooltip(self, field_id: str) -> Optional[TooltipInfo]:
        """Obtiene tooltip para un campo.
        
        Args:
            field_id: Identificador del campo.
            
        Returns:
            Información del tooltip o None.
        """
        if field_id in self._custom_tooltips:
            return self._custom_tooltips[field_id]
        return self._tooltips.get(field_id)
    
    def get_short_tooltip(self, field_id: str) -> str:
        """Obtiene texto corto del tooltip.
        
        Args:
            field_id: Identificador del campo.
            
        Returns:
            Texto corto o cadena vacía.
        """
        tooltip = self.get_tooltip(field_id)
        return tooltip.short_text if tooltip else ""
    
    def get_full_tooltip(self, field_id: str) -> str:
        """Obtiene tooltip completo formateado.
        
        Args:
            field_id: Identificador del campo.
            
        Returns:
            Texto completo formateado.
        """
        tooltip = self.get_tooltip(field_id)
        if not tooltip:
            return ""
        
        parts = [f"<b>{tooltip.field_name}</b>"]
        parts.append(f"<p>{tooltip.short_text}</p>")
        
        if tooltip.long_text:
            parts.append(f"<p><i>{tooltip.long_text}</i></p>")
        
        if tooltip.example:
            parts.append(f"<p><b>Ejemplo:</b> {tooltip.example}</p>")
        
        if tooltip.warning:
            parts.append(f"<p style='color: orange;'>⚠️ {tooltip.warning}</p>")
        
        return "".join(parts)
    
    def add_custom_tooltip(self, field_id: str, tooltip: TooltipInfo):
        """Añade un tooltip personalizado.
        
        Args:
            field_id: Identificador del campo.
            tooltip: Información del tooltip.
        """
        self._custom_tooltips[field_id] = tooltip
    
    def get_tooltips_by_category(self, category: HelpCategory) -> List[TooltipInfo]:
        """Obtiene tooltips de una categoría.
        
        Args:
            category: Categoría a filtrar.
            
        Returns:
            Lista de tooltips.
        """
        return [
            t for t in self._tooltips.values()
            if t.category == category
        ]


@dataclass
class TutorialStep:
    """Paso del tutorial de inicio."""
    step_number: int
    title: str
    description: str
    target_widget: str = ""  # ID del widget a resaltar
    action_required: str = ""  # Acción que el usuario debe realizar
    next_condition: str = "click"  # click, input, auto


# Tutorial de bienvenida
WELCOME_TUTORIAL: List[TutorialStep] = [
    TutorialStep(
        step_number=1,
        title="¡Bienvenido a BotSOS!",
        description=(
            "Este asistente le guiará en la configuración inicial de BotSOS.\n\n"
            "BotSOS es un administrador de sesiones de automatización de navegador "
            "con integración de modelos de lenguaje (LLM).\n\n"
            "⚠️ ADVERTENCIA ÉTICA: Esta herramienta debe usarse únicamente para "
            "fines legítimos y de prueba. El uso para manipulación o fraude "
            "viola los Términos de Servicio de YouTube."
        ),
        next_condition="click"
    ),
    TutorialStep(
        step_number=2,
        title="Requisitos del Sistema",
        description=(
            "Antes de continuar, verifique que su sistema cumple los requisitos:\n\n"
            "✓ Windows 10 o superior\n"
            "✓ Python 3.10 o superior\n"
            "✓ Al menos 4 GB de RAM (8 GB recomendado)\n"
            "✓ Ollama instalado con un modelo (llama3.1:8b recomendado)\n"
            "✓ Playwright instalado (pip install playwright && playwright install)\n\n"
            "Opcional:\n"
            "○ Docker Desktop para contenedores\n"
            "○ Cuenta AWS para escalabilidad cloud"
        ),
        next_condition="click"
    ),
    TutorialStep(
        step_number=3,
        title="Crear su Primera Sesión",
        description=(
            "Para comenzar, debe crear una sesión:\n\n"
            "1. Haga clic en '➕ Agregar Sesión' en la barra lateral\n"
            "2. Ingrese un nombre descriptivo para la sesión\n"
            "3. Configure los parámetros según sus necesidades\n\n"
            "Cada sesión puede tener configuraciones diferentes de proxy, "
            "huella digital y comportamiento."
        ),
        target_widget="add_session_btn",
        action_required="Crear una sesión",
        next_condition="click"
    ),
    TutorialStep(
        step_number=4,
        title="Configurar el Modelo LLM",
        description=(
            "El modelo LLM controla las decisiones de la sesión.\n\n"
            "Modelos recomendados según su RAM:\n"
            "• 4-6 GB: phi3.5:3.8b (más ligero)\n"
            "• 6-8 GB: qwen2.5:7b (buen balance)\n"
            "• 8+ GB: llama3.1:8b (más capaz)\n"
            "• 16+ GB: mistral-nemo:12b (mejor calidad)\n\n"
            "Asegúrese de que Ollama esté corriendo antes de iniciar sesiones."
        ),
        target_widget="model_combo",
        next_condition="click"
    ),
    TutorialStep(
        step_number=5,
        title="Configurar Proxy (Opcional)",
        description=(
            "Los proxies ocultan su IP real.\n\n"
            "Si tiene proxies:\n"
            "1. Vaya a la pestaña 'Proxy/IP'\n"
            "2. Habilite el uso de proxy\n"
            "3. Configure el servidor, puerto y credenciales\n"
            "4. O importe una lista desde archivo\n\n"
            "La rotación automática cambia de proxy periódicamente "
            "para mayor anonimato."
        ),
        target_widget="proxy_tab",
        next_condition="click"
    ),
    TutorialStep(
        step_number=6,
        title="Huella Digital",
        description=(
            "La huella digital simula un dispositivo real.\n\n"
            "Recomendaciones:\n"
            "• Use presets que coincidan con su ubicación geográfica\n"
            "• Habilite ruido de canvas (nivel 3-7)\n"
            "• Active protección WebRTC\n"
            "• Marque 'Aleatorizar al iniciar' para variación\n\n"
            "Una huella consistente es mejor que cambiar constantemente."
        ),
        target_widget="fingerprint_tab",
        next_condition="click"
    ),
    TutorialStep(
        step_number=7,
        title="¡Listo para Comenzar!",
        description=(
            "Ha completado la configuración básica.\n\n"
            "Para iniciar una sesión:\n"
            "1. Seleccione la sesión en la lista\n"
            "2. Haga clic en '▶️ Iniciar Seleccionada'\n"
            "3. Observe los logs en la pestaña 'Registros'\n\n"
            "Recuerde guardar su configuración con '💾 Guardar Configuración'.\n\n"
            "Para más ayuda, pase el cursor sobre cualquier campo para ver "
            "su descripción."
        ),
        next_condition="click"
    )
]


class TutorialWizard:
    """Asistente de tutorial para nuevos usuarios.
    
    Guía paso a paso por la configuración inicial.
    """
    
    def __init__(self, on_step_change: Optional[Callable] = None):
        """Inicializa el asistente.
        
        Args:
            on_step_change: Callback cuando cambia el paso.
        """
        self.steps = WELCOME_TUTORIAL
        self.current_step = 0
        self.on_step_change = on_step_change
        self._completed = False
    
    @property
    def total_steps(self) -> int:
        return len(self.steps)
    
    @property
    def is_completed(self) -> bool:
        return self._completed
    
    @property
    def current_step_info(self) -> TutorialStep:
        if 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return self.steps[-1]
    
    def next_step(self) -> bool:
        """Avanza al siguiente paso.
        
        Returns:
            True si hay más pasos, False si terminó.
        """
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            if self.on_step_change:
                self.on_step_change(self.current_step_info)
            return True
        else:
            self._completed = True
            return False
    
    def previous_step(self) -> bool:
        """Retrocede al paso anterior.
        
        Returns:
            True si retrocedió, False si está al inicio.
        """
        if self.current_step > 0:
            self.current_step -= 1
            if self.on_step_change:
                self.on_step_change(self.current_step_info)
            return True
        return False
    
    def skip_tutorial(self):
        """Salta el tutorial."""
        self._completed = True
        self.current_step = len(self.steps)
    
    def reset(self):
        """Reinicia el tutorial."""
        self.current_step = 0
        self._completed = False


class EthicalConsentManager:
    """Administrador de consentimiento ético.
    
    Gestiona la aceptación de términos éticos antes de usar la aplicación.
    """
    
    CONSENT_FILE = "ethical_consent.json"
    
    CONSENT_TEXT = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           ADVERTENCIA ÉTICA                                   ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  BotSOS es una herramienta de automatización de navegador que puede usarse   ║
║  para interactuar con sitios web de manera automatizada.                      ║
║                                                                               ║
║  ⚠️  TÉRMINOS DE USO:                                                         ║
║                                                                               ║
║  • Esta herramienta está diseñada ÚNICAMENTE para fines educativos,          ║
║    investigación de seguridad y pruebas autorizadas.                          ║
║                                                                               ║
║  • El uso de esta herramienta para manipular métricas, cometer fraude,       ║
║    o violar los Términos de Servicio de cualquier plataforma es ILEGAL       ║
║    y está ESTRICTAMENTE PROHIBIDO.                                            ║
║                                                                               ║
║  • El usuario asume TODA la responsabilidad por el uso de esta herramienta.  ║
║                                                                               ║
║  • El uso indebido puede resultar en:                                         ║
║    - Suspensión de cuentas                                                    ║
║    - Acciones legales                                                         ║
║    - Otras consecuencias                                                      ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  Al continuar, usted confirma que:                                            ║
║                                                                               ║
║  ✓ Ha leído y comprendido esta advertencia                                    ║
║  ✓ Usará esta herramienta de manera ética y legal                            ║
║  ✓ Acepta toda la responsabilidad por sus acciones                           ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Inicializa el administrador de consentimiento.
        
        Args:
            data_dir: Directorio de datos.
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._consent_file = self.data_dir / self.CONSENT_FILE
        self._consent_given = self._load_consent()
    
    def _load_consent(self) -> bool:
        """Carga el estado del consentimiento."""
        import json
        
        if self._consent_file.exists():
            try:
                with open(self._consent_file, 'r') as f:
                    data = json.load(f)
                    return data.get("consent_given", False)
            except (FileNotFoundError, PermissionError, json.JSONDecodeError) as e:
                logger.warning(f"Error cargando consentimiento: {e}")
        return False
    
    def _save_consent(self, consent: bool):
        """Guarda el estado del consentimiento."""
        import json
        from datetime import datetime
        
        data = {
            "consent_given": consent,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        try:
            with open(self._consent_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando consentimiento: {e}")
    
    @property
    def has_consent(self) -> bool:
        """Verifica si hay consentimiento."""
        return self._consent_given
    
    def give_consent(self):
        """Registra el consentimiento."""
        self._consent_given = True
        self._save_consent(True)
        logger.info("Consentimiento ético registrado")
    
    def revoke_consent(self):
        """Revoca el consentimiento."""
        self._consent_given = False
        self._save_consent(False)
        logger.info("Consentimiento ético revocado")
    
    def get_consent_text(self) -> str:
        """Obtiene el texto del consentimiento."""
        return self.CONSENT_TEXT


class HelpSystem:
    """Sistema de ayuda integrado.
    
    Combina tooltips, tutorial y documentación.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Inicializa el sistema de ayuda.
        
        Args:
            data_dir: Directorio de datos.
        """
        self.tooltip_manager = TooltipManager()
        self.tutorial = TutorialWizard()
        self.consent_manager = EthicalConsentManager(data_dir)
    
    def should_show_consent(self) -> bool:
        """Verifica si debe mostrar el diálogo de consentimiento."""
        return not self.consent_manager.has_consent
    
    def should_show_tutorial(self) -> bool:
        """Verifica si debe mostrar el tutorial."""
        # Mostrar tutorial si es la primera vez después del consentimiento
        # Esto se puede hacer más sofisticado con un archivo de configuración
        return self.consent_manager.has_consent and not self.tutorial.is_completed
    
    def get_tooltip(self, field_id: str) -> str:
        """Obtiene tooltip para un campo."""
        return self.tooltip_manager.get_full_tooltip(field_id)
    
    def get_quick_help(self, field_id: str) -> str:
        """Obtiene ayuda rápida (texto corto)."""
        return self.tooltip_manager.get_short_tooltip(field_id)
    
    def get_category_help(self, category: HelpCategory) -> List[Dict[str, str]]:
        """Obtiene ayuda para una categoría completa."""
        tooltips = self.tooltip_manager.get_tooltips_by_category(category)
        return [
            {
                "field": t.field_name,
                "description": t.short_text,
                "details": t.long_text
            }
            for t in tooltips
        ]
