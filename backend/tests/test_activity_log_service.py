"""Tests for the activity log service"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog, ActivityType
from app.models.user import User
from app.services.activity_log_service import ActivityLogService


class TestActivityLogServiceLogActivity:
    """Tests for log_activity method"""

    def test_log_basic_activity(self, db: Session, test_user: User):
        """Test logging a basic activity"""
        service = ActivityLogService(db)

        activity = service.log_activity(
            user_id=test_user.id,
            activity_type=ActivityType.EMAIL_SCANNED,
            message="Scanned inbox",
        )

        assert activity.id is not None
        assert activity.user_id == test_user.id
        assert activity.activity_type == ActivityType.EMAIL_SCANNED
        assert activity.message == "Scanned inbox"
        assert activity.details is None

    def test_log_activity_with_details(self, db: Session, test_user: User):
        """Test logging activity with details"""
        service = ActivityLogService(db)

        activity = service.log_activity(
            user_id=test_user.id,
            activity_type=ActivityType.BROKER_DETECTED,
            message="Found data broker email",
            details='{"broker": "TestBroker", "email_count": 5}',
        )

        assert activity.details == '{"broker": "TestBroker", "email_count": 5}'

    def test_log_activity_with_related_entities(
        self, db: Session, test_user: User, test_broker, test_deletion_request
    ):
        """Test logging activity with related entity IDs"""
        service = ActivityLogService(db)

        activity = service.log_activity(
            user_id=test_user.id,
            activity_type=ActivityType.REQUEST_SENT,
            message="Deletion request sent",
            broker_id=test_broker.id,
            deletion_request_id=test_deletion_request.id,
        )

        assert activity.broker_id == test_broker.id
        assert activity.deletion_request_id == test_deletion_request.id

    def test_log_activity_persisted(self, db: Session, test_user: User):
        """Test that activity is persisted to database"""
        service = ActivityLogService(db)

        activity = service.log_activity(
            user_id=test_user.id,
            activity_type=ActivityType.INFO,
            message="Test activity",
        )

        # Query directly to verify persistence
        found = db.query(ActivityLog).filter(ActivityLog.id == activity.id).first()
        assert found is not None
        assert found.message == "Test activity"

    def test_log_all_activity_types(self, db: Session, test_user: User):
        """Test that all activity types can be logged"""
        service = ActivityLogService(db)

        for activity_type in ActivityType:
            activity = service.log_activity(
                user_id=test_user.id,
                activity_type=activity_type,
                message=f"Test {activity_type.value}",
            )
            assert activity.activity_type == activity_type


class TestActivityLogServiceGetActivities:
    """Tests for get_user_activities method"""

    def test_get_activities_empty(self, db: Session, test_user: User):
        """Test getting activities when none exist"""
        service = ActivityLogService(db)
        activities = service.get_user_activities(test_user.id)

        assert activities == []

    def test_get_activities_returns_user_activities(
        self, db: Session, test_user: User, test_activity_log: ActivityLog
    ):
        """Test getting activities returns user's activities"""
        service = ActivityLogService(db)
        activities = service.get_user_activities(test_user.id)

        assert len(activities) == 1
        assert activities[0].id == test_activity_log.id

    def test_get_activities_does_not_return_other_users(
        self, db: Session, test_user: User, admin_user: User
    ):
        """Test that activities from other users are not returned"""
        service = ActivityLogService(db)

        # Create activity for admin user
        service.log_activity(
            user_id=admin_user.id,
            activity_type=ActivityType.INFO,
            message="Admin activity",
        )

        # Create activity for test user
        service.log_activity(
            user_id=test_user.id,
            activity_type=ActivityType.INFO,
            message="Test user activity",
        )

        # Get test user's activities
        activities = service.get_user_activities(test_user.id)

        assert len(activities) == 1
        assert activities[0].message == "Test user activity"

    def test_get_activities_filter_by_broker(
        self, db: Session, test_user: User, test_broker
    ):
        """Test filtering activities by broker ID"""
        service = ActivityLogService(db)

        # Create activity with broker
        service.log_activity(
            user_id=test_user.id,
            activity_type=ActivityType.BROKER_DETECTED,
            message="Broker activity",
            broker_id=test_broker.id,
        )

        # Create activity without broker
        service.log_activity(
            user_id=test_user.id,
            activity_type=ActivityType.INFO,
            message="General activity",
        )

        activities = service.get_user_activities(test_user.id, broker_id=test_broker.id)

        assert len(activities) == 1
        assert activities[0].message == "Broker activity"

    def test_get_activities_filter_by_type(self, db: Session, test_user: User):
        """Test filtering activities by activity type"""
        service = ActivityLogService(db)

        # Create different types
        service.log_activity(
            user_id=test_user.id,
            activity_type=ActivityType.ERROR,
            message="Error activity",
        )
        service.log_activity(
            user_id=test_user.id,
            activity_type=ActivityType.INFO,
            message="Info activity",
        )

        activities = service.get_user_activities(
            test_user.id, activity_type=ActivityType.ERROR
        )

        assert len(activities) == 1
        assert activities[0].message == "Error activity"

    def test_get_activities_respects_days_back(self, db: Session, test_user: User):
        """Test that days_back filter works"""
        service = ActivityLogService(db)

        # Create recent activity
        recent = service.log_activity(
            user_id=test_user.id,
            activity_type=ActivityType.INFO,
            message="Recent",
        )

        # Create old activity (manually set date)
        old = ActivityLog(
            user_id=test_user.id,
            activity_type=ActivityType.INFO,
            message="Old",
            created_at=datetime.utcnow() - timedelta(days=60),
        )
        db.add(old)
        db.commit()

        activities = service.get_user_activities(test_user.id, days_back=30)

        assert len(activities) == 1
        assert activities[0].message == "Recent"

    def test_get_activities_respects_limit(self, db: Session, test_user: User):
        """Test that limit parameter works"""
        service = ActivityLogService(db)

        # Create multiple activities
        for i in range(10):
            service.log_activity(
                user_id=test_user.id,
                activity_type=ActivityType.INFO,
                message=f"Activity {i}",
            )

        activities = service.get_user_activities(test_user.id, limit=5)

        assert len(activities) == 5

    def test_get_activities_ordered_by_date_desc(self, db: Session, test_user: User):
        """Test that activities are ordered by date descending"""
        service = ActivityLogService(db)

        # Create activities with slight time gaps
        for i in range(3):
            service.log_activity(
                user_id=test_user.id,
                activity_type=ActivityType.INFO,
                message=f"Activity {i}",
            )

        activities = service.get_user_activities(test_user.id)

        # Most recent should be first (Activity 2)
        assert activities[0].message == "Activity 2"
        assert activities[-1].message == "Activity 0"
