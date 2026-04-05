from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.deps import get_db, require_roles
from api.schemas.schemas import TeamCreate, TeamUpdate, TeamResponse, TeamWithProgram
from . import service as team_service
from db.models import UserRole, User
from api.routes.team_applications.schemas import TeamApplicationResponse, TeamApplicationUpdate, unpack_metadata
from api.routes.team_applications.service import delete_for_team, get_template_for_team, upsert_for_team

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/directory", response_model=List[TeamWithProgram])
def list_teams_public(
    active_only: bool = Query(True, description="Only return active teams"),
    db: Session = Depends(get_db),
):
    """Public read-only list of teams (for the marketing site)."""
    return team_service.get_teams(
        db,
        skip=0,
        limit=500,
        active_only=active_only,
        include_program=True,
        manager_user=None,
    )


@router.get("/", response_model=List[TeamResponse])
def list_teams(
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = Query(False, description="Filter to only active teams"),
    db: Session = Depends(get_db)
):
    """Get all teams"""
    teams = team_service.get_teams(
        db,
        skip=skip,
        limit=limit,
        active_only=active_only,
        manager_user=current_user if current_user.role == UserRole.program_manager else None,
    )
    return teams

@router.get("/{team_id}", response_model=TeamWithProgram)
def get_team(
    team_id: UUID,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager, UserRole.member])),
    include_program: bool = Query(True, description="Include program details"),
    db: Session = Depends(get_db)
):
    """Get a specific team by ID"""
    team = team_service.get_team(db, team_id, include_program=include_program)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return team

@router.get("/program/{program_id}", response_model=List[TeamResponse])
def get_teams_by_program(
    program_id: UUID,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    active_only: bool = Query(False, description="Filter to only active teams"),
    db: Session = Depends(get_db)
):
    """Get all teams for a specific program"""
    teams = team_service.get_teams_by_program(db, program_id, active_only=active_only)
    return teams

@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team: TeamCreate,
    current_user: User = Depends(require_roles([UserRole.president])),
    db: Session = Depends(get_db)
):
    """Create a new team"""
    team_data = team.model_dump()
    return team_service.create_team(db, team_data)

@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: UUID,
    team_update: TeamUpdate,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.program_manager])),
    db: Session = Depends(get_db)
):
    """Update a team"""
    update_data = team_update.model_dump(exclude_unset=True)
    team = team_service.update_team(db, team_id, update_data)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return team

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: UUID,
    current_user: User = Depends(require_roles([UserRole.president])),
    db: Session = Depends(get_db)
):
    """Delete a team"""
    success = team_service.delete_team(db, team_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return None


@router.get("/{team_id}/application-template", response_model=TeamApplicationResponse)
def get_team_application_template(team_id: UUID, db: Session = Depends(get_db)) -> TeamApplicationResponse:
    """
    Public endpoint to fetch a team's application template/questions.
    Returns 404 if the team has not configured an application yet.
    """
    metadata_json = get_template_for_team(db, team_id)
    if not metadata_json:
        raise HTTPException(status_code=404, detail="Team application not found")
    return TeamApplicationResponse(team_id=team_id, questions=unpack_metadata(metadata_json))


@router.put(
    "/{team_id}/application-template",
    response_model=TeamApplicationResponse,
    status_code=status.HTTP_200_OK,
)
def upsert_team_application_template(
    team_id: UUID,
    body: TeamApplicationUpdate,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    db: Session = Depends(get_db),
) -> TeamApplicationResponse:
    """
    Admin endpoint: create or replace the application questions for a team.
    """
    if body.questions is None:
        raise HTTPException(status_code=422, detail="questions is required")

    team = upsert_for_team(db, team_id=team_id, questions=body.questions)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamApplicationResponse(team_id=team_id, questions=body.questions)


@router.delete("/{team_id}/application-template", status_code=status.HTTP_204_NO_CONTENT)
def delete_team_application_template(
    team_id: UUID,
    current_user: User = Depends(require_roles([UserRole.president])),
    db: Session = Depends(get_db),
):
    """
    Admin endpoint: delete a team's application template.
    """
    ok = delete_for_team(db, team_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Team application not found")
    return None