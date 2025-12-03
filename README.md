# BotSOS - Multi-Model Session Manager

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/PyQt6-6.6+-green.svg" alt="PyQt6">
  <img src="https://img.shields.io/badge/Playwright-1.40+-orange.svg" alt="Playwright">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

A professional session manager for running multiple LLM-powered browser automation instances with advanced anti-detection features.

## 🚀 Features

### Core Functionality
- **Multi-Session Management**: Run and manage multiple browser automation sessions simultaneously
- **Professional GUI**: Modern PyQt6-based interface with dark theme
- **LLM Integration**: Connect with local LLM models via Ollama (Llama 3.1, Qwen, Mistral, etc.)
- **Browser Automation**: Powered by Playwright for reliable browser control

### Anti-Detection Features
- **Device Fingerprinting**: Customizable device profiles (Windows, macOS, Android, Linux)
- **Canvas/WebGL Noise**: Inject noise to prevent canvas fingerprinting
- **WebRTC Protection**: Block WebRTC IP leaks
- **Audio Context Spoofing**: Randomize audio fingerprints
- **User-Agent Randomization**: Rotate user agents from predefined pools

### Proxy Management
- **Proxy Pool**: Manage a pool of proxies with rotation
- **Multiple Protocols**: Support for HTTP, HTTPS, and SOCKS5 proxies
- **Health Tracking**: Monitor proxy success/failure rates
- **Smart Rotation**: Round-robin, random, or best-performance selection

### Session Configuration
- **Behavior Settings**: Configure action delays, view times, and enabled actions
- **Persistent Sessions**: Save browser cookies and state across runs
- **Custom Routines**: Define predefined automation routines (YAML/JSON)
- **Resource Monitoring**: Real-time CPU and RAM usage display

## 📋 Requirements

- Python 3.11 or higher
- Windows 11 / macOS / Linux
- 16GB RAM recommended (minimum 8GB)
- Ollama (for LLM integration)

## 🛠️ Installation

### Windows

1. Clone the repository:
```bash
git clone https://github.com/yourusername/botsos.git
cd botsos
```

2. Run the installation script:
```bash
install_deps.bat
```

3. Install Ollama from [ollama.ai](https://ollama.ai) and pull a model:
```bash
ollama pull llama3.1:8b
```

### Linux/macOS

1. Clone the repository:
```bash
git clone https://github.com/yourusername/botsos.git
cd botsos
```

2. Run the installation script:
```bash
chmod +x install_deps.sh
./install_deps.sh
```

3. Install Ollama and pull a model:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.1:8b
```

## 🎮 Usage

### Starting the Application

```bash
# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate

# Run the application
python main.py
```

### Creating a Session

1. Click "➕ Add Session" in the sidebar
2. Configure the session in the tabs:
   - **Behaviors**: Set LLM model, timing, and enabled actions
   - **Proxy/IP**: Configure proxy settings if needed
   - **Fingerprint**: Choose device preset and spoofing options
3. Click "💾 Save Configuration"
4. Click "▶️ Start Selected" to run the session

### Using Predefined Routines

Edit the `config/rutinas.json` file to define automation routines:

```json
{
  "rutinas": {
    "my_routine": {
      "id": "my_routine",
      "nombre": "My Custom Routine",
      "descripcion": "Description of what this routine does",
      "acciones": ["buscar", "reproducir", "like"],
      "parametros": {
        "query": "search term",
        "tiempo_reproduccion_sec": 60
      }
    }
  }
}
```

## 📁 Project Structure

```
botsos/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── install_deps.bat        # Windows installation script
├── install_deps.sh         # Linux/macOS installation script
├── config/
│   ├── devices.json        # Device fingerprint presets
│   ├── default_config.json # Default session settings
│   └── rutinas.json        # Predefined automation routines
├── src/
│   ├── __init__.py
│   ├── session_manager_gui.py  # Main GUI application
│   ├── session_config.py       # Session configuration model
│   ├── proxy_manager.py        # Proxy pool management
│   ├── fingerprint_manager.py  # Device fingerprint handling
│   └── browser_session.py      # Browser automation logic
├── data/                   # Persistent data storage
├── logs/                   # Application logs
└── browser_context/        # Browser session data
```

## ⚙️ Configuration

### Device Presets (config/devices.json)

Customize device fingerprints with different profiles:
- Windows Desktop
- macOS Laptop
- Android Mobile
- Linux Server

### Default Settings (config/default_config.json)

Configure default values for:
- Session behavior
- Proxy settings
- Fingerprint options
- Resource limits
- Logging

## ⚠️ Disclaimer

This tool is intended for educational and testing purposes only. Please ensure you comply with the terms of service of any websites you interact with. The developers are not responsible for any misuse of this software.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) - Browser automation framework
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [Ollama](https://ollama.ai/) - Local LLM runtime
