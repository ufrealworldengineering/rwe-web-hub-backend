"""
tests/test_team_applications.py

What this file tests:
- Public retrieval of a team's application template/questions
- RBAC enforcement for writing/deleting application templates
- Validation of question structure (supported types + multiple choice options + unique ids)

These tests run against a real Postgres test database (DATABASE_URL_TEST).
Each test rolls back its DB changes for isolation.
"""

from __future__ import annotations

from tests.conftest import auth_header_for_email, log_passed


def test_public_get_returns_404_when_not_configured(client, seeded_data):
    """
    Ensures the public GET endpoint returns 404 when a team has no application template.
    """
    team = seeded_data["pres_team"]
    res = client.get(f"/api/teams/{team.id}/application-template")
    assert res.status_code == 404
    log_passed("public get returns 404 when not configured")


def test_president_can_upsert_and_public_can_read(client, seeded_data):
    """
    Ensures an admin (president) can create/update a team's template, and the public can fetch it.
    """
    team = seeded_data["team"]
    president = seeded_data["president"]

    put_body = {
        "questions": [
            {
                "id": "why",
                "question": "Why do you want to join?",
                "type": "input",
                "required": True,
                "placeholder": "Short answer",
            },
            {
                "id": "exp",
                "question": "Have you used Git before?",
                "type": "multiple_choice",
                "required": True,
                "options": ["Yes", "No"],
            },
        ]
    }

    put_res = client.put(
        f"/api/teams/{team.id}/application-template",
        headers=auth_header_for_email(president.email),
        json=put_body,
    )
    assert put_res.status_code == 200
    data = put_res.json()
    assert data["team_id"] == str(team.id)
    assert len(data["questions"]) == 2

    get_res = client.get(f"/api/teams/{team.id}/application-template")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert [q["id"] for q in get_data["questions"]] == ["why", "exp"]
    log_passed("president can upsert and public can read")


def test_member_cannot_upsert_template(client, seeded_data):
    """
    Ensures RBAC blocks non-admin roles (member) from modifying a team's application template.
    """
    team = seeded_data["team"]
    member = seeded_data["member"]

    res = client.put(
        f"/api/teams/{team.id}/application-template",
        headers=auth_header_for_email(member.email),
        json={"questions": [{"id": "q1", "question": "Q?", "type": "input", "required": True}]},
    )
    assert res.status_code == 403
    log_passed("member cannot upsert template")


def test_validation_rejects_duplicate_question_ids(client, seeded_data):
    """
    Ensures validation rejects duplicate question ids within the same template.
    """
    team = seeded_data["team"]
    president = seeded_data["president"]

    body = {
        "questions": [
            {"id": "dup", "question": "First?", "type": "input", "required": True},
            {"id": "dup", "question": "Second?", "type": "input", "required": True},
        ]
    }
    res = client.put(
        f"/api/teams/{team.id}/application-template",
        headers=auth_header_for_email(president.email),
        json=body,
    )
    assert res.status_code == 422
    log_passed("validation rejects duplicate question ids")


def test_validation_rejects_multiple_choice_without_options(client, seeded_data):
    """
    Ensures multiple_choice questions require a non-empty options list.
    """
    team = seeded_data["team"]
    president = seeded_data["president"]

    body = {
        "questions": [
            {
                "id": "mc",
                "question": "Pick one",
                "type": "multiple_choice",
                "required": True,
                "options": [],
            }
        ]
    }
    res = client.put(
        f"/api/teams/{team.id}/application-template",
        headers=auth_header_for_email(president.email),
        json=body,
    )
    assert res.status_code == 422
    log_passed("validation rejects multiple choice without options")


def test_only_president_can_delete_template(client, seeded_data):
    """
    Ensures delete is restricted to president role (stronger than upsert roles).
    """
    team = seeded_data["team"]
    president = seeded_data["president"]
    member = seeded_data["member"]

    # Seed a template first.
    client.put(
        f"/api/teams/{team.id}/application-template",
        headers=auth_header_for_email(president.email),
        json={"questions": [{"id": "q1", "question": "Q?", "type": "input", "required": True}]},
    )

    member_del = client.delete(
        f"/api/teams/{team.id}/application-template",
        headers=auth_header_for_email(member.email),
    )
    assert member_del.status_code == 403

    pres_del = client.delete(
        f"/api/teams/{team.id}/application-template",
        headers=auth_header_for_email(president.email),
    )
    assert pres_del.status_code == 204

    after = client.get(f"/api/teams/{team.id}/application-template")
    assert after.status_code == 404
    log_passed("only president can delete template")

