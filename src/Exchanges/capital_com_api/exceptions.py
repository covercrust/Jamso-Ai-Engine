"""
Custom exceptions for the Capital.com API client.
"""

class CapitalAPIException(Exception):
    """Base exception for Capital.com API errors."""
    def __init__(self, status_code=None, message=None, response=None):
        self.status_code = status_code
        self.message = message
        self.response = response
        
        # Create a more informative error message
        msg = []
        if status_code:
            msg.append(f"HTTP {status_code}")
        if message:
            msg.append(message)
        
        super().__init__(": ".join(msg) if msg else "Unknown Capital.com API error")

class AuthenticationError(CapitalAPIException):
    """Exception raised for authentication issues."""
    pass

class ConnectionError(CapitalAPIException):
    """Exception raised for network connection issues."""
    pass

class TimeoutError(CapitalAPIException):
    """Exception raised when API request times out."""
    pass

class ValidationError(CapitalAPIException):
    """Exception raised when request validation fails."""
    pass

class RateLimitError(CapitalAPIException):
    """Exception raised when API rate limits are exceeded."""
    pass

class PositionError(CapitalAPIException):
    """Exception raised for position-related errors."""
    pass

class OrderError(CapitalAPIException):
    """Exception raised for order-related errors."""
    pass

class MarketDataError(CapitalAPIException):
    """Exception raised for market data errors."""
    pass

class ParameterError(CapitalAPIException):
    """Exception raised for invalid parameter values."""
    pass

# Map HTTP status codes to exception types
ERROR_CLASSES = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthenticationError,
    404: ValidationError,
    408: TimeoutError,
    429: RateLimitError,
    500: CapitalAPIException,
    502: ConnectionError,
    503: ConnectionError,
    504: TimeoutError
}

def get_exception_for_status(status_code, message=None, response=None):
    """Factory function to create the appropriate exception based on status code."""
    exception_class = ERROR_CLASSES.get(status_code, CapitalAPIException)
    return exception_class(status_code, message, response)