import asyncio
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from db.models import Application, AppStatus, Team, Program


# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------

_ACCEPTANCE_SUBJECT = "Real World Engineering {team} Design Team"
_ACCEPTANCE_BODY = """\
Hello {name},

We are thrilled to let you know that we are offering you a spot on the {team} design team. \
We are looking forward to having you on the team. To let us know of your continued interest, \
please email {manager_email} and they will follow up with further details.

Best,
Real World Engineering"""

_REJECTION_SUBJECT = "Real World Engineering {team} Design Team"
_REJECTION_BODY = """\
Hello {name},

We regret to inform you that we are unable to offer you a spot on the {team} design team at \
this time. We appreciate your time and interest, and encourage you to stay up to date with the \
club, apply again next semester, or reach out with a proposal for a design team of your own.

Best,
Real World Engineering"""


def _build_message(first_name: str, team_name: str, manager_email: str, app_status: AppStatus) -> tuple[str, str]:
    """Return (subject, body) for the given application status."""
    if app_status == AppStatus.accepted:
        subject = _ACCEPTANCE_SUBJECT.format(team=team_name)
        body = _ACCEPTANCE_BODY.format(name=first_name, team=team_name, manager_email=manager_email)
    elif app_status == AppStatus.denied:
        subject = _REJECTION_SUBJECT.format(team=team_name)
        body = _REJECTION_BODY.format(name=first_name, team=team_name)
    else:
        raise ValueError(
            f"Cannot send notification for status '{app_status}'. "
            "Status must be 'accepted' or 'denied'."
        )
    return subject, body


def _send_smtp(to_email: str, subject: str, body: str) -> None:
    """Synchronous SMTP send via STARTTLS. Run via asyncio.to_thread."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    email_from = os.getenv("EMAIL_FROM") or smtp_user

    msg = MIMEMultipart()
    msg["From"] = email_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(email_from, to_email, msg.as_string())


async def send_notification(
    application_id: UUID, db: Session, *, force: bool = False
) -> Application:
    """
    Look up the application, send the acceptance/rejection email,
    mark notified=True, and return the updated application.

    When ``force`` is False and the row is already ``notified``, returns without
    sending (idempotent path for status updates). Use ``force=True`` for explicit
    resend via POST /notify.
    """
    application = (
        db.query(Application)
        .options(
            joinedload(Application.team_rel).joinedload(Team.program_rel).joinedload(
                Program.manager_rel
            )
        )
        .filter(Application.id == application_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if application.notified and not force:
        return application

    if application.status not in (AppStatus.accepted, AppStatus.denied):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot notify applicant with status '{application.status}'. "
                "Status must be 'accepted' or 'denied'."
            ),
        )

    team = application.team_rel
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found for this application"
        )

    manager_email = ""
    program = team.program_rel
    if program and program.manager_rel:
        manager_email = program.manager_rel.email

    try:
        subject, body = _build_message(
            first_name=application.first_name,
            team_name=team.name,
            manager_email=manager_email,
            app_status=application.status,
        )
        await asyncio.to_thread(_send_smtp, application.email, subject, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except smtplib.SMTPException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send email: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while sending email: {str(e)}"
        )

    application.notified = True
    db.commit()
    db.refresh(application)
    return application
