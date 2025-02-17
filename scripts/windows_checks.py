#!/usr/bin/env python3
"""
Windows-specific validation checks for the Visio Agent installation.
This module provides functionality to verify Windows-specific requirements
and configurations needed for the Visio Agent to run properly.
"""

import os
import sys
import winreg
import platform
from pathlib import Path
from typing import Tuple, Optional
import subprocess

def check_windows_version() -> Tuple[bool, str]:
    """
    Check if the Windows version is compatible (Windows 10 or later).
    Returns:
        Tuple[bool, str]: (is_compatible, message)
    """
    if platform.system() != 'Windows':
        return False, "Not a Windows system"
    
    try:
        version = sys.getwindowsversion()
        # Windows 10 is 10.0, Windows 11 is 10.0 with build number >= 22000
        if version.major >= 10:
            build_number = platform.version().split('.')[-1]
            if int(build_number) >= 22000:
                return True, "Windows 11 detected"
            return True, "Windows 10 detected"
        return False, f"Unsupported Windows version: {platform.version()}"
    except Exception as e:
        return False, f"Error checking Windows version: {str(e)}"

def check_visio_installation() -> Tuple[bool, str, Optional[str]]:
    """
    Check if Microsoft Visio is installed and get its version.
    Returns:
        Tuple[bool, str, Optional[str]]: (is_installed, message, version)
    """
    try:
        # Check both 32-bit and 64-bit registry
        for registry_view in [winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY]:
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration",
                    0,
                    winreg.KEY_READ | registry_view
                )
                try:
                    value, _ = winreg.QueryValueEx(key, "VersionToReport")
                    if "visio" in value.lower():
                        return True, "Microsoft Visio is installed", value
                except WindowsError:
                    continue
                finally:
                    winreg.CloseKey(key)
            except WindowsError:
                continue
                
        return False, "Microsoft Visio installation not found", None
    except Exception as e:
        return False, f"Error checking Visio installation: {str(e)}", None

def check_path_length_limit() -> Tuple[bool, str]:
    """
    Check if long path support is enabled in Windows.
    Returns:
        Tuple[bool, str]: (is_enabled, message)
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\FileSystem",
            0,
            winreg.KEY_READ
        )
        try:
            value, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
            if value == 1:
                return True, "Long path support is enabled"
            return False, "Long path support is not enabled"
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        return False, f"Error checking long path support: {str(e)}"

def check_cuda_availability() -> Tuple[bool, str]:
    """
    Check if CUDA is available on the system.
    Returns:
        Tuple[bool, str]: (is_available, message)
    """
    try:
        # Check if nvidia-smi is available
        subprocess.run(['nvidia-smi'], capture_output=True, check=True)
        
        # Get CUDA version
        result = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'], 
                              capture_output=True, text=True, check=True)
        cuda_version = result.stdout.strip()
        
        return True, f"CUDA is available (Driver Version: {cuda_version})"
    except subprocess.CalledProcessError:
        return False, "NVIDIA GPU/CUDA not detected"
    except Exception as e:
        return False, f"Error checking CUDA availability: {str(e)}"

def check_windows_requirements() -> Tuple[bool, list]:
    """
    Run all Windows-specific checks and return results.
    Returns:
        Tuple[bool, list]: (all_passed, [check_results])
    """
    results = []
    all_passed = True
    
    # Check Windows version
    win_compatible, win_msg = check_windows_version()
    results.append(("Windows Version", win_compatible, win_msg))
    all_passed &= win_compatible
    
    # Check Visio installation
    visio_installed, visio_msg, visio_version = check_visio_installation()
    if visio_version:
        visio_msg += f" (Version: {visio_version})"
    results.append(("Microsoft Visio", visio_installed, visio_msg))
    all_passed &= visio_installed
    
    # Check path length limit
    paths_enabled, paths_msg = check_path_length_limit()
    results.append(("Long Path Support", paths_enabled, paths_msg))
    all_passed &= paths_enabled
    
    # Check CUDA availability
    cuda_available, cuda_msg = check_cuda_availability()
    results.append(("CUDA Support", cuda_available, cuda_msg))
    # Don't make CUDA mandatory for all_passed since it's optional
    
    return all_passed, results

def print_windows_check_results(results: list):
    """Print the results of Windows requirement checks in a formatted way."""
    print("\nWindows Environment Check Results:")
    print("-" * 60)
    
    for check_name, passed, message in results:
        status = "✓" if passed else "✗"
        print(f"{status} {check_name}: {message}")
    
    print("-" * 60)

if __name__ == '__main__':
    if platform.system() != 'Windows':
        print("This script should only be run on Windows systems.")
        sys.exit(1)
        
    all_passed, results = check_windows_requirements()
    print_windows_check_results(results)
    
    if not all_passed:
        print("\nSome Windows requirements are not met. Please address the issues marked with ✗")
        sys.exit(1)
    
    print("\nAll Windows requirements are met!")
    sys.exit(0) 