"""
tests/test_auth_routes.py

What this file tests:
- `/api/auth/login` issues access + refresh tokens for valid credentials
- `/api/auth/login` rejects invalid credentials
- `/api/auth/refresh` returns a new access token from a valid refresh token
"""

from __future__ import annotations

from tests.conftest import log_passed


def test_login_success_issues_tokens(client, seeded_data):
    """
    Ensures login with correct email/password returns access and refresh tokens.
    """
    president = seeded_data["president"]
    res = client.post(
        "/api/auth/login",
        data={"username": president.email, "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    log_passed("auth login success issues tokens")


def test_login_rejects_bad_password(client, seeded_data):
    """
    Ensures login with an incorrect password is rejected with 401.
    """
    president = seeded_data["president"]
    res = client.post(
        "/api/auth/login",
        data={"username": president.email, "password": "wrong-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 401
    log_passed("auth login rejects bad password")


def test_refresh_returns_new_access_token(client, seeded_data):
    """
    Ensures `/api/auth/refresh` accepts a valid refresh token and returns a new access token.
    """
    president = seeded_data["president"]
    login_res = client.post(
        "/api/auth/login",
        data={"username": president.email, "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_res.status_code == 200
    tokens = login_res.json()

    refresh_res = client.post(
        "/api/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    log_passed("auth refresh returns new access token")

