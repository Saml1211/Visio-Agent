#!/usr/bin/env python3
"""
Dependency validation script for the LLD Automation Project.
Checks installed package versions against requirements files.
"""

import importlib.metadata
import platform
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pkg_resources
from packaging import version

# Import Windows checks if on Windows
if platform.system() == 'Windows':
    try:
        from scripts.windows_checks import check_windows_requirements, print_windows_check_results
        WINDOWS_CHECKS_AVAILABLE = True
    except ImportError:
        WINDOWS_CHECKS_AVAILABLE = False
else:
    WINDOWS_CHECKS_AVAILABLE = False


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
    """Main function to validate dependencies."""
    print(f"\nValidating dependencies for {platform.system()} platform...")
    
    # Run Windows-specific checks if applicable
    if platform.system() == 'Windows':
        if WINDOWS_CHECKS_AVAILABLE:
            print("\nRunning Windows environment checks...")
            win_checks_passed, win_results = check_windows_requirements()
            print_windows_check_results(win_results)
            
            if not win_checks_passed:
                print("\nCritical: Windows environment requirements not met.")
                print("Please address the issues marked with ✗ before proceeding.")
                return True
        else:
            print("\nWarning: Windows checks module not available.")
            print("Please run scripts/windows_checks.py separately to validate Windows requirements.")
    
    # Check core requirements
    core_missing, core_outdated, core_ok = check_dependencies('requirements-core.txt')
    
    # Check main requirements
    main_missing, main_outdated, main_ok = check_dependencies('requirements.txt')
    
    # Check dev requirements if they exist
    if os.path.exists('requirements-dev.txt'):
        dev_missing, dev_outdated, dev_ok = check_dependencies('requirements-dev.txt')
    else:
        dev_missing, dev_outdated, dev_ok = [], [], []
    
    # Print summary
    print("\nDependency Validation Summary:")
    print("Core Dependencies:")
    print_dependency_status(core_missing, core_outdated, core_ok)
    
    print("\nMain Dependencies:")
    print_dependency_status(main_missing, main_outdated, main_ok)
    
    if os.path.exists('requirements-dev.txt'):
        print("\nDev Dependencies:")
        print_dependency_status(dev_missing, dev_outdated, dev_ok)
    
    # Return overall status
    has_issues = bool(
        core_missing or core_outdated or
        main_missing or main_outdated or
        dev_missing or dev_outdated
    )
    
    if not has_issues and platform.system() == 'Windows':
        print("\nNote: On Windows, please ensure you've run scripts/windows_checks.py")
        print("to validate Windows-specific requirements.")
    
    return has_issues


def print_dependency_status(missing: List[str], outdated: List[str], ok: List[str]):
    if missing:
        print("\nMissing packages:")
        for pkg in missing:
            print(f"  - {pkg}")
            
    if outdated:
        print("\nOutdated packages:")
        for pkg in outdated:
            print(f"  - {pkg}")
            
    if ok:
        print("\nCorrectly installed packages:")
        for pkg in sorted(ok):
            print(f"  - {pkg}")


if __name__ == '__main__':
    main() 