"""Tests for ResponseMatcher service"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.broker_response import BrokerResponse, ResponseType
from app.models.data_broker import DataBroker
from app.models.deletion_request import DeletionRequest, RequestStatus
from app.models.user import User
from app.services.response_matcher import ResponseMatcher


class TestResponseMatcherByThreadId:
    """Tests for _match_by_thread_id method"""

    def test_match_by_thread_id_success(
        self, db: Session, test_user: User, sent_deletion_request: DeletionRequest
    ):
        """Test matching response by Gmail thread ID"""
        matcher = ResponseMatcher(db)

        # Create a response with same thread_id as the sent request
        response = BrokerResponse(
            user_id=test_user.id,
            gmail_message_id="response-123",
            gmail_thread_id=sent_deletion_request.gmail_thread_id,
            sender_email="privacy@testbroker.com",
            response_type=ResponseType.CONFIRMATION,
        )
        db.add(response)
        db.commit()

        request_id, matched_by = matcher.match_response_to_request(response)

        assert request_id == str(sent_deletion_request.id)
        assert matched_by == "thread_id"

    def test_match_by_thread_id_no_match(
        self, db: Session, test_user: User, sent_deletion_request: DeletionRequest
    ):
        """Test no match when thread_id doesn't match"""
        matcher = ResponseMatcher(db)

        # Create a response with different thread_id
        response = BrokerResponse(
            user_id=test_user.id,
            gmail_message_id="response-456",
            gmail_thread_id="different-thread",
            sender_email="privacy@testbroker.com",
            response_type=ResponseType.CONFIRMATION,
        )
        db.add(response)
        db.commit()

        request_id, matched_by = matcher.match_response_to_request(response)

        # Should not match by thread_id, but might match by other methods
        if matched_by == "thread_id":
            pytest.fail("Should not match by thread_id with different thread")


