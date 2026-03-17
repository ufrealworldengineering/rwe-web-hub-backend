"""
tests/test_programs_router.py

What this file tests:
- RBAC on `/api/programs/` list (president allowed, member forbidden)
"""

from __future__ import annotations

from tests.conftest import auth_header_for_email, log_passed


def test_programs_list_allows_president(client, seeded_data):
    """
    Ensures president role can list programs.
    """
    president = seeded_data["president"]
    res = client.get(
        "/api/programs/",
        headers=auth_header_for_email(president.email),
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    log_passed("programs list allows president")


def test_programs_list_forbids_member(client, seeded_data):
    """
    Ensures member role is forbidden from listing programs.
    """
    member = seeded_data["member"]
    res = client.get(
        "/api/programs/",
        headers=auth_header_for_email(member.email),
    )
    assert res.status_code == 403
    log_passed("programs list forbids member")

