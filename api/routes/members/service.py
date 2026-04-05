from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload

from db.models import Member, Program, Team

def get_member(db: Session, member_id: UUID, include_team: bool = False) -> Optional[Member]:
    """Get a single member by ID"""
    query = db.query(Member)
    if include_team:
        query = query.options(joinedload(Member.team_rel))
    return query.filter(Member.id == member_id).first()

def get_member_by_email(db: Session, email: str) -> Optional[Member]:
    """Get a member by email"""
    return db.query(Member).filter(Member.email == email).first()

def get_members(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    include_team: bool = False,
    program_manager_user_id: Optional[UUID] = None,
) -> List[Member]:
    """Get all members with pagination"""
    query = db.query(Member)
    
    if include_team:
        query = query.options(
            joinedload(Member.team_rel)
            .joinedload(Team.program_rel)
            .joinedload(Program.manager_rel)
        )

    if program_manager_user_id is not None:
        query = (
            query.join(Member.team_rel)
            .join(Team.program_rel)
            .filter(Program.manager == program_manager_user_id)
        )
    
    return query.offset(skip).limit(limit).all()

def get_members_by_team(db: Session, team_id: UUID, program_manager_user_id: Optional[UUID] = None) -> List[Member]:
    """Get all members for a specific team"""
    query = db.query(Member).filter(Member.team == team_id)
    if program_manager_user_id is not None:
        query = (
            query.join(Member.team_rel)
            .join(Team.program_rel)
            .filter(Program.manager == program_manager_user_id)
        )
    return query.all()

def create_member(db: Session, member_data: dict) -> Member:
    """Create a new member"""
    db_member = Member(**member_data)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def update_member(db: Session, member_id: UUID, member_update: dict) -> Optional[Member]:
    """Update a member"""
    db_member = get_member(db, member_id)
    if not db_member:
        return None
    
    for field, value in member_update.items():
        setattr(db_member, field, value)
    
    db.commit()
    db.refresh(db_member)
    return db_member

def delete_member(db: Session, member_id: UUID) -> bool:
    """Delete a member"""
    db_member = get_member(db, member_id)
    if not db_member:
        return False
    
    db.delete(db_member)
    db.commit()
    return True