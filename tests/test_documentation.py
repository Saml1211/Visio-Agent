def test_readme_integration_section():
    with open('README.md') as f:
        content = f.read()
    
    assert "LangGraph-powered workflow state management" in content
    assert "Real-time collaboration backend" in content
    assert "AI-powered validation engine" in content

def test_cursorrules_security():
    with open('.cursorrules') as f:
        content = f.read()
    
    assert 'https://collab.visio-automation.com' in content
    assert 'visio:generate' in content 