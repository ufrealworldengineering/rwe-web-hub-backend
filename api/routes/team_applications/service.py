from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from db.models import Team
from .schemas import pack_metadata


def get_team(db: Session, team_id: UUID) -> Optional[Team]:
    return db.query(Team).filter(Team.id == team_id).first()


def get_template_for_team(db: Session, team_id: UUID) -> Optional[dict]:
    team = get_team(db, team_id)
    if not team:
        return None
    return team.application_template


def upsert_for_team(db: Session, team_id: UUID, questions: list) -> Optional[Team]:
    team = get_team(db, team_id)
    if not team:
        return None
    team.application_template = pack_metadata(questions)
    db.commit()
    db.refresh(team)
    return team


def delete_for_team(db: Session, team_id: UUID) -> bool:
    team = get_team(db, team_id)
    if not team or not team.application_template:
        return False
    team.application_template = None
    db.commit()
    return True

