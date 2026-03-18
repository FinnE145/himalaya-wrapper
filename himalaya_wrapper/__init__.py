"""Himalaya CLI wrapper for Python."""

from .client import EmailMessage, HimalayaClient, HimalayaError

__all__ = ["HimalayaClient", "HimalayaError", "EmailMessage"]
__version__ = "0.1.0"
