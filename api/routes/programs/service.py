from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload

from db.models import Program

def get_program(db: Session, program_id: UUID, include_manager: bool = False) -> Optional[Program]:
    """Get a single program by ID"""
    query = db.query(Program)
    if include_manager:
        query = query.options(joinedload(Program.manager_rel))
    return query.filter(Program.id == program_id).first()

def get_programs(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    active_only: bool = False,
    include_manager: bool = False
) -> List[Program]:
    """Get all programs with pagination"""
    query = db.query(Program)
    
    if include_manager:
        query = query.options(joinedload(Program.manager_rel))
    
    if active_only:
        query = query.filter(Program.active == True)
    
    return query.offset(skip).limit(limit).all()

def get_programs_by_manager(db: Session, manager_id: UUID) -> List[Program]:
    """Get all programs managed by a specific user"""
    return db.query(Program).filter(Program.manager == manager_id).all()

def create_program(db: Session, program_data: dict) -> Program:
    """Create a new program"""
    db_program = Program(**program_data)
    db.add(db_program)
    db.commit()
    db.refresh(db_program)
    return db_program

def update_program(db: Session, program_id: UUID, program_update: dict) -> Optional[Program]:
    """Update a program"""
    db_program = get_program(db, program_id)
    if not db_program:
        return None
    
    for field, value in program_update.items():
        setattr(db_program, field, value)
    
    db.commit()
    db.refresh(db_program)
    return db_program

def delete_program(db: Session, program_id: UUID) -> bool:
    """Delete a program"""
    db_program = get_program(db, program_id)
    if not db_program:
        return False
    
    db.delete(db_program)
    db.commit()
    return True