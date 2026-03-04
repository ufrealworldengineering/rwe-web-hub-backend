from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas.schemas import MemberCreate, MemberUpdate, MemberResponse, MemberWithTeam
from .service import * 

from deps import get_current_user_with_role
from db.models import UserRole, User

router = APIRouter(prefix="/members", tags=["members"])

@router.get("/", response_model=List[MemberResponse])
def list_members(
    current_user: User = Depends(get_current_user_with_role([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all members"""
    members = get_members(db, skip=skip, limit=limit)
    return members

@router.get("/{member_id}", response_model=MemberWithTeam)
def get_member(
    member_id: UUID,
    include_team: bool = Query(True, description="Include team details"),
    current_user: User = Depends(get_current_user_with_role([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    db: Session = Depends(get_db)
):
    """Get a specific member by ID"""
    member = get_member(db, member_id, include_team=include_team)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    return member

@router.get("/email/{email}", response_model=MemberResponse)
def get_member_by_email(
    email: str,
    current_user: User = Depends(get_current_user_with_role([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    db: Session = Depends(get_db)
):
    """Get a member by email"""
    member = get_member_by_email(db, email)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    return member

@router.get("/team/{team_id}", response_model=List[MemberResponse])
def get_members_by_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user_with_role([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    db: Session = Depends(get_db)
):
    """Get all members for a specific team"""
    members = get_members_by_team(db, team_id)
    return members

@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def create_member(
    member: MemberCreate,
    current_user: User = Depends(get_current_user_with_role([UserRole.president])),
    db: Session = Depends(get_db)
):
    """Create a new member"""
    member_data = member.model_dump()
    return create_member(db, member_data)

@router.patch("/{member_id}", response_model=MemberResponse)
def update_member(
    member_id: UUID,
    member_update: MemberUpdate,
    current_user: User = Depends(get_current_user_with_role([UserRole.president])),
    db: Session = Depends(get_db)
):
    """Update a member"""
    update_data = member_update.model_dump(exclude_unset=True)
    member = update_member(db, member_id, update_data)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    return member

@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    member_id: UUID,
    current_user: User = Depends(get_current_user_with_role([UserRole.president])),
    db: Session = Depends(get_db)
):
    """Delete a member"""
    success = delete_member(db, member_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    return None