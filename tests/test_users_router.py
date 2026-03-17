"""
tests/test_users_router.py

What this file tests:
- RBAC on `/api/users/` list (president allowed, member forbidden)
"""

from __future__ import annotations

from tests.conftest import auth_header_for_email, log_passed
from db.models import UserRole


def test_users_list_allows_president(client, seeded_data):
    """
    Ensures president role can list users.
    """
    president = seeded_data["president"]
    res = client.get(
        "/api/users/",
        headers=auth_header_for_email(president.email),
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    log_passed("users list allows president")


def test_users_list_forbids_member(client, seeded_data):
    """
    Ensures member role is forbidden from listing users.
    """
    member = seeded_data["member"]
    res = client.get(
        "/api/users/",
        headers=auth_header_for_email(member.email),
    )
    assert res.status_code == 403
    log_passed("users list forbids member")


def test_users_crud_flow_as_president(client, seeded_data):
    """
    Full CRUD flow:
    - president creates a new user
    - fetches it by id
    - updates the user
    - deletes the user
    """
    president = seeded_data["president"]

    create_body = {
        "email": "newuser@example.com",
        "role": UserRole.member.value,
        "first_name": "New",
        "last_name": "User",
        "year": None,
        "password": "testpass123",
    }

    create_res = client.post(
        "/api/users/",
        headers=auth_header_for_email(president.email),
        json=create_body,
    )
    assert create_res.status_code == 201
    created = create_res.json()

    get_res = client.get(
        f"/api/users/{created['id']}",
        headers=auth_header_for_email(president.email),
    )
    assert get_res.status_code == 200
    assert get_res.json()["email"] == "newuser@example.com"

    patch_res = client.patch(
        f"/api/users/{created['id']}",
        headers=auth_header_for_email(president.email),
        json={"first_name": "Updated"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["first_name"] == "Updated"

    delete_res = client.delete(
        f"/api/users/{created['id']}",
        headers=auth_header_for_email(president.email),
    )
    assert delete_res.status_code == 204

    gone_res = client.get(
        f"/api/users/{created['id']}",
        headers=auth_header_for_email(president.email),
    )
    assert gone_res.status_code == 404

    log_passed("users CRUD flow as president")

