import pytest
from flask import json
from unittest.mock import patch, MagicMock
from datetime import datetime
from Webhook.app import create_app

class MockCursor:
    def __init__(self, fetchone_return=None):
        self.fetchone_return = fetchone_return or ("mock_deal_id",)
    
    def execute(self, *args, **kwargs):
        return self
        
    def fetchone(self):
        return self.fetchone_return
        
    def fetchall(self):
        return [self.fetchone_return]
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass

class MockDB:
    def __init__(self, cursor=None):
        self.cursor_instance = cursor or MockCursor()
    
    def cursor(self):
        return self.cursor_instance
        
    def execute(self, *args, **kwargs):
        # Some routes call execute directly on the db connection
        return self.cursor_instance.execute(*args, **kwargs)
        
    def commit(self):
        pass
        
    def close(self):
        pass
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass

def simple_json_mock():
    """Create a simple mock that returns a dict instead of a MagicMock object"""
    return {"success": True}

# Patches for both endpoints
@patch('Webhook.routes.datetime')
@patch('Webhook.routes.get_db')
@patch('Webhook.routes.get_client')
def test_webhook_endpoints(mock_get_client, mock_get_db, mock_datetime):
    """Test both webhook endpoints with proper JSON-serializable mocks"""
    # Setup datetime mock
    mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
    mock_datetime.isoformat = datetime.isoformat
    
    # Setup database mock
    mock_db = MockDB()
    mock_get_db.return_value = mock_db
    
    # Setup mock client with JSON-serializable return values
    mock_client = MagicMock()
    mock_client.session_manager.create_session.return_value = {"success": True}
    mock_client.session_manager.is_authenticated = True
    mock_client.create_position.return_value = {"dealReference": "mock_close_ref"}
    mock_get_client.return_value = mock_client
    
    # Create test app
    app = create_app()
    client = app.test_client()
    
    # Setup auth headers
    headers = {
        'X-Trading-Token': '6a87cf683ac94bc7f83bc09ba643dc578538d4eb46c931a60dc4fe3ec3c159cd',
        'Content-Type': 'application/json'
    }
    
    # Test tradingview webhook endpoint
    with patch('Webhook.routes.save_signal') as mock_save_signal:
        with patch('Webhook.routes.execute_trade') as mock_execute_trade:
            with patch('Webhook.routes.save_trade_result') as mock_save_trade_result:
                # Configure mocks with JSON-serializable return values
                mock_save_signal.return_value = 1
                mock_execute_trade.return_value = {"dealReference": "mock_deal_ref"}
                mock_save_trade_result.return_value = 1
                
                # Test data
                open_data = {
                    "ticker": "BTCUSD",
                    "order_action": "BUY",
                    "position_size": 0.01,
                    "order_id": "12345"
                }
                
                # Make request
                response = client.post(
                    '/webhook/tradingview',
                    data=json.dumps(open_data),
                    headers=headers
                )
                
                # Verify response
                assert response.status_code == 200
                response_data = json.loads(response.data)
                assert response_data["status"] == "success"
    
    # Test close_position endpoint
    with patch('Webhook.routes.get_position_details') as mock_get_position:
        # Configure mock with JSON-serializable return value
        mock_get_position.return_value = {
            "position": {
                "direction": "BUY",
                "market": {"epic": "BTCUSD"}
            }
        }
        
        # Test data
        close_data = {
            "ticker": "BTCUSD",
            "size": 0.01,
            "order_id": "12345"
        }
        
        # Make request
        response = client.post(
            '/close_position',
            data=json.dumps(close_data),
            headers=headers
        )
        
        # Verify response
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["status"] == "success"
