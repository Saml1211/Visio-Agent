class SecurityError(Exception):
    """Custom security exception"""
    def __init__(self, message="Security violation detected"):
        super().__init__(message) 