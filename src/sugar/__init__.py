"""
Simple
Utility for
Generating
Argument
Runners
"""

from sugar._action import Build, Converter, Event, Store, auto
from sugar._app import ArgumentApp, CommandApp, Meta, sugar
from sugar._parser import ArgumentParser, CommandParser

__version__ = "0.1.0"

__all__ = [
    "ArgumentApp",
    "ArgumentParser",
    "Build",
    "CommandApp",
    "CommandParser",
    "Converter",
    "Event",
    "Meta",
    "Store",
    "auto",
    "sugar",
]
