from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas.schemas import ProgramCreate, ProgramUpdate, ProgramResponse, ProgramWithManager
from .service import *

router = APIRouter(prefix="/programs", tags=["programs"])

@router.get("/", response_model=List[ProgramResponse])
def list_programs(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = Query(False, description="Filter to only active programs"),
    db: Session = Depends(get_db)
):
    """Get all programs"""
    programs = get_programs(db, skip=skip, limit=limit, active_only=active_only)
    return programs

@router.get("/{program_id}", response_model=ProgramWithManager)
def get_program(
    program_id: UUID,
    include_manager: bool = Query(True, description="Include manager details"),
    db: Session = Depends(get_db)
):
    """Get a specific program by ID"""
    program = get_program(db, program_id, include_manager=include_manager)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )
    return program

@router.get("/manager/{manager_id}", response_model=List[ProgramResponse])
def get_programs_by_manager(
    manager_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all programs managed by a specific user"""
    programs = get_programs_by_manager(db, manager_id)
    return programs

@router.post("/", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
def create_program(
    program: ProgramCreate,
    db: Session = Depends(get_db)
):
    """Create a new program"""
    program_data = program.model_dump()
    return create_program(db, program_data)

@router.patch("/{program_id}", response_model=ProgramResponse)
def update_program(
    program_id: UUID,
    program_update: ProgramUpdate,
    db: Session = Depends(get_db)
):
    """Update a program"""
    update_data = program_update.model_dump(exclude_unset=True)
    program = update_program(db, program_id, update_data)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )
    return program

@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(
    program_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a program"""
    success = delete_program(db, program_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )
    return None