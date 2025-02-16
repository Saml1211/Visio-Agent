#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def main():
    # Get project root
    root = Path(__file__).parent.parent
    
    # Create virtual environment
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", ".venv"], cwd=root)
    
    # Activate virtual environment and install dependencies
    if sys.platform == "win32":
        python = root / ".venv" / "Scripts" / "python"
    else:
        python = root / ".venv" / "bin" / "python"
    
    print("Installing dependencies...")
    subprocess.run([str(python), "-m", "pip", "install", "-r", "requirements.txt"], cwd=root)
    
    # Create required directories
    (root / "data").mkdir(exist_ok=True)
    (root / "static").mkdir(exist_ok=True)
    
    print("Installation complete!")

if __name__ == "__main__":
    main() 