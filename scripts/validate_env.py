import os
from dotenv import load_dotenv
from typing import List, Dict
import re

class EnvironmentValidator:
    """Enforces environment configuration standards"""
    
    REQUIRED_VARS = {
        'JWT_SECRET': {
            'min_length': 32,
            'generator': 'openssl rand -hex 32'
        },
        'VISIO_LICENSE_KEY': {
            'pattern': r'^VISIO\d{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'
        },
        'API_BASE_URL': {
            'is_url': True
        }
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
            
        # Validate Visio license format
        if not re.match(self.REQUIRED_VARS['VISIO_LICENSE_KEY']['pattern'], 
                       os.getenv('VISIO_LICENSE_KEY', '')):
            errors['VISIO_LICENSE_KEY'] = ['Invalid license format']
            
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