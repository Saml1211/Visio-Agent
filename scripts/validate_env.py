import os
from dotenv import load_dotenv
from typing import List, Dict
import re
import platform

class EnvironmentValidator:
    """Enforces environment configuration standards"""
    
    REQUIRED_VARS = {
        'JWT_SECRET': {
            'min_length': 32,
            'generator': 'openssl rand -hex 32'
        },
        'API_BASE_URL': {
            'is_url': True
        }
    }

    PLATFORM_CHECKS = {
        "Windows": [
            ("VISIO_EXE_PATH", r"\\VISIO\.EXE$"),
            ("TEMPLATES_DIR", "data/templates")
        ],
        "Darwin": [
            ("VISIO_EXE_PATH", r"Microsoft Visio\.app$"),
            ("UPLOAD_DIR", "temp/uploads")
        ]
    }

    def __init__(self):
        load_dotenv()
        
    def validate(self) -> Dict[str, List[str]]:
        """Performs comprehensive environment validation"""
        errors = {}
        
        # Check presence
        missing = [var for var in self.REQUIRED_VARS if not os.getenv(var)]
        if missing:
            errors['missing'] = missing
            
        # Validate JWT_SECENT
        jwt_secret = os.getenv('JWT_SECRET', '')
        if len(jwt_secret) < 32:
            errors['JWT_SECRET'] = ['Must be at least 32 characters']
            
        return errors

    def validate_paths(self):
        system = platform.system()
        errors = {}
        
        for var, pattern in self.PLATFORM_CHECKS.get(system, []):
            path = os.getenv(var)
            if path and not re.search(pattern, path):
                errors[var] = [f"Invalid path pattern: {path}"]
            
        # Check write permissions
        for dir_var in ['UPLOAD_DIR', 'OUTPUT_DIR']:
            dir_path = os.getenv(dir_var)
            if dir_path and not os.access(dir_path, os.W_OK):
                errors[dir_var] = ["Directory not writable"]
            
        return errors

if __name__ == "__main__":
    validator = EnvironmentValidator()
    issues = validator.validate()
    
    if issues:
        print("Configuration errors detected:")
        for category, messages in issues.items():
            print(f"  {category}: {', '.join(messages)}")
        exit(1)
    print("Environment configuration valid") 