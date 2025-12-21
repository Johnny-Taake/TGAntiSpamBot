"""
AI Service Errors
"""


class AIServiceError(RuntimeError):
    """Base AI service error."""

    pass


class AIHTTPError(AIServiceError):
    """Raised when HTTP errors occur during AI service requests."""

    pass


class AIResponseFormatError(AIServiceError):
    """Raised when the AI response format is invalid."""

    pass
