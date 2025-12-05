"""
Módulo de validación de entrada.

Proporciona funciones de validación para configuraciones de sesión,
proxies y otros datos de entrada del usuario.

Diseñado exclusivamente para Windows.
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Resultado de una validación."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __bool__(self) -> bool:
        return self.is_valid
    
    @classmethod
    def success(cls) -> 'ValidationResult':
        """Crear un resultado exitoso."""
        return cls(is_valid=True, errors=[], warnings=[])
    
    @classmethod
    def failure(cls, errors: List[str]) -> 'ValidationResult':
        """Crear un resultado fallido."""
        return cls(is_valid=False, errors=errors, warnings=[])


class InputValidator:
    """
    Validador de entrada para configuraciones de sesión.
    
    Implementa validación de entrada como se sugiere en el documento de análisis.
    """
    
    # Patrones de validación
    PROXY_SERVER_PATTERN = re.compile(
        r'^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}|'
        r'(?:\d{1,3}\.){3}\d{1,3})$'
    )
    
    TIME_PATTERN = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    @classmethod
    def validate_session_name(cls, name: str) -> ValidationResult:
        """
        Validar nombre de sesión.
        
        Args:
            name: Nombre de la sesión.
            
        Returns:
            Resultado de validación.
        """
        errors = []
        warnings = []
        
        if not name:
            errors.append("El nombre de sesión no puede estar vacío")
        elif len(name) > 100:
            errors.append("El nombre de sesión no puede exceder 100 caracteres")
        
        if name and not name.strip():
            errors.append("El nombre de sesión no puede contener solo espacios")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @classmethod
    def validate_proxy_config(
        cls,
        server: str,
        port: int,
        proxy_type: str,
        username: str = "",
        password: str = ""
    ) -> ValidationResult:
        """
        Validar configuración de proxy.
        
        Args:
            server: Servidor proxy.
            port: Puerto del proxy.
            proxy_type: Tipo de proxy (http, https, socks5).
            username: Usuario opcional.
            password: Contraseña opcional.
            
        Returns:
            Resultado de validación.
        """
        errors = []
        warnings = []
        
        # Validar servidor
        if not server:
            errors.append("El servidor proxy no puede estar vacío")
        elif not cls.PROXY_SERVER_PATTERN.match(server):
            errors.append(f"Formato de servidor inválido: {server}")
        
        # Validar puerto
        if port < 1 or port > 65535:
            errors.append(f"Puerto fuera de rango (1-65535): {port}")
        
        # Validar tipo
        valid_types = ["http", "https", "socks5"]
        if proxy_type not in valid_types:
            errors.append(f"Tipo de proxy inválido. Debe ser uno de: {valid_types}")
        
        # Validar credenciales
        if username and not password:
            warnings.append("Se proporcionó usuario pero no contraseña")
        if password and not username:
            warnings.append("Se proporcionó contraseña pero no usuario")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @classmethod
    def validate_port(cls, port: int, name: str = "puerto") -> ValidationResult:
        """
        Validar un número de puerto.
        
        Args:
            port: Número de puerto.
            name: Nombre descriptivo para mensajes de error.
            
        Returns:
            Resultado de validación.
        """
        errors = []
        
        if not isinstance(port, int):
            errors.append(f"El {name} debe ser un número entero")
        elif port < 1 or port > 65535:
            errors.append(f"El {name} debe estar entre 1 y 65535")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
    
    @classmethod
    def validate_range(
        cls,
        min_val: float,
        max_val: float,
        name: str = "rango"
    ) -> ValidationResult:
        """
        Validar que un rango mínimo/máximo sea correcto.
        
        Args:
            min_val: Valor mínimo.
            max_val: Valor máximo.
            name: Nombre descriptivo.
            
        Returns:
            Resultado de validación.
        """
        errors = []
        warnings = []
        
        if min_val > max_val:
            errors.append(f"El valor mínimo de {name} ({min_val}) no puede ser mayor que el máximo ({max_val})")
        elif min_val == max_val:
            warnings.append(f"Los valores mínimo y máximo de {name} son iguales ({min_val})")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @classmethod
    def validate_percentage(
        cls,
        value: float,
        name: str = "porcentaje"
    ) -> ValidationResult:
        """
        Validar que un valor sea un porcentaje válido (0-100).
        
        Args:
            value: Valor a validar.
            name: Nombre descriptivo.
            
        Returns:
            Resultado de validación.
        """
        errors = []
        
        if value < 0 or value > 100:
            errors.append(f"El {name} debe estar entre 0 y 100")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
    
    @classmethod
    def validate_cron_expression(cls, expression: str) -> ValidationResult:
        """
        Validar una expresión cron.
        
        Args:
            expression: Expresión cron.
            
        Returns:
            Resultado de validación.
        """
        errors = []
        warnings = []
        
        if not expression:
            # Vacío es válido (deshabilitado)
            return ValidationResult.success()
        
        # Validación básica de formato
        parts = expression.split()
        if len(parts) != 5:
            errors.append("La expresión cron debe tener 5 partes (minuto hora día mes día_semana)")
        else:
            # Validar cada parte
            ranges = [
                (0, 59, "minuto"),
                (0, 23, "hora"),
                (1, 31, "día"),
                (1, 12, "mes"),
                (0, 6, "día_semana")
            ]
            for i, (min_val, max_val, name) in enumerate(ranges):
                part = parts[i]
                if part != "*" and not part.startswith("*/"):
                    try:
                        val = int(part)
                        if val < min_val or val > max_val:
                            errors.append(f"Valor de {name} fuera de rango ({min_val}-{max_val}): {val}")
                    except ValueError:
                        errors.append(f"Valor de {name} inválido: {part}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @classmethod
    def validate_time(cls, time_str: str, name: str = "hora") -> ValidationResult:
        """
        Validar formato de hora (HH:MM).
        
        Args:
            time_str: Cadena de hora.
            name: Nombre descriptivo.
            
        Returns:
            Resultado de validación.
        """
        errors = []
        
        if not time_str:
            # Vacío es válido
            return ValidationResult.success()
        
        if not cls.TIME_PATTERN.match(time_str):
            errors.append(f"Formato de {name} inválido. Use HH:MM")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
    
    @classmethod
    def validate_email(cls, email: str) -> ValidationResult:
        """
        Validar formato de email.
        
        Args:
            email: Dirección de email.
            
        Returns:
            Resultado de validación.
        """
        errors = []
        
        if not email:
            errors.append("El email no puede estar vacío")
        elif not cls.EMAIL_PATTERN.match(email):
            errors.append(f"Formato de email inválido: {email}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
    
    @classmethod
    def validate_behavior_config(
        cls,
        action_delay_min: int,
        action_delay_max: int,
        view_time_min: int,
        view_time_max: int,
        idle_time_min: float,
        idle_time_max: float
    ) -> ValidationResult:
        """
        Validar configuración de comportamiento.
        
        Args:
            action_delay_min: Retraso mínimo de acción.
            action_delay_max: Retraso máximo de acción.
            view_time_min: Tiempo mínimo de vista.
            view_time_max: Tiempo máximo de vista.
            idle_time_min: Tiempo mínimo de inactividad.
            idle_time_max: Tiempo máximo de inactividad.
            
        Returns:
            Resultado de validación.
        """
        all_errors = []
        all_warnings = []
        
        # Validar rangos
        result = cls.validate_range(action_delay_min, action_delay_max, "retraso de acción")
        all_errors.extend(result.errors)
        all_warnings.extend(result.warnings)
        
        result = cls.validate_range(view_time_min, view_time_max, "tiempo de vista")
        all_errors.extend(result.errors)
        all_warnings.extend(result.warnings)
        
        result = cls.validate_range(idle_time_min, idle_time_max, "tiempo de inactividad")
        all_errors.extend(result.errors)
        all_warnings.extend(result.warnings)
        
        # Validar valores positivos
        if action_delay_min < 0:
            all_errors.append("El retraso mínimo de acción debe ser positivo")
        if view_time_min < 0:
            all_errors.append("El tiempo mínimo de vista debe ser positivo")
        if idle_time_min < 0:
            all_errors.append("El tiempo mínimo de inactividad debe ser positivo")
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )


def validate_session_config(config: Any) -> ValidationResult:
    """
    Validar una configuración de sesión completa.
    
    Args:
        config: Configuración de sesión (SessionConfig).
        
    Returns:
        Resultado de validación completo.
    """
    all_errors = []
    all_warnings = []
    
    # Validar nombre
    result = InputValidator.validate_session_name(config.name)
    all_errors.extend(result.errors)
    all_warnings.extend(result.warnings)
    
    # Validar comportamiento
    result = InputValidator.validate_behavior_config(
        config.behavior.action_delay_min_ms,
        config.behavior.action_delay_max_ms,
        config.behavior.view_time_min_sec,
        config.behavior.view_time_max_sec,
        config.behavior.idle_time_min_sec,
        config.behavior.idle_time_max_sec
    )
    all_errors.extend(result.errors)
    all_warnings.extend(result.warnings)
    
    # Validar proxy si está habilitado
    if config.proxy.enabled:
        result = InputValidator.validate_proxy_config(
            config.proxy.server,
            config.proxy.port,
            config.proxy.proxy_type,
            config.proxy.username,
            config.proxy.password
        )
        all_errors.extend(result.errors)
        all_warnings.extend(result.warnings)
    
    # Validar programación si está habilitada
    if config.scheduling.scheduling_enabled:
        result = InputValidator.validate_cron_expression(config.scheduling.cron_expression)
        all_errors.extend(result.errors)
        all_warnings.extend(result.warnings)
        
        result = InputValidator.validate_time(config.scheduling.start_time, "hora de inicio")
        all_errors.extend(result.errors)
        
        result = InputValidator.validate_time(config.scheduling.end_time, "hora de fin")
        all_errors.extend(result.errors)
    
    return ValidationResult(
        is_valid=len(all_errors) == 0,
        errors=all_errors,
        warnings=all_warnings
    )
