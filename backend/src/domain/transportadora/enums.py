"""Transportadora enumerations."""

from enum import Enum


class TransportadoraStatus(str, Enum):
    """Status of a Transportadora."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
