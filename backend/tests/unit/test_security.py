from __future__ import annotations

from prepos.core.security import hash_password, verify_password


def test_hash_and_verify_password() -> None:
    hashed = hash_password("StrongPass123!")
    assert hashed != "StrongPass123!"
    assert verify_password("StrongPass123!", hashed)
    assert not verify_password("wrong", hashed)