class TestResponseMatcherBySubjectSender:
    """Tests for _match_by_subject_and_sender method"""

    def test_match_by_subject_sender_success(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test matching response by subject keywords and sender domain"""
        matcher = ResponseMatcher(db)

        # Create a sent deletion request without thread_id
        request = DeletionRequest(
            user_id=test_user.id,
            broker_id=test_broker.id,
            status=RequestStatus.SENT,
            sent_at=datetime.utcnow() - timedelta(days=5),
            gmail_sent_message_id="sent-msg",
            gmail_thread_id=None,  # No thread_id to force subject matching
        )
        db.add(request)
        db.commit()

        # Create a response from broker domain with reply-like subject
        response = BrokerResponse(
            user_id=test_user.id,
            gmail_message_id="response-789",
            gmail_thread_id=None,
            sender_email="privacy@testbroker.com",
            subject="Re: Data Deletion Request",
            response_type=ResponseType.CONFIRMATION,
        )
        db.add(response)
        db.commit()

        request_id, matched_by = matcher.match_response_to_request(response)

        assert request_id == str(request.id)
        assert matched_by == "subject_sender"

    def test_match_by_subject_sender_no_keywords(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test no match when subject has no reply keywords"""
        matcher = ResponseMatcher(db)

        # Create a sent deletion request
        request = DeletionRequest(
            user_id=test_user.id,
            broker_id=test_broker.id,
            status=RequestStatus.SENT,
            sent_at=datetime.utcnow() - timedelta(days=5),
        )
        db.add(request)
        db.commit()

        # Create a response without reply keywords
        response = BrokerResponse(
            user_id=test_user.id,
            gmail_message_id="response-aaa",
            gmail_thread_id=None,
            sender_email="privacy@testbroker.com",
            subject="Weekly Newsletter",
            response_type=ResponseType.UNKNOWN,
        )
        db.add(response)
        db.commit()

        # Will still try domain matching
        request_id, matched_by = matcher.match_response_to_request(response)

        # Should not match by subject_sender
        assert matched_by != "subject_sender" or request_id is None


class TestResponseMatcherByDomainTime:
    """Tests for _match_by_domain_and_time method"""

    def test_match_by_domain_time_success(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test matching response by sender domain and time window"""
        matcher = ResponseMatcher(db)

        # Create a sent deletion request
        request = DeletionRequest(
            user_id=test_user.id,
            broker_id=test_broker.id,
            status=RequestStatus.SENT,
            sent_at=datetime.utcnow() - timedelta(days=5),
        )
        db.add(request)
        db.commit()

        # Create a response from broker domain (no thread, no keywords)
        response = BrokerResponse(
            user_id=test_user.id,
            gmail_message_id="response-bbb",
            gmail_thread_id=None,
            sender_email="noreply@testbroker.com",
            subject="Automated Response",
            response_type=ResponseType.ACKNOWLEDGMENT,
        )
        db.add(response)
        db.commit()

        request_id, matched_by = matcher.match_response_to_request(response)

        assert request_id == str(request.id)
        assert matched_by == "domain_time"

    def test_match_by_domain_time_excludes_already_matched(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test that requests with existing responses are excluded"""
        matcher = ResponseMatcher(db)

        # Create a sent deletion request
        request = DeletionRequest(
            user_id=test_user.id,
            broker_id=test_broker.id,
            status=RequestStatus.SENT,
            sent_at=datetime.utcnow() - timedelta(days=5),
        )
        db.add(request)
        db.commit()

        # Create an existing response linked to this request
        existing_response = BrokerResponse(
            user_id=test_user.id,
            deletion_request_id=request.id,
            gmail_message_id="existing-response",
            sender_email="privacy@testbroker.com",
            response_type=ResponseType.ACKNOWLEDGMENT,
        )
        db.add(existing_response)
        db.commit()

        # Create a new response from same broker
        new_response = BrokerResponse(
            user_id=test_user.id,
            gmail_message_id="new-response",
            gmail_thread_id=None,
            sender_email="noreply@testbroker.com",
            subject="Automated Response",
            response_type=ResponseType.CONFIRMATION,
        )
        db.add(new_response)
        db.commit()

        request_id, matched_by = matcher.match_response_to_request(new_response)

        # Should not match since request already has a response
        assert request_id is None


class TestResponseMatcherExtractDomain:
    """Tests for _extract_domain helper method"""

    def test_extract_domain_simple_email(self, db: Session):
        """Test extracting domain from simple email"""
        matcher = ResponseMatcher(db)

        domain = matcher._extract_domain("user@example.com")
        assert domain == "example.com"

    def test_extract_domain_with_name(self, db: Session):
        """Test extracting domain from email with display name"""
        matcher = ResponseMatcher(db)

        domain = matcher._extract_domain("John Doe <john@example.com>")
        assert domain == "example.com"

    def test_extract_domain_uppercase(self, db: Session):
        """Test that domain is lowercased"""
        matcher = ResponseMatcher(db)

        domain = matcher._extract_domain("user@EXAMPLE.COM")
        assert domain == "example.com"

    def test_extract_domain_invalid_email(self, db: Session):
        """Test handling of invalid email"""
        matcher = ResponseMatcher(db)

        assert matcher._extract_domain("not-an-email") is None
        assert matcher._extract_domain("") is None
        assert matcher._extract_domain(None) is None


class TestResponseMatcherNoMatch:
    """Tests for scenarios where no match is found"""

    def test_no_match_unknown_sender(
        self, db: Session, test_user: User, sent_deletion_request: DeletionRequest
    ):
        """Test no match when sender domain is not a known broker"""
        matcher = ResponseMatcher(db)

        # Create response from unknown domain
        response = BrokerResponse(
            user_id=test_user.id,
            gmail_message_id="unknown-response",
            gmail_thread_id=None,
            sender_email="noreply@unknown-broker.com",
            subject="Re: Data Request",
            response_type=ResponseType.CONFIRMATION,
        )
        db.add(response)
        db.commit()

        request_id, matched_by = matcher.match_response_to_request(response)

        assert request_id is None
        assert matched_by is None

    def test_no_match_different_user(
        self, db: Session, test_user: User, admin_user: User, test_broker: DataBroker
    ):
        """Test no match when response is from different user"""
        matcher = ResponseMatcher(db)

        # Create a request for test_user
        request = DeletionRequest(
            user_id=test_user.id,
            broker_id=test_broker.id,
            status=RequestStatus.SENT,
            sent_at=datetime.utcnow() - timedelta(days=5),
            gmail_thread_id="thread-abc",
        )
        db.add(request)
        db.commit()

        # Create response for admin_user with same thread_id
        response = BrokerResponse(
            user_id=admin_user.id,
            gmail_message_id="admin-response",
            gmail_thread_id="thread-abc",
            sender_email="privacy@testbroker.com",
            response_type=ResponseType.CONFIRMATION,
        )
        db.add(response)
        db.commit()

        request_id, matched_by = matcher.match_response_to_request(response)

        # Should not match since users are different
        assert request_id is None


class TestResponseMatcherOldRequests:
    """Tests for time-based filtering"""

    def test_no_match_old_request(
        self, db: Session, test_user: User, test_broker: DataBroker
    ):
        """Test no match when request is older than 90 days"""
        matcher = ResponseMatcher(db)

        # Create a request sent 100 days ago
        old_request = DeletionRequest(
            user_id=test_user.id,
            broker_id=test_broker.id,
            status=RequestStatus.SENT,
            sent_at=datetime.utcnow() - timedelta(days=100),
        )
        db.add(old_request)
        db.commit()

        # Create response from broker
        response = BrokerResponse(
            user_id=test_user.id,
            gmail_message_id="old-response",
            gmail_thread_id=None,
            sender_email="privacy@testbroker.com",
            subject="Regarding your request",
            response_type=ResponseType.CONFIRMATION,
        )
        db.add(response)
        db.commit()

        request_id, matched_by = matcher.match_response_to_request(response)

        # Should not match since request is too old
        assert request_id is None
