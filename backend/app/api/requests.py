from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.deletion_request import RequestStatus, DeletionRequest as DeletionRequestModel
from app.models.broker_response import BrokerResponse as BrokerResponseModel, ResponseType
from app.models.activity_log import ActivityType
from app.schemas.request import (
    DeletionRequestCreate,
    DeletionRequestUpdate,
    DeletionRequest,
    EmailPreview
)
from app.schemas.ai import AiClassifyResult, AiThreadClassification
from app.services.deletion_request_service import DeletionRequestService
from app.services.broker_service import BrokerService
from app.services.activity_log_service import ActivityLogService
from app.services.ai_settings import resolve_model
from app.services.gemini_service import GeminiService, GeminiServiceError
from app.dependencies.auth import get_current_user

router = APIRouter()


def serialize_request(req: DeletionRequestModel, warning: str | None = None) -> DeletionRequest:
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
        warning=warning
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
        deletion_request, warning = service.create_request(user, broker, request.framework)

        # Log activity
        activity_service.log_activity(
            user_id=str(user.id),
            activity_type=ActivityType.REQUEST_CREATED,
            message=f"Created deletion request for {broker.name}",
            broker_id=request.broker_id,
            deletion_request_id=str(deletion_request.id)
        )

        return serialize_request(deletion_request, warning)

    except Exception as e:
        # Log error
        activity_service.log_activity(
            user_id=str(user.id),
            activity_type=ActivityType.ERROR,
            message=f"Failed to create deletion request for {broker.name}",
            details=str(e),
            broker_id=request.broker_id
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[DeletionRequest])
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
        broker_name=broker.name if broker else "Unknown"
    )


def _truncate_text(text: str | None, limit: int = 4000) -> str | None:
    if not text:
        return text
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _build_thread_payload(
    request_record: DeletionRequestModel,
    broker_name: str | None,
    responses: List[BrokerResponseModel],
) -> Dict[str, Any]:
    return {
        "thread_id": request_record.gmail_thread_id,
        "request": {
            "request_id": str(request_record.id),
            "broker_name": broker_name,
            "status": request_record.status.value,
            "sent_at": request_record.sent_at.isoformat() if request_record.sent_at else None,
            "created_at": request_record.created_at.isoformat(),
            "subject": _truncate_text(request_record.generated_email_subject),
            "body": _truncate_text(request_record.generated_email_body),
        },
        "responses": [
            {
                "response_id": str(response.id),
                "sender_email": response.sender_email,
                "subject": _truncate_text(response.subject),
                "body": _truncate_text(response.body_text),
                "received_at": (response.received_date or response.created_at).isoformat(),
            }
            for response in responses
        ],
    }


@router.post("/{request_id}/ai-classify", response_model=AiClassifyResult)
def classify_responses_with_ai(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually classify a request's thread using Gemini"""
    service = DeletionRequestService(db)
    request_record = service.get_request_by_id(request_id)

    if not request_record:
        raise HTTPException(status_code=404, detail="Request not found")

    if str(request_record.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to classify this request")

    api_key = current_user.get_gemini_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API key not configured")

    query = db.query(BrokerResponseModel).filter(
        BrokerResponseModel.user_id == current_user.id
    )

    if request_record.gmail_thread_id:
        query = query.filter(
            (BrokerResponseModel.deletion_request_id == request_id)
            | (BrokerResponseModel.gmail_thread_id == request_record.gmail_thread_id)
        )
    else:
        query = query.filter(BrokerResponseModel.deletion_request_id == request_id)

    responses = query.all()

    if not responses:
        raise HTTPException(status_code=400, detail="No responses found for this request")

    responses.sort(
        key=lambda resp: (resp.received_date or resp.created_at)
    )

    broker_service = BrokerService(db)
    broker = broker_service.get_broker_by_id(str(request_record.broker_id))
    thread_payload = _build_thread_payload(request_record, broker.name if broker else None, responses)

    model = resolve_model(current_user.gemini_model)
    gemini_service = GeminiService(api_key, model)
    try:
        ai_payload = gemini_service.classify_thread(thread_payload)
    except GeminiServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        ai_result = AiThreadClassification.model_validate(ai_payload)  # type: ignore[attr-defined]
    except AttributeError:
        ai_result = AiThreadClassification.parse_obj(ai_payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="AI response did not match the expected schema") from exc

    response_map = {item.response_id: item for item in ai_result.responses}
    response_ids = {str(response.id) for response in responses}
    output_ids = set(response_map.keys())
    if response_ids != output_ids:
        missing = sorted(response_ids - output_ids)
        extra = sorted(output_ids - response_ids)
        detail = "AI response did not cover every thread message."
        if missing:
            detail += f" Missing: {', '.join(missing)}."
        if extra:
            detail += f" Extra: {', '.join(extra)}."
        raise HTTPException(status_code=422, detail=detail)

    updated_count = 0
    updated_ids = set()
    now = datetime.utcnow()

    for response in responses:
        classification = response_map.get(str(response.id))
        if not classification:
            continue

        try:
            response.response_type = ResponseType(classification.response_type)
        except ValueError:
            response.response_type = ResponseType.UNKNOWN

        response.confidence_score = classification.confidence_score
        response.matched_by = "gemini"
        response.is_processed = True
        response.processed_at = now
        updated_count += 1
        updated_ids.add(str(response.id))

    status_updated = False
    eligible = [
        r for r in responses
        if str(r.id) in updated_ids
        if r.confidence_score is not None
        and r.confidence_score >= 0.75
        and r.response_type in (ResponseType.CONFIRMATION, ResponseType.REJECTION)
    ]

    if eligible:
        latest = max(
            eligible,
            key=lambda r: (r.received_date or r.created_at)
        )
        if latest.response_type == ResponseType.CONFIRMATION:
            request_record.status = RequestStatus.CONFIRMED
            request_record.confirmed_at = now
            request_record.rejected_at = None
            status_updated = True
        elif latest.response_type == ResponseType.REJECTION:
            request_record.status = RequestStatus.REJECTED
            request_record.rejected_at = now
            request_record.confirmed_at = None
            status_updated = True

    db.commit()

    response_type_counts: Dict[str, int] = {}
    for item in ai_result.responses:
        response_type_counts[item.response_type] = response_type_counts.get(item.response_type, 0) + 1

    details_summary = (
        f"Model {ai_result.model} | Updated {updated_count} response(s) | "
        f"Status updated: {'yes' if status_updated else 'no'} | "
        f"Request status: {request_record.status.value} | "
        f"Types: {', '.join(f'{key}={value}' for key, value in response_type_counts.items())}"
    )

    activity_service = ActivityLogService(db)
    activity_service.log_activity(
        user_id=str(current_user.id),
        activity_type=ActivityType.INFO,
        message=f"AI reclassified {updated_count} response(s) for {broker.name if broker else 'broker'}",
        details=details_summary,
        broker_id=str(request_record.broker_id),
        deletion_request_id=str(request_record.id),
    )

    return AiClassifyResult(
        request_id=str(request_record.id),
        updated_responses=updated_count,
        status_updated=status_updated,
        request_status=request_record.status.value,
        model=ai_result.model,
        ai_output=ai_result,
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
            deletion_request_id=request_id
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
                    deletion_request_id=request_id
                )
        except Exception:
            pass  # Don't fail on logging errors
        raise HTTPException(status_code=400, detail=str(e))
