#!/usr/bin/env python3
"""
Script to organize the Visio Agent project structure.
"""

import os
import shutil
from pathlib import Path

def create_directory(path):
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)

def main():
    # Project root directory
    root = Path(__file__).parent.parent

    # Create main directory structure
    directories = [
        'src/api',
        'src/core',
        'src/models',
        'src/services',
        'src/utils',
        'tests',
        'docs',
        'config',
        'static',
        'scripts',
    ]

    # Create directories
    for directory in directories:
        create_directory(root / directory)

    # Clean up unnecessary files and directories
    to_remove = [
        'requirements-temp.txt',
        'requirements-core.txt',
        'requirements-mac.txt',
        'requirements-win.txt',
        'requirements.in',
        'base-requirements.txt',
        'venv_py311/',
        'venv_clean/',
        'venv_py311_new/',
        'temp/',
        '.DS_Store',
    ]

    for item in to_remove:
        path = root / item
        if path.exists():
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)

    # Ensure essential files exist
    essential_files = [
        '.env.example',
        'requirements.txt',
        'README.md',
        'setup.py',
        'pytest.ini',
        '.gitignore',
    ]

    for file in essential_files:
        if not (root / file).exists():
            print(f"Warning: Essential file {file} is missing")

if __name__ == '__main__':
    main() 