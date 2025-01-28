from typing import Dict, List
import subprocess

class WorkflowVerifier:
    """Validates end-to-end workflow components"""
    
    COMPONENTS = [
        ("frontend", ["npm run build", "npm test"]),
        ("api", ["pytest tests/api"]),
        ("visio", ["python -m pytest tests/visio"]),
        ("ai", ["python -m pytest tests/ai"])
    ]
    
    def verify(self):
        # Run component tests and return results
        results = {}
        
        for component, commands in self.COMPONENTS:
            component_results = []
            for cmd in commands:
                try:
                    subprocess.run(cmd, check=True, shell=True, capture_output=True)
                    component_results.append(f"✓ {cmd}")
                except subprocess.CalledProcessError as e:
                    component_results.append(f"✗ {cmd} - {e.stderr.decode()}")
            results[component] = component_results
            
        return results 