@echo off
REM BotSOS - Installation Script for Windows
REM This script sets up the development environment

echo ========================================
echo BotSOS - Multi-Model Session Manager
echo Installation Script
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip

echo [4/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [5/5] Installing Playwright browsers...
playwright install chromium
if errorlevel 1 (
    echo WARNING: Failed to install Playwright browsers
    echo You may need to run 'playwright install' manually
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To run the application:
echo   1. Activate the virtual environment: venv\Scripts\activate
echo   2. Run: python main.py
echo.
echo Make sure Ollama is installed and running:
echo   - Download from: https://ollama.ai
echo   - Run: ollama pull llama3.1:8b
echo.
pause
