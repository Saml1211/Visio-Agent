from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class SecurityManager:
    def __init__(self):
        self.key = self._derive_key()
        
    def _derive_key(self):
        salt = os.environ.get('SECURITY_SALT').encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(os.environ.get('SECRET_KEY').encode()))
    
    def encrypt(self, data: str) -> str:
        fernet = Fernet(self.key)
        return fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, token: str) -> str:
        fernet = Fernet(self.key)
        return fernet.decrypt(token.encode()).decode() 