from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.activity_log import ActivityType
from app.models.user import User
from app.schemas.activity import ActivityLogResponse
from app.services.activity_log_service import ActivityLogService

router = APIRouter()


@router.get("/", response_model=list[ActivityLogResponse])
def get_activities(
    broker_id: str | None = Query(None),
    activity_type: ActivityType | None = Query(None),
    days_back: int = Query(30),
    limit: int = Query(100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get activity logs for a user"""
    service = ActivityLogService(db)
    activities = service.get_user_activities(
        user_id=str(current_user.id),
        broker_id=broker_id,
        activity_type=activity_type,
        days_back=days_back,
        limit=limit,
    )
    return [
        ActivityLogResponse(
            id=str(activity.id),
            user_id=str(activity.user_id),
            activity_type=activity.activity_type,
            message=activity.message,
            details=activity.details,
            broker_id=str(activity.broker_id) if activity.broker_id else None,
            deletion_request_id=str(activity.deletion_request_id)
            if activity.deletion_request_id
            else None,
            response_id=str(activity.response_id) if activity.response_id else None,
            email_scan_id=str(activity.email_scan_id) if activity.email_scan_id else None,
            created_at=activity.created_at,
        )
        for activity in activities
    ]
