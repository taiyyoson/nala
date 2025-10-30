"""
Adapter Layer - Data Transformation Components

This package contains adapters for transforming data between different layers
of the application (API models <-> Service models <-> RAG system format).
"""

from .request_adapter import RequestAdapter
from .response_adapter import ResponseAdapter

__all__ = [
    "RequestAdapter",
    "ResponseAdapter",
]
