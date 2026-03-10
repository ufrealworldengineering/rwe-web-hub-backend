from typing import List, Optional
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, UploadFile, File, Form
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas.schemas import (
    ApplicationCreate, 
    ApplicationUpdate, 
    ApplicationResponse, 
    ApplicationWithTeam,
    AppStatus,
    AppYear
)
from .service import *
from db.models import Application
from db.storage import upload_resume

from api.deps import require_roles
from db.models import UserRole, User

router = APIRouter(prefix="/applications", tags=["applications"])

# ============================================================================
# PUBLIC APPLICATION ENDPOINT
# ============================================================================

@router.post("/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_team(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    team_id: str = Form(...),
    year: str = Form(...),
    major: str = Form(...),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Public endpoint for students to apply to a team.
    Uploads resume to Supabase Storage and creates application record.
    """
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF resumes are accepted.")
    try:
        # Uncomment and configure when you have Supabase client set up
        # 1. Upload Resume to Supabase Storage
        file_ext = resume.filename.split(".")[-1]
        file_path = f"resumes/{uuid.uuid4()}.{file_ext}"
        
        file_content = await resume.read()
        
        # 2. Get the public URL for the stored file
        resume_url = await upload_resume(file_content, resume.filename)
        
        # 3. Create application data
        app_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "team": UUID(team_id),
            "year": AppYear(year),
            "major": major,
            "resume": resume_url,
            "status": AppStatus.applied
        }
        
        # 4. Save to database
        application = create_application(db, app_data)
        return application
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process application: {str(e)}"
        )

# ============================================================================
# ADMIN ENDPOINTS - DYNAMIC FILTERING
# ============================================================================

@router.get("/filter", response_model=List[ApplicationResponse])
def filter_applications(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    team_id: Optional[UUID] = Query(None, description="Filter by team ID"),
    status: Optional[AppStatus] = Query(None, description="Filter by application status"),
    year: Optional[AppYear] = Query(None, description="Filter by student year"),
    notified: Optional[bool] = Query(None, description="Filter by notification status"),
    email: Optional[str] = Query(None, description="Filter by email (partial match)"),
    major: Optional[str] = Query(None, description="Filter by major (partial match)"),
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    db: Session = Depends(get_db)
):
    """
    Dynamic filtering endpoint for applications.
    
    Combine multiple query parameters to filter results.
    
    Examples:
    - Get unnotified accepted applications: ?status=accepted&notified=false
    - Get all applications for a team: ?team_id=xxx
    - Get second-year CS applicants: ?year=second&major=Computer
    - Combine filters: ?team_id=xxx&status=applied&year=third
    """
    
    # Start with base query
    query = db.query(Application)
    
    # Apply filters dynamically
    if team_id:
        query = query.filter(Application.team == team_id)
    
    if status:
        query = query.filter(Application.status == status)
    
    if year:
        query = query.filter(Application.year == year)
    
    if notified is not None:
        query = query.filter(Application.notified == notified)
    
    if email:
        query = query.filter(Application.email.ilike(f"%{email}%"))
    
    if major:
        query = query.filter(Application.major.ilike(f"%{major}%"))
    
    # Apply pagination
    applications = query.offset(skip).limit(limit).all()
    
    return applications

# ============================================================================
# INDIVIDUAL APPLICATION ENDPOINTS
# ============================================================================

@router.get("/{application_id}", response_model=ApplicationWithTeam)
def get_application(
    application_id: UUID,
    include_team: bool = Query(True, description="Include team details"),
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager, UserRole.member])),
    db: Session = Depends(get_db)
):
    """Get a specific application by ID"""
    application = get_application(db, application_id, include_team=include_team)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return application

@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: UUID,
    application_update: ApplicationUpdate,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    db: Session = Depends(get_db)
):
    """Update an application"""
    update_data = application_update.model_dump(exclude_unset=True)
    application = update_application(db, application_id, update_data)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return application

@router.patch("/{application_id}/status", response_model=ApplicationResponse)
def update_application_status(
    application_id: UUID,
    status: AppStatus = Body(..., embed=True),
    notified: bool = Body(False, embed=True),
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    db: Session = Depends(get_db)
):
    """Update application status and notification flag"""
    application = update_application_status(db, application_id, status, notified)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return application

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: UUID,
    current_user: User = Depends(require_roles([UserRole.president])),
    db: Session = Depends(get_db)
):
    """Delete an application"""
    success = delete_application(db, application_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return None

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/notify/bulk")
def mark_applications_notified(
    application_ids: List[UUID] = Body(..., embed=True),
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    db: Session = Depends(get_db)
):
    """Mark multiple applications as notified"""
    count = mark_applications_notified(db, application_ids)
    return {"updated": count, "application_ids": application_ids}

@router.post("/bulk-update-status")
def bulk_update_status(
    application_ids: List[UUID] = Body(..., embed=True),
    status: AppStatus = Body(..., embed=True),
    notified: bool = Body(False, embed=True),
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    db: Session = Depends(get_db)
):
    """
    Update status for multiple applications at once.
    Useful for accepting/rejecting multiple applications.
    """
    
    count = db.query(Application).filter(
        Application.id.in_(application_ids)
    ).update(
        {"status": status, "notified": notified},
        synchronize_session=False
    )
    
    db.commit()
    
    return {
        "updated": count,
        "application_ids": application_ids,
        "status": status,
        "notified": notified
    }