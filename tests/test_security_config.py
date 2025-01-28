import pytest
from unittest.mock import patch
from src.services.auth.jwt_service import OrchestratorClaims, GraphPolicy

def test_mao_claims_registration():
    with patch('multi_agent_orchestrator.claims.register') as mock_register:
        # Test required claims exist
        assert 'visio_generate' in OrchestratorClaims.required_claims
        assert 'collaboration_write' in OrchestratorClaims.required_claims
        mock_register.assert_called()

def test_langgraph_policy_config():
    with patch('langgraph.security.policy_registry') as mock_registry:
        # Verify workflow policy registration
        assert 'visio_workflow' in GraphPolicy.registered_policies
        policy = GraphPolicy.get('visio_workflow')
        assert 'visio:generate' in policy.requires
        assert 'workflow:manage' in policy.requires 