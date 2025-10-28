"""Utilities for generating strong passwords."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from typing import List


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


@dataclass(frozen=True)
class PasswordStrength:
    score: int
    label: str
    color: str
    suggestions: List[str]


def estimate_password_strength(password: str) -> PasswordStrength:
    """Rudimentary password strength estimator.

    This avoids third-party dependencies while still giving users actionable
    feedback on how to improve their password choices.
    """

    if not password:
        return PasswordStrength(0, "Empty", "#808080", ["Use at least 12 characters."])

    score = 0
    suggestions: List[str] = []
    length = len(password)

    if length >= 8:
        score += 1
    else:
        suggestions.append("Use at least 8 characters.")

    if length >= 12:
        score += 1
    else:
        suggestions.append("Aim for 12 or more characters.")

    categories = [
        any(c.islower() for c in password),
        any(c.isupper() for c in password),
        any(c.isdigit() for c in password),
        any(c in string.punctuation for c in password),
    ]
    diversity = sum(1 for flag in categories if flag)
    if diversity >= 3:
        score += 1
    else:
        suggestions.append("Mix upper, lower, digits and symbols.")

    if diversity == 4 and length >= 14:
        score += 1
    elif diversity < 4:
        suggestions.append("Add more character types for extra strength.")

    score = max(1, min(score, 4))

    if score <= 1:
        label = "Weak"
        color = "#d64541"
    elif score == 2:
        label = "Fair"
        color = "#e67e22"
    elif score == 3:
        label = "Strong"
        color = "#2980b9"
    else:
        label = "Very strong"
        color = "#27ae60"

    return PasswordStrength(score, label, color, suggestions)
