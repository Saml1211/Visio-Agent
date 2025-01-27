from cryptography.fernet import Fernet
import json
import os

class SecureVault:
    def __init__(self):
        self.key = os.getenv("CONFIG_KEY") or Fernet.generate_key()
        self.cipher = Fernet(self.key)
        
    def encrypt_config(self, config: dict) -> str:
        return self.cipher.encrypt(json.dumps(config).encode()).decode()
    
    def decrypt_config(self, encrypted: str) -> dict:
        return json.loads(self.cipher.decrypt(encrypted.encode()).decode())

class ConfigManager:
    def __init__(self):
        self.vault = SecureVault()
        self.config_path = os.path.expanduser("~/.visio/config.vault")
        
    def save_config(self, config: dict):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            f.write(self.vault.encrypt_config(config))
            
    def load_config(self) -> dict:
        with open(self.config_path, 'r') as f:
            return self.vault.decrypt_config(f.read()) 