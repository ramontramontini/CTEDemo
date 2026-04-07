"""Cte enumerations."""

from enum import Enum


class CteStatus(str, Enum):
    """Status of a Cte."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
