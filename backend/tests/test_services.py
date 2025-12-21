"""Tests for service layer"""

from sqlalchemy.orm import Session

from app.models.data_broker import DataBroker
from app.services.broker_service import BrokerService
from app.services.response_detector import ResponseDetector


class TestBrokerService:
    """Tests for BrokerService"""

    def test_get_all_brokers_empty(self, db: Session):
        """Test getting brokers when none exist"""
        service = BrokerService(db)
        brokers = service.get_all_brokers()
        assert brokers == []

    def test_get_all_brokers_with_data(self, db: Session, test_broker: DataBroker):
        """Test getting all brokers"""
        service = BrokerService(db)
        brokers = service.get_all_brokers()
        assert len(brokers) == 1
        assert brokers[0].name == "Test Broker"

    def test_get_broker_by_id(self, db: Session, test_broker: DataBroker):
        """Test getting a broker by ID"""
        service = BrokerService(db)
        broker = service.get_broker_by_id(str(test_broker.id))
        assert broker is not None
        assert broker.name == "Test Broker"

    def test_get_broker_by_id_not_found(self, db: Session):
        """Test getting a non-existent broker"""
        service = BrokerService(db)
        broker = service.get_broker_by_id("00000000-0000-0000-0000-000000000000")
        assert broker is None

    def test_find_broker_by_domain(self, db: Session, test_broker: DataBroker):
        """Test finding a broker by domain"""
        service = BrokerService(db)
        broker = service.find_broker_by_domain("testbroker.com")
        assert broker is not None
        assert broker.name == "Test Broker"

    def test_find_broker_by_domain_not_found(self, db: Session, test_broker: DataBroker):
        """Test finding a broker by non-matching domain"""
        service = BrokerService(db)
        broker = service.find_broker_by_domain("unknown.com")
        assert broker is None


class TestResponseDetector:
    """Tests for ResponseDetector"""

    def test_detect_confirmation_response(self):
        """Test detecting a confirmation response"""
        detector = ResponseDetector()
        response_type, confidence = detector.detect_response_type(
            subject=None, body="Your data has been successfully deleted from our systems."
        )
        assert response_type.value == "confirmation"
        assert confidence > 0.3

    def test_detect_rejection_response(self):
        """Test detecting a rejection response"""
        detector = ResponseDetector()
        response_type, confidence = detector.detect_response_type(
            subject=None, body="We were unable to locate any records matching your request."
        )
        assert response_type.value == "rejection"
        assert confidence > 0.3

    def test_detect_acknowledgment_response(self):
        """Test detecting an acknowledgment response"""
        detector = ResponseDetector()
        response_type, confidence = detector.detect_response_type(
            subject=None, body="We have received your request and it is currently under review."
        )
        assert response_type.value == "acknowledgment"
        assert confidence > 0.3

    def test_detect_request_info_response(self):
        """Test detecting a request for more information"""
        detector = ResponseDetector()
        response_type, confidence = detector.detect_response_type(
            subject=None, body="Please verify your identity by providing additional documentation."
        )
        assert response_type.value == "request_info"
        assert confidence > 0.3

    def test_detect_unknown_response(self):
        """Test detecting an unknown response type"""
        detector = ResponseDetector()
        response_type, confidence = detector.detect_response_type(
            subject=None, body="The weather is nice today."
        )
        assert response_type.value == "unknown"
