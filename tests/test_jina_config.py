from config.jina_settings import JINA_API_URL, JINA_TIMEOUT, MAO_ORCHESTRATOR_CONFIG

def test_jina_defaults():
    assert JINA_API_URL == "https://api.jina.ai"
    assert JINA_TIMEOUT == 30
    assert JINA_TIMEOUT == 30

def test_mao_config_structure():
    assert MAO_ORCHESTRATOR_CONFIG['agent_timeout'] == 30
    assert MAO_ORCHESTRATOR_CONFIG['visio_operations']['max_shapes'] == 500
    assert MAO_ORCHESTRATOR_CONFIG['visio_operations']['auto_cleanup'] is True 