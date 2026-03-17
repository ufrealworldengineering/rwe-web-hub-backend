"""
tests/test_applications_router.py

What this file tests:
- RBAC on `/api/applications/filter` (president allowed, member forbidden)
- That the filter endpoint responds successfully and returns a JSON list
"""

from __future__ import annotations

from uuid import uuid4

from tests.conftest import auth_header_for_email, log_passed
from db.models import AppStatus, AppYear


def test_applications_filter_allows_president(client, seeded_data):
    """
    Ensures president role can access the applications filter endpoint.
    """
    president = seeded_data["president"]
    res = client.get(
        "/api/applications/filter",
        headers=auth_header_for_email(president.email),
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    log_passed("applications filter allows president")


def test_applications_filter_forbids_member(client, seeded_data):
    """
    Ensures member role is forbidden from accessing the applications filter endpoint.
    """
    member = seeded_data["member"]
    res = client.get(
        "/api/applications/filter",
        headers=auth_header_for_email(member.email),
    )
    assert res.status_code == 403
    log_passed("applications filter forbids member")


def test_applications_flow_public_apply_and_admin_filter(client, seeded_data):
    """
    Simple flow:
    - public applicant submits an application via /apply
    - president can see that application via /filter
    """
    from db.models import Team

    president = seeded_data["president"]
    team = seeded_data["team"]

    # Simulate a minimal form submission for /apply: use multipart form-data.
    files = {
        "resume": ("resume.pdf", b"%PDF-1.4 fake pdf content", "application/pdf"),
    }
    data = {
        "first_name": "App",
        "last_name": "Licant",
        "email": "applicant@example.com",
        "team_id": str(team.id),
        "year": AppYear.first.value,
        "major": "Engineering",
    }

    apply_res = client.post("/api/applications/apply", data=data, files=files)
    assert apply_res.status_code == 201

    filter_res = client.get(
        "/api/applications/filter?email=applicant@example.com",
        headers=auth_header_for_email(president.email),
    )
    assert filter_res.status_code == 200
    apps = filter_res.json()
    assert len(apps) >= 1
    log_passed("applications flow public apply and admin filter")

