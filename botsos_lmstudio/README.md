# BotSOS-LMStudio - Administrador de Sesiones Multi-Modelo

<p align="center">
  <img src="https://img.shields.io/badge/Versión-1.0.0-brightgreen.svg" alt="Versión 1.0.0">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/PyQt6-6.6+-green.svg" alt="PyQt6">
  <img src="https://img.shields.io/badge/Playwright-1.40+-orange.svg" alt="Playwright">
  <img src="https://img.shields.io/badge/LM%20Studio-Compatible-purple.svg" alt="LM Studio">
  <img src="https://img.shields.io/badge/Windows-10%2F11-0078D6.svg" alt="Windows 10/11">
  <img src="https://img.shields.io/badge/Licencia-MIT-yellow.svg" alt="Licencia">
</p>

Un administrador de sesiones profesional para ejecutar múltiples instancias de automatización de navegador con LLM, con características avanzadas de anti-detección, escalabilidad y sistema de plugins.

**Esta versión está adaptada para usar LM Studio como backend de LLM, proporcionando una API compatible con OpenAI para ejecutar modelos de lenguaje localmente.**

**⚠️ Este proyecto está diseñado exclusivamente para Windows.**

## ⚠️ ADVERTENCIA ÉTICA

Esta herramienta está diseñada **únicamente para fines educativos, investigación de seguridad y pruebas autorizadas**. El uso para manipular métricas, cometer fraude, o violar los Términos de Servicio de cualquier plataforma es **ilegal y está estrictamente prohibido**. El usuario asume toda la responsabilidad por el uso de esta herramienta.

## 🆚 Diferencias con BotSOS Original

| Característica | BotSOS Original | BotSOS-LMStudio |
|---|---|---|
| Backend LLM | Ollama | LM Studio |
| API | Ollama Python Client | OpenAI Compatible API |
| Gestión de Modelos | CLI (`ollama pull`) | GUI de LM Studio |
| Puerto por defecto | 11434 | 1234 |
| Modelos recomendados | llama3.1:8b, qwen2.5:7b | llama-2-7b-chat, mistral-7b |

## 🚀 Características

### Funcionalidad Principal
- **Gestión Multi-Sesión**: Ejecuta y administra múltiples sesiones de automatización de navegador simultáneamente
- **Interfaz Gráfica Profesional**: Interfaz moderna basada en PyQt6 con tema oscuro
- **Integración con LM Studio**: Conecta con modelos LLM locales a través de LM Studio (Llama 2, Mistral, Phi-3, Qwen, Gemma, etc.)
- **Automatización del Navegador**: Potenciado por Playwright para control confiable del navegador
- **Paralelismo con QThreadPool**: Ejecución paralela segura de sesiones (Fase 2)
- **Detección Automática de Modelos**: Detecta automáticamente los modelos cargados en LM Studio

### Características Anti-Detección
- **Huella Digital de Dispositivo**: Perfiles de dispositivo personalizables (Windows, Android)
- **Ruido en Canvas/WebGL**: Inyecta ruido para prevenir fingerprinting de canvas
- **Protección WebRTC**: Bloquea fugas de IP por WebRTC
- **Suplantación de Contexto de Audio**: Aleatoriza huellas digitales de audio
- **Aleatorización de User-Agent**: Rota user agents de pools predefinidos
- **Suplantación de Huella Digital TLS/JA3**: Imita firmas TLS de navegadores (Fase 2)
- **Suplantación de WebGPU**: Suplanta información de GPU (Fase 2)
- **Sobrescritura de Client Hints**: Personaliza client hints del navegador (Fase 2)
- **Suplantación de Fuentes**: Lista de fuentes personalizada para evitar fingerprinting (Fase 2)

