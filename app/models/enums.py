from enum import Enum


class Role(str, Enum):
    """User role enumeration."""

    ADMIN = "ADMIN"
    USER = "USER"
