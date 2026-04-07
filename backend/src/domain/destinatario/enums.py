"""Destinatario enumerations."""

from enum import Enum


class DestinatarioStatus(str, Enum):
    """Status of a Destinatario."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
