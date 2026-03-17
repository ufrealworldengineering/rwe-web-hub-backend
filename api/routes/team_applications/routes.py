from __future__ import annotations

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, require_roles
from db.models import User, UserRole
from . import service
from .schemas import (
    TeamApplicationResponse,
    TeamApplicationUpdate,
    unpack_metadata,
)


router = APIRouter(prefix="/team-applications", tags=["team-applications"])


@router.get("/team/{team_id}", response_model=TeamApplicationResponse)
def get_team_application_for_team(team_id: UUID, db: Session = Depends(get_db)) -> TeamApplicationResponse:
    """
    Public endpoint to fetch a team's application template/questions.
    Returns 404 if the team has not configured an application yet.
    """
    metadata_json = service.get_template_for_team(db, team_id)
    if not metadata_json:
        raise HTTPException(status_code=404, detail="Team application not found")
    return TeamApplicationResponse(team_id=team_id, questions=unpack_metadata(metadata_json))


@router.put(
    "/team/{team_id}",
    response_model=TeamApplicationResponse,
    status_code=status.HTTP_200_OK,
)
def upsert_team_application_for_team(
    team_id: UUID,
    body: TeamApplicationUpdate,
    current_user: Annotated[User, Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager]))],
    db: Session = Depends(get_db),
) -> TeamApplicationResponse:
    """
    Admin endpoint: create or replace the application questions for a team.
    """
    if body.questions is None:
        raise HTTPException(status_code=422, detail="questions is required")

    team = service.upsert_for_team(db, team_id=team_id, questions=body.questions)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamApplicationResponse(team_id=team_id, questions=body.questions)


@router.delete("/team/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team_application_for_team(
    team_id: UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.president]))],
    db: Session = Depends(get_db),
):
    """
    Admin endpoint: delete a team's application template.
    """
    ok = service.delete_for_team(db, team_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Team application not found")
    return None

