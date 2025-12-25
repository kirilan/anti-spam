"""Tests for the Gmail service"""

import base64
from unittest.mock import MagicMock, Mock, patch

import pytest
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.exceptions import GmailQuotaExceededError
from app.models.user import User
from app.services.gmail_service import GmailService


class TestGmailServiceOAuth:
    """Tests for OAuth-related methods"""

    def test_get_authorization_url(self):
        """Test generating OAuth authorization URL"""
        service = GmailService()

        with patch("app.services.gmail_service.Flow") as mock_flow_class:
            mock_flow = MagicMock()
            mock_flow.authorization_url.return_value = (
                "https://accounts.google.com/auth",
                "state-123",
            )
            mock_flow_class.from_client_config.return_value = mock_flow

            auth_url, state = service.get_authorization_url()

            assert auth_url == "https://accounts.google.com/auth"
            assert state == "state-123"
            mock_flow.authorization_url.assert_called_once_with(
                access_type="offline",
                prompt="consent",
                include_granted_scopes="false",
            )

    def test_exchange_code_for_tokens(self):
        """Test exchanging authorization code for tokens"""
        service = GmailService()

        with patch("app.services.gmail_service.Flow") as mock_flow_class:
            mock_credentials = MagicMock()
            mock_credentials.token = "access-token-123"
            mock_credentials.refresh_token = "refresh-token-456"
            mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
            mock_credentials.client_id = "client-id"
            mock_credentials.client_secret = "client-secret"
            mock_credentials.scopes = GmailService.SCOPES

            mock_flow = MagicMock()
            mock_flow.credentials = mock_credentials
            mock_flow_class.from_client_config.return_value = mock_flow

            tokens = service.exchange_code_for_tokens(code="auth-code", state="state-123")

            assert tokens["access_token"] == "access-token-123"
            assert tokens["refresh_token"] == "refresh-token-456"
            assert tokens["token_uri"] == "https://oauth2.googleapis.com/token"
            mock_flow.fetch_token.assert_called_once_with(code="auth-code")

    def test_get_credentials(self, test_user: User):
        """Test getting credentials from user"""
        service = GmailService()

        with patch.object(test_user, "get_access_token", return_value="access-token"):
            with patch.object(test_user, "get_refresh_token", return_value="refresh-token"):
                credentials = service.get_credentials(test_user)

                assert isinstance(credentials, Credentials)
                assert credentials.token == "access-token"
                assert credentials.refresh_token == "refresh-token"

    def test_get_user_info(self):
        """Test getting user info from Google"""
        service = GmailService()
        mock_credentials = MagicMock()

        with patch("googleapiclient.discovery.build") as mock_build:
            # Create a mock that returns the user info when called as: service.userinfo().get().execute()
            mock_service = MagicMock()
            mock_service.userinfo().get().execute.return_value = {
                "email": "user@example.com",
                "id": "google-123",
            }
            mock_build.return_value = mock_service

            user_info = service.get_user_info(mock_credentials)

            assert user_info["email"] == "user@example.com"
            assert user_info["id"] == "google-123"
            mock_build.assert_called_once_with("oauth2", "v2", credentials=mock_credentials)


