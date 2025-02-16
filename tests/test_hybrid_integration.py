import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, patch
import socketio
import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

from services.gui_service import HybridGUI
from models.shared_state import SharedState
from models.user import User

# Test fixtures
@pytest.fixture
def app():
    app = FastAPI()
    return app

@pytest.fixture
def hybrid_gui(app):
    return HybridGUI(app)

@pytest.fixture
def test_client(app):
    return TestClient(app)

@pytest.fixture
def mock_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        is_admin=True
    )

@pytest.fixture
def mock_socket():
    return Mock(spec=socketio.AsyncServer)

# Test cases
class TestHybridGUI:
    @pytest.mark.asyncio
    async def test_shared_state_initialization(self, hybrid_gui):
        """Test that shared state is properly initialized"""
        assert isinstance(hybrid_gui.shared_state, dict)
        assert len(hybrid_gui.shared_state) == 0

    @pytest.mark.asyncio
    async def test_state_update_handler(self, hybrid_gui):
        """Test WebSocket state update handler"""
        test_data = {
            "key": "value",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Mock socket.io emit
        hybrid_gui.sio.emit = Mock()
        
        # Simulate state update
        await hybrid_gui.handle_state_update("test-sid", test_data)
        
        assert hybrid_gui.shared_state["key"] == "value"
        hybrid_gui.sio.emit.assert_called_once_with('state_changed', hybrid_gui.shared_state)

    @pytest.mark.asyncio
    async def test_preview_tool_authentication(self, hybrid_gui, mock_user):
        """Test that preview tool requires authentication"""
        with patch('services.gui_service.get_current_user', return_value=mock_user):
            # Mock ui context
            with patch('nicegui.ui.card') as mock_card:
                mock_card.return_value.__enter__ = Mock()
                mock_card.return_value.__exit__ = Mock()
                
                # Call preview tool
                await hybrid_gui.preview_tool(mock_user)
                
                mock_card.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_dashboard_authorization(self, hybrid_gui, mock_user):
        """Test that admin dashboard requires admin privileges"""
        # Test with admin user
        with patch('services.gui_service.get_current_user', return_value=mock_user):
            with patch('nicegui.ui.card') as mock_card:
                mock_card.return_value.__enter__ = Mock()
                mock_card.return_value.__exit__ = Mock()
                
                await hybrid_gui.admin_dashboard(mock_user)
                mock_card.assert_called_once()
        
        # Test with non-admin user
        mock_user.is_admin = False
        with patch('services.gui_service.get_current_user', return_value=mock_user):
            with patch('nicegui.ui.notify') as mock_notify:
                await hybrid_gui.admin_dashboard(mock_user)
                mock_notify.assert_called_once_with('Unauthorized access')

    @pytest.mark.asyncio
    async def test_websocket_connection_handlers(self, hybrid_gui):
        """Test WebSocket connection and disconnection handlers"""
        test_sid = "test-connection-id"
        test_environ = {"HTTP_ORIGIN": "http://localhost:3000"}
        
        # Test connection
        await hybrid_gui.connect(test_sid, test_environ)
        # Add assertions based on your connection handling logic
        
        # Test disconnection
        await hybrid_gui.disconnect(test_sid)
        # Add assertions based on your disconnection handling logic

    def test_shared_state_model_validation(self):
        """Test SharedState model validation"""
        # Valid state
        valid_state = SharedState(
            user_id=uuid4(),
            state={
                "current_diagram": {
                    "id": "test-diagram",
                    "svg_content": "<svg></svg>",
                    "modified": datetime.now(timezone.utc).isoformat()
                }
            },
            last_update=datetime.now(timezone.utc).isoformat()
        )
        assert valid_state.state["current_diagram"]["id"] == "test-diagram"
        
        # Invalid state (should raise validation error)
        with pytest.raises(ValueError):
            SharedState(
                user_id="invalid-uuid",  # Invalid UUID
                state={"invalid": None}
            )

    @pytest.mark.asyncio
    async def test_pipeline_monitor_updates(self, hybrid_gui, mock_user):
        """Test pipeline monitor state updates"""
        test_pipeline_state = {
            "stage": "processing",
            "progress": 50,
            "message": "Processing diagram components"
        }
        
        # Update pipeline state
        hybrid_gui.shared_state["pipeline_status"] = test_pipeline_state
        
        # Mock ui components
        with patch('nicegui.ui.card') as mock_card:
            mock_card.return_value.__enter__ = Mock()
            mock_card.return_value.__exit__ = Mock()
            
            await hybrid_gui.pipeline_monitor(mock_user)
            mock_card.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self, hybrid_gui, mock_user):
        """Test error handling in NiceGUI routes"""
        # Mock an error in preview tool
        with patch('services.gui_service.get_current_user', return_value=mock_user):
            with patch('nicegui.ui.card', side_effect=Exception("Test error")):
                with patch('nicegui.ui.notify') as mock_notify:
                    await hybrid_gui.preview_tool(mock_user)
                    mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_state_synchronization(self, hybrid_gui):
        """Test state synchronization between components"""
        test_states = [
            {"diagram_id": "1", "progress": 25},
            {"diagram_id": "1", "progress": 50},
            {"diagram_id": "1", "progress": 75},
            {"diagram_id": "1", "progress": 100}
        ]
        
        # Mock socket.io emit
        hybrid_gui.sio.emit = Mock()
        
        # Simulate multiple state updates
        for state in test_states:
            await hybrid_gui.handle_state_update("test-sid", state)
            assert hybrid_gui.shared_state["progress"] == state["progress"]
        
        # Verify final state
        assert hybrid_gui.sio.emit.call_count == len(test_states)

    def test_cors_configuration(self, app, test_client):
        """Test CORS configuration"""
        # Test preflight request
        response = test_client.options(
            "/api/shared-state",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    @pytest.mark.asyncio
    async def test_performance_metrics(self, hybrid_gui):
        """Test performance metrics collection"""
        # Mock socket.io connections
        hybrid_gui.sio.eio.sockets = {"1": None, "2": None}
        
        # Add some test state
        hybrid_gui.shared_state = {
            "large_data": "x" * 1000  # Simulate large state
        }
        
        # Mock logger
        with patch('services.gui_service.logger.info') as mock_logger:
            await hybrid_gui.log_performance_metrics()
            
            # Verify metrics logging
            mock_logger.assert_called_once()
            call_args = mock_logger.call_args[1]
            assert call_args["connected_clients"] == 2
            assert call_args["state_size"] > 1000

if __name__ == "__main__":
    pytest.main([__file__]) 