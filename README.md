# Visio Agent - AI-Powered Technical Diagram Generator

<p align="center">
  <img src="docs/images/visio-agent-logo.png" alt="Visio Agent Logo" width="200"/>
</p>

## Overview

Visio Agent is an AI-powered system that automates the creation and optimization of technical diagrams using Microsoft Visio. It features intelligent connector routing, collaborative editing, and automated diagram validation.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- Node.js 14 or higher
- Docker Desktop
- Microsoft Visio (licensed version)
- Git

## Quick Start

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/visio-agent.git
cd visio-agent
```

2. **Set Up Environment**
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd src/frontend
npm install
cd ../..
```

3. **Configure Local Database**
```bash
# Start Supabase locally
docker-compose up -d
```

4. **First-Time Setup**
- Open your browser and navigate to `http://localhost:3000`
- Follow the setup wizard to configure:
  - Database location
  - Supabase connection
  - Security settings
  - Visio integration

## Project Structure
```
visio-agent/
├── src/
│   ├── api/                 # FastAPI backend
│   ├── frontend/           # React frontend
│   ├── services/           # Core services
│   │   ├── ai/            # AI services
│   │   ├── storage/       # Storage services
│   │   └── visio/         # Visio integration
│   └── config/            # Configuration files
├── tests/                 # Test suites
├── docs/                  # Documentation
└── docker-compose.yml     # Docker configuration
```

## Key Features

### 1. AI-Powered Diagram Generation
- Intelligent component placement
- Automated connector routing
- Style optimization
- Layout suggestions

### 2. Collaborative Editing
- Real-time cursor tracking
- Concurrent editing support
- Version control
- Change history

### 3. Security
- Encrypted configuration storage
- Role-based access control
- Secure credential management
- Audit logging

## Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
SUPABASE_URL=http://localhost:8000
SUPABASE_KEY=your-supabase-key
JWT_SECRET=your-jwt-secret
CONFIG_KEY=your-config-key
VISIO_HOST=http://localhost:3000
```

### Database Setup
The first-time setup wizard will guide you through:
1. Choosing database location
2. Setting up Supabase locally
3. Configuring security policies
4. Testing connections

## Usage Guide

### 1. Starting the Application
```bash
# Start all services
docker-compose up -d

# Start backend
cd src
uvicorn api.main:app --reload

# Start frontend (in another terminal)
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

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
```bash
# Check Supabase status
docker-compose ps

# View logs
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

- Store sensitive data in `.env`
- Use secure vault for credentials
- Enable audit logging
- Regular security updates
- Proper access control

## Support

- GitHub Issues: [Report bugs](https://github.com/yourusername/visio-agent/issues)
- Documentation: [Full docs](docs/index.md)
- Discord: [Join community](https://discord.gg/visio-agent)

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT License - see [LICENSE](LICENSE) file

## Acknowledgments

- OpenAI for AI models
- Supabase for database
- Microsoft for Visio SDK# visio-agent
