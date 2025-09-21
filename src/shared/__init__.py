"""
Shared modules for the Edeka Scraper project.
Contains database models, repositories, configuration, and AI utilities.
"""
from . import config
from . import database

__all__ = [
    "config",
    "database"
]
