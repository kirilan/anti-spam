"""Tests for the broker detector service"""

import pytest

from app.models.data_broker import DataBroker
from app.services.broker_detector import BrokerDetector


class TestBrokerDetectorDetectBroker:
    """Tests for detect_broker method"""

    @pytest.fixture
    def detector(self):
        """Create a BrokerDetector instance"""
        return BrokerDetector()

    @pytest.fixture
    def sample_brokers(self):
        """Create sample brokers for testing"""
        return [
            DataBroker(
                id="broker-1",
                name="SpyOnYou",
                domains=["spyonyou.com", "spy-on-you.net"],
                privacy_email="privacy@spyonyou.com",
            ),
            DataBroker(
                id="broker-2",
                name="PeopleSearch Pro",
                domains=["peoplesearchpro.com"],
                privacy_email="remove@peoplesearchpro.com",
            ),
        ]

    def test_detect_broker_direct_domain_match(
        self, detector: BrokerDetector, sample_brokers: list[DataBroker]
    ):
        """Test detection by direct domain match"""
        broker, confidence, notes = detector.detect_broker(
            sender_email="noreply@spyonyou.com",
            sender_domain="spyonyou.com",
            subject="Your account update",
            body_html="",
            body_text="Hello, your account has been updated.",
            all_brokers=sample_brokers,
        )

        assert broker is not None
        assert broker.name == "SpyOnYou"
        assert confidence == 1.0
        assert "Direct domain match" in notes

    def test_detect_broker_subdomain_match(
        self, detector: BrokerDetector, sample_brokers: list[DataBroker]
    ):
        """Test detection matches subdomains"""
        broker, confidence, notes = detector.detect_broker(
            sender_email="noreply@mail.spyonyou.com",
            sender_domain="mail.spyonyou.com",
            subject="Newsletter",
            body_html="",
            body_text="Weekly newsletter",
            all_brokers=sample_brokers,
        )

        assert broker is not None
        assert broker.name == "SpyOnYou"
        assert confidence == 1.0

    def test_detect_broker_keyword_high_confidence(
        self, detector: BrokerDetector, sample_brokers: list[DataBroker]
    ):
        """Test detection with multiple keyword matches (high confidence)"""
        broker, confidence, notes = detector.detect_broker(
            sender_email="unknown@example.com",
            sender_domain="example.com",
            subject="Your GDPR privacy rights",
            body_html="",
            body_text="Opt out of our data broker marketing list. Personal information removal available.",
            all_brokers=sample_brokers,
        )

        # No broker match but high keyword confidence
        assert broker is None
        assert confidence >= 0.7
        assert "Keyword matches" in notes

    def test_detect_broker_keyword_medium_confidence(
        self, detector: BrokerDetector, sample_brokers: list[DataBroker]
    ):
        """Test detection with two keyword matches (medium confidence)"""
        broker, confidence, notes = detector.detect_broker(
            sender_email="unknown@example.com",
            sender_domain="example.com",
            subject="Data privacy update",
            body_html="",
            body_text="Please unsubscribe if you don't want our emails.",
            all_brokers=sample_brokers,
        )

        assert broker is None
        assert confidence >= 0.5
        assert confidence < 0.7

    def test_detect_broker_keyword_low_confidence(
        self, detector: BrokerDetector, sample_brokers: list[DataBroker]
    ):
        """Test detection with single keyword match (low confidence)"""
        broker, confidence, notes = detector.detect_broker(
            sender_email="unknown@example.com",
            sender_domain="example.com",
            subject="Account update",
            body_html="",
            body_text="Click here to unsubscribe from our list.",
            all_brokers=sample_brokers,
        )

        assert broker is None
        assert confidence >= 0.3
        assert confidence < 0.5

    def test_detect_broker_no_match(
        self, detector: BrokerDetector, sample_brokers: list[DataBroker]
    ):
        """Test detection with no broker indicators"""
        broker, confidence, notes = detector.detect_broker(
            sender_email="friend@gmail.com",
            sender_domain="gmail.com",
            subject="Hey, how are you?",
            body_html="",
            body_text="Just checking in to say hi!",
            all_brokers=sample_brokers,
        )

        assert broker is None
        assert confidence == 0.0
        assert "No broker indicators found" in notes

    def test_detect_broker_parses_html(
        self, detector: BrokerDetector, sample_brokers: list[DataBroker]
    ):
        """Test that HTML body is parsed for keywords"""
        broker, confidence, notes = detector.detect_broker(
            sender_email="unknown@example.com",
            sender_domain="example.com",
            subject="Message",
            body_html="<html><body><p>Please opt-out using the link below.</p><p>Data privacy is important. GDPR compliance.</p></body></html>",
            body_text="",
            all_brokers=sample_brokers,
        )

        assert confidence >= 0.7  # Should find opt-out, data privacy, gdpr

    def test_detect_broker_empty_brokers_list(self, detector: BrokerDetector):
        """Test detection with empty brokers list"""
        broker, confidence, notes = detector.detect_broker(
            sender_email="test@test.com",
            sender_domain="test.com",
            subject="Test",
            body_html="",
            body_text="Test message",
            all_brokers=[],
        )

        assert broker is None
        assert confidence == 0.0


class TestBrokerDetectorExtractDomain:
    """Tests for extract_domain_from_email method"""

    @pytest.fixture
    def detector(self):
        return BrokerDetector()

    def test_extract_domain_simple(self, detector: BrokerDetector):
        """Test domain extraction from simple email"""
        domain = detector.extract_domain_from_email("user@example.com")
        assert domain == "example.com"

    def test_extract_domain_uppercase(self, detector: BrokerDetector):
        """Test domain is lowercased"""
        domain = detector.extract_domain_from_email("USER@EXAMPLE.COM")
        assert domain == "example.com"

    def test_extract_domain_no_at(self, detector: BrokerDetector):
        """Test handling input without @ symbol"""
        domain = detector.extract_domain_from_email("example.com")
        assert domain == "example.com"


class TestBrokerDetectorBodyPreview:
    """Tests for get_body_preview method"""

    @pytest.fixture
    def detector(self):
        return BrokerDetector()

    def test_get_body_preview_text(self, detector: BrokerDetector):
        """Test preview from text body"""
        preview = detector.get_body_preview("", "Hello world! This is a test message.", 20)
        assert "Hello world" in preview

    def test_get_body_preview_html(self, detector: BrokerDetector):
        """Test preview from HTML body"""
        preview = detector.get_body_preview(
            "<html><body><p>Hello world!</p></body></html>", "", 20
        )
        assert "Hello world" in preview

    def test_get_body_preview_truncated(self, detector: BrokerDetector):
        """Test that long previews are truncated with ellipsis"""
        long_text = "A" * 300
        preview = detector.get_body_preview("", long_text, 100)
        assert len(preview) <= 103  # 100 chars + "..."
        assert preview.endswith("...")

    def test_get_body_preview_empty(self, detector: BrokerDetector):
        """Test preview with empty body"""
        preview = detector.get_body_preview("", "", 100)
        assert preview == ""

    def test_get_body_preview_whitespace_normalized(self, detector: BrokerDetector):
        """Test that whitespace is normalized"""
        preview = detector.get_body_preview("", "Hello    world\n\ntest", 50)
        assert "  " not in preview  # No double spaces
        assert "\n" not in preview  # No newlines
