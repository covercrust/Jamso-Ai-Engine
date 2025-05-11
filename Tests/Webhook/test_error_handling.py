"""
Test module for error handling utilities.

This module tests the error handling functions defined in Webhook.utils.
"""
import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock
import logging
import requests

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from Webhook.utils import (
    create_error_response,
    handle_request_error,
    jsonify_error
)
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException

class TestCreateErrorResponse(unittest.TestCase):
    """Test cases for create_error_response utility."""
    
    def test_basic_error_response(self):
        """Test creating a basic error response."""
        message = "Test error message"
        response, status_code = create_error_response(message)
        
        self.assertEqual(status_code, 400)  # Default status code
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], message)
        self.assertNotIn("code", response)
        self.assertNotIn("details", response)
        
    def test_error_response_with_code(self):
        """Test creating an error response with an error code."""
        message = "Test error message"
        error_code = "TEST_ERROR"
        response, status_code = create_error_response(message, error_code=error_code)
        
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], message)
        self.assertEqual(response["code"], error_code)
        
    def test_error_response_with_custom_status(self):
        """Test creating an error response with a custom status code."""
        message = "Not found"
        status_code = 404
        response, returned_status = create_error_response(message, status_code=status_code)
        
        self.assertEqual(returned_status, status_code)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], message)
        
    def test_error_response_with_details(self):
        """Test creating an error response with additional details."""
        message = "Validation failed"
        details = {"field": "username", "reason": "already exists"}
        response, status_code = create_error_response(message, details=details)
        
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], message)
        self.assertEqual(response["details"], details)
        
    def test_complete_error_response(self):
        """Test creating a complete error response with all parameters."""
        message = "Validation failed"
        error_code = "VALIDATION_ERROR"
        status_code = 422
        details = {"errors": ["Field 'name' is required", "Field 'email' is invalid"]}
        
        response, returned_status = create_error_response(
            message, 
            status_code=status_code,
            error_code=error_code,
            details=details
        )
        
        self.assertEqual(returned_status, status_code)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], message)
        self.assertEqual(response["code"], error_code)
        self.assertEqual(response["details"], details)


class TestHandleRequestError(unittest.TestCase):
    """Test cases for handle_request_error utility."""
    
    def test_handle_value_error(self):
        """Test handling a ValueError."""
        error_message = "Invalid value"
        exception = ValueError(error_message)
        
        response, status_code = handle_request_error(exception)
        
        self.assertEqual(status_code, 400)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], error_message)
        self.assertEqual(response["code"], "VALIDATION_ERROR")
        
    def test_handle_capital_api_exception(self):
        """Test handling a CapitalAPIException."""
        error_message = "API error occurred"
        exception = CapitalAPIException(500, "Internal Server Error", error_message)
        
        response, status_code = handle_request_error(exception)
        
        self.assertEqual(status_code, 502)  # Bad Gateway for API errors
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], str(exception))
        self.assertEqual(response["code"], "API_ERROR")
        
    def test_handle_requests_timeout(self):
        """Test handling a requests.Timeout exception."""
        error_message = "Request timed out"
        exception = requests.exceptions.Timeout(error_message)
        
        response, status_code = handle_request_error(exception)
        
        self.assertEqual(status_code, 504)  # Gateway Timeout
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], str(exception))
        self.assertEqual(response["code"], "TIMEOUT_ERROR")
        
    def test_handle_requests_connection_error(self):
        """Test handling a requests.ConnectionError exception."""
        error_message = "Connection failed"
        exception = requests.exceptions.ConnectionError(error_message)
        
        response, status_code = handle_request_error(exception)
        
        self.assertEqual(status_code, 503)  # Service Unavailable
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], str(exception))
        self.assertEqual(response["code"], "CONNECTION_ERROR")
        
    def test_handle_key_error(self):
        """Test handling a KeyError exception."""
        key = "missing_key"
        exception = KeyError(key)
        
        response, status_code = handle_request_error(exception)
        
        self.assertEqual(status_code, 400)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["code"], "MISSING_FIELD")
        
    def test_handle_permission_error(self):
        """Test handling a PermissionError exception."""
        error_message = "Permission denied"
        exception = PermissionError(error_message)
        
        response, status_code = handle_request_error(exception)
        
        self.assertEqual(status_code, 403)  # Forbidden
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], error_message)
        self.assertEqual(response["code"], "PERMISSION_DENIED")
        
    def test_handle_generic_exception(self):
        """Test handling a generic Exception."""
        error_message = "An unexpected error occurred"
        exception = Exception(error_message)
        
        response, status_code = handle_request_error(exception)
        
        self.assertEqual(status_code, 500)  # Internal Server Error (default)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], error_message)
        self.assertEqual(response["code"], "INTERNAL_ERROR")
        
    def test_handle_exception_with_custom_default_status(self):
        """Test handling an exception with a custom default status code."""
        error_message = "An error occurred"
        exception = Exception(error_message)
        custom_status = 418  # I'm a teapot
        
        response, status_code = handle_request_error(exception, default_status=custom_status)
        
        self.assertEqual(status_code, custom_status)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], error_message)


class TestJsonifyError(unittest.TestCase):
    """Test cases for jsonify_error utility."""
    
    @patch('Webhook.utils.jsonify')
    def test_jsonify_error(self, mock_jsonify):
        """Test converting an error tuple to a Flask JSON response."""
        # Mock jsonify to return its input and the status code
        mock_jsonify.return_value = MagicMock()
        
        # Create an error response tuple
        error_data = ({"status": "error", "message": "Test error"}, 400)
        
        # Call jsonify_error
        jsonify_error(error_data)
        
        # Verify jsonify was called with the correct arguments
        mock_jsonify.assert_called_once_with({"status": "error", "message": "Test error"})
        
        # Verify the response has the correct status code
        mock_jsonify.return_value.__getitem__.assert_not_called()  # No indexing occurred
        

if __name__ == '__main__':
    unittest.main()