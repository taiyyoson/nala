"""
Subscribers Package - Event handlers for the pub/sub system

This package contains subscribers that listen to events and perform
actions, primarily focused on database persistence operations.
"""

from .database_subscriber import DatabaseSubscriber, database_subscriber

__all__ = [
    "DatabaseSubscriber",
    "database_subscriber",
]
