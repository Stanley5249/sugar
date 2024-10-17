__all__ = [
    "SugarExit",
    "SugarError",
]


class SugarError(Exception):
    """Exception raised for user input errors during argument parsing."""


class SugarExit(SystemExit):
    """Exception raised when a `SugarError` is suppressed and the application exits."""
