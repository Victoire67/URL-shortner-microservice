class ShortCodeNotFound(Exception):
    """Raised when a short code does not exist in storage."""


class ShortCodeGenerationError(Exception):
    """Raised when a unique short code could not be generated."""
