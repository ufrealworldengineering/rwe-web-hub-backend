"""
tests/test_teams_router.py

What this file tests:
- RBAC on `/api/teams/` list (president allowed, member forbidden)
- Public-style access to a single team for members with permitted roles
"""

from __future__ import annotations

from tests.conftest import auth_header_for_email, log_passed
from db.models import UserRole


def test_teams_list_allows_president(client, seeded_data):
    """
    Ensures president role can list teams.
    """
    president = seeded_data["president"]
    res = client.get(
        "/api/teams/",
        headers=auth_header_for_email(president.email),
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    log_passed("teams list allows president")


def test_teams_list_forbids_member(client, seeded_data):
    """
    Ensures member role is forbidden from listing teams.
    """
    member = seeded_data["member"]
    res = client.get(
        "/api/teams/",
        headers=auth_header_for_email(member.email),
    )
    assert res.status_code == 403
    log_passed("teams list forbids member")


def test_teams_list_scopes_program_manager_to_managed_program(client, seeded_data):
    pm = seeded_data["program_manager"]
    res = client.get(
        "/api/teams/",
        headers=auth_header_for_email(pm.email),
    )
    assert res.status_code == 200
    ids = {t["id"] for t in res.json()}
    assert str(seeded_data["pm_team"].id) in ids
    assert str(seeded_data["pres_team"].id) not in ids
    log_passed("teams list scopes program manager")


def test_get_team_allows_member_role(client, seeded_data, db_session):
    """
    Ensures a user with member role can access `/api/teams/{team_id}` (per RBAC config).
    """
    from db.models import User, UserRole

    team = seeded_data["team"]

    member_user = seeded_data["member"]
    member_user.role = UserRole.member
    db_session.commit()

    res = client.get(
        f"/api/teams/{team.id}",
        headers=auth_header_for_email(member_user.email),
    )
    assert res.status_code == 200
    log_passed("get single team allows member role")


def test_teams_crud_flow_as_president(client, seeded_data):
    """
    Full CRUD flow for teams:
    - president creates a new team
    - fetches it by id
    - updates the team name
    - deletes the team
    """
    president = seeded_data["president"]
    program = seeded_data["program"]

    create_body = {
        "name": "Flow Test Team",
        "program": str(program.id),
        "active": True,
    }

    create_res = client.post(
        "/api/teams/",
        headers=auth_header_for_email(president.email),
        json=create_body,
    )
    assert create_res.status_code == 201
    created = create_res.json()

    get_res = client.get(
        f"/api/teams/{created['id']}",
        headers=auth_header_for_email(president.email),
    )
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Flow Test Team"

    patch_res = client.patch(
        f"/api/teams/{created['id']}",
        headers=auth_header_for_email(president.email),
        json={"name": "Flow Test Team Updated"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Flow Test Team Updated"

    delete_res = client.delete(
        f"/api/teams/{created['id']}",
        headers=auth_header_for_email(president.email),
    )
    assert delete_res.status_code == 204

    gone_res = client.get(
        f"/api/teams/{created['id']}",
        headers=auth_header_for_email(president.email),
    )
    assert gone_res.status_code == 404

    log_passed("teams CRUD flow as president")