### Gestión de Proxies
- **Pool de Proxies**: Administra un pool de proxies con rotación
- **Múltiples Protocolos**: Soporte para proxies HTTP, HTTPS y SOCKS5
- **Seguimiento de Salud**: Monitorea tasas de éxito/fallo de proxies
- **Rotación Inteligente**: Selección round-robin, aleatoria o por mejor rendimiento
- **Validación de Proxies**: Prueba proxies antes de usar (Fase 2)
- **Auto-desactivación**: Desactiva automáticamente proxies fallidos (Fase 2)

### Simulación de Comportamiento (Fase 2)
- **Movimiento Aleatorio del Ratón**: Movimiento de ratón tipo humano con jitter configurable
- **Hover Aleatorio**: Simula comportamiento de hover natural
- **Simulación de Desplazamiento**: Patrones de desplazamiento realistas
- **Simulación de Escritura**: Retrasos variables entre teclas con simulación de errores
- **Tiempo Inactivo**: Pausas aleatorias entre acciones
- **Acciones Aleatorias**: Probabilidad configurable para interacciones aleatorias

### Manejo de CAPTCHA (Fase 2)
- **Integración con 2Captcha**: Resolución automática de CAPTCHA
- **Múltiples Proveedores**: Soporte para 2captcha, anticaptcha, capsolver
- **Tipos Soportados**: reCAPTCHA v2/v3, hCaptcha
- **Almacenamiento Seguro**: Claves API almacenadas de forma segura vía keyring

### Configuración de Sesión
- **Ajustes de Comportamiento**: Configura modelo LLM, tiempos y acciones habilitadas
- **Configuración de LM Studio**: URL del servidor, temperatura, máximo de tokens
- **Sesiones Persistentes**: Guarda cookies y estado del navegador entre ejecuciones
- **Rutinas Personalizadas**: Define rutinas de automatización predefinidas (YAML/JSON)
- **Monitoreo de Recursos**: Visualización en tiempo real de uso de CPU y RAM
- **Lógica de Reintentos**: Reintentos configurables con retroceso exponencial (Fase 2)
- **Registro Avanzado**: Archivos de registro rotativos por sesión (Fase 2)

## 📋 Requisitos

- Windows 10 o Windows 11
- Python 3.10 o superior
- 8GB de RAM mínimo (16GB recomendados para múltiples sesiones)
- **LM Studio** (para integración con LLM local)
- Docker Desktop (opcional, para escalabilidad)
- AWS CLI (opcional, para escalabilidad cloud)

### Requisitos de Hardware para LM Studio

LM Studio ejecuta modelos de lenguaje localmente. Los requisitos dependen del modelo:

| Modelo | RAM Mínima | RAM Recomendada | VRAM GPU |
|--------|------------|-----------------|----------|
| Phi-3 Mini (3.8B) | 6 GB | 8 GB | 4 GB |
| Llama 2 7B | 8 GB | 16 GB | 6 GB |
| Mistral 7B | 8 GB | 16 GB | 6 GB |
| Llama 2 13B | 16 GB | 24 GB | 10 GB |

## 🛠️ Instalación

### Windows

1. Clona el repositorio:
```cmd
git clone https://github.com/yourusername/botsos.git
cd botsos/botsos_lmstudio
```

2. Ejecuta el script de instalación:
```cmd
install_deps.bat
```

