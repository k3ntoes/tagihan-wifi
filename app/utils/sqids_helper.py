"""
Sqids helper utilities for encoding/decoding ID strings.

Sqids is used to convert integer IDs to short, unique, URL-safe strings.
This allows us to expose integer IDs safely in API URLs without revealing
sensitive information about ID sequences.

Example:
    >>> from app.utils.sqids_helper import SqidsHelper
    >>> helper = SqidsHelper()
    >>> sqid = helper.encode([123])
    >>> helper.decode(sqid)
    [123]
"""

from sqids import Sqids

from app.core.config import settings


class SqidsHelper:
    """
    Helper class for Sqids encoding/decoding operations.
    
    Provides convenient methods to convert between integer IDs and
    URL-safe short strings using consistent configuration.
    """

    def __init__(self):
        """Initialize Sqids with configured alphabet."""
        self.sqids = Sqids(alphabet=settings.SQIDS_ALPHABET, min_length=8)

    def encode(self, numbers: list[int]) -> str:
        """
        Encode integer IDs to Sqid string.

        Args:
            numbers: List of integers to encode (typically single ID)

        Returns:
            URL-safe Sqid string

        Example:
            >>> encode([123]) -> "ABC123xyz"
        """
        try:
            return self.sqids.encode(numbers)
        except Exception as e:
            raise ValueError(f"Failed to encode numbers: {e}")

    def decode(self, sqid: str) -> list[int]:
        """
        Decode Sqid string back to integer IDs.

        Args:
            sqid: Sqid string to decode

        Returns:
            List of decoded integers

        Example:
            >>> decode("ABC123xyz") -> [123]
        """
        try:
            result = self.sqids.decode(sqid)
            return list(result) if result else []
        except Exception as e:
            raise ValueError(f"Failed to decode sqid: {e}")

    def encode_single(self, number: int) -> str:
        """Encode single integer to Sqid string."""
        return self.encode([number])

    def decode_single(self, sqid: str) -> int:
        """Decode Sqid string to single integer."""
        decoded = self.decode(sqid)
        if not decoded:
            raise ValueError(f"Invalid sqid: {sqid}")
        return decoded[0]


# Singleton instance
_sqids_helper = None


def get_sqids_helper() -> SqidsHelper:
    """Get or create singleton Sqids helper instance."""
    global _sqids_helper
    if _sqids_helper is None:
        _sqids_helper = SqidsHelper()
    return _sqids_helper
