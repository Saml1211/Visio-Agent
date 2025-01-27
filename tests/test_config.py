import pytest
from src.config.service_config import ServiceConfig

def test_config_loading():
    config = ServiceConfig()
    assert config.browserbase_api_key is not None
    assert config.screenpipe_api_key is not None
    assert config.visio_style_rules.exists()

def test_service_initialization():
    from services.initialization import initialize_services
    services = initialize_services()
    assert services["browserbase"] is not None
    assert services["screenpipe"] is not None 