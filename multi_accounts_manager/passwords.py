"""Utilities for generating strong passwords."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass


@dataclass
class PasswordPolicy:
    length: int = 16
    use_lowercase: bool = True
    use_uppercase: bool = True
    use_digits: bool = True
    use_symbols: bool = True

    def character_pool(self) -> str:
        pool = ""
        if self.use_lowercase:
            pool += string.ascii_lowercase
        if self.use_uppercase:
            pool += string.ascii_uppercase
        if self.use_digits:
            pool += string.digits
        if self.use_symbols:
            pool += string.punctuation
        if not pool:
            raise ValueError("At least one character group must be enabled")
        return pool


def generate_password(policy: PasswordPolicy | None = None) -> str:
    policy = policy or PasswordPolicy()
    pool = policy.character_pool()
    return "".join(secrets.choice(pool) for _ in range(policy.length))
