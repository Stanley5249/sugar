__all__ = [
    "SugarError",
    "SugarExit",
]


class SugarExit(SystemExit):
    """Exception raised when the application exits."""


class SugarError(Exception):
    """Exception raised for errors in the Sugar library."""
