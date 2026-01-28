"""
Sqids helper utilities for encoding/decoding ID strings with Laravel-style prefixes.

Inspired by Laravel Sqids library, this helper:
- Adds model-specific prefixes (e.g., 'cust_', 'pack_', 'pay_', 'user_')
- Appends random key for additional security
- Converts integer IDs to short, unique, URL-safe strings

Format: {prefix}{encoded_id}_{random_key}
Example: cust_ABC123xyz_aB9

This approach:
- Prevents ID enumeration attacks
- Adds context to IDs (what model they belong to)
- Makes IDs more secure with random suffix
- Maintains URL-safe format

Example:
    >>> from app.utils.sqids_helper import SqidsHelper
    >>> helper = SqidsHelper()
    >>> sqid = helper.encode_with_prefix(123, 'customer')
    >>> # Returns: "cust_ABC123xyz_aB9"
    >>> helper.decode_with_prefix(sqid)
    >>> # Returns: (123, 'customer')
"""

import secrets
import string
from typing import Tuple, Optional

from sqids import Sqids

from app.core.config import settings


class SqidsHelper:
    """
    Laravel-inspired Sqids helper for encoding/decoding with model prefixes and random keys.
    
    Provides convenient methods to convert between integer IDs and
    URL-safe short strings with model context and security enhancement.
    
    Model Prefixes:
    - customer: 'cust_'
    - package: 'pack_'
    - payment: 'pay_'
    - user: 'user_'
    - default: 'id_'
    """

    # Model prefix mapping (Laravel Sqids style)
    MODEL_PREFIXES = {
        'customer': 'cust_',
        'package': 'pack_',
        'payment': 'pay_',
        'user': 'user_',
    }

    # Random key configuration
    RANDOM_KEY_LENGTH = 6  # Length of random suffix
    RANDOM_KEY_CHARSET = string.ascii_letters + string.digits  # a-z, A-Z, 0-9

    def __init__(self):
        """Initialize Sqids with configured alphabet."""
        self.sqids = Sqids(alphabet=settings.SQIDS_ALPHABET, min_length=8)

    def _generate_random_key(self) -> str:
        """
        Generate cryptographically secure random key for ID obfuscation.
        
        Returns:
            Random string of configured length using alphanumeric characters
            
        Example:
            >>> _generate_random_key() -> "aB9xYz"
        """
        return ''.join(secrets.choice(self.RANDOM_KEY_CHARSET) for _ in range(self.RANDOM_KEY_LENGTH))

    def _get_prefix(self, model: str) -> str:
        """
        Get prefix for given model name.
        
        Args:
            model: Model name (e.g., 'customer', 'package')
            
        Returns:
            Prefix string (e.g., 'cust_', 'pack_')
        """
        return self.MODEL_PREFIXES.get(model.lower(), 'id_')

    def _extract_prefix(self, sqid: str) -> Optional[str]:
        """
        Extract model prefix from sqid string.
        
        Args:
            sqid: Full sqid string with prefix
            
        Returns:
            Model name if prefix found, None otherwise
        """
        for model, prefix in self.MODEL_PREFIXES.items():
            if sqid.startswith(prefix):
                return model
        return None

    def encode_with_prefix(self, number: int, model: str) -> str:
        """
        Encode integer ID with model prefix and random key (Laravel Sqids style).
        
        Format: {prefix}{encoded_id}_{random_key}
        
        Args:
            number: Integer ID to encode
            model: Model name (customer, package, payment, user)
            
        Returns:
            Full sqid string with prefix and random key
            
        Example:
            >>> encode_with_prefix(123, 'customer')
            >>> # Returns: "cust_ABC123xyz_aB9xYz"
        """
        try:
            prefix = self._get_prefix(model)
            encoded = self.sqids.encode([number])
            random_key = self._generate_random_key()
            return f"{prefix}{encoded}_{random_key}"
        except Exception as e:
            raise ValueError(f"Failed to encode {model} ID {number}: {e}")

    def decode_with_prefix(self, sqid: str) -> Tuple[int, Optional[str]]:
        """
        Decode sqid string with prefix and random key back to integer ID and model.
        
        Args:
            sqid: Full sqid string (format: {prefix}{encoded_id}_{random_key})
            
        Returns:
            Tuple of (decoded_id, model_name)
            
        Raises:
            ValueError: If sqid is invalid or cannot be decoded
            
        Example:
            >>> decode_with_prefix("cust_ABC123xyz_aB9xYz")
            >>> # Returns: (123, 'customer')
        """
        try:
            # Extract model from prefix
            model = self._extract_prefix(sqid)
            
            # Remove prefix
            if model:
                prefix = self._get_prefix(model)
                sqid_without_prefix = sqid[len(prefix):]
            else:
                # Try without known prefix (might be 'id_' or custom)
                if '_' in sqid:
                    parts = sqid.split('_', 1)
                    sqid_without_prefix = parts[1] if len(parts) > 1 else sqid
                else:
                    sqid_without_prefix = sqid
            
            # Remove random key suffix (everything after last underscore)
            if '_' in sqid_without_prefix:
                encoded_part = sqid_without_prefix.rsplit('_', 1)[0]
            else:
                encoded_part = sqid_without_prefix
            
            # Decode the ID
            result = self.sqids.decode(encoded_part)
            if not result:
                raise ValueError(f"Could not decode sqid: {sqid}")
            
            return result[0], model
            
        except Exception as e:
            raise ValueError(f"Failed to decode sqid '{sqid}': {e}")

    def encode(self, numbers: list[int]) -> str:
        """
        Encode integer IDs to Sqid string (basic encoding without prefix).

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
        Decode Sqid string back to integer IDs (basic decoding without prefix handling).

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
        """
        Encode single integer to Sqid string (basic, without prefix).
        
        Note: For production use, prefer encode_with_prefix() for better security.
        """
        return self.encode([number])

    def decode_single(self, sqid: str) -> int:
        """
        Decode Sqid string to single integer (basic, without prefix handling).
        
        Note: For production use, prefer decode_with_prefix() if sqid has prefix.
        """
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
