"""
Custom exceptions for the application.
Provides standardized error handling patterns across the codebase.
"""


class IFGenBaseException(Exception):
    """Base exception for the IF Generation Tool."""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ConfigurationError(IFGenBaseException):
    """Raised when there are configuration issues."""

    pass


class AIServiceError(IFGenBaseException):
    """Raised when there are AI service related errors."""

    pass


class DatabaseError(IFGenBaseException):
    """Raised when there are database related errors."""

    pass


class FileProcessingError(IFGenBaseException):
    """Raised when there are file processing errors."""

    pass


class TokenTrackingError(IFGenBaseException):
    """Raised when there are token tracking errors."""

    pass


class ResourceCleanupError(IFGenBaseException):
    """Raised when there are resource cleanup errors."""

    pass


class RetryExhaustedError(IFGenBaseException):
    """Raised when retry attempts are exhausted."""

    def __init__(self, message: str, attempts: int, last_exception: Exception = None):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception
