# LLD Automation Project

A powerful automation system for generating and validating Low Level Design (LLD) diagrams using AI and computer vision.

## Features

- 🎨 Automated Visio diagram generation from various input sources
- 🤖 AI-powered diagram validation and enhancement
- 📊 Comprehensive validation of diagram elements and relationships
- 🔍 Advanced computer vision for diagram analysis
- 🔄 Real-time collaboration and feedback
- 📱 Cross-platform support (Windows and macOS)

## Prerequisites

### Common Requirements
- Python 3.8 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Windows-Specific Requirements
- Microsoft Visio 2019 or higher
- Visual C++ build tools
- Tesseract OCR (for text recognition)

### macOS-Specific Requirements
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required system dependencies
brew install mupdf
brew install opencv
brew install tesseract
```

## Installation

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/lld-automation.git
cd lld-automation
```

2. **Create and Activate Virtual Environment**

For Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

For macOS:
```bash
python -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**

For Windows:
```bash
pip install -r requirements-win.txt
```

For macOS:
```bash
pip install -r requirements-mac.txt
```

For development:
```bash
pip install -r requirements-dev.txt
```

4. **Validate Installation**
```bash
python validate_dependencies.py
```

## Project Structure

```
lld-automation/
├── src/
│   ├── api/              # FastAPI application and endpoints
│   ├── core/             # Core business logic
│   ├── services/         # External service integrations
│   ├── utils/            # Utility functions and helpers
│   └── validation/       # Diagram validation logic
├── tests/                # Test suite
├── docs/                 # Documentation
├── examples/            # Example diagrams and usage
└── scripts/             # Utility scripts
```

## Usage

1. **Start the API Server**
```bash
uvicorn src.api.main:app --reload
```

2. **Access the API Documentation**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

3. **Basic Usage Example**
```python
from src.core.validator import DeepValidator
from src.utils.visio import VisioAutomation

# Initialize validator
validator = DeepValidator()

# Load and validate diagram
result = validator.validate_diagram("path/to/diagram.vsdx")
print(result.summary())
```

## Development

1. **Setup Development Environment**
```bash
pip install -r requirements-dev.txt
pre-commit install
```

2. **Run Tests**
```bash
pytest tests/
```

3. **Code Quality Checks**
```bash
# Format code
black .
isort .

# Run linters
flake8
mypy .

# Run security checks
bandit -r .
safety check
```

## API Documentation

Detailed API documentation is available at:
- [API Reference](docs/api-reference.md)
- [Validation Rules](docs/validation-rules.md)
- [Integration Guide](docs/integration-guide.md)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
1. Check the [Documentation](docs/)
2. Search [existing issues](https://github.com/yourusername/lld-automation/issues)
3. Create a new issue if needed

## Acknowledgments

- OpenAI for GPT models
- Microsoft for Visio automation support
- The open-source community for various tools and libraries
