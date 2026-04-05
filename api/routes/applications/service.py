from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload

from db.models import Application, AppStatus

def get_application(db: Session, application_id: UUID, include_team: bool = False) -> Optional[Application]:
    """Get a single application by ID"""
    query = db.query(Application)
    if include_team:
        query = query.options(joinedload(Application.team_rel))
    return query.filter(Application.id == application_id).first()

def get_application_by_email(db: Session, email: str, team_id: Optional[UUID] = None) -> Optional[Application]:
    """Get an application by email, optionally filtered by team"""
    query = db.query(Application).filter(Application.email == email)
    if team_id:
        query = query.filter(Application.team == team_id)
    return query.first()

def get_applications(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    include_team: bool = False
) -> List[Application]:
    """Get all applications with pagination"""
    query = db.query(Application)
    
    if include_team:
        query = query.options(joinedload(Application.team_rel))
    
    return query.offset(skip).limit(limit).all()

def get_applications_by_team(
    db: Session,
    team_id: UUID,
    status: Optional[AppStatus] = None
) -> List[Application]:
    """Get all applications for a specific team, optionally filtered by status"""
    query = db.query(Application).filter(Application.team == team_id)
    
    if status:
        query = query.filter(Application.status == status)
    
    return query.all()

def get_applications_by_status(
    db: Session,
    status: AppStatus,
    team_id: Optional[UUID] = None
) -> List[Application]:
    """Get all applications by status, optionally filtered by team"""
    query = db.query(Application).filter(Application.status == status)
    
    if team_id:
        query = query.filter(Application.team == team_id)
    
    return query.all()

def get_unnotified_applications(db: Session, team_id: Optional[UUID] = None) -> List[Application]:
    """Get all applications that haven't been notified"""
    query = db.query(Application).filter(Application.notified == False)
    
    if team_id:
        query = query.filter(Application.team == team_id)
    
    return query.all()

def create_application(db: Session, application_data: dict) -> Application:
    """Create a new application"""
    db_application = Application(**application_data)
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

def update_application(db: Session, application_id: UUID, application_update: dict) -> Optional[Application]:
    """Update an application"""
    db_application = get_application(db, application_id)
    if not db_application:
        return None
    
    for field, value in application_update.items():
        setattr(db_application, field, value)
    
    db.commit()
    db.refresh(db_application)
    return db_application

def update_application_status(
    db: Session,
    application_id: UUID,
    status: AppStatus,
    notified: bool = False
) -> Optional[Application]:
    """Update application status. If the decision status changes, clear ``notified`` so a new email can be sent."""
    db_application = get_application(db, application_id)
    if not db_application:
        return None

    old_status = db_application.status
    db_application.status = status
    if old_status != status:
        db_application.notified = False
    else:
        db_application.notified = notified

    db.commit()
    db.refresh(db_application)
    return db_application

def mark_applications_notified(db: Session, application_ids: List[UUID]) -> int:
    """Mark multiple applications as notified"""
    count = db.query(Application).filter(
        Application.id.in_(application_ids)
    ).update({"notified": True}, synchronize_session=False)
    
    db.commit()
    return count

def delete_application(db: Session, application_id: UUID) -> bool:
    """Delete an application"""
    db_application = get_application(db, application_id)
    if not db_application:
        return False
    
    db.delete(db_application)
    db.commit()
    return True