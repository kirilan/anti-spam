"""Tests for email template generation"""

from app.utils.email_templates import EmailTemplates


class TestEmailTemplates:
    """Tests for EmailTemplates class"""

    def setup_method(self):
        """Clear template cache before each test"""
        EmailTemplates.clear_cache()

    def test_generate_gdpr_request(self):
        """Test generating a GDPR deletion request"""
        subject, body = EmailTemplates.generate_gdpr_request(
            user_email="test@example.com", broker_name="Test Broker"
        )
        assert "GDPR" in subject
        assert "test@example.com" in body
        assert "Test Broker" in body
        assert "Article 17" in body

    def test_generate_ccpa_request(self):
        """Test generating a CCPA deletion request"""
        subject, body = EmailTemplates.generate_ccpa_request(
            user_email="test@example.com", broker_name="Test Broker"
        )
        assert "CCPA" in subject
        assert "test@example.com" in body
        assert "Test Broker" in body
        assert "California Consumer Privacy Act" in body

    def test_generate_combined_request(self):
        """Test generating a combined GDPR/CCPA deletion request"""
        subject, body = EmailTemplates.generate_deletion_request_email(
            user_email="test@example.com", broker_name="Test Broker", framework="GDPR/CCPA"
        )
        assert "GDPR/CCPA" in subject
        assert "test@example.com" in body
        assert "Test Broker" in body

    def test_unknown_framework_defaults_to_combined(self):
        """Test that unknown framework defaults to GDPR/CCPA"""
        subject, body = EmailTemplates.generate_deletion_request_email(
            user_email="test@example.com", broker_name="Test Broker", framework="UNKNOWN"
        )
        assert "GDPR/CCPA" in subject

    def test_template_contains_deadline(self):
        """Test that generated email contains a deadline"""
        subject, body = EmailTemplates.generate_deletion_request_email(
            user_email="test@example.com", broker_name="Test Broker"
        )
        assert "Deadline for completion:" in body or "by" in body.lower()

    def test_template_caching(self):
        """Test that templates are cached after first load"""
        # First call loads the template
        EmailTemplates.generate_gdpr_request("test@example.com", "Broker")

        # Check cache is populated
        assert len(EmailTemplates._template_cache) > 0

        # Clear and verify
        EmailTemplates.clear_cache()
        assert len(EmailTemplates._template_cache) == 0

    def test_email_escaping(self):
        """Test that email addresses are included as-is"""
        subject, body = EmailTemplates.generate_deletion_request_email(
            user_email="user+tag@example.com", broker_name="Test Broker"
        )
        assert "user+tag@example.com" in body