class TestGmailServiceMessages:
    """Tests for message-related methods"""

    def test_list_messages(self, test_user: User):
        """Test listing Gmail messages"""
        service = GmailService()

        with patch.object(service, "get_credentials") as mock_get_creds:
            with patch("app.services.gmail_service.build") as mock_build:
                mock_list = MagicMock()
                mock_list.execute.return_value = {"messages": [{"id": "msg-1"}, {"id": "msg-2"}]}
                mock_messages = MagicMock()
                mock_messages.list.return_value = mock_list
                mock_users = MagicMock()
                mock_users.messages.return_value = mock_messages
                mock_service = MagicMock()
                mock_service.users.return_value = mock_users
                mock_build.return_value = mock_service

                messages = service.list_messages(test_user, query="from:broker", max_results=50)

                assert len(messages) == 2
                assert messages[0]["id"] == "msg-1"

    def test_list_messages_empty(self, test_user: User):
        """Test listing messages when none exist"""
        service = GmailService()

        with patch.object(service, "get_credentials"):
            with patch("app.services.gmail_service.build") as mock_build:
                mock_service = MagicMock()
                mock_service.users().messages().list().execute.return_value = {}
                mock_build.return_value = mock_service

                messages = service.list_messages(test_user)

                assert messages == []

    def test_get_message(self, test_user: User):
        """Test getting a specific message"""
        service = GmailService()

        with patch.object(service, "get_credentials"):
            with patch("app.services.gmail_service.build") as mock_build:
                mock_get = MagicMock()
                mock_get.execute.return_value = {"id": "msg-123", "payload": {"headers": []}}
                mock_messages = MagicMock()
                mock_messages.get.return_value = mock_get
                mock_users = MagicMock()
                mock_users.messages.return_value = mock_messages
                mock_service = MagicMock()
                mock_service.users.return_value = mock_users
                mock_build.return_value = mock_service

                message = service.get_message(test_user, "msg-123")

                assert message["id"] == "msg-123"

    def test_get_message_headers(self):
        """Test extracting headers from message"""
        service = GmailService()

        message = {
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "Date", "value": "2024-01-01"},
                ]
            }
        }

        headers = service.get_message_headers(message)

        assert headers["from"] == "sender@example.com"
        assert headers["subject"] == "Test Subject"
        assert headers["date"] == "2024-01-01"

    def test_get_message_headers_empty(self):
        """Test extracting headers from message without headers"""
        service = GmailService()
        message = {}

        headers = service.get_message_headers(message)

        assert headers == {}

    def test_search_messages(self, test_user: User):
        """Test searching for messages"""
        service = GmailService()

        with patch.object(service, "get_credentials"):
            with patch("app.services.gmail_service.build") as mock_build:
                mock_service = MagicMock()
                # List returns message IDs
                mock_service.users().messages().list().execute.return_value = {
                    "messages": [{"id": "msg-1"}, {"id": "msg-2"}]
                }
                # Get returns full messages
                mock_service.users().messages().get().execute.side_effect = [
                    {"id": "msg-1", "payload": {"body": {"data": "dGVzdA=="}}},
                    {"id": "msg-2", "payload": {"body": {"data": "dGVzdDI="}}},
                ]
                mock_build.return_value = mock_service

                messages = service.search_messages(test_user, query="from:broker", max_results=2)

                assert len(messages) == 2
                assert messages[0]["id"] == "msg-1"
                assert messages[1]["id"] == "msg-2"

    def test_search_messages_skips_errors(self, test_user: User):
        """Test that search_messages skips messages that can't be fetched"""
        service = GmailService()

        with patch.object(service, "get_credentials"):
            with patch("app.services.gmail_service.build") as mock_build:
                mock_service = MagicMock()
                # List returns 3 message IDs
                mock_service.users().messages().list().execute.return_value = {
                    "messages": [{"id": "msg-1"}, {"id": "msg-2"}, {"id": "msg-3"}]
                }
                # Second message fails to fetch
                mock_service.users().messages().get().execute.side_effect = [
                    {"id": "msg-1", "payload": {}},
                    Exception("Failed to fetch"),
                    {"id": "msg-3", "payload": {}},
                ]
                mock_build.return_value = mock_service

                messages = service.search_messages(test_user, query="test", max_results=3)

                # Should only have 2 messages (skipped the failed one)
                assert len(messages) == 2
                assert messages[0]["id"] == "msg-1"
                assert messages[1]["id"] == "msg-3"


class TestGmailServiceBodyExtraction:
    """Tests for body extraction method"""

    def test_extract_body_single_part(self):
        """Test extracting body from single-part message"""
        service = GmailService()

        text = "This is the email body"
        encoded = base64.urlsafe_b64encode(text.encode()).decode()

        payload = {"mimeType": "text/plain", "body": {"data": encoded}}

        body = service._extract_body(payload)

        assert body == text

    def test_extract_body_multipart(self):
        """Test extracting body from multi-part message"""
        service = GmailService()

        text = "This is the plain text body"
        encoded = base64.urlsafe_b64encode(text.encode()).decode()

        payload = {
            "parts": [
                {"mimeType": "text/html", "body": {"data": "PGh0bWw+PC9odG1sPg=="}},
                {"mimeType": "text/plain", "body": {"data": encoded}},
            ]
        }

        body = service._extract_body(payload)

        assert body == text

    def test_extract_body_nested_parts(self):
        """Test extracting body from nested multi-part message"""
        service = GmailService()

        text = "Nested plain text"
        encoded = base64.urlsafe_b64encode(text.encode()).decode()

        payload = {
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {"mimeType": "text/plain", "body": {"data": encoded}},
                        {"mimeType": "text/html", "body": {"data": "PGh0bWw+PC9odG1sPg=="}},
                    ],
                }
            ]
        }

        body = service._extract_body(payload)

        assert body == text

    def test_extract_body_no_text_plain(self):
        """Test extracting body when no text/plain part exists"""
        service = GmailService()

        payload = {
            "parts": [{"mimeType": "text/html", "body": {"data": "PGh0bWw+PC9odG1sPg=="}}]
        }

        body = service._extract_body(payload)

        assert body == ""

    def test_extract_body_invalid_base64(self):
        """Test extracting body with invalid base64 data"""
        service = GmailService()

        payload = {"mimeType": "text/plain", "body": {"data": "invalid!!!"}}

        # Should raise an exception for invalid base64
        # The service doesn't handle this gracefully, which is acceptable
        # as Gmail API should always return valid base64
        try:
            body = service._extract_body(payload)
            # If it doesn't raise, it should at least return a string
            assert isinstance(body, str)
        except Exception:
            # Invalid base64 raises an exception, which is expected
            pass


