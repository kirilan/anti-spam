from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.broker_response import BrokerResponse as BrokerResponseModel
from app.models.user import User
from app.schemas.response import BrokerResponse
from app.tasks.email_tasks import scan_for_responses_task

router = APIRouter()


@router.get("/", response_model=list[BrokerResponse])
def list_broker_responses(
    request_id: str | None = Query(None, description="Filter by deletion request ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List broker responses for a user

    Optionally filter by deletion request ID
    """
    query = db.query(BrokerResponseModel).filter(BrokerResponseModel.user_id == current_user.id)

    # Filter by request_id if provided
    if request_id:
        query = query.filter(BrokerResponseModel.deletion_request_id == request_id)

    # Order by received date descending
    responses = query.order_by(BrokerResponseModel.received_date.desc()).all()

    return [
        BrokerResponse(
            id=str(resp.id),
            user_id=str(resp.user_id),
            deletion_request_id=str(resp.deletion_request_id) if resp.deletion_request_id else None,
            gmail_message_id=resp.gmail_message_id,
            gmail_thread_id=resp.gmail_thread_id,
            sender_email=resp.sender_email,
            subject=resp.subject,
            body_text=resp.body_text,
            received_date=resp.received_date,
            response_type=resp.response_type.value,
            confidence_score=resp.confidence_score,
            matched_by=resp.matched_by,
            is_processed=resp.is_processed,
            processed_at=resp.processed_at,
            created_at=resp.created_at,
        )
        for resp in responses
    ]


@router.post("/scan")
def scan_responses(
    days_back: int = Query(7, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger a scan for broker responses

    This starts a background task to scan the user's inbox for responses
    to deletion requests.
    """
    # Start background task
    task = scan_for_responses_task.delay(str(current_user.id), days_back)

    return {
        "task_id": task.id,
        "status": "started",
        "message": f"Started scanning for responses from last {days_back} days",
    }


@router.get("/{response_id}", response_model=BrokerResponse)
def get_broker_response(
    response_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific broker response by ID"""
    response = db.query(BrokerResponseModel).filter(BrokerResponseModel.id == response_id).first()

    if not response:
        raise HTTPException(status_code=404, detail="Response not found")

    if str(response.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this response")

    return BrokerResponse(
        id=str(response.id),
        user_id=str(response.user_id),
        deletion_request_id=str(response.deletion_request_id)
        if response.deletion_request_id
        else None,
        gmail_message_id=response.gmail_message_id,
        gmail_thread_id=response.gmail_thread_id,
        sender_email=response.sender_email,
        subject=response.subject,
        body_text=response.body_text,
        received_date=response.received_date,
        response_type=response.response_type.value,
        confidence_score=response.confidence_score,
        matched_by=response.matched_by,
        is_processed=response.is_processed,
        processed_at=response.processed_at,
        created_at=response.created_at,
    )
