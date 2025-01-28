#!/usr/bin/env python3
"""
Dependency validation script for the LLD Automation Project.
Checks installed package versions against requirements files.
"""

import importlib.metadata
import platform
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pkg_resources
from packaging import version


def parse_requirements(filename: str) -> List[Tuple[str, Optional[str]]]:
    """Parse a requirements file into (package, version) tuples."""
    requirements = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-r'):
                continue
            
            # Split package name from version and platform specifiers
            parts = line.split(';')[0].strip()  # Remove platform specifiers
            if '==' in parts:
                name, ver = parts.split('==')
                requirements.append((name.strip(), ver.strip()))
            elif '>=' in parts:
                name, ver = parts.split('>=')
                requirements.append((name.strip(), ver.strip()))
            else:
                requirements.append((parts.strip(), None))
    return requirements


def get_installed_version(package: str) -> Optional[str]:
    """Get the installed version of a package."""
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def check_dependencies(requirements_file: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Check dependencies against requirements file.
    Returns lists of missing, outdated, and ok packages.
    """
    missing = []
    outdated = []
    ok = []
    
    requirements = parse_requirements(requirements_file)
    
    for package, required_version in requirements:
        installed_version = get_installed_version(package)
        
        if installed_version is None:
            missing.append(package)
            continue
            
        if required_version:
            try:
                if '>=' in required_version:
                    min_version = version.parse(required_version.replace('>=', ''))
                    if version.parse(installed_version) < min_version:
                        outdated.append(f"{package} (installed: {installed_version}, required: >={required_version})")
                        continue
                else:
                    if version.parse(installed_version) != version.parse(required_version):
                        outdated.append(f"{package} (installed: {installed_version}, required: {required_version})")
                        continue
                        
            except version.InvalidVersion:
                # Skip version comparison if version string is invalid
                pass
                
        ok.append(f"{package}=={installed_version}")
        
    return missing, outdated, ok


def main():
    """Main validation function."""
    system = platform.system()
    print(f"\nValidating dependencies for {system} platform...")
    
    # Base requirements
    base_missing, base_outdated, base_ok = check_dependencies('base-requirements.txt')
    
    # Platform-specific requirements
    if system == "Darwin":
        platform_file = 'requirements-mac.txt'
    elif system == "Windows":
        platform_file = 'requirements-win.txt'
    else:
        platform_file = None
        
    if platform_file and Path(platform_file).exists():
        plat_missing, plat_outdated, plat_ok = check_dependencies(platform_file)
        base_missing.extend(plat_missing)
        base_outdated.extend(plat_outdated)
        base_ok.extend(plat_ok)
    
    # Development requirements if present
    if Path('requirements-dev.txt').exists():
        dev_missing, dev_outdated, dev_ok = check_dependencies('requirements-dev.txt')
        print("\nDevelopment dependencies:")
        if dev_missing:
            print("\nMissing development packages:")
            for pkg in dev_missing:
                print(f"  - {pkg}")
        if dev_outdated:
            print("\nOutdated development packages:")
            for pkg in dev_outdated:
                print(f"  - {pkg}")
        if dev_ok:
            print("\nCorrectly installed development packages:")
            for pkg in sorted(dev_ok):
                print(f"  - {pkg}")
    
    # Print results
    print("\nBase and platform-specific dependencies:")
    if base_missing:
        print("\nMissing packages:")
        for pkg in base_missing:
            print(f"  - {pkg}")
            
    if base_outdated:
        print("\nOutdated packages:")
        for pkg in base_outdated:
            print(f"  - {pkg}")
            
    if base_ok:
        print("\nCorrectly installed packages:")
        for pkg in sorted(base_ok):
            print(f"  - {pkg}")
    
    # Exit with error if there are missing or outdated packages
    if base_missing or base_outdated:
        print("\nPlease install missing packages and update outdated ones.")
        sys.exit(1)
    else:
        print("\nAll required packages are installed and up to date!")
        sys.exit(0)


if __name__ == '__main__':
    main() 