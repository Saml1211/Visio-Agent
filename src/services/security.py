from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import ssl
import socket

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

    def validate_ai_connections(self):
        """AV-specific security validation for AI services"""
        # Verify encrypted connections
        endpoints = [
            ("vision.googleapis.com", 443),
            ("generativelanguage.googleapis.com", 443)
        ]
        
        for host, port in endpoints:
            if not self._verify_ssl_connection(host, port):
                raise SecurityError(f"Unencrypted connection detected to {host}:{port}")
        
        # Validate data sanitization
        test_input = "Control System\nIP: 192.168.1.1\nPassword: admin123"
        sanitized = sanitize_av_data(test_input)
        
        assert "192.168.1.1" not in sanitized, "IP address leakage detected"
        assert "admin123" not in sanitized, "Credential leakage detected"

    def _verify_ssl_connection(self, host: str, port: int) -> bool:
        """Verify SSL/TLS connection security"""
        context = ssl.create_default_context()
        with socket.create_connection((host, port)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                return ssock.version() in ("TLSv1.2", "TLSv1.3") 