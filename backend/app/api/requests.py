from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.activity_log import ActivityType
from app.models.deletion_request import DeletionRequest as DeletionRequestModel
from app.models.deletion_request import RequestStatus
from app.models.user import User
from app.schemas.request import (
    DeletionRequest,
    DeletionRequestCreate,
    DeletionRequestUpdate,
    EmailPreview,
)
from app.services.activity_log_service import ActivityLogService
from app.services.broker_service import BrokerService
from app.services.deletion_request_service import DeletionRequestService

router = APIRouter()


def serialize_request(req: DeletionRequestModel) -> DeletionRequest:
    return DeletionRequest(
        id=str(req.id),
        user_id=str(req.user_id),
        broker_id=str(req.broker_id),
        status=req.status.value,
        generated_email_subject=req.generated_email_subject,
        generated_email_body=req.generated_email_body,
        sent_at=req.sent_at,
        confirmed_at=req.confirmed_at,
        rejected_at=req.rejected_at,
        notes=req.notes,
        gmail_sent_message_id=req.gmail_sent_message_id,
        gmail_thread_id=req.gmail_thread_id,
        send_attempts=req.send_attempts,
        last_send_error=req.last_send_error,
        next_retry_at=req.next_retry_at,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


@router.post("/", response_model=DeletionRequest)
def create_deletion_request(
    request: DeletionRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new deletion request"""

    # Get user
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get broker
    broker_service = BrokerService(db)
    broker = broker_service.get_broker_by_id(request.broker_id)
    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")

    # Create request
    service = DeletionRequestService(db)
    activity_service = ActivityLogService(db)

    try:
        deletion_request = service.create_request(user, broker, request.framework)

        # Log activity
        activity_service.log_activity(
            user_id=str(user.id),
            activity_type=ActivityType.REQUEST_CREATED,
            message=f"Created deletion request for {broker.name}",
            broker_id=request.broker_id,
            deletion_request_id=str(deletion_request.id),
        )

        return serialize_request(deletion_request)

    except Exception as e:
        # Log error
        activity_service.log_activity(
            user_id=str(user.id),
            activity_type=ActivityType.ERROR,
            message=f"Failed to create deletion request for {broker.name}",
            details=str(e),
            broker_id=request.broker_id,
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[DeletionRequest])
def list_deletion_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all deletion requests for a user"""

    service = DeletionRequestService(db)
    requests = service.get_user_requests(str(current_user.id))

    return [serialize_request(req) for req in requests]


@router.get("/{request_id}", response_model=DeletionRequest)
def get_deletion_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific deletion request"""

    service = DeletionRequestService(db)
    req = service.get_request_by_id(request_id)

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if str(req.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this request")

    return serialize_request(req)


@router.put("/{request_id}/status", response_model=DeletionRequest)
def update_request_status(
    request_id: str,
    update: DeletionRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the status of a deletion request"""

    service = DeletionRequestService(db)

    try:
        status = RequestStatus(update.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {update.status}")

    try:
        req = service.update_request_status(request_id, status, update.notes)

        if str(req.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to modify this request")

        return serialize_request(req)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{request_id}/email-preview", response_model=EmailPreview)
def preview_deletion_email(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get email preview for a deletion request"""

    service = DeletionRequestService(db)
    req = service.get_request_by_id(request_id)

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if str(req.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this request")

    # Get broker for additional info
    broker_service = BrokerService(db)
    broker = broker_service.get_broker_by_id(str(req.broker_id))

    return EmailPreview(
        subject=req.generated_email_subject,
        body=req.generated_email_body,
        to_email=broker.privacy_email if broker else None,
        broker_name=broker.name if broker else "Unknown",
    )


@router.post("/{request_id}/send", response_model=DeletionRequest)
def send_deletion_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a deletion request email via Gmail"""
    from app.services.gmail_service import GmailService

    service = DeletionRequestService(db)
    gmail_service = GmailService()
    activity_service = ActivityLogService(db)

    try:
        request_record = service.get_request_by_id(request_id)
        if not request_record:
            raise HTTPException(status_code=404, detail="Request not found")

        if str(request_record.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to send this request")

        req = service.send_request_email(request_id, gmail_service)

        # Get broker for logging
        broker_service = BrokerService(db)
        broker = broker_service.get_broker_by_id(str(req.broker_id))

        # Log activity
        activity_service.log_activity(
            user_id=str(req.user_id),
            activity_type=ActivityType.REQUEST_SENT,
            message=f"Sent deletion request to {broker.name if broker else 'broker'}",
            broker_id=str(req.broker_id),
            deletion_request_id=request_id,
        )

        return serialize_request(req)

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        # Log error
        try:
            req = service.get_request_by_id(request_id)
            if req:
                broker_service = BrokerService(db)
                broker = broker_service.get_broker_by_id(str(req.broker_id))
                activity_service.log_activity(
                    user_id=str(req.user_id),
                    activity_type=ActivityType.ERROR,
                    message=f"Failed to send deletion request to {broker.name if broker else 'broker'}",
                    details=str(e),
                    broker_id=str(req.broker_id),
                    deletion_request_id=request_id,
                )
        except Exception:
            pass  # Don't fail on logging errors
        raise HTTPException(status_code=400, detail=str(e))
