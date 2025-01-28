def test_required_versions():
    with open('requirements.txt') as f:
        requirements = f.read()
    
    assert 'langgraph==0.1.3' in requirements
    assert 'multi-agent-orchestrator==2.1.0' in requirements
    assert 'psycopg2-binary==2.9.9' in requirements
    assert 'haystack-ai==2.0.0' in requirements 