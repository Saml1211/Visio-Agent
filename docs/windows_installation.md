# Windows Installation Guide

This guide provides detailed instructions for installing and running the Visio Agent on Windows systems.

## System Requirements

- Windows 10 or Windows 11 (64-bit)
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- Administrator privileges

## Required Software

1. **Python 3.8+**
2. **Node.js 16+ LTS**
3. **Microsoft Visio 2019 or later**
4. **Git for Windows**
5. **Microsoft Visual C++ Build Tools**

## Step-by-Step Installation

### 1. Install Required Software

#### Python Installation
1. Download [Python 3.8 or later](https://www.python.org/downloads/windows/)
2. Run the installer
   - ✅ Check "Add Python to PATH"
   - ✅ Enable "py launcher"
   - ✅ Enable "pip package installer"
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

#### Node.js Installation
1. Download [Node.js 16+ LTS](https://nodejs.org/)
2. Run the installer with default settings
3. Verify installation:
   ```cmd
   node --version
   npm --version
   ```

#### Git Installation
1. Download [Git for Windows](https://git-scm.com/download/windows)
2. Run the installer with default settings
3. Verify installation:
   ```cmd
   git --version
   ```

#### Visual C++ Build Tools
1. Download [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Run the installer
3. Select "Desktop development with C++"
4. Install selected components

### 2. Microsoft Visio Setup

1. Install Microsoft Visio 2019 or later
2. Ensure you have a valid Microsoft 365 account
3. Launch Visio once to complete initial setup
4. Enable macros and ActiveX controls if prompted

### 3. Project Setup

1. **Clone Repository**:
   ```cmd
   git clone https://github.com/yourusername/visio-agent.git
   cd visio-agent
   ```

2. **Create Virtual Environment**:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```cmd
   python -m pip install --upgrade pip
   pip install wheel setuptools
   pip install -r requirements.txt
   ```

   If you encounter SSL errors:
   ```cmd
   pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

4. **Configure Environment**:
   ```cmd
   copy .env.example .env
   ```
   Edit `.env` file:
   - Set `VISIO_EXE_PATH` (typically `C:\Program Files\Microsoft Office\root\Office16\VISIO.EXE`)
   - Configure API keys and other settings

5. **Run Application**:
   ```cmd
   python run.py
   ```

## Troubleshooting

### Common Issues and Solutions

1. **Python Path Issues**
   ```cmd
   # Add to System Environment Variables:
   C:\Users\YourUsername\AppData\Local\Programs\Python\Python3x
   C:\Users\YourUsername\AppData\Local\Programs\Python\Python3x\Scripts
   ```

2. **DLL Load Failures**
   - Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
   - Restart computer after installation

3. **COM Automation Errors**
   ```cmd
   # Run PowerShell as Administrator:
   Set-ExecutionPolicy RemoteSigned
   ```

4. **Package Installation Errors**
   ```cmd
   pip install --no-cache-dir -r requirements.txt
   ```

5. **Visio Integration Issues**
   - Run Visio as administrator once
   - Check Office COM automation:
     ```cmd
     # Run PowerShell as Administrator:
     Get-ItemProperty "HKLM:\SOFTWARE\Classes\CLSID\{00020970-0000-0000-C000-000000000046}"
     ```

### Performance Optimization

1. **Windows Defender Exclusions**:
   - Add project directory to Windows Security exclusions
   - Exclude Python interpreter path

2. **System Performance**:
   ```cmd
   # Run PowerShell as Administrator:
   powercfg /setactive SCHEME_MIN
   ```

3. **Memory Management**:
   - Close unnecessary applications
   - Monitor memory usage with Task Manager

## Additional Resources

- [Python Windows Setup Guide](https://docs.python.org/3/using/windows.html)
- [Node.js Windows Guide](https://nodejs.org/en/download/package-manager/#windows)
- [Visual Studio Build Tools Guide](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
- [Microsoft Visio Documentation](https://docs.microsoft.com/en-us/office/client-developer/visio/visio-home)

## Support

If you encounter any issues:
1. Check the [Windows Troubleshooting Guide](docs/windows_troubleshooting.md)
2. Search [existing issues](https://github.com/yourusername/visio-agent/issues)
3. Create a new issue with:
   - Windows version
   - Python version
   - Error messages
   - Steps to reproduce 