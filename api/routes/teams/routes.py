from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas.schemas import TeamCreate, TeamUpdate, TeamResponse, TeamWithProgram
from .service import * 

from api.deps import require_roles
from db.models import UserRole, User

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/", response_model=List[TeamResponse])
def list_teams(
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer])),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = Query(False, description="Filter to only active teams"),
    db: Session = Depends(get_db)
):
    """Get all teams"""
    teams = get_teams(db, skip=skip, limit=limit, active_only=active_only)
    return teams

@router.get("/{team_id}", response_model=TeamWithProgram)
def get_team(
    team_id: UUID,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager, UserRole.member])),
    include_program: bool = Query(True, description="Include program details"),
    db: Session = Depends(get_db)
):
    """Get a specific team by ID"""
    team = get_team(db, team_id, include_program=include_program)
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
    teams = get_teams_by_program(db, program_id, active_only=active_only)
    return teams

@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team: TeamCreate,
    current_user: User = Depends(require_roles([UserRole.president])),
    db: Session = Depends(get_db)
):
    """Create a new team"""
    team_data = team.model_dump()
    return create_team(db, team_data)

@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: UUID,
    team_update: TeamUpdate,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.program_manager])),
    db: Session = Depends(get_db)
):
    """Update a team"""
    update_data = team_update.model_dump(exclude_unset=True)
    team = update_team(db, team_id, update_data)
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
    success = delete_team(db, team_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    return None