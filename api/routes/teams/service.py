from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload

from db.models import Team

def get_team(db: Session, team_id: UUID, include_program: bool = False) -> Optional[Team]:
    """Get a single team by ID"""
    query = db.query(Team)
    if include_program:
        query = query.options(joinedload(Team.program_rel))
    return query.filter(Team.id == team_id).first()

def get_teams(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    include_program: bool = False
) -> List[Team]:
    """Get all teams with pagination"""
    query = db.query(Team)
    
    if include_program:
        query = query.options(joinedload(Team.program_rel))
    
    if active_only:
        query = query.filter(Team.active == True)
    
    return query.offset(skip).limit(limit).all()

def get_teams_by_program(db: Session, program_id: UUID, active_only: bool = False) -> List[Team]:
    """Get all teams for a specific program"""
    query = db.query(Team).filter(Team.program == program_id)
    
    if active_only:
        query = query.filter(Team.active == True)
    
    return query.all()

def create_team(db: Session, team_data: dict) -> Team:
    """Create a new team"""
    db_team = Team(**team_data)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

def update_team(db: Session, team_id: UUID, team_update: dict) -> Optional[Team]:
    """Update a team"""
    db_team = get_team(db, team_id)
    if not db_team:
        return None
    
    for field, value in team_update.items():
        setattr(db_team, field, value)
    
    db.commit()
    db.refresh(db_team)
    return db_team

def delete_team(db: Session, team_id: UUID) -> bool:
    """Delete a team"""
    db_team = get_team(db, team_id)
    if not db_team:
        return False
    
    db.delete(db_team)
    db.commit()
    return True