"""
tests/conftest.py

Pytest fixtures:
- Provision a Postgres-backed test DB session (DATABASE_URL_TEST).
- Create the schema once per session; rollback data after each test.
- Provide a FastAPI TestClient with dependency override for get_db().
- Provide simple seeded objects (users/program/team) used across tests.
"""

from __future__ import annotations

import os
from typing import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


# Ensure JWT secrets exist for tests (api.core.security reads env at import time).
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key")


def _get_test_db_url() -> str | None:
    url = os.getenv("DATABASE_URL_TEST")
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


@pytest.fixture(scope="session")
def test_engine():
    """
    Create the SQLAlchemy engine for the test database.

    Requires DATABASE_URL_TEST (Postgres). If not set, tests are skipped.
    """
    url = _get_test_db_url()
    if not url:
        pytest.skip("DATABASE_URL_TEST is not set; skipping DB integration tests.")

    engine = create_engine(url, echo=False, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except OperationalError as e:
        raise RuntimeError(
            "Could not connect to DATABASE_URL_TEST. "
            "Verify Postgres is running and credentials are correct.\n"
            f"DATABASE_URL_TEST={url}\n"
            f"Original error: {e}"
        ) from e
    return engine


@pytest.fixture(scope="session", autouse=True)
def _create_schema(test_engine):
    """
    Create all tables once for the test session.
    """
    from db.models import Base

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Database session scoped to a single test.
    All changes are rolled back at the end of the test.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """
    FastAPI TestClient with DB dependency override to use the test session.
    """
    from api.deps import get_db
    from main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture()
def seeded_data(db_session: Session) -> dict:
    """
    Naive fake data dump for tests:
    - users: president + member + program_manager
    - programs: one managed by program_manager, one by president
    - teams: one in each program
    - members: one in each team
    """
    import uuid

    from api.deps import hash_password
    from db.models import Member, Program, Team, User, UserRole

    president = User(
        id=uuid.uuid4(),
        email="president@example.com",
        role=UserRole.president,
        password_hash=hash_password("password123"),
        is_active=True,
    )
    program_manager = User(
        id=uuid.uuid4(),
        email="pm@example.com",
        role=UserRole.program_manager,
        password_hash=hash_password("password123"),
        is_active=True,
    )
    member = User(
        id=uuid.uuid4(),
        email="member@example.com",
        role=UserRole.member,
        password_hash=hash_password("password123"),
        is_active=True,
    )
    pm_program = Program(id=uuid.uuid4(), name="PM Program", manager=program_manager.id, active=True)
    pres_program = Program(id=uuid.uuid4(), name="President Program", manager=president.id, active=True)
    pm_team = Team(id=uuid.uuid4(), name="PM Team", program=pm_program.id, active=True)
    pres_team = Team(id=uuid.uuid4(), name="President Team", program=pres_program.id, active=True)
    pm_team.application_template = {
        "questions": [
            {
                "id": "year",
                "question": "What year are you in?",
                "type": "multiple_choice",
                "required": True,
                "options": ["first", "second", "third", "fourth", "other"],
            },
            {"id": "why_join", "question": "Why join RWE?", "type": "input", "required": True},
            {
                "id": "background",
                "question": "Explain your background and experience",
                "type": "input",
                "required": True,
            },
        ]
    }
    pm_member = Member(id=uuid.uuid4(), team=pm_team.id, first_name="PM", last_name="Member", email="pm.member@example.com")
    pres_member = Member(id=uuid.uuid4(), team=pres_team.id, first_name="Pres", last_name="Member", email="pres.member@example.com")

    db_session.add_all(
        [president, program_manager, member, pm_program, pres_program, pm_team, pres_team, pm_member, pres_member]
    )
    db_session.commit()

    return {
        "president": president,
        "program_manager": program_manager,
        "member": member,
        "pm_program": pm_program,
        "pres_program": pres_program,
        "pm_team": pm_team,
        "pres_team": pres_team,
        "pm_member": pm_member,
        "pres_member": pres_member,
        # Backwards compat for older tests that assume one program/team exist.
        "program": pm_program,
        "team": pm_team,
    }


def auth_header_for_email(email: str) -> dict:
    from api.core.security import create_access_token

    token = create_access_token(subject=email)
    return {"Authorization": f"Bearer {token}"}


def log_passed(message: str) -> None:
    """
    Small helper so tests can consistently print a one-line '... - passed' message.
    """
    print(f"{message} - passed")

