"""Remetente enumerations."""

from enum import Enum


class RemetenteStatus(str, Enum):
    """Status of a Remetente."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
