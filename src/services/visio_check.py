import platform
import winreg
from pathlib import Path
import os
import win32com.client

def verify_visio_installation():
    """Enhanced installation verification"""
    system = platform.system()
    
    if system == "Windows":
        try:
            # Check registry entry
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\visio.exe")
            exe_path = winreg.QueryValue(key, "")
            
            # Verify COM interoperability
            try:
                win32com.client.Dispatch("Visio.Application")
            except Exception as e:
                raise EnvironmentError(f"COM access denied: {str(e)}")
                
            return Path(exe_path).exists()
            
        except FileNotFoundError:
            raise FileNotFoundError("Visio not found. Requires Visio 2019+ with Click-to-Run installation")
            
    elif system == "Darwin":
        app_path = Path("/Applications/Microsoft Visio.app")
        if not app_path.exists():
            raise FileNotFoundError("Visio for Mac required. Download from Microsoft 365 portal")
            
        # Verify execution permissions
        if not os.access(app_path / "Contents/MacOS/Microsoft Visio", os.X_OK):
            raise PermissionError("Visio app lacks execute permissions")
            
        return True
        
    else:
        raise OSError("Unsupported OS") 