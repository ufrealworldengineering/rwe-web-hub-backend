from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.deps import get_db, require_roles
from db.models import UserRole, User
from .schemas import NotifyRequest, BulkNotifyRequest, BulkNotifyResponse
from .service import send_notification

router = APIRouter(prefix="/notify", tags=["notify"])


@router.post("", status_code=status.HTTP_200_OK)
async def notify_applicant(
    payload: NotifyRequest,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    db: Session = Depends(get_db),
):
    """Send an acceptance or rejection email to a single applicant."""
    application = await send_notification(payload.application_id, db)
    return {
        "success": True,
        "application_id": str(application.id),
        "notified": application.notified,
    }


@router.post("/bulk", status_code=status.HTTP_200_OK, response_model=BulkNotifyResponse)
async def notify_applicants_bulk(
    payload: BulkNotifyRequest,
    current_user: User = Depends(require_roles([UserRole.president, UserRole.treasurer, UserRole.program_manager])),
    db: Session = Depends(get_db),
):
    """
    Send acceptance or rejection emails to multiple applicants.
    Processes each independently — failures are collected and returned
    without stopping the remaining sends.
    """
    succeeded = []
    failed = []

    for app_id in payload.application_ids:
        try:
            application = await send_notification(app_id, db)
            succeeded.append(str(application.id))
        except Exception as e:
            failed.append({"application_id": str(app_id), "error": str(e)})

    return BulkNotifyResponse(
        succeeded=succeeded,
        failed=failed,
        total=len(payload.application_ids),
    )
