# Visio Agent - AI-Powered Technical Diagram Generator

<p align="center">
  <img src="/docs/images/visio-agent-logo.png" alt="Visio Agent Logo" width="200"/>
</p>

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Detailed Setup Instructions](#detailed-setup-instructions)
   - [Windows Setup](#windows-setup)
   - [macOS Setup](#macos-setup)
5. [Configuration](#configuration)
6. [Usage Guide](#usage-guide)
7. [Function-Specific Examples](#function-specific-examples)
8. [Troubleshooting](#troubleshooting)
9. [Development](#development)
10. [Security](#security)
11. [Support](#support)
12. [Contributing](#contributing)
13. [License](#license)
14. [Acknowledgments](#acknowledgments)

## Overview
Visio Agent is an AI-powered system that automates the creation and optimization of technical diagrams using Microsoft Visio. It features intelligent connector routing, collaborative editing, and automated diagram validation. The system integrates multiple AI services and technologies to provide a comprehensive solution for technical diagram generation, including:

- **AI-Powered Diagram Generation**: Intelligent component placement, automated connector routing, and style optimization
- **Document Processing**: Advanced OCR and document analysis using Jina AI
- **Knowledge Management**: RAG (Retrieval-Augmented Generation) memory for context-aware diagram generation
- **Collaborative Features**: Real-time editing and version control
- **Validation & Quality Assurance**: Automated diagram validation and quality scoring

## Prerequisites
Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- Node.js 14 or higher
- Docker Desktop (20.10.0 or higher)
- Microsoft Visio 2019 or higher (licensed version)
- Git 2.x or higher

## Quick Start
```bash
# Clone the repository
git clone https://github.com/Saml1211/visio-agent.git
cd visio-agent

# Set up environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start services
docker-compose up -d
uvicorn src.api.main:app --reload
cd src/frontend && npm start
```

## Detailed Setup Instructions

### Windows Setup
1. Install Python 3.8+ from [python.org](https://www.python.org/)
2. Install Node.js from [nodejs.org](https://nodejs.org/)
3. Install Docker Desktop from [docker.com](https://www.docker.com/)
4. Install Visual C++ Build Tools
5. Install Microsoft Visio 2019+
6. Clone the repository and set up virtual environment:
```bash
git clone https://github.com/Saml1211/visio-agent.git
cd visio-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements-win.txt
```

### macOS Setup
1. Install Homebrew:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
2. Install dependencies:
```bash
brew install python@3.8 node docker
brew install tesseract
```
3. Clone the repository and set up virtual environment:
```bash
git clone https://github.com/Saml1211/visio-agent.git
cd visio-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements-mac.txt
```

## Configuration

### Environment Variables

Create `.env` file from template:
```bash
cp .env.example .env
```

#### Required Variables
| Variable | Description | Validation |
|----------|-------------|------------|
| `JWT_SECRET` | JWT token signing secret | 32+ character random string |
| `VISIO_LICENSE_KEY` | Valid Visio commercial license | Active Visio 2021+ subscription |
| `API_BASE_URL` | Backend server URL | Valid HTTP/HTTPS URL |

#### AI Service Requirements
| Variable | Provider | Required For | Example |
|----------|----------|--------------|---------|
| `OPENAI_API_KEY` | OpenAI | GPT-based analysis | `sk-...` |
| `HUGGINGFACE_API_KEY` | HuggingFace | OSS model alternatives | `hf_...` |
| `DEEPSEEK_API_KEY` | Deepseek | Code analysis | `ds_...` |

#### Optional Settings
```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Visio Rendering
MAX_ZOOM_LEVEL=3.0
MIN_ZOOM_LEVEL=0.5
VISIO_STYLE_RULES=config/visio_style_rules

# Security
CORS_ORIGINS=["http://localhost:3000"]
```

### Validation Script
A pre-configured validation script ensures proper configuration:
```bash
python scripts/validate_env.py
```

## Usage Guide

### 1. Starting the Application
```bash
# Start all services
docker-compose up -d

# Start backend
cd src
uvicorn api.main:app --reload

# Start frontend
cd src/frontend
npm start
```

### 2. Creating Your First Diagram
1. Navigate to `http://localhost:3000`
2. Click "New Diagram"
3. Choose a template
4. Add components using the sidebar
5. Let AI optimize the layout
6. Save and export

### 3. Collaborative Features
- Share diagram URL with team members
- See real-time cursor positions
- Track changes in version history
- Add comments and feedback

## Function-Specific Examples

### Generate BOM Report
```python
from src.services.bom_service import BOMGenerator

bom = BOMGenerator()
report = bom.generate(components)
print(report)
```

### Run Data Validation
```python
from src.services.validation_service import DataValidator

validator = DataValidator()
results = validator.validate(components)
print(results)
```

### Test RAG Memory
```python
from src.services.rag_memory_service import RAGMemoryService

rag = RAGMemoryService()
results = rag.query("Find similar AV systems", top_k=3)
print(results)
```

## Shape Identification and Classification

The system includes a robust shape identification and classification system that uses deep learning to recognize and categorize Visio shapes. Key features:

- **Model Architecture**: ResNet50-based CNN with custom classification head
- **Training Data**: Diverse dataset of Visio shapes categorized by:
  - Device type (display, speaker, microphone, etc.)
  - Specific device properties
  - Connection point types
- **Accuracy**: >95% on test dataset
- **Integration**: Seamlessly integrated with data analysis and diagram generation

### Training the Model
```python
from src.services.shape_classifier import ShapeClassifierService

classifier = ShapeClassifierService()
classifier.train(Path("data/shapes"))
classifier.save_model(Path("models/shape_classifier.pth"))
```

### Using the Classifier
```python
classifier = ShapeClassifierService(Path("models/shape_classifier.pth"))
classification = classifier.classify_shape(image)
print(classification)
```

## Troubleshooting

### Common Issues
1. **Database Connection Failed**
```bash
docker-compose ps
docker-compose logs supabase
```

2. **Visio Integration Issues**
- Ensure Visio is installed and licensed
- Check COM server registration
- Verify file permissions

3. **Setup Wizard Stuck**
- Clear browser cache
- Check network connectivity
- Verify environment variables

## Development

### Running Tests
```bash
# Backend tests
pytest

# Frontend tests
cd src/frontend
npm test
```

### Adding New Features
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

## Security Considerations

### API Key Security
- Never commit API keys to version control
- Use environment variables or secure vaults for key storage
- Rotate API keys periodically (recommended every 90 days)
- Set up IP restrictions where supported (OpenAI, Azure)
- Monitor API key usage regularly for unusual patterns
- Use separate API keys for development and production

## Support
- GitHub Issues: [Report bugs](https://github.com/Saml1211/visio-agent/issues)
- Documentation: [Full docs](/docs/index.md)
- Discord: [Join community](https://discord.com/invite/visio-agent-community)

## Contributing
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License
MIT License - see [/LICENSE](/LICENSE) file

## Acknowledgments
The Visio Agent project builds upon and integrates with several powerful technologies and services. We would like to acknowledge and thank the following:

- **OpenAI** for providing the core AI models that power our natural language processing and diagram generation capabilities
- **Supabase** for providing the database and backend infrastructure that enables secure data storage and real-time collaboration
- **Microsoft** for the Visio SDK that enables deep integration with Visio's diagramming capabilities
- **Jina AI** for their advanced document processing and OCR capabilities that enable us to extract information from various document formats
- **Deepseek** for their advanced language models that enhance our system's understanding of technical documentation
- **Firecrawl** for their web crawling and content extraction capabilities that enable us to process web-based technical documentation
- **Browserbase** for their browser automation capabilities that enable us to interact with web-based technical resources
- **Chroma** for their vector database capabilities that power our RAG memory system
- **Hugging Face** for their transformer models and model hosting capabilities
- **ScreenPipe** for their screen capture and analysis capabilities that enable us to process visual technical documentation
- **n8n** for their workflow automation capabilities that help streamline our internal processes
- **Ollama** for their local LLM capabilities that provide an alternative to cloud-based AI services
- **Azure Computer Vision** for their advanced image analysis capabilities that enhance our OCR and document processing

We are grateful to all these organizations and communities for their contributions to the open source and AI ecosystems that make projects like Visio Agent possible.

## AV-Specific Configuration

```python
# config/av_models.yaml
model_assignments:
  schematic_validation: vertexai/vision@imagetext-av-1.0
  component_selection: vertexai/generative@gemini-av-1.2
  signal_flow_analysis: openai/gpt-4-vision-av
  compliance_checking: vertexai/generative@gemini-compliance-1.1
```

Key AV Considerations:
1. Pre-configured AV component library
2. CTS/AVIXA compliance templates
3. Signal flow validation rules
4. Rack space optimization profiles
5. Cable management best practices
