"""
tests/test_auth_me.py

What this file tests:
- `/api/auth/me` returns the current user for a valid JWT
- Inactive users are blocked with 403

These tests exercise the JWT dependency + `User.is_active` behavior against the test DB.
"""

from __future__ import annotations

from tests.conftest import auth_header_for_email, log_passed


def test_me_returns_current_user(client, seeded_data):
    """
    Ensures `/api/auth/me` returns the authenticated user's record.
    """
    president = seeded_data["president"]
    res = client.get("/api/auth/me", headers=auth_header_for_email(president.email))
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == president.email
    log_passed("me returns current user")


def test_me_blocks_inactive_user(client, seeded_data, db_session):
    """
    Ensures inactive users cannot access `/api/auth/me` even with a valid JWT.
    """
    member = seeded_data["member"]
    member.is_active = False
    db_session.commit()

    res = client.get("/api/auth/me", headers=auth_header_for_email(member.email))
    assert res.status_code == 403
    log_passed("me blocks inactive user")

