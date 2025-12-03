#!/bin/bash
# BotSOS - Installation Script for Linux/macOS
# This script sets up the development environment

echo "========================================"
echo "BotSOS - Multi-Model Session Manager"
echo "Installation Script"
echo "========================================"
echo

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.11+ from https://python.org"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo "[2/5] Activating virtual environment..."
source venv/bin/activate

echo "[3/5] Upgrading pip..."
python -m pip install --upgrade pip

echo "[4/5] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "[5/5] Installing Playwright browsers..."
playwright install chromium
if [ $? -ne 0 ]; then
    echo "WARNING: Failed to install Playwright browsers"
    echo "You may need to run 'playwright install' manually"
fi

echo
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo
echo "To run the application:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run: python main.py"
echo
echo "Make sure Ollama is installed and running:"
echo "  - Download from: https://ollama.ai"
echo "  - Run: ollama pull llama3.1:8b"
echo
