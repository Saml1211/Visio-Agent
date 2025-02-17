# Windows Installation Guide

This guide provides detailed instructions for installing and configuring the Visio Agent on Windows systems.

## Prerequisites

### Required Software
1. **Windows 10 or 11**
   - Windows 10 version 1903 or later
   - Windows 11 (any version)
   - Both 64-bit versions only

2. **Microsoft Visio**
   - Visio 2019 or later
   - Professional or Standard edition
   - Must be installed and activated

3. **Python Environment**
   - Python 3.8 or later (64-bit)
   - pip (latest version)
   - virtualenv or venv

4. **Git**
   - Latest version from https://git-scm.com/
   - Git Credential Manager configured

5. **Visual Studio Build Tools**
   - Visual C++ build tools
   - Windows 10/11 SDK

## System Configuration

### 1. Enable Long Path Support

Windows has a default path length limit of 260 characters. The Visio Agent may require longer paths, so we need to enable long path support:

1. Open PowerShell as Administrator
2. Run the following command:
   ```powershell
   Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
                    -Name "LongPathsEnabled" -Value 1
   ```
3. Restart your computer

### 2. Configure Python

1. **Install Python**
   - Download Python from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation
   - Choose "Customize installation"
   - Select all optional features
   - Install for all users

2. **Verify Installation**
   ```bash
   python --version
   pip --version
   ```

3. **Update pip**
   ```bash
   python -m pip install --upgrade pip
   ```

### 3. Install Build Tools

1. **Using Visual Studio Installer**
   - Download the [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Run the installer
   - Select "Desktop development with C++"
   - Ensure "Windows 10/11 SDK" is selected
   - Install

2. **Alternative: Using Chocolatey**
   ```powershell
   # Install Chocolatey first if not installed
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
   
   # Install build tools
   choco install visualstudio2019buildtools
   choco install visualstudio2019-workload-vctools
   ```

## Installation Steps

### 1. Prepare Installation Directory

Choose a location with a short path, for example:
```bash
mkdir C:\Projects
cd C:\Projects
```

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/visio-agent.git
cd visio-agent
```

### 3. Create Virtual Environment

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 4. Install Dependencies

```bash
# Upgrade pip in virtual environment
python -m pip install --upgrade pip

# Install wheels for binary packages
pip install wheel

# Install core Microsoft dependencies first
pip install O365 msal msgraph-core

# Install PyTorch with CUDA support (if you have an NVIDIA GPU)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Install remaining dependencies
pip install -r requirements.txt
```

Note: The PyTorch installation command above installs the latest version with CUDA 12.1 support. If you need a different CUDA version, adjust the URL accordingly (e.g., cu118 for CUDA 11.8).

### 5. Verify Windows Requirements

```bash
python scripts/windows_checks.py
```

This script will verify:
- Windows version compatibility
- Microsoft Visio installation
- Long path support
- Other system requirements

### 6. Configure Environment

1. Copy example environment file:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` with appropriate values:
   - Set paths using Windows-style paths (use \\ or /)
   - Configure Visio-specific settings
   - Set up API keys and credentials

### 7. Validate Installation

```bash
python validate_dependencies.py
```

## Troubleshooting

### Common Issues

1. **Path Length Errors**
   ```
   ERROR: Could not install packages [...] filename too long
   ```
   **Solution:**
   - Enable long path support as described above
   - Move project to a shorter path
   - Use `pip install --no-cache-dir` to avoid temp directory issues

2. **Visio Not Detected**
   ```
   Error: Microsoft Visio installation not found
   ```
   **Solutions:**
   - Verify Visio is installed for all users
   - Repair Visio installation
   - Run as administrator
   - Check registry permissions

3. **Build Errors**
   ```
   error: Microsoft Visual C++ 14.0 or greater is required
   ```
   **Solutions:**
   - Install/repair Visual Studio Build Tools
   - Use pre-built wheels:
     ```bash
     pip install --only-binary :all: -r requirements.txt
     ```

4. **Permission Errors**
   ```
   Access is denied: 'C:\\Program Files\\...'
   ```
   **Solutions:**
   - Run command prompt as Administrator
   - Check folder permissions
   - Disable Windows Defender real-time protection temporarily

### Getting Help

If you encounter issues not covered here:

1. Check the [GitHub Issues](https://github.com/yourusername/visio-agent/issues)
2. Run diagnostics:
   ```bash
   python scripts/windows_checks.py --verbose
   python validate_dependencies.py --verbose
   ```
3. Create a new issue with:
   - Windows version and build number
   - Python version
   - Visio version
   - Error messages and logs
   - Steps to reproduce

## Post-Installation

After successful installation:

1. **Test the Application**
   ```bash
   python run.py
   ```

2. **Configure Development Environment**
   - Set up VS Code or PyCharm
   - Install recommended extensions
   - Configure debugger

3. **Set Up Git Hooks**
   ```bash
   pre-commit install
   ```

4. **Review Documentation**
   - Read the API documentation
   - Check the development guidelines
   - Review security best practices

## Updating

To update an existing installation:

1. **Backup Your Environment**
   ```bash
   copy .env .env.backup
   ```

2. **Update Repository**
   ```bash
   git pull origin main
   ```

3. **Update Dependencies**
   ```bash
   .\venv\Scripts\activate
   pip install -r requirements.txt --upgrade
   ```

4. **Verify Update**
   ```bash
   python validate_dependencies.py
   python scripts/windows_checks.py
   ``` 