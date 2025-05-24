"""
Test module for validators functionality.

This module tests the validation functions defined in Webhook.validators.
"""
import unittest
import sys
import os
from unittest.mock import patch
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Patch: Use absolute imports for validators
from src.Webhook.validators import (
    validate_webhook_data,
    validate_close_position_data,
    sanitize_input,
    validate_api_input
)

class TestWebhookDataValidation(unittest.TestCase):
    """Test cases for webhook data validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample valid webhook data
        self.valid_data = {
            'order_id': 'test_order_123',
            'ticker': 'AAPL',
            'order_action': 'BUY',
            'position_size': 1.5,
            'price': 150.0
        }
        
    def test_valid_data(self):
        """Test validation with valid data."""
        errors = validate_webhook_data(self.valid_data)
        self.assertEqual(errors, [], "Valid data should not produce errors")
        
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        data = {}
        errors = validate_webhook_data(data)
        self.assertTrue(any("Missing required field: ticker or symbol" in e for e in errors))
        self.assertTrue(any("Missing required field: order_action or direction" in e for e in errors))
        
    def test_invalid_order_action(self):
        """Test validation with invalid order_action."""
        data = self.valid_data.copy()
        data['order_action'] = 'INVALID_ACTION'
        errors = validate_webhook_data(data)
        self.assertTrue(any("Invalid order_action" in e for e in errors))
        
    def test_invalid_position_size(self):
        """Test validation with invalid position_size."""
        data = {
            "order_id": "12345",
            "ticker": "BTCUSD",
            "order_action": "BUY",
            "position_size": 0
        }
        errors = validate_webhook_data(data)
        print('DEBUG test_invalid_position_size errors:', errors)
        self.assertTrue(any("position_size/quantity must be greater than 0" in e for e in errors))
        
        # Test non-numeric position size
        data = {
            "order_id": "12345",
            "ticker": "BTCUSD",
            "order_action": "BUY",
            "position_size": "not_a_number"
        }
        errors = validate_webhook_data(data)
        print('DEBUG test_invalid_position_size errors (non-numeric):', errors)
        self.assertTrue(any("position_size/quantity must be a number" in e for e in errors))
        
    def test_invalid_ticker(self):
        """Test validation with invalid ticker."""
        data = {
            "order_id": "12345",
            "ticker": 12345,  # Not a string
            "order_action": "BUY",
            "position_size": 1
        }
        errors = validate_webhook_data(data)
        self.assertTrue(any("ticker/symbol must be a string" in e for e in errors))
        
        # Test ticker with invalid characters
        data = {
            "order_id": "12345",
            "ticker": "AAPL!@#",
            "order_action": "BUY",
            "position_size": 1
        }
        errors = validate_webhook_data(data)
        self.assertTrue(any("ticker/symbol contains invalid characters" in e for e in errors))
        
    def test_stop_loss_validation(self):
        """Test stop loss validation."""
        # Test stop loss for BUY order (should be below price)
        data = self.valid_data.copy()
        data['price'] = 100.0
        data['stop_loss'] = 90.0  # valid: below price for BUY
        errors = validate_webhook_data(data)
        self.assertEqual(errors, [])
        
        # Test invalid stop loss for BUY order (above price)
        data = self.valid_data.copy()
        data['price'] = 100.0
        data['stop_loss'] = 110.0  # invalid: above price for BUY
        errors = validate_webhook_data(data)
        self.assertTrue(any("stop_loss" in e and "should be below" in e for e in errors))
        
        # Test stop loss for SELL order (should be above price)
        data = self.valid_data.copy()
        data['order_action'] = 'SELL'
        data['price'] = 100.0
        data['stop_loss'] = 110.0  # valid: above price for SELL
        errors = validate_webhook_data(data)
        self.assertEqual(errors, [])
        
        # Test invalid stop loss for SELL order (below price)
        data = self.valid_data.copy()
        data['order_action'] = 'SELL'
        data['price'] = 100.0
        data['stop_loss'] = 90.0  # invalid: below price for SELL
        errors = validate_webhook_data(data)
        self.assertTrue(any("stop_loss" in e and "should be above" in e for e in errors))
        
    def test_take_profit_validation(self):
        """Test take profit validation."""
        # Test take profit for BUY order (should be above price)
        data = self.valid_data.copy()
        data['price'] = 100.0
        data['take_profit'] = 110.0  # valid: above price for BUY
        errors = validate_webhook_data(data)
        self.assertEqual(errors, [])
        
        # Test invalid take profit for BUY order (below price)
        data = self.valid_data.copy()
        data['price'] = 100.0
        data['take_profit'] = 90.0  # invalid: below price for BUY
        errors = validate_webhook_data(data)
        self.assertTrue(any("take_profit" in e and "should be above" in e for e in errors))
        
        # Test take profit for SELL order (should be below price)
        data = self.valid_data.copy()
        data['order_action'] = 'SELL'
        data['price'] = 100.0
        data['take_profit'] = 90.0  # valid: below price for SELL
        errors = validate_webhook_data(data)
        self.assertEqual(errors, [])
        
        # Test invalid take profit for SELL order (above price)
        data = self.valid_data.copy()
        data['order_action'] = 'SELL'
        data['price'] = 100.0
        data['take_profit'] = 110.0  # invalid: above price for SELL
        errors = validate_webhook_data(data)
        self.assertTrue(any("take_profit" in e and "should be below" in e for e in errors))
        
    def test_trailing_stop_validation(self):
        """Test trailing stop validation."""
        # Test valid trailing stop with trailing_step_percent
        data = self.valid_data.copy()
        data['trailing_stop'] = True
        data['trailing_step_percent'] = 1.0
        errors = validate_webhook_data(data)
        self.assertEqual(errors, [])
        
        # Test invalid trailing stop with negative trailing_step_percent
        data = self.valid_data.copy()
        data['trailing_stop'] = True
        data['trailing_step_percent'] = -1.0
        errors = validate_webhook_data(data)
        self.assertTrue(any("trailing_step_percent must be between" in e for e in errors))
        
        # Test trailing stop without required parameters
        data = self.valid_data.copy()
        data['trailing_stop'] = True
        errors = validate_webhook_data(data)
        self.assertTrue(any("trailing_stop is enabled" in e for e in errors))


class TestClosePositionValidation(unittest.TestCase):
    """Test cases for close position data validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample valid close position data
        self.valid_data = {
            'order_id': 'test_order_123',
            'size': 1.0
        }
        
    def test_valid_data(self):
        """Test validation with valid data."""
        errors = validate_close_position_data(self.valid_data)
        self.assertEqual(errors, [], "Valid data should not produce errors")
        
    def test_missing_order_id(self):
        """Test validation with missing order_id."""
        data = self.valid_data.copy()
        data.pop('order_id')
        errors = validate_close_position_data(data)
        self.assertIn("Missing required field: order_id", errors)
        
    def test_invalid_size(self):
        """Test validation with invalid size."""
        # Test negative size
        data = self.valid_data.copy()
        data['size'] = -1.0
        errors = validate_close_position_data(data)
        self.assertTrue(any("size must be positive" in e for e in errors))
        
        # Test non-numeric size
        data = self.valid_data.copy()
        data['size'] = 'not_a_number'
        errors = validate_close_position_data(data)
        self.assertTrue(any("size must be a number" in e for e in errors))


