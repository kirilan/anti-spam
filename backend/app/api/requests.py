from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.activity_log import ActivityType
from app.models.deletion_request import DeletionRequest as DeletionRequestModel
from app.models.deletion_request import RequestStatus
from app.models.user import User
from app.schemas.ai import AiClassifyResult, AiResponseClassification, AiThreadClassification
from app.schemas.request import (
    DeletionRequest,
    DeletionRequestCreate,
    DeletionRequestUpdate,
    EmailPreview,
    ThreadEmail,
)
from app.services.activity_log_service import ActivityLogService
from app.services.ai_settings import resolve_model
from app.services.broker_service import BrokerService
from app.services.deletion_request_service import DeletionRequestService
from app.services.gemini_service import GeminiService, GeminiServiceError

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


@router.post("/{request_id}/ai-classify", response_model=AiClassifyResult)
def ai_classify_request_responses(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Use AI to classify responses for a deletion request"""
    from app.models.broker_response import BrokerResponse as BrokerResponseModel
    from app.models.broker_response import ResponseType

    # Check if user has Gemini API key
    if not current_user.encrypted_gemini_api_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key not configured. Please add your API key in Settings.",
        )

    # Get deletion request
    service = DeletionRequestService(db)
    req = service.get_request_by_id(request_id)

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if str(req.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this request")

    # Get responses for this request
    responses = (
        db.query(BrokerResponseModel)
        .filter(BrokerResponseModel.deletion_request_id == req.id)
        .order_by(BrokerResponseModel.received_date)
        .all()
    )

    if not responses:
        raise HTTPException(status_code=400, detail="No responses found for this request")

    # Get broker
    broker_service = BrokerService(db)
    broker = broker_service.get_broker_by_id(str(req.broker_id))

    # Build thread payload
    thread_payload = {
        "deletion_request": {
            "broker_name": broker.name if broker else "Unknown",
            "sent_at": req.sent_at.isoformat() if req.sent_at else None,
        },
        "responses": [
            {
                "response_id": str(resp.id),
                "sender_email": resp.sender_email,
                "subject": resp.subject,
                "body_text": resp.body_text,
                "received_date": resp.received_date.isoformat() if resp.received_date else None,
            }
            for resp in responses
        ],
    }

    # Call Gemini service
    api_key = current_user.get_gemini_api_key()
    model = resolve_model(current_user.gemini_model)
    gemini_service = GeminiService(api_key=api_key, model=model)

    try:
        ai_output = gemini_service.classify_thread(thread_payload)
    except GeminiServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Update responses with AI classifications
    updated_count = 0
    ai_responses = []

    for ai_resp in ai_output.get("responses", []):
        response_id = ai_resp.get("response_id")
        response_type = ai_resp.get("response_type")
        confidence = ai_resp.get("confidence_score", 0.0)
        rationale = ai_resp.get("rationale")

        if not response_id or not response_type:
            continue

        # Find the response
        resp = next((r for r in responses if str(r.id) == response_id), None)
        if not resp:
            continue

        # Only update if confidence is high enough
        if confidence >= 0.75:
            try:
                resp.response_type = ResponseType(response_type)
                resp.confidence_score = confidence
                updated_count += 1
            except ValueError:
                pass  # Invalid response type

        ai_responses.append(
            AiResponseClassification(
                response_id=response_id,
                response_type=response_type,
                confidence_score=confidence,
                rationale=rationale,
            )
        )

    # Update request status based on classifications
    status_updated = False
    original_status = req.status

    # Check if any responses are confirmations
    confirmations = [r for r in responses if r.response_type == ResponseType.CONFIRMATION]
    rejections = [r for r in responses if r.response_type == ResponseType.REJECTION]

    if confirmations and req.status != RequestStatus.CONFIRMED:
        req.status = RequestStatus.CONFIRMED
        req.confirmed_at = max(r.received_date for r in confirmations if r.received_date)
        status_updated = True
    elif rejections and not confirmations and req.status != RequestStatus.REJECTED:
        req.status = RequestStatus.REJECTED
        req.rejected_at = max(r.received_date for r in rejections if r.received_date)
        status_updated = True

    db.commit()

    # Log activity
    activity_service = ActivityLogService(db)
    activity_service.log_activity(
        user_id=str(current_user.id),
        activity_type=ActivityType.INFO,
        message=f"AI classified {updated_count} responses for deletion request",
        details=f"Model: {model}, Status: {original_status.value} → {req.status.value}"
        if status_updated
        else f"Model: {model}",
        deletion_request_id=request_id,
    )

    return AiClassifyResult(
        request_id=request_id,
        updated_responses=updated_count,
        status_updated=status_updated,
        request_status=req.status.value,
        model=model,
        ai_output=AiThreadClassification(
            model=ai_output.get("model", model), responses=ai_responses
        ),
    )


@router.get("/{request_id}/thread", response_model=list[ThreadEmail])
def get_request_thread(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all emails in the thread for a deletion request

    Returns chronologically sorted emails including:
    - Sent email(s) from user to broker
    - Received responses from broker
    - Response type classification if available
    """
    from app.models.broker_response import BrokerResponse as BrokerResponseModel
    from app.models.email_scan import EmailScan as EmailScanModel

    # Get deletion request
    service = DeletionRequestService(db)
    req = service.get_request_by_id(request_id)

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if str(req.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this request")

    # If no thread_id, return empty list
    if not req.gmail_thread_id:
        return []

    # Get all email scans in this thread
    email_scans = (
        db.query(EmailScanModel)
        .filter(
            EmailScanModel.user_id == current_user.id,
            EmailScanModel.gmail_thread_id == req.gmail_thread_id,
        )
        .all()
    )

    # Get all broker responses linked to this request
    broker_responses = (
        db.query(BrokerResponseModel)
        .filter(BrokerResponseModel.deletion_request_id == req.id)
        .all()
    )

    # Build response map keyed by gmail_message_id
    response_map = {resp.gmail_message_id: resp for resp in broker_responses}

    # Convert to ThreadEmail objects
    thread_emails = []
    for scan in email_scans:
        # Check if this email has a classified response
        response = response_map.get(scan.gmail_message_id)

        thread_emails.append(
            ThreadEmail(
                id=str(scan.id),
                gmail_message_id=scan.gmail_message_id,
                gmail_thread_id=scan.gmail_thread_id,
                sender_email=scan.sender_email,
                recipient_email=scan.recipient_email,
                subject=scan.subject,
                body_preview=scan.body_preview,
                direction=scan.email_direction,
                received_date=scan.received_date,
                response_type=response.response_type.value if response else None,
                confidence_score=response.confidence_score if response else None,
            )
        )

    # Sort chronologically by received_date
    thread_emails.sort(key=lambda e: e.received_date or datetime.min)

    return thread_emails
