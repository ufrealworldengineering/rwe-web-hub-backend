from __future__ import annotations

import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.deps import hash_password
from api.core.security import create_access_token
from db.models import Base, Program, Team, User, UserRole
from db.session import SessionLocal, engine


@dataclass(frozen=True)
class SeedUser:
    email: str
    role: UserRole
    password: str
    is_active: bool = True
    first_name: Optional[str] = None
    last_name: Optional[str] = None


def _env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


def upsert_user(db, su: SeedUser) -> User:
    existing = db.query(User).filter(User.email == su.email).first()
    if existing:
        existing.role = su.role
        existing.is_active = su.is_active
        existing.first_name = su.first_name
        existing.last_name = su.last_name
        # Always reset to the shared dev password (intended for non-prod usage).
        existing.password_hash = hash_password(su.password)
        db.commit()
        db.refresh(existing)
        return existing

    created = User(
        id=uuid.uuid4(),
        email=su.email,
        role=su.role,
        password_hash=hash_password(su.password),
        is_active=su.is_active,
        first_name=su.first_name,
        last_name=su.last_name,
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return created


def upsert_program(db, *, name: str, manager_id: uuid.UUID) -> Program:
    existing = db.query(Program).filter(Program.name == name).first()
    if existing:
        existing.manager = manager_id
        existing.active = True
        db.commit()
        db.refresh(existing)
        return existing

    created = Program(id=uuid.uuid4(), name=name, manager=manager_id, active=True)
    db.add(created)
    db.commit()
    db.refresh(created)
    return created


def upsert_team(db, *, name: str, program_id: uuid.UUID) -> Team:
    existing = db.query(Team).filter(Team.name == name, Team.program == program_id).first()
    if existing:
        existing.active = True
        db.commit()
        db.refresh(existing)
        return existing

    created = Team(id=uuid.uuid4(), name=name, program=program_id, active=True)
    db.add(created)
    db.commit()
    db.refresh(created)
    return created


def set_team_application_template(db, *, team_id: uuid.UUID, questions: list) -> None:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise RuntimeError(f"Team not found for template: {team_id}")
    # Stored format matches what `unpack_metadata()` reads:
    # {"questions": [ {id, question, type, ...}, ... ]}
    team.application_template = {"questions": questions}
    db.commit()


def main() -> int:
    load_dotenv()

    # Guardrail: never run seeding against production.
    env_name = os.getenv("ENV", "local").lower()
    if env_name in {"prod", "production"}:
        raise RuntimeError("Refusing to run seed script with ENV=production.")

    # Ensure JWT secrets exist (token creation reads env at import time).
    os.environ.setdefault("SECRET_KEY", "dev-secret-key")
    os.environ.setdefault("REFRESH_SECRET_KEY", "dev-refresh-secret-key")

    # Ensure DB is reachable and tables exist (works for fresh local DBs).
    Base.metadata.create_all(bind=engine)

    shared_password = os.getenv("SEED_DEV_PASSWORD", "devpassword123")
    email_domain = os.getenv("SEED_EMAIL_DOMAIN", "example.com").lstrip("@")

    default_questions = [
        {
            "id": "year",
            "question": "What year are you in?",
            "type": "multiple_choice",
            "required": True,
            "options": ["first", "second", "third", "fourth", "other"],
        },
        {
            "id": "why_join",
            "question": "Why join RWE?",
            "type": "input",
            "required": True,
            "placeholder": "Tell us what you're hoping to learn or build",
        },
        {
            "id": "background",
            "question": "Explain your background and experience",
            "type": "input",
            "required": True,
            "placeholder": "Projects, tools, coursework, clubs, anything relevant",
        },
    ]

    seed_users = [
        SeedUser(
            email=f"president@{email_domain}",
            role=UserRole.president,
            password=shared_password,
            first_name="Dev",
            last_name="President",
        ),
        SeedUser(
            email=f"treasurer@{email_domain}",
            role=UserRole.treasurer,
            password=shared_password,
            first_name="Dev",
            last_name="Treasurer",
        ),
        SeedUser(
            email=f"web.manager@{email_domain}",
            role=UserRole.program_manager,
            password=shared_password,
            first_name="Dev",
            last_name="WebManager",
        ),
        SeedUser(
            email=f"mech.manager@{email_domain}",
            role=UserRole.program_manager,
            password=shared_password,
            first_name="Dev",
            last_name="MechManager",
        ),
    ]

    with SessionLocal() as db:
        created_users = [upsert_user(db, su) for su in seed_users]

        president = next(u for u in created_users if u.role == UserRole.president)
        web_manager = next(u for u in created_users if u.email == f"web.manager@{email_domain}")
        mech_manager = next(u for u in created_users if u.email == f"mech.manager@{email_domain}")

        web_program = upsert_program(db, name="Web Hub (Dev)", manager_id=web_manager.id)
        web_frontend_id = upsert_team(db, name="Frontend Team (Dev)", program_id=web_program.id).id
        web_backend_id = upsert_team(db, name="Backend Team (Dev)", program_id=web_program.id).id

        mech_program = upsert_program(db, name="Mechanical Engineering", manager_id=mech_manager.id)
        robot_arm_id = upsert_team(db, name="Robot Arm", program_id=mech_program.id).id

        for tid in (web_frontend_id, web_backend_id, robot_arm_id):
            set_team_application_template(db, team_id=tid, questions=default_questions)

    # Create 5 members per team via the real API endpoint (RBAC + validation).
    from fastapi.testclient import TestClient
    from main import app

    token = create_access_token(subject=f"president@{email_domain}")
    headers = {"Authorization": f"Bearer {token}"}

    client = TestClient(app)

    teams = [
        ("frontend", web_frontend_id),
        ("backend", web_backend_id),
        ("robotarm", robot_arm_id),
    ]

    for prefix, team_id in teams:
        for i in range(1, 6):
            payload = {
                "team": str(team_id),
                "first_name": f"{prefix.capitalize()}Member{i}",
                "last_name": "Seeded",
                "email": f"{prefix}.member{i}@{email_domain}",
            }
            res = client.post("/api/members/", headers=headers, json=payload)
            if res.status_code not in (200, 201):
                raise RuntimeError(f"Failed to create member via endpoint: {res.status_code} {res.text}")

    print("Seed complete.\n")
    print("Share these dev credentials with the frontend team:")
    print(f"  Shared password: {shared_password}")
    for su in seed_users:
        print(f"  - {su.role.value:15} {su.email}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

