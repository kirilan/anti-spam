"""Tests for the analytics service"""

from datetime import datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from app.models.broker_response import BrokerResponse, ResponseType
from app.models.data_broker import DataBroker
from app.models.deletion_request import DeletionRequest, RequestStatus
from app.models.user import User
from app.services.analytics_service import AnalyticsService


class TestAnalyticsServiceUserStats:
    """Tests for get_user_stats method"""

    def test_get_user_stats_empty_db(self, db: Session, test_user: User):
        """Test stats with no deletion requests"""
        service = AnalyticsService(db)
        stats = service.get_user_stats(test_user.id)

        assert stats["total_requests"] == 0
        assert stats["confirmed_deletions"] == 0
        assert stats["sent_requests"] == 0
        assert stats["rejected"] == 0
        assert stats["pending_requests"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["avg_response_time_days"] is None

    def test_get_user_stats_with_data(
        self,
        db: Session,
        test_user: User,
        multiple_deletion_requests: list[DeletionRequest],
    ):
        """Test stats with multiple requests"""
        service = AnalyticsService(db)
        stats = service.get_user_stats(test_user.id)

        # 7 total requests: 1 pending, 2 sent, 3 confirmed, 1 rejected
        assert stats["total_requests"] == 7
        assert stats["confirmed_deletions"] == 3
        assert stats["sent_requests"] == 2  # SENT + ACTION_REQUIRED
        assert stats["rejected"] == 1
        assert stats["pending_requests"] == 1

    def test_get_user_stats_success_rate(self, db: Session, test_user: User, test_broker: DataBroker):
        """Test success rate calculation"""
        # Create requests with known outcomes
        now = datetime.utcnow()
        for status in [RequestStatus.CONFIRMED, RequestStatus.CONFIRMED, RequestStatus.REJECTED]:
            request = DeletionRequest(
                user_id=test_user.id,
                broker_id=test_broker.id,
                status=status,
                source="manual",
                sent_at=now,
            )
            db.add(request)
        db.commit()

        service = AnalyticsService(db)
        stats = service.get_user_stats(test_user.id)

        # 2 confirmed out of 3 completed = 66.7%
        assert stats["success_rate"] == pytest.approx(66.7, abs=0.1)

    def test_get_user_stats_avg_response_time(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test average response time calculation"""
        now = datetime.utcnow()

        # Create confirmed requests with known response times
        for days in [5, 10, 15]:
            request = DeletionRequest(
                user_id=test_user.id,
                broker_id=test_broker.id,
                status=RequestStatus.CONFIRMED,
                source="manual",
                sent_at=now - timedelta(days=days + 5),
                confirmed_at=now - timedelta(days=5),  # All confirmed 5 days ago
            )
            db.add(request)
        db.commit()

        service = AnalyticsService(db)
        stats = service.get_user_stats(test_user.id)

        # Average of 5, 10, 15 days = 10 days
        assert stats["avg_response_time_days"] == 10.0


class TestAnalyticsServiceBrokerRanking:
    """Tests for get_broker_compliance_ranking method"""

    def test_get_broker_ranking_empty(self, db: Session, test_user: User):
        """Test ranking with no requests"""
        service = AnalyticsService(db)
        rankings = service.get_broker_compliance_ranking(test_user.id)

        assert rankings == []

    def test_get_broker_ranking_with_data(
        self,
        db: Session,
        test_user: User,
        multiple_deletion_requests: list[DeletionRequest],
    ):
        """Test ranking with multiple requests"""
        service = AnalyticsService(db)
        rankings = service.get_broker_compliance_ranking(test_user.id)

        assert len(rankings) == 1  # Only one broker in test data
        ranking = rankings[0]
        assert ranking["broker_name"] == "Test Broker"
        assert ranking["total_requests"] == 7

    def test_get_broker_ranking_without_user_filter(
        self,
        db: Session,
        test_user: User,
        admin_user: User,
        test_broker: DataBroker,
    ):
        """Test ranking without user filter includes all users"""
        # Create requests for both users
        for user in [test_user, admin_user]:
            request = DeletionRequest(
                user_id=user.id,
                broker_id=test_broker.id,
                status=RequestStatus.CONFIRMED,
                source="manual",
            )
            db.add(request)
        db.commit()

        service = AnalyticsService(db)
        rankings = service.get_broker_compliance_ranking(user_id=None)

        assert len(rankings) == 1
        assert rankings[0]["total_requests"] == 2

    def test_get_broker_ranking_sorted_by_success_rate(
        self, db: Session, test_user: User
    ):
        """Test that rankings are sorted by success rate"""
        # Create two brokers with different success rates
        broker_high = DataBroker(
            name="High Success Broker",
            domains=["high.com"],
            privacy_email="privacy@high.com",
        )
        broker_low = DataBroker(
            name="Low Success Broker",
            domains=["low.com"],
            privacy_email="privacy@low.com",
        )
        db.add_all([broker_high, broker_low])
        db.commit()

        # High success broker: 3 confirmed, 1 rejected (75%)
        for _ in range(3):
            db.add(
                DeletionRequest(
                    user_id=test_user.id,
                    broker_id=broker_high.id,
                    status=RequestStatus.CONFIRMED,
                    source="manual",
                )
            )
        db.add(
            DeletionRequest(
                user_id=test_user.id,
                broker_id=broker_high.id,
                status=RequestStatus.REJECTED,
                source="manual",
            )
        )

        # Low success broker: 1 confirmed, 3 rejected (25%)
        db.add(
            DeletionRequest(
                user_id=test_user.id,
                broker_id=broker_low.id,
                status=RequestStatus.CONFIRMED,
                source="manual",
            )
        )
        for _ in range(3):
            db.add(
                DeletionRequest(
                    user_id=test_user.id,
                    broker_id=broker_low.id,
                    status=RequestStatus.REJECTED,
                    source="manual",
                )
            )
        db.commit()

        service = AnalyticsService(db)
        rankings = service.get_broker_compliance_ranking(test_user.id)

        assert len(rankings) == 2
        assert rankings[0]["broker_name"] == "High Success Broker"
        assert rankings[0]["success_rate"] == 75.0
        assert rankings[1]["broker_name"] == "Low Success Broker"
        assert rankings[1]["success_rate"] == 25.0


class TestAnalyticsServiceTimeline:
    """Tests for get_timeline_data method"""

    def test_get_timeline_empty(self, db: Session, test_user: User):
        """Test timeline with no data"""
        service = AnalyticsService(db)
        timeline = service.get_timeline_data(test_user.id, days=30)

        assert timeline == []

    def test_get_timeline_with_sent_requests(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test timeline includes sent requests"""
        now = datetime.utcnow()
        request = DeletionRequest(
            user_id=test_user.id,
            broker_id=test_broker.id,
            status=RequestStatus.SENT,
            source="manual",
            sent_at=now,
        )
        db.add(request)
        db.commit()

        service = AnalyticsService(db)
        timeline = service.get_timeline_data(test_user.id, days=30)

        assert len(timeline) == 1
        assert timeline[0]["requests_sent"] == 1
        assert timeline[0]["confirmations_received"] == 0

    def test_get_timeline_with_confirmations(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test timeline includes confirmations"""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        request = DeletionRequest(
            user_id=test_user.id,
            broker_id=test_broker.id,
            status=RequestStatus.CONFIRMED,
            source="manual",
            sent_at=yesterday,
            confirmed_at=now,
        )
        db.add(request)
        db.commit()

        service = AnalyticsService(db)
        timeline = service.get_timeline_data(test_user.id, days=30)

        assert len(timeline) == 2  # One for sent, one for confirmed
        # Find the confirmation entry
        confirmation_entry = next(t for t in timeline if t["confirmations_received"] > 0)
        assert confirmation_entry["confirmations_received"] == 1

    def test_get_timeline_respects_days_filter(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test that timeline respects the days filter"""
        now = datetime.utcnow()
        # Create request outside the filter window
        old_request = DeletionRequest(
            user_id=test_user.id,
            broker_id=test_broker.id,
            status=RequestStatus.SENT,
            source="manual",
            sent_at=now - timedelta(days=40),
        )
        db.add(old_request)
        db.commit()

        service = AnalyticsService(db)
        timeline = service.get_timeline_data(test_user.id, days=30)

        # Request from 40 days ago should not be in 30-day timeline
        assert timeline == []


class TestAnalyticsServiceResponseDistribution:
    """Tests for get_response_type_distribution method"""

    def test_get_response_distribution_empty(self, db: Session, test_user: User):
        """Test distribution with no responses"""
        service = AnalyticsService(db)
        distribution = service.get_response_type_distribution(test_user.id)

        assert distribution == []

    def test_get_response_distribution_with_data(
        self,
        db: Session,
        test_user: User,
        multiple_deletion_requests: list[DeletionRequest],
        multiple_broker_responses: list[BrokerResponse],
    ):
        """Test distribution with multiple response types"""
        service = AnalyticsService(db)
        distribution = service.get_response_type_distribution(test_user.id)

        # Should have entries for each response type present
        assert len(distribution) > 0

        # Total percentage should equal 100%
        total_percentage = sum(d["percentage"] for d in distribution)
        assert total_percentage == pytest.approx(100.0, abs=0.5)

    def test_get_response_distribution_percentages(
        self, db: Session, test_user: User, sent_deletion_request: DeletionRequest
    ):
        """Test that percentages are calculated correctly"""
        # Create responses with known distribution
        for i in range(3):
            db.add(
                BrokerResponse(
                    user_id=test_user.id,
                    deletion_request_id=sent_deletion_request.id,
                    gmail_message_id=f"msg-confirm-{i}",
                    sender_email="test@broker.com",
                    response_type=ResponseType.CONFIRMATION,
                )
            )
        db.add(
            BrokerResponse(
                user_id=test_user.id,
                deletion_request_id=sent_deletion_request.id,
                gmail_message_id="msg-reject-1",
                sender_email="test@broker.com",
                response_type=ResponseType.REJECTION,
            )
        )
        db.commit()

        service = AnalyticsService(db)
        distribution = service.get_response_type_distribution(test_user.id)

        # 3 confirmations out of 4 = 75%, 1 rejection = 25%
        confirmation = next(d for d in distribution if d["response_type"] == "confirmation")
        rejection = next(d for d in distribution if d["response_type"] == "rejection")

        assert confirmation["count"] == 3
        assert confirmation["percentage"] == 75.0
        assert rejection["count"] == 1
        assert rejection["percentage"] == 25.0