3. **Instala y configura LM Studio:**

   a. Descarga LM Studio desde [lmstudio.ai](https://lmstudio.ai)
   
   b. Instala y abre LM Studio
   
   c. En la pestaña "Search", busca y descarga un modelo compatible:
      - **Recomendados para 8GB RAM:**
        - `TheBloke/Llama-2-7B-Chat-GGUF`
        - `TheBloke/Mistral-7B-Instruct-v0.2-GGUF`
        - `microsoft/Phi-3-mini-4k-instruct-gguf`
      - **Recomendados para 16GB+ RAM:**
        - `TheBloke/Llama-2-13B-Chat-GGUF`
        - `TheBloke/CodeLlama-7B-Instruct-GGUF`
   
   d. En el panel izquierdo, selecciona "Local Server"
   
   e. Selecciona el modelo descargado
   
   f. Haz clic en "Start Server"
   
   g. El servidor estará disponible en: `http://localhost:1234`

4. Verifica la instalación:
```cmd
python main.py --check-system
```

## 🎮 Uso

### Iniciando la Aplicación

```cmd
REM Activar entorno virtual
venv\Scripts\activate

REM Ejecutar la aplicación
python main.py

REM Ver opciones disponibles
python main.py --help
```

### Opciones de Línea de Comandos

```
python main.py                 # Iniciar la aplicación
python main.py --version       # Mostrar versión
python main.py --check-system  # Verificar requisitos del sistema
python main.py --debug         # Modo debug con logging detallado
```

### Configurando LM Studio en la Aplicación

1. Asegúrese de que LM Studio esté ejecutándose con un modelo cargado
2. En la aplicación, vaya a la pestaña "🎮 Comportamientos"
3. Verifique que la URL de LM Studio sea correcta (por defecto: `http://localhost:1234/v1`)
4. Haga clic en "🔄 Detectar Modelos" para ver los modelos disponibles
5. Seleccione el modelo deseado
6. Ajuste la temperatura y máximo de tokens según sus necesidades

### Creando una Sesión

1. Haz clic en "➕ Agregar Sesión" en la barra lateral
2. Configura la sesión en las pestañas:
   - **Comportamientos**: Configura modelo LLM (LM Studio), tiempos y acciones habilitadas
   - **Proxy/IP**: Configura ajustes de proxy si es necesario
   - **Huella Digital**: Elige preset de dispositivo y opciones de suplantación
   - **Suplantación Avanzada**: Configura TLS, WebGPU y ruido de canvas (Fase 2)
   - **Simulación de Comportamiento**: Configura movimiento del ratón, velocidad de escritura y tiempos (Fase 2)
   - **CAPTCHA**: Habilita resolución automática de CAPTCHA (Fase 2)
3. Haz clic en "💾 Guardar Configuración"
4. Haz clic en "▶️ Iniciar Seleccionada" para ejecutar la sesión

### Usando Rutinas Predefinidas

Edita el archivo `config/rutinas.json` para definir rutinas de automatización:

```json
{
  "rutinas": {
    "mi_rutina": {
      "id": "mi_rutina",
      "nombre": "Mi Rutina Personalizada",
      "descripcion": "Descripción de lo que hace esta rutina",
      "acciones": ["buscar", "reproducir", "like"],
      "parametros": {
        "query": "término de búsqueda",
        "tiempo_reproduccion_sec": 60
      }
    }
  }
}
```

## 📁 Estructura del Proyecto

```
botsos_lmstudio/
├── main.py                     # Punto de entrada de la aplicación
├── VERSION                     # Versión actual (1.0.0)
├── requirements.txt            # Dependencias de Python
├── pytest.ini                  # Configuración de pytest
├── install_deps.bat            # Script de instalación para Windows
├── basebot.py                  # Bot de ejemplo con LM Studio
├── config/
│   ├── devices.json            # Presets de huella digital de dispositivos
│   ├── default_config.json     # Configuración por defecto de sesiones
│   └── rutinas.json            # Rutinas de automatización predefinidas
├── src/
│   ├── __init__.py
│   ├── session_manager_gui.py  # Aplicación GUI principal
│   ├── session_config.py       # Modelo de configuración de sesión
│   ├── proxy_manager.py        # Gestión de pool de proxies
│   ├── fingerprint_manager.py  # Manejo de huellas digitales
│   ├── browser_session.py      # Lógica de automatización del navegador
│   ├── advanced_features.py    # Características anti-detección avanzadas
│   ├── account_manager.py      # Gestión de cuentas con encriptación
│   ├── scaling_manager.py      # Escalabilidad Docker/AWS
│   ├── analytics_manager.py    # Métricas y analíticas Prometheus
│   ├── scheduler_manager.py    # Programación de tareas (APScheduler)
│   ├── ml_proxy_selector.py    # Selección de proxy con ML
│   ├── windows_manager.py      # Gestión específica de Windows (UAC, Docker)
│   ├── plugin_system.py        # Sistema de plugins de evasión
│   ├── help_system.py          # Tooltips, tutorial y documentación
│   └── packaging_manager.py    # Empaquetado con PyInstaller
├── plugins/                    # Plugins de evasión (YAML/JSON)
├── tests/                      # Suite de pruebas pytest
│   └── test_core.py
├── data/                       # Almacenamiento de datos persistentes
├── logs/                       # Registros de la aplicación
└── browser_context/            # Datos de sesión del navegador
```

## 🔧 Configuración de LM Studio

### Modelos Recomendados

Para BotSOS-LMStudio, recomendamos los siguientes modelos basados en sus recursos:

#### Para equipos con 8GB RAM
- **Phi-3 Mini 4k** - Rápido y eficiente, ideal para tareas simples
- **Llama 2 7B Chat Q4** - Buen balance entre calidad y rendimiento
- **Mistral 7B Instruct Q4** - Excelente para instrucciones

#### Para equipos con 16GB+ RAM
- **Llama 2 13B Chat Q4** - Mayor capacidad de razonamiento
- **CodeLlama 7B Instruct** - Ideal para tareas técnicas

### Configuración del Servidor

En LM Studio:
1. Seleccione "Local Server" en el panel izquierdo
2. Configure las opciones del servidor:
   - **Port**: 1234 (por defecto)
   - **CORS**: Habilitado
   - **Request Queuing**: Habilitado para múltiples sesiones
3. Ajuste los parámetros de generación según sus necesidades

## 🧪 Pruebas

Ejecutar la suite de pruebas:

```cmd
pytest tests/ -v
```

Ejecutar pruebas con cobertura:

```cmd
pytest tests/ -v --cov=src --cov-report=html
```

## 📦 Empaquetado

Para crear un ejecutable standalone:

```cmd
python -c "from src.packaging_manager import PackagingManager; pm = PackagingManager(); print(pm.build())"
```

O usando PyInstaller directamente:

```cmd
pyinstaller BotSOS.spec --noconfirm
```

## ⚙️ Configuración

### Presets de Dispositivo (config/devices.json)

Personaliza huellas digitales de dispositivo con diferentes perfiles:
- Windows Desktop
- Android Mobile

### Configuración por Defecto (config/default_config.json)

Configura valores por defecto para:
- Configuración de LM Studio
- Comportamiento de sesión
- Configuración de proxy
- Opciones de huella digital
- Límites de recursos
- Registro

## 🔍 Solución de Problemas

### LM Studio no se conecta

1. Verifique que LM Studio esté ejecutándose
2. Asegúrese de que el servidor local esté iniciado (panel "Local Server")
3. Verifique que el puerto 1234 no esté bloqueado
4. Compruebe la URL en la aplicación: `http://localhost:1234/v1`

### El modelo no responde

1. Verifique que haya un modelo cargado en LM Studio
2. Asegúrese de tener suficiente RAM disponible
3. Intente con un modelo más pequeño (Q4 en lugar de Q8)

### Error de memoria

1. Cierre otras aplicaciones para liberar RAM
2. Use un modelo más pequeño
3. Reduzca el número de sesiones simultáneas

## ⚠️ Aviso Legal

Esta herramienta está destinada únicamente para propósitos educativos y de prueba. Por favor asegúrate de cumplir con los términos de servicio de cualquier sitio web con el que interactúes. Los desarrolladores no son responsables por cualquier uso indebido de este software.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor siéntete libre de enviar issues y pull requests.

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- [Playwright](https://playwright.dev/) - Framework de automatización de navegador
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - Framework de GUI
- [LM Studio](https://lmstudio.ai/) - Runtime de LLM local con GUI
- [OpenAI](https://openai.com/) - Especificación de API
- [2Captcha](https://2captcha.com/) - Servicio de resolución de CAPTCHA
