# Visio Agent

An advanced AI-powered system for automating the generation and maintenance of professional AV system diagrams using Microsoft Visio.

## Features

- 🤖 AI-powered diagram generation from technical documentation
- 📊 Automated AV system diagramming
- 🔄 Real-time collaboration and updates
- 🎨 Industry-standard Visio templates and stencils
- 🔍 Smart document analysis and interpretation
- 🛡️ Enterprise-grade security and authentication
- 📱 Responsive web interface

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Microsoft Visio (2019 or later)
- Microsoft 365 Account with appropriate licenses

## Windows Installation Requirements

Before installing Visio Agent on Windows, ensure your system meets the following requirements:

### System Requirements
- Windows 10 or Windows 11
- Microsoft Visio (2019 or later) installed
- Python 3.8 or later
- Git

### Windows-Specific Setup

1. **Enable Long Path Support**
   ```powershell
   # Run PowerShell as Administrator
   Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1
   ```

2. **Verify Windows Requirements**
   ```bash
   # Run from the project root
   python scripts/windows_checks.py
   ```
   This script will verify:
   - Windows version compatibility
   - Microsoft Visio installation
   - Long path support status

3. **Install Visual C++ Build Tools**
   Some dependencies require Visual C++ Build Tools. Install them using one of these methods:
   - Download from [Visual Studio Downloads](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Or using Chocolatey: `choco install visualstudio2019buildtools`

### Installation Steps for Windows

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/visio-agent.git
   cd visio-agent
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Validate Installation**
   ```bash
   python validate_dependencies.py
   ```

### Troubleshooting Windows Installation

1. **Path Length Issues**
   - If you encounter path length errors, ensure long path support is enabled
   - Consider installing in a shorter path (e.g., `C:\Projects\visio-agent`)

2. **Visio Detection Issues**
   - Verify Visio is installed for your user account
   - Try repairing the Visio installation
   - Check if Visio is accessible from Python

3. **Build Errors**
   - Ensure Visual C++ Build Tools are installed
   - Try installing wheels instead of building from source:
     ```bash
     pip install --only-binary :all: -r requirements.txt
     ```

4. **Permission Issues**
   - Run PowerShell/Command Prompt as Administrator when needed
   - Check Windows Defender or antivirus settings

For additional help with Windows-specific issues, please check our [Windows Installation Guide](docs/windows_installation.md) or open an issue on GitHub.

## Project Structure

```
visio-agent/
├── src/                    # Source code
│   ├── api/               # API endpoints
│   ├── core/              # Core business logic
│   ├── models/            # Data models
│   ├── services/          # Service layer
│   └── utils/             # Utility functions
├── tests/                 # Test suite
├── docs/                  # Documentation
├── config/               # Configuration files
├── static/               # Static assets
└── scripts/              # Utility scripts
```

## Development

### Setting Up Development Environment

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Install pre-commit hooks:
```bash
pre-commit install
```

### Running Tests

```bash
pytest
```

### Code Style

This project follows:
- PEP 8 for Python code style
- Black for code formatting
- isort for import sorting
- Flake8 for linting
- MyPy for type checking

## Documentation

Detailed documentation is available in the `docs/` directory:

- [Architecture Overview](docs/architecture.md)
- [API Documentation](docs/api.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

For security concerns, please email security@yourdomain.com

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for GPT models
- Microsoft for Visio and Graph API
- The open-source community

## Support

For support, please:
1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/yourusername/visio-agent/issues)
3. Create a new issue if needed

---

Made with ❤️ by Your Team Name
