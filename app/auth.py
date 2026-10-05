"""
Simple auth helpers for citizen login/registration.

Deliberately uses only Python's built-in hashlib/secrets (no bcrypt/passlib)
to avoid the Windows compiler issues those packages sometimes trigger — see
the IndicTransToolkit saga earlier in this project's history. This is
adequate for a student project demo; it is NOT the same hardening a real
production auth system would need (e.g. rate limiting, password complexity
rules, HTTPS-only tokens).
"""
import hashlib
import secrets


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Returns (hash, salt). Generates a new random salt if none is given."""
    if salt is None:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return pw_hash, salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    test_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(test_hash, expected_hash)


def generate_token() -> str:
    return secrets.token_hex(24)
