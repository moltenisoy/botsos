"""
Módulo de Cliente LM Studio.

Proporciona una interfaz para comunicarse con LM Studio a través
de su API compatible con OpenAI.

Diseñado para Windows.
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LMStudioConfig:
    """Configuración para el cliente de LM Studio."""
    base_url: str = "http://localhost:1234/v1"
    api_key: str = "lm-studio"  # LM Studio no requiere API key real
    timeout: int = 120
    max_tokens: int = 2048
    temperature: float = 0.7


class LMStudioClient:
    """Cliente para comunicarse con LM Studio.
    
    LM Studio proporciona una API compatible con OpenAI para ejecutar
    modelos de lenguaje localmente.
    """
    
    def __init__(self, config: Optional[LMStudioConfig] = None):
        """Inicializa el cliente de LM Studio.
        
        Args:
            config: Configuración del cliente. Si es None, usa valores por defecto.
        """
        self.config = config or LMStudioConfig()
        self._client = None
        self._available_models: List[str] = []
    
    def _get_client(self):
        """Obtiene o crea el cliente de OpenAI."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(
                    base_url=self.config.base_url,
                    api_key=self.config.api_key,
                    timeout=self.config.timeout
                )
            except ImportError:
                logger.error("El paquete 'openai' no está instalado. Instale con: pip install openai")
                raise
        return self._client
    
    def is_available(self) -> bool:
        """Verifica si LM Studio está disponible y respondiendo.
        
        Returns:
            True si LM Studio está disponible, False de lo contrario.
        """
        try:
            client = self._get_client()
            models = client.models.list()
            return len(models.data) > 0
        except Exception as e:
            logger.warning(f"No se pudo conectar con LM Studio: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Obtiene la lista de modelos disponibles en LM Studio.
        
        Returns:
            Lista de IDs de modelos disponibles.
        """
        try:
            client = self._get_client()
            models = client.models.list()
            self._available_models = [model.id for model in models.data]
            return self._available_models
        except Exception as e:
            logger.error(f"Error obteniendo modelos: {e}")
            return []
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """Envía un mensaje al modelo y obtiene una respuesta.
        
        Args:
            messages: Lista de mensajes en formato OpenAI.
            model: Nombre del modelo a usar. Si es None, usa el modelo por defecto.
            temperature: Temperatura de generación. Si es None, usa la configuración.
            max_tokens: Máximo de tokens a generar. Si es None, usa la configuración.
            stream: Si es True, retorna un stream de respuestas.
            
        Returns:
            Respuesta del modelo como string.
        """
        try:
            client = self._get_client()
            
            response = client.chat.completions.create(
                model=model or "local-model",
                messages=messages,
                temperature=temperature if temperature is not None else self.config.temperature,
                max_tokens=max_tokens if max_tokens is not None else self.config.max_tokens,
                stream=stream
            )
            
            if stream:
                return response  # Retorna el generador
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error en chat con LM Studio: {e}")
            return ""
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Genera una completación para el prompt dado.
        
        Args:
            prompt: El prompt del usuario.
            system_prompt: Prompt de sistema opcional.
            model: Nombre del modelo a usar.
            temperature: Temperatura de generación.
            max_tokens: Máximo de tokens a generar.
            
        Returns:
            Respuesta del modelo como string.
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def analyze_page(
        self,
        html_content: str,
        task_description: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analiza el contenido de una página web usando el LLM.
        
        Args:
            html_content: Contenido HTML de la página.
            task_description: Descripción de la tarea a realizar.
            model: Nombre del modelo a usar.
            
        Returns:
            Diccionario con las acciones sugeridas.
        """
        import json
        
        system_prompt = """Eres un asistente de automatización de navegador. 
Analiza el HTML proporcionado y sugiere acciones para completar la tarea.
Responde SOLO con un JSON válido con el siguiente formato:
{
    "actions": [
        {"type": "click|type|scroll|wait", "selector": "selector_css", "value": "valor_opcional"}
    ],
    "reasoning": "explicación breve"
}"""

        prompt = f"""Tarea: {task_description}

HTML (truncado):
{html_content[:5000]}

Analiza y sugiere las acciones necesarias."""

        response = self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=0.3  # Más determinístico para análisis
        )
        
        try:
            # Intentar extraer JSON de la respuesta
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"actions": [], "reasoning": response}
        except json.JSONDecodeError:
            return {"actions": [], "reasoning": response}
    
    def generate_comment(
        self,
        video_title: str,
        video_description: str = "",
        style: str = "positivo",
        model: Optional[str] = None
    ) -> str:
        """Genera un comentario para un video.
        
        Args:
            video_title: Título del video.
            video_description: Descripción del video.
            style: Estilo del comentario (positivo, neutral, pregunta).
            model: Nombre del modelo a usar.
            
        Returns:
            Comentario generado.
        """
        style_prompts = {
            "positivo": "El comentario debe ser positivo y alentador.",
            "neutral": "El comentario debe ser neutral e informativo.",
            "pregunta": "El comentario debe hacer una pregunta relevante sobre el contenido."
        }
        
        system_prompt = f"""Eres un espectador genuino. 
Genera un comentario corto (máximo 2 oraciones) para el video.
{style_prompts.get(style, style_prompts['positivo'])}
No uses emojis excesivos. Sé natural."""

        prompt = f"""Video: {video_title}
Descripción: {video_description[:200] if video_description else 'No disponible'}

Genera un comentario:"""

        return self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=0.8,  # Más creativo para comentarios
            max_tokens=100
        )
    
    def update_config(
        self,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> None:
        """Actualiza la configuración del cliente.
        
        Args:
            base_url: Nueva URL base.
            temperature: Nueva temperatura.
            max_tokens: Nuevo máximo de tokens.
            timeout: Nuevo timeout.
        """
        if base_url is not None:
            self.config.base_url = base_url
            self._client = None  # Forzar recreación del cliente
        
        if temperature is not None:
            self.config.temperature = temperature
        
        if max_tokens is not None:
            self.config.max_tokens = max_tokens
        
        if timeout is not None:
            self.config.timeout = timeout
            self._client = None


# Singleton para uso global
_default_client: Optional[LMStudioClient] = None


def get_lmstudio_client() -> LMStudioClient:
    """Obtiene el cliente de LM Studio por defecto (singleton).
    
    Returns:
        Instancia del cliente de LM Studio.
    """
    global _default_client
    if _default_client is None:
        _default_client = LMStudioClient()
    return _default_client


def check_lmstudio_connection() -> bool:
    """Verifica si LM Studio está disponible.
    
    Returns:
        True si está disponible, False de lo contrario.
    """
    return get_lmstudio_client().is_available()