class TestInputSanitization(unittest.TestCase):
    """Test cases for input sanitization."""
    
    def test_string_sanitization(self):
        """Test sanitization of string inputs."""
        sanitized_value = sanitize_input("hello<script>alert(xss)</script>")
        self.assertNotIn("<script>", sanitized_value)
        self.assertNotIn("</script>", sanitized_value)
        self.assertEqual(sanitized_value, "helloalert(xss)")
        
    def test_number_sanitization(self):
        """Test sanitization of numeric inputs."""
        # Test valid integer
        value, is_valid = sanitize_input("123", int)
        self.assertEqual(value, 123)
        self.assertTrue(is_valid)
        
        # Test valid float
        value, is_valid = sanitize_input("123.45", float)
        self.assertEqual(value, 123.45)
        self.assertTrue(is_valid)
        
        # Test invalid number
        value, is_valid = sanitize_input("not_a_number", int)
        self.assertIsNone(value)
        self.assertFalse(is_valid)
        
    def test_boolean_sanitization(self):
        """Test sanitization of boolean inputs."""
        # Test boolean true values
        for true_value in ["true", "yes", "1", "on", True, 1]:
            value, is_valid = sanitize_input(true_value, bool)
            self.assertTrue(value)
            self.assertTrue(is_valid)
            
        # Test boolean false values
        for false_value in ["false", "no", "0", "off", False, 0]:
            value, is_valid = sanitize_input(false_value, bool)
            self.assertFalse(value)
            self.assertTrue(is_valid)
            
        # Test invalid boolean
        value, is_valid = sanitize_input("not_a_boolean", bool)
        self.assertIsNone(value)
        self.assertFalse(is_valid)


