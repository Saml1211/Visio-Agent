#!/usr/bin/env python3
import subprocess
import sys
import platform
from pathlib import Path
import pkg_resources
import re
import shutil
import os
from typing import Tuple, List, Optional

def get_nvidia_smi_path() -> Optional[str]:
    """Get the path to nvidia-smi executable."""
    if platform.system() == "Windows":
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            return nvidia_smi
        # Check common Windows paths
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        paths = [
            Path(program_files) / "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe",
            Path("C:\\Windows\\System32\\nvidia-smi.exe"),
        ]
        for path in paths:
            if path.exists():
                return str(path)
    else:
        return shutil.which("nvidia-smi")
    return None

def check_cuda_windows() -> Tuple[bool, str]:
    """Check CUDA availability on Windows with improved detection."""
    if platform.system() != "Windows":
        return False, "Not Windows system"
    
    try:
        nvidia_smi = get_nvidia_smi_path()
        if not nvidia_smi:
            return False, "NVIDIA driver not found"
            
        # Check nvidia-smi
        result = subprocess.run([nvidia_smi], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "NVIDIA driver not responding"
        
        # Try multiple regex patterns for different nvidia-smi output formats
        cuda_patterns = [
            r'CUDA Version: (\d+\.\d+)',
            r'CUDA v(\d+\.\d+\.\d+)',
            r'CUDA (\d+\.\d+)',
        ]
        
        cuda_version = None
        for pattern in cuda_patterns:
            match = re.search(pattern, result.stdout)
            if match:
                cuda_version = float('.'.join(match.group(1).split('.')[:2]))
                break
                
        if cuda_version is None:
            # Try checking CUDA_PATH environment variable
            cuda_path = os.environ.get('CUDA_PATH')
            if cuda_path:
                version_file = Path(cuda_path) / 'version.txt'
                if version_file.exists():
                    with open(version_file) as f:
                        content = f.read()
                        match = re.search(r'(\d+\.\d+)', content)
                        if match:
                            cuda_version = float(match.group(1))
        
        if cuda_version is None:
            return False, "CUDA version not found"
            
        if cuda_version < 11.8:
            return False, f"CUDA version {cuda_version} is less than required 11.8"
        
        # Check available GPU memory
        memory_result = subprocess.run([nvidia_smi, '--query-gpu=memory.total', '--format=csv,noheader,nounits'], 
                                     capture_output=True, text=True)
        if memory_result.returncode == 0:
            try:
                memory = int(memory_result.stdout.strip())
                if memory < 4096:  # Less than 4GB
                    return True, f"CUDA {cuda_version} found (Warning: Low GPU memory: {memory}MB)"
            except ValueError:
                pass
        
        return True, f"CUDA {cuda_version} found"
    except FileNotFoundError:
        return False, "nvidia-smi not found"
    except Exception as e:
        return False, f"Error checking CUDA: {str(e)}"

def check_system_requirements() -> List[str]:
    """Check system requirements beyond Python packages."""
    issues = []
    
    # Check available RAM
    try:
        import psutil
        memory = psutil.virtual_memory()
        if memory.total < 8 * 1024 * 1024 * 1024:  # 8GB
            issues.append("Less than 8GB RAM available")
    except:
        issues.append("Unable to check system memory")
    
    # Check disk space
    try:
        disk = psutil.disk_usage('/')
        if disk.free < 10 * 1024 * 1024 * 1024:  # 10GB
            issues.append("Less than 10GB free disk space")
    except:
        issues.append("Unable to check disk space")
    
    # Check CPU cores
    try:
        if psutil.cpu_count() < 2:
            issues.append("Less than 2 CPU cores available")
    except:
        issues.append("Unable to check CPU cores")
    
    return issues

def validate_dependencies(python_path: Path) -> List[str]:
    """Validate installed dependencies with improved checks."""
    issues = []
    
    # Check Python version
    py_version = sys.version_info
    if py_version < (3, 8):
        issues.append(f"Python version {py_version.major}.{py_version.minor} is less than required 3.8")
    elif py_version >= (3, 12):
        issues.append(f"Python version {py_version.major}.{py_version.minor} is not yet fully supported")
    
    # Run pip check
    result = subprocess.run([str(python_path), '-m', 'pip', 'check'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        issues.extend(result.stdout.splitlines())
    
    # Check for common problematic package combinations
    try:
        import pkg_resources
        
        # Check torch and torchvision compatibility
        torch_version = pkg_resources.get_distribution('torch').version
        vision_version = pkg_resources.get_distribution('torchvision').version
        if not vision_version.startswith(torch_version.split('+')[0]):
            issues.append(f"Torch ({torch_version}) and TorchVision ({vision_version}) versions may be incompatible")
        
        # Check pydantic version compatibility with FastAPI
        pydantic_version = pkg_resources.get_distribution('pydantic').version
        if pydantic_version.startswith('1.') and float(pydantic_version.split('.')[1]) < 9:
            issues.append("Pydantic version < 1.9 may cause issues with FastAPI")
    except Exception as e:
        issues.append(f"Error checking package versions: {str(e)}")
    
    return issues

def main():
    """Main installation function."""
    # Get project root
    root = Path(__file__).parent.parent
    
    # Check system requirements first
    print("\nChecking system requirements...")
    system_issues = check_system_requirements()
    if system_issues:
        print("\nWarning: System requirement issues found:")
        for issue in system_issues:
            print(f"  - {issue}")
        proceed = input("\nDo you want to proceed with installation? (y/N): ")
        if proceed.lower() != 'y':
            print("Installation aborted.")
            sys.exit(1)
    
    # Create virtual environment
    print("\nCreating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", ".venv"], cwd=root, check=True)
    
    # Set up paths
    if sys.platform == "win32":
        python = root / ".venv" / "Scripts" / "python"
        pip = root / ".venv" / "Scripts" / "pip"
    else:
        python = root / ".venv" / "bin" / "python"
        pip = root / ".venv" / "bin" / "pip"
    
    # Check CUDA on Windows
    if platform.system() == "Windows":
        cuda_available, cuda_msg = check_cuda_windows()
        print(f"\nCUDA Status: {cuda_msg}")
        if not cuda_available:
            print("Warning: CUDA 11.8+ is required for GPU support on Windows")
            proceed = input("Do you want to proceed with CPU-only installation? (y/N): ")
            if proceed.lower() != 'y':
                print("Installation aborted.")
                sys.exit(1)

        # Add Visio check
        visio_path = os.environ.get("VISIO_EXE_PATH", "C:\\Program Files\\Microsoft Office\\root\\Office16\\VISIO.EXE")
        if not Path(visio_path).exists():
            print(f"Visio not found at {visio_path}")
            proceed = input("Continue without Visio detection? (y/N): ")
            if proceed.lower() != 'y':
                sys.exit(1)
    
    print("\nInstalling dependencies...")
    # Upgrade pip first
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], 
                  cwd=root, check=True)
    
    # Install wheel and setuptools
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "wheel", "setuptools"], 
                  cwd=root, check=True)
    
    # Install requirements with platform-specific dependencies
    try:
        subprocess.run([str(python), "-m", "pip", "install", "-r", "requirements.txt"], 
                      cwd=root, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nError installing dependencies: {e}")
        print("\nTrying to install dependencies with --no-deps flag first...")
        try:
            # Try installing packages one by one with --no-deps
            with open(root / "requirements.txt") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            subprocess.run([str(python), "-m", "pip", "install", "--no-deps", line],
                                         cwd=root, check=True)
                        except subprocess.CalledProcessError:
                            print(f"Warning: Failed to install {line}")
            
            # Then install dependencies
            subprocess.run([str(python), "-m", "pip", "install", "-r", "requirements.txt"],
                         cwd=root, check=True)
        except subprocess.CalledProcessError as e:
            print(f"\nError: Failed to install dependencies: {e}")
            sys.exit(1)
    
    # Validate dependencies
    print("\nValidating dependencies...")
    issues = validate_dependencies(python)
    if issues:
        print("\nWarning: Dependency issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("All dependencies validated successfully!")
    
    # Create required directories
    print("\nCreating project directories...")
    directories = [
        "data",
        "data/memory",
        "data/templates",
        "data/stencils",
        "data/output",
        "static",
        "temp/uploads",
    ]
    
    for directory in directories:
        try:
            (root / directory).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            if e.winerror == 206:  # Windows path length error
                print(f"Path too long: {directory}. Enable long paths in Windows registry.")
                sys.exit(1)
        print(f"  Created {directory}/")
    
    print("\nInstallation complete!")
    
    # Print system information
    print("\nSystem Information:")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Platform: {platform.platform()}")
    print(f"  Architecture: {platform.machine()}")
    if platform.system() == "Windows":
        print(f"  CUDA: {cuda_msg}")
    
    # Print next steps
    print("\nNext Steps:")
    print("1. Create a .env file from .env.example")
    print("2. Configure your environment variables")
    print("3. Run 'python run.py' to start the application")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nError during installation: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1) 