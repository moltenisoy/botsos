@echo off
REM BotSOS-LMStudio - Script de Instalación para Windows
REM Este script configura el entorno de desarrollo
REM Versión adaptada para usar LM Studio como backend de LLM

echo ========================================
echo BotSOS-LMStudio - Administrador de Sesiones Multi-Modelo
echo Backend: LM Studio (API compatible con OpenAI)
echo Script de Instalacion
echo ========================================
echo.

REM Verificar instalación de Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en PATH
    echo Por favor instale Python 3.11+ desde https://python.org
    pause
    exit /b 1
)

echo [1/5] Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Fallo al crear el entorno virtual
    pause
    exit /b 1
)

echo [2/5] Activando entorno virtual...
call venv\Scripts\activate.bat

echo [3/5] Actualizando pip...
python -m pip install --upgrade pip

echo [4/5] Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Fallo al instalar dependencias
    pause
    exit /b 1
)

echo [5/5] Instalando navegadores de Playwright...
playwright install chromium
if errorlevel 1 (
    echo ADVERTENCIA: Fallo al instalar navegadores de Playwright
    echo Puede que necesite ejecutar 'playwright install' manualmente
)

echo.
echo ========================================
echo Instalacion Completa!
echo ========================================
echo.
echo Para ejecutar la aplicacion:
echo   1. Active el entorno virtual: venv\Scripts\activate
echo   2. Ejecute: python main.py
echo.
echo ========================================
echo IMPORTANTE: Configuracion de LM Studio
echo ========================================
echo.
echo Asegurese de que LM Studio este instalado y configurado:
echo.
echo   1. Descargue LM Studio desde: https://lmstudio.ai
echo.
echo   2. Instale y abra LM Studio
echo.
echo   3. Descargue un modelo compatible (recomendados):
echo      - Llama 2 7B Chat
echo      - Mistral 7B Instruct
echo      - Phi-3 Mini
echo      - Qwen 7B Chat
echo      - Gemma 7B
echo.
echo   4. En LM Studio, vaya a "Local Server" (panel izquierdo)
echo.
echo   5. Seleccione el modelo que descargo
echo.
echo   6. Haga clic en "Start Server"
echo.
echo   El servidor estara disponible en: http://localhost:1234
echo.
echo ========================================
echo Verificacion del Sistema
echo ========================================
echo.
echo Ejecute el siguiente comando para verificar la instalacion:
echo   python main.py --check-system
echo.
pause