class TestApiInputValidation(unittest.TestCase):
    """Test cases for API input validation against schemas."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample schema for testing
        self.test_schema = {
            'name': {'type': str, 'required': True, 'max_length': 50},
            'age': {'type': int, 'required': True},
            'email': {'type': str, 'required': False},
            'is_active': {'type': bool, 'required': False, 'default': True},
            'role': {'type': str, 'required': False, 'allowed_values': ['admin', 'user', 'guest']}
        }
        
    def test_valid_input(self):
        """Test validation with valid input."""
        data = {
            'name': 'John Doe',
            'age': 30,
            'email': 'john@example.com',
            'is_active': True,
            'role': 'admin'
        }
        sanitized, errors = validate_api_input(data, self.test_schema)
        self.assertEqual(errors, [])
        self.assertEqual(sanitized['name'], 'John Doe')
        self.assertEqual(sanitized['age'], 30)
        self.assertEqual(sanitized['email'], 'john@example.com')
        self.assertTrue(sanitized['is_active'])
        self.assertEqual(sanitized['role'], 'admin')
        
    def test_missing_required_field(self):
        """Test validation with missing required field."""
        data = {
            'name': 'John Doe'
            # missing 'age' which is required
        }
        sanitized, errors = validate_api_input(data, self.test_schema)
        self.assertIn("Missing required field: age", errors)
        
    def test_default_values(self):
        """Test that default values are used when fields are missing."""
        data = {
            'name': 'John Doe',
            'age': 30
            # missing 'is_active' which has a default value
        }
        sanitized, errors = validate_api_input(data, self.test_schema)
        self.assertEqual(errors, [])
        self.assertTrue(sanitized['is_active'])  # should use default value
        
    def test_invalid_type(self):
        """Test validation with invalid type."""
        data = {
            'name': 'John Doe',
            'age': 'thirty'  # should be an integer
        }
        sanitized, errors = validate_api_input(data, self.test_schema)
        self.assertTrue(any("Invalid type for age" in e for e in errors))
        
    def test_allowed_values(self):
        """Test validation against allowed values."""
        # Test valid role
        data = {
            'name': 'John Doe',
            'age': 30,
            'role': 'admin'  # valid role
        }
        sanitized, errors = validate_api_input(data, self.test_schema)
        self.assertEqual(errors, [])
        
        # Test invalid role
        data = {
            'name': 'John Doe',
            'age': 30,
            'role': 'superuser'  # invalid role
        }
        sanitized, errors = validate_api_input(data, self.test_schema)
        self.assertTrue(any("Invalid value for role" in e for e in errors))


if __name__ == '__main__':
    unittest.main()