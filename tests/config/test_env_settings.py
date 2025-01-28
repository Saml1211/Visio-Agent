import os
from config.jina_settings import MAO_ORCHESTRATOR_CONFIG

def test_visio_operations_config():
    assert MAO_ORCHESTRATOR_CONFIG['visio_operations']['max_shapes'] == 500
    assert MAO_ORCHESTRATOR_CONFIG['visio_operations']['auto_cleanup'] is True

def test_jina_env_defaults():
    assert os.getenv("JINA_TIMEOUT") == "30"
    assert os.getenv("JINA_MAX_RETRIES") == "3"
    assert os.getenv("JINA_RATE_LIMIT") == "100/60s" 