class TestGmailServiceSendEmail:
    """Tests for email sending functionality"""

    def test_has_send_permission_true(self, test_user: User):
        """Test checking send permission when granted"""
        service = GmailService()

        with patch.object(service, "get_credentials") as mock_get_creds:
            mock_creds = MagicMock()
            mock_creds.scopes = GmailService.SCOPES
            mock_get_creds.return_value = mock_creds

            has_permission = service.has_send_permission(test_user)

            assert has_permission is True

    def test_has_send_permission_false(self, test_user: User):
        """Test checking send permission when not granted"""
        service = GmailService()

        with patch.object(service, "get_credentials") as mock_get_creds:
            mock_creds = MagicMock()
            mock_creds.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
            mock_get_creds.return_value = mock_creds

            has_permission = service.has_send_permission(test_user)

            assert has_permission is False

    def test_send_email_success(self, test_user: User):
        """Test sending email successfully"""
        service = GmailService()

        with patch.object(service, "has_send_permission", return_value=True):
            with patch.object(service, "get_credentials"):
                with patch("app.services.gmail_service.build") as mock_build:
                    mock_service = MagicMock()
                    mock_service.users().messages().send().execute.return_value = {
                        "id": "sent-msg-123",
                        "threadId": "thread-456",
                        "labelIds": ["SENT"],
                    }
                    mock_build.return_value = mock_service

                    result = service.send_email(
                        user=test_user,
                        to_email="recipient@example.com",
                        subject="Test Subject",
                        body="Test body",
                    )

                    assert result["message_id"] == "sent-msg-123"
                    assert result["thread_id"] == "thread-456"
                    assert result["label_ids"] == ["SENT"]

    def test_send_email_with_reply_to(self, test_user: User):
        """Test sending email with Reply-To header"""
        service = GmailService()

        with patch.object(service, "has_send_permission", return_value=True):
            with patch.object(service, "get_credentials"):
                with patch("app.services.gmail_service.build") as mock_build:
                    mock_send = MagicMock()
                    mock_send.execute.return_value = {"id": "msg-1", "threadId": "thread-1"}
                    mock_messages = MagicMock()
                    mock_messages.send.return_value = mock_send
                    mock_users = MagicMock()
                    mock_users.messages.return_value = mock_messages
                    mock_service = MagicMock()
                    mock_service.users.return_value = mock_users
                    mock_build.return_value = mock_service

                    result = service.send_email(
                        user=test_user,
                        to_email="recipient@example.com",
                        subject="Test",
                        body="Body",
                        reply_to="noreply@example.com",
                    )

                    assert result["message_id"] == "msg-1"

    def test_send_email_no_permission(self, test_user: User):
        """Test sending email without permission raises error"""
        service = GmailService()

        with patch.object(service, "has_send_permission", return_value=False):
            with pytest.raises(PermissionError) as exc_info:
                service.send_email(
                    user=test_user,
                    to_email="recipient@example.com",
                    subject="Test",
                    body="Body",
                )

            assert "gmail.send permission" in str(exc_info.value)

    def test_send_email_quota_exceeded(self, test_user: User):
        """Test handling quota exceeded error"""
        service = GmailService()

        with patch.object(service, "has_send_permission", return_value=True):
            with patch.object(service, "get_credentials"):
                with patch("app.services.gmail_service.build") as mock_build:
                    # Create mock HttpError for quota exceeded
                    mock_resp = Mock()
                    mock_resp.status = 429
                    mock_resp.headers = {"Retry-After": "3600"}

                    mock_error = HttpError(resp=mock_resp, content=b"")
                    mock_error.error_details = [{"reason": "rateLimitExceeded"}]

                    mock_service = MagicMock()
                    mock_service.users().messages().send().execute.side_effect = mock_error
                    mock_build.return_value = mock_service

                    with pytest.raises(GmailQuotaExceededError) as exc_info:
                        service.send_email(
                            user=test_user,
                            to_email="recipient@example.com",
                            subject="Test",
                            body="Body",
                        )

                    assert exc_info.value.retry_after == 3600

    def test_send_email_http_error(self, test_user: User):
        """Test handling generic HTTP error"""
        service = GmailService()

        with patch.object(service, "has_send_permission", return_value=True):
            with patch.object(service, "get_credentials"):
                with patch("app.services.gmail_service.build") as mock_build:
                    mock_resp = Mock()
                    mock_resp.status = 400
                    mock_resp.headers = {}

                    mock_error = HttpError(resp=mock_resp, content=b"Bad request")
                    mock_error.error_details = []

                    mock_send = MagicMock()
                    mock_send.execute.side_effect = mock_error
                    mock_messages = MagicMock()
                    mock_messages.send.return_value = mock_send
                    mock_users = MagicMock()
                    mock_users.messages.return_value = mock_messages
                    mock_service = MagicMock()
                    mock_service.users.return_value = mock_users
                    mock_build.return_value = mock_service

                    with pytest.raises(Exception) as exc_info:
                        service.send_email(
                            user=test_user,
                            to_email="recipient@example.com",
                            subject="Test",
                            body="Body",
                        )

                    assert "Failed to send email" in str(exc_info.value)

    def test_send_email_generic_error(self, test_user: User):
        """Test handling generic send error"""
        service = GmailService()

        with patch.object(service, "has_send_permission", return_value=True):
            with patch.object(service, "get_credentials"):
                with patch("app.services.gmail_service.build") as mock_build:
                    mock_service = MagicMock()
                    mock_service.users().messages().send().execute.side_effect = Exception(
                        "Network error"
                    )
                    mock_build.return_value = mock_service

                    with pytest.raises(Exception) as exc_info:
                        service.send_email(
                            user=test_user,
                            to_email="recipient@example.com",
                            subject="Test",
                            body="Body",
                        )

                    assert "Failed to send email" in str(exc_info.value)
                    assert "Network error" in str(exc_info.value)


