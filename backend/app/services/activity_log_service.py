from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog, ActivityType


class ActivityLogService:
    """Service for creating and querying activity logs"""

    def __init__(self, db: Session):
        self.db = db

    def log_activity(
        self,
        user_id: str,
        activity_type: ActivityType,
        message: str,
        details: str | None = None,
        broker_id: str | None = None,
        deletion_request_id: str | None = None,
        response_id: str | None = None,
        email_scan_id: str | None = None,
    ) -> ActivityLog:
        """Create an activity log entry"""
        # Convert string UUIDs to UUID objects for database
        activity = ActivityLog(
            user_id=UUID(user_id) if user_id and isinstance(user_id, str) else user_id,
            activity_type=activity_type,
            message=message,
            details=details,
            broker_id=UUID(broker_id) if broker_id and isinstance(broker_id, str) else broker_id,
            deletion_request_id=UUID(deletion_request_id)
            if deletion_request_id and isinstance(deletion_request_id, str)
            else deletion_request_id,
            response_id=UUID(response_id)
            if response_id and isinstance(response_id, str)
            else response_id,
            email_scan_id=UUID(email_scan_id)
            if email_scan_id and isinstance(email_scan_id, str)
            else email_scan_id,
        )
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def get_user_activities(
        self,
        user_id: str,
        broker_id: str | None = None,
        activity_type: ActivityType | None = None,
        days_back: int = 30,
        limit: int = 100,
    ) -> list[ActivityLog]:
        """Get activity logs for a user"""
        # Convert string UUIDs to UUID objects
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        query = self.db.query(ActivityLog).filter(ActivityLog.user_id == user_uuid)

        if broker_id:
            broker_uuid = UUID(broker_id) if isinstance(broker_id, str) else broker_id
            query = query.filter(ActivityLog.broker_id == broker_uuid)

        if activity_type:
            query = query.filter(ActivityLog.activity_type == activity_type)

        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.filter(ActivityLog.created_at >= cutoff_date)

        return query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
