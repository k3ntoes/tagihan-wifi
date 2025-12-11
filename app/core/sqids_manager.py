import random
import secrets
import time
from typing import Optional

from sqids import Sqids

from app.core.config import LOGGER, Settings


class SqidsManager:
    def __init__(self):
        self.settings = Settings()
        self.base_sqids = Sqids(
            alphabet=self.settings.sqids_alphabet,
            min_length=self.settings.sqids_min_length,
        )

    def _shuffle_alphabet(self, alphabet: str, salt: str) -> str:
        alphabet_list = list(alphabet)

        for i, char in enumerate(salt):
            seed_val = ord(char) + i
            # Use random.Random instead of SystemRandom for deterministic shuffle
            random.Random(seed_val).shuffle(alphabet_list)

        return "".join(alphabet_list)

    def encode(self, number: int, salt: Optional[int] = None) -> str:
        random1 = secrets.randbelow(1_000)
        random2 = secrets.randbelow(10_000)
        timestamp_component = int(time.time() * 1000) % 100_000
        return (
            self.base_sqids.encode([number, random1, random2, timestamp_component])
            if not salt
            else self.base_sqids.encode([number, salt])
        )

    def decode(self, encoded_str: str) -> Optional[int]:
        try:
            decode_numbers = self.base_sqids.decode(encoded_str)
            return decode_numbers[0]
        except Exception as e:
            LOGGER.error(f"Error decoding sqid: {e}")
            return None


def get_sqids_manager():
    return SqidsManager()