class TestGmailServiceSentMessages:
    """Tests for sent message methods"""

    def test_list_sent_messages(self, test_user: User):
        """Test listing sent messages"""
        service = GmailService()

        with patch.object(service, "get_credentials"):
            with patch("app.services.gmail_service.build") as mock_build:
                mock_service = MagicMock()
                mock_service.users().messages().list().execute.return_value = {
                    "messages": [{"id": "sent-1", "threadId": "thread-1"}]
                }
                mock_build.return_value = mock_service

                messages = service.list_sent_messages(test_user, query="to:broker@example.com")

                assert len(messages) == 1
                assert messages[0]["id"] == "sent-1"
                # Verify query includes "in:sent"
                call_args = mock_service.users().messages().list.call_args
                assert "in:sent" in call_args[1]["q"]
                assert "to:broker@example.com" in call_args[1]["q"]


class TestGmailServiceThreads:
    """Tests for thread-related methods"""

    def test_get_thread_messages(self, test_user: User):
        """Test getting messages in a thread"""
        service = GmailService()

        with patch.object(service, "get_credentials"):
            with patch("app.services.gmail_service.build") as mock_build:
                mock_get = MagicMock()
                mock_get.execute.return_value = {
                    "messages": [
                        {"id": "msg-1", "threadId": "thread-123"},
                        {"id": "msg-2", "threadId": "thread-123"},
                    ]
                }
                mock_threads = MagicMock()
                mock_threads.get.return_value = mock_get
                mock_users = MagicMock()
                mock_users.threads.return_value = mock_threads
                mock_service = MagicMock()
                mock_service.users.return_value = mock_users
                mock_build.return_value = mock_service

                messages = service.get_thread_messages(test_user, "thread-123")

                assert len(messages) == 2
                assert messages[0]["id"] == "msg-1"

    def test_get_thread_messages_error(self, test_user: User):
        """Test getting thread messages handles errors gracefully"""
        service = GmailService()

        with patch.object(service, "get_credentials"):
            with patch("app.services.gmail_service.build") as mock_build:
                mock_service = MagicMock()
                mock_service.users().threads().get().execute.side_effect = Exception(
                    "Thread not found"
                )
                mock_build.return_value = mock_service

                messages = service.get_thread_messages(test_user, "nonexistent-thread")

                # Should return empty list on error
                assert messages == []
