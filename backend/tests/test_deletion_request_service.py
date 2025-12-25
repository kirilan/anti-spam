"""Tests for DeletionRequestService"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.models.data_broker import DataBroker
from app.models.deletion_request import DeletionRequest, RequestStatus
from app.models.user import User
from app.services.deletion_request_service import DeletionRequestService


class TestDeletionRequestServiceCreate:
    """Tests for create_request method"""

    def test_create_request_success(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test creating a new deletion request"""
        service = DeletionRequestService(db)
        request = service.create_request(test_user, test_broker)

        assert request is not None
        assert request.user_id == test_user.id
        assert request.broker_id == test_broker.id
        assert request.status == RequestStatus.PENDING
        assert request.source == "manual"
        assert request.generated_email_subject is not None
        assert request.generated_email_body is not None

    def test_create_request_with_framework(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test creating a request with specific framework"""
        service = DeletionRequestService(db)
        request = service.create_request(test_user, test_broker, framework="CCPA")

        assert request is not None
        # Body should mention CCPA or California
        assert "CCPA" in request.generated_email_body or "California" in request.generated_email_body

    def test_create_request_duplicate_fails(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test that duplicate requests for same broker fail"""
        service = DeletionRequestService(db)

        # Create first request
        service.create_request(test_user, test_broker)

        # Try to create duplicate - should fail
        with pytest.raises(Exception) as exc_info:
            service.create_request(test_user, test_broker)

        assert "already exists" in str(exc_info.value)

    def test_create_request_after_soft_delete_allowed(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test that new request can be created after soft-deleting previous one"""
        service = DeletionRequestService(db)

        # Create and soft-delete first request
        request1 = service.create_request(test_user, test_broker)
        request1.deleted_at = datetime.utcnow()
        db.commit()

        # Should be able to create new request
        request2 = service.create_request(test_user, test_broker)
        assert request2 is not None
        assert request2.id != request1.id


class TestDeletionRequestServiceGetRequests:
    """Tests for get_user_requests and get_request_by_id methods"""

    def test_get_user_requests_empty(self, db: Session, test_user: User):
        """Test getting requests when none exist"""
        service = DeletionRequestService(db)
        requests = service.get_user_requests(test_user.id)

        assert requests == []

    def test_get_user_requests_returns_user_requests(
        self, db: Session, test_user: User, multiple_deletion_requests: list[DeletionRequest]
    ):
        """Test getting all requests for a user"""
        service = DeletionRequestService(db)
        requests = service.get_user_requests(test_user.id)

        assert len(requests) == 7

    def test_get_user_requests_excludes_deleted(
        self, db: Session, test_user: User, test_deletion_request: DeletionRequest
    ):
        """Test that soft-deleted requests are excluded"""
        service = DeletionRequestService(db)

        # Soft delete the request
        test_deletion_request.deleted_at = datetime.utcnow()
        db.commit()

        requests = service.get_user_requests(test_user.id)
        assert len(requests) == 0

    def test_get_user_requests_ordered_by_date_desc(
        self, db: Session, test_user: User, multiple_deletion_requests: list[DeletionRequest]
    ):
        """Test that requests are ordered by created_at descending"""
        service = DeletionRequestService(db)
        requests = service.get_user_requests(test_user.id)

        # Check ordering
        dates = [r.created_at for r in requests]
        assert dates == sorted(dates, reverse=True)

    def test_get_request_by_id_found(
        self, db: Session, test_deletion_request: DeletionRequest
    ):
        """Test getting a specific request by ID"""
        service = DeletionRequestService(db)
        request = service.get_request_by_id(test_deletion_request.id)

        assert request is not None
        assert request.id == test_deletion_request.id

    def test_get_request_by_id_not_found(self, db: Session):
        """Test getting a non-existent request"""
        import uuid

        service = DeletionRequestService(db)
        request = service.get_request_by_id(uuid.uuid4())

        assert request is None


class TestDeletionRequestServiceUpdateStatus:
    """Tests for update_request_status method"""

    def test_update_status_to_sent(
        self, db: Session, test_deletion_request: DeletionRequest
    ):
        """Test updating status to SENT sets sent_at"""
        service = DeletionRequestService(db)

        request = service.update_request_status(
            test_deletion_request.id, RequestStatus.SENT
        )

        assert request.status == RequestStatus.SENT
        assert request.sent_at is not None

    def test_update_status_to_confirmed(
        self, db: Session, sent_deletion_request: DeletionRequest
    ):
        """Test updating status to CONFIRMED sets confirmed_at"""
        service = DeletionRequestService(db)

        request = service.update_request_status(
            sent_deletion_request.id, RequestStatus.CONFIRMED
        )

        assert request.status == RequestStatus.CONFIRMED
        assert request.confirmed_at is not None

    def test_update_status_to_rejected(
        self, db: Session, sent_deletion_request: DeletionRequest
    ):
        """Test updating status to REJECTED sets rejected_at"""
        service = DeletionRequestService(db)

        request = service.update_request_status(
            sent_deletion_request.id, RequestStatus.REJECTED
        )

        assert request.status == RequestStatus.REJECTED
        assert request.rejected_at is not None

    def test_update_status_with_notes(
        self, db: Session, test_deletion_request: DeletionRequest
    ):
        """Test updating status with notes"""
        service = DeletionRequestService(db)

        request = service.update_request_status(
            test_deletion_request.id, RequestStatus.SENT, notes="Sent via Gmail"
        )

        assert request.notes == "Sent via Gmail"

    def test_update_status_not_found(self, db: Session):
        """Test updating non-existent request fails"""
        import uuid

        service = DeletionRequestService(db)

        with pytest.raises(Exception) as exc_info:
            service.update_request_status(uuid.uuid4(), RequestStatus.SENT)

        assert "not found" in str(exc_info.value)


class TestDeletionRequestServiceSendEmail:
    """Tests for send_request_email method"""

    def test_send_email_success(
        self, db: Session, test_deletion_request: DeletionRequest, test_broker: DataBroker
    ):
        """Test successful email sending"""
        service = DeletionRequestService(db)

        # Mock gmail service
        mock_gmail = MagicMock()
        mock_gmail.send_email.return_value = {
            "message_id": "sent-msg-123",
            "thread_id": "thread-456",
        }

        request = service.send_request_email(test_deletion_request.id, mock_gmail)

        assert request.status == RequestStatus.SENT
        assert request.sent_at is not None
        assert request.gmail_sent_message_id == "sent-msg-123"
        assert request.gmail_thread_id == "thread-456"
        mock_gmail.send_email.assert_called_once()

    def test_send_email_not_pending_fails(
        self, db: Session, sent_deletion_request: DeletionRequest
    ):
        """Test that sending already-sent request fails"""
        service = DeletionRequestService(db)
        mock_gmail = MagicMock()

        with pytest.raises(Exception) as exc_info:
            service.send_request_email(sent_deletion_request.id, mock_gmail)

        assert "Cannot send request with status" in str(exc_info.value)

    def test_send_email_no_privacy_email_fails(
        self, db: Session, test_user: User
    ):
        """Test that sending fails if broker has no privacy email"""
        # Create broker without privacy email
        broker = DataBroker(
            name="No Email Broker",
            domains=["noemail.com"],
            privacy_email=None,
        )
        db.add(broker)
        db.commit()

        # Create request for this broker
        request = DeletionRequest(
            user_id=test_user.id,
            broker_id=broker.id,
            status=RequestStatus.PENDING,
            generated_email_subject="Test",
            generated_email_body="Test body",
        )
        db.add(request)
        db.commit()

        service = DeletionRequestService(db)
        mock_gmail = MagicMock()

        with pytest.raises(Exception) as exc_info:
            service.send_request_email(request.id, mock_gmail)

        assert "no privacy email" in str(exc_info.value)

    def test_send_email_rate_limited(
        self, db: Session, test_deletion_request: DeletionRequest
    ):
        """Test that rate-limited requests can't be sent"""
        service = DeletionRequestService(db)

        # Set next_retry_at to future
        test_deletion_request.next_retry_at = datetime.utcnow() + timedelta(minutes=10)
        db.commit()

        mock_gmail = MagicMock()

        with pytest.raises(Exception) as exc_info:
            service.send_request_email(test_deletion_request.id, mock_gmail)

        assert "rate limit" in str(exc_info.value).lower()

    def test_send_email_permission_error(
        self, db: Session, test_deletion_request: DeletionRequest
    ):
        """Test handling of permission errors"""
        service = DeletionRequestService(db)

        mock_gmail = MagicMock()
        mock_gmail.send_email.side_effect = PermissionError("Missing gmail.send scope")

        with pytest.raises(PermissionError) as exc_info:
            service.send_request_email(test_deletion_request.id, mock_gmail)

        assert "permissions" in str(exc_info.value).lower()

    def test_send_email_generic_error(
        self, db: Session, test_deletion_request: DeletionRequest
    ):
        """Test handling of generic send errors"""
        service = DeletionRequestService(db)

        mock_gmail = MagicMock()
        mock_gmail.send_email.side_effect = Exception("Network error")

        with pytest.raises(Exception) as exc_info:
            service.send_request_email(test_deletion_request.id, mock_gmail)

        assert "Failed to send email" in str(exc_info.value)

        # Verify error was logged
        db.refresh(test_deletion_request)
        assert test_deletion_request.last_send_error == "Network error"

    def test_send_email_increments_attempts(
        self, db: Session, test_deletion_request: DeletionRequest
    ):
        """Test that send attempts are incremented"""
        service = DeletionRequestService(db)

        initial_attempts = test_deletion_request.send_attempts

        mock_gmail = MagicMock()
        mock_gmail.send_email.return_value = {"message_id": "msg-1", "thread_id": "thread-1"}

        service.send_request_email(test_deletion_request.id, mock_gmail)

        db.refresh(test_deletion_request)
        assert test_deletion_request.send_attempts == initial_attempts + 1
