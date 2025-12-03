@echo off
REM BotSOS - Script de Instalación para Windows
REM Este script configura el entorno de desarrollo

echo ========================================
echo BotSOS - Administrador de Sesiones Multi-Modelo
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
echo Asegurese de que Ollama este instalado y ejecutandose:
echo   - Descargue desde: https://ollama.ai
echo   - Ejecute: ollama pull llama3.1:8b
echo.
pause
