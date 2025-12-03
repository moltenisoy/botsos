# Guía de la Estructura Modular de la GUI

Este documento describe la nueva estructura modular de la interfaz gráfica de BotSOS.

## Estructura de Directorios

```
src/gui/
├── __init__.py              # Punto de entrada del módulo GUI
├── main_window.py           # (Opcional) Ventana principal refactorizada
├── tabs/                    # Pestañas de configuración
│   ├── __init__.py
│   ├── behavior_tab.py      # Pestaña de comportamiento
│   ├── proxy_tab.py         # Pestaña de proxy
│   ├── fingerprint_tab.py   # Pestaña de huella digital
│   ├── advanced_tabs.py     # Pestañas avanzadas (suplantación, CAPTCHA, etc.)
│   └── phase5_tabs.py       # Pestañas de Fase 5 (escalabilidad, ML, etc.)
├── widgets/                 # Widgets reutilizables
│   ├── __init__.py
│   ├── resource_monitor.py  # Monitor de recursos del sistema
│   └── session_list.py      # Lista de sesiones
└── workers/                 # Trabajadores de sesión
    ├── __init__.py
    ├── base_worker.py       # Clase base abstracta
    ├── session_worker.py    # Trabajador QThread
    └── session_runnable.py  # Trabajador QRunnable
```

## Componentes Principales

### Workers (Trabajadores)

#### BaseSessionExecutor
Clase base abstracta que elimina la duplicación de lógica entre `SessionWorker` y `SessionRunnable`.

```python
from gui.workers import BaseSessionExecutor

class MyCustomWorker(BaseSessionExecutor):
    def emit_status_update(self, session_id, status):
        # Implementar emisión de señal
        pass
```

#### SessionWorker
Trabajador basado en QThread para ejecución de sesiones.

```python
from gui.workers import SessionWorker

worker = SessionWorker(session_config)
worker.status_update.connect(on_status_update)
worker.start()
```

#### SessionRunnable
Trabajador basado en QRunnable para uso con QThreadPool.

```python
from gui.workers import SessionRunnable

runnable = SessionRunnable(session_config)
runnable.signals.status_update.connect(on_status_update)
threadpool.start(runnable)
```

### Tabs (Pestañas)

Las pestañas son funciones factory que crean widgets de pestaña:

```python
from gui.tabs import create_behavior_tab, create_proxy_tab

# Crear pestañas
behavior = create_behavior_tab(parent)
proxy = create_proxy_tab(parent)

# Agregar al TabWidget
tabs.addTab(behavior, "Comportamiento")
tabs.addTab(proxy, "Proxy")
```

### Widgets

Widgets reutilizables para la interfaz:

```python
from gui.widgets import ResourceMonitor, SessionListWidget

# Monitor de recursos
monitor = ResourceMonitor()
monitor.update_values()  # Actualizar valores de CPU/RAM

# Lista de sesiones
session_list = SessionListWidget()
session_list.session_selected.connect(on_session_selected)
session_list.add_session(session_id, session_name)
```

## Módulos de Soporte

### Validación (validation.py)

Proporciona validación robusta de entrada:

```python
from validation import InputValidator, validate_session_config

# Validar proxy
result = InputValidator.validate_proxy_config(
    server="proxy.example.com",
    port=8080,
    proxy_type="http"
)
if not result.is_valid:
    print(result.errors)
```

### Resiliencia (resilience.py)

Patrones de resiliencia para mejorar robustez:

```python
from resilience import CircuitBreaker, TTLCache, JsonSessionRepository

# Circuit Breaker para proxies
breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60)
try:
    result = breaker.call(make_request, proxy_url)
except CircuitOpenError:
    use_alternative_proxy()

# Cache con TTL para respuestas LLM
cache = TTLCache[str](max_size=100, ttl=3600)
cache.set("prompt_hash", "response")
cached = cache.get("prompt_hash")

# Repository Pattern para persistencia
repo = JsonSessionRepository(data_dir)
repo.save(session_id, config)
config = repo.load(session_id)
```

## Beneficios de la Estructura Modular

1. **Mantenibilidad**: Cada componente tiene una responsabilidad clara
2. **Reutilización**: Los widgets y trabajadores son reutilizables
3. **Testabilidad**: Los componentes pueden ser probados de forma aislada
4. **Escalabilidad**: Fácil agregar nuevas pestañas o funcionalidades
5. **Cohesión**: Mayor cohesión dentro de cada módulo
6. **Eliminación de Duplicación**: La lógica común está en clases base
