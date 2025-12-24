from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# IMPORTANT: Do NOT set OAUTHLIB_RELAX_TOKEN_SCOPE=1 in production
# This would allow tokens without the required scopes to be accepted
# os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
from app.config import settings
from app.exceptions import GmailQuotaExceededError
from app.models.user import User


class GmailService:
    SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ]

    def __init__(self):
        self.client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        }

    def get_authorization_url(self) -> tuple[str, str]:
        """Generate OAuth authorization URL and state"""
        flow = Flow.from_client_config(
            self.client_config, scopes=self.SCOPES, redirect_uri=settings.google_redirect_uri
        )

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",  # Always show consent screen
            include_granted_scopes="false",  # Don't use incremental auth
        )

        return authorization_url, state

    def exchange_code_for_tokens(self, code: str, state: str | None = None) -> dict[str, str]:
        """Exchange authorization code for access and refresh tokens"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=settings.google_redirect_uri,
            state=state,
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }

    def get_credentials(self, user: User) -> Credentials:
        """Get Google credentials from user's encrypted tokens"""
        access_token = user.get_access_token()
        refresh_token = user.get_refresh_token()

        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=self.client_config["web"]["token_uri"],
            client_id=self.client_config["web"]["client_id"],
            client_secret=self.client_config["web"]["client_secret"],
            scopes=self.SCOPES,
        )

        return credentials

    def get_user_info(self, credentials: Credentials) -> dict[str, str]:
        """Get user info from Google"""
        from googleapiclient.discovery import build

        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info

    def list_messages(self, user: User, query: str = "", max_results: int = 100) -> list[dict]:
        """List Gmail messages for a user"""
        credentials = self.get_credentials(user)
        service = build("gmail", "v1", credentials=credentials)

        results = (
            service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        )

        return results.get("messages", [])

    def get_message(self, user: User, message_id: str) -> dict:
        """Get a specific Gmail message"""
        credentials = self.get_credentials(user)
        service = build("gmail", "v1", credentials=credentials)

        message = (
            service.users().messages().get(userId="me", id=message_id, format="full").execute()
        )

        return message

    def get_message_headers(self, message: dict) -> dict[str, str]:
        """Extract headers from a Gmail message"""
        headers = {}
        if "payload" in message and "headers" in message["payload"]:
            for header in message["payload"]["headers"]:
                headers[header["name"].lower()] = header["value"]
        return headers

    def search_messages(self, user: User, query: str, max_results: int = 50) -> list[dict]:
        """
        Search for Gmail messages and fetch their full content

        Args:
            user: User object
            query: Gmail search query
            max_results: Maximum number of messages to fetch

        Returns:
            List of full message objects with content
        """
        credentials = self.get_credentials(user)
        service = build("gmail", "v1", credentials=credentials)

        # List message IDs
        results = (
            service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        )

        message_ids = results.get("messages", [])

        # Fetch full message content
        messages = []
        for msg in message_ids:
            try:
                full_message = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )
                messages.append(full_message)
            except Exception:
                # Skip messages that can't be fetched
                continue

        return messages

    def _extract_body(self, payload: dict) -> str:
        """
        Extract plain text body from Gmail message payload

        Args:
            payload: Gmail message payload

        Returns:
            Extracted plain text body
        """
        import base64

        body_text = ""

        def parse_parts(parts):
            nonlocal body_text
            for part in parts:
                mime_type = part.get("mimeType", "")

                if mime_type == "text/plain" and "data" in part.get("body", {}):
                    body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8", errors="ignore"
                    )
                    return  # Use first text/plain part found

                if "parts" in part:
                    parse_parts(part["parts"])

        # Single part message
        if "body" in payload and "data" in payload["body"]:
            mime_type = payload.get("mimeType", "")
            if mime_type == "text/plain":
                body_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                    "utf-8", errors="ignore"
                )

        # Multi-part message
        if "parts" in payload:
            parse_parts(payload["parts"])

        return body_text

    def has_send_permission(self, user: User) -> bool:
        """Check if user has granted gmail.send scope"""
        credentials = self.get_credentials(user)
        return "https://www.googleapis.com/auth/gmail.send" in (credentials.scopes or [])

    def send_email(
        self, user: User, to_email: str, subject: str, body: str, reply_to: str | None = None
    ) -> dict[str, str]:
        """
        Send email via Gmail API

        Args:
            user: User object with OAuth credentials
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            reply_to: Optional Reply-To email address

        Returns:
            Dict with 'message_id', 'thread_id', 'label_ids'

        Raises:
            PermissionError: If user lacks gmail.send permission
            Exception: For other send failures
        """
        # Check permissions
        if not self.has_send_permission(user):
            raise PermissionError("User has not granted gmail.send permission")

        # Build credentials
        credentials = self.get_credentials(user)
        service = build("gmail", "v1", credentials=credentials)

        # Create MIME message
        import base64
        from email.mime.text import MIMEText

        message = MIMEText(body, "plain")
        message["To"] = to_email
        message["From"] = user.email
        message["Subject"] = subject
        if reply_to:
            message["Reply-To"] = reply_to

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send via API
        try:
            sent_message = (
                service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
            )

            return {
                "message_id": sent_message["id"],
                "thread_id": sent_message.get("threadId"),
                "label_ids": sent_message.get("labelIds", []),
            }
        except HttpError as http_error:
            status = getattr(http_error.resp, "status", None)
            retry_after_header = None
            if hasattr(http_error, "resp") and getattr(http_error.resp, "headers", None):
                retry_after_header = http_error.resp.headers.get("Retry-After")

            rate_limit_reasons = {"rateLimitExceeded", "userRateLimitExceeded", "quotaExceeded"}
            reasons = []
            if getattr(http_error, "error_details", None):
                for detail in http_error.error_details:
                    reason = detail.get("reason")
                    if reason:
                        reasons.append(reason)

            if not reasons:
                try:
                    reasons.append(http_error._get_reason())
                except Exception:
                    pass

            # Determine if the error is due to Gmail quota/rate limit
            if status in (403, 429) and any(
                reason
                for reason in reasons
                if reason and any(r in reason for r in rate_limit_reasons)
            ):
                retry_after = None
                if retry_after_header:
                    try:
                        retry_after = int(retry_after_header)
                    except ValueError:
                        retry_after = None

                message = (
                    http_error._get_reason()
                    if hasattr(http_error, "_get_reason")
                    else "Gmail quota exceeded"
                )
                raise GmailQuotaExceededError(message=message, retry_after=retry_after)

            raise Exception(f"Failed to send email: {http_error}")
        except Exception as e:
            # Handle other failures
            raise Exception(f"Failed to send email: {str(e)}")

    def list_sent_messages(self, user: User, query: str = "", max_results: int = 100) -> list[dict]:
        """
        List sent Gmail messages for a user

        Args:
            user: User object
            query: Additional Gmail search query (will be combined with 'in:sent')
            max_results: Maximum number of messages to fetch

        Returns:
            List of message metadata (id, threadId)
        """
        credentials = self.get_credentials(user)
        service = build("gmail", "v1", credentials=credentials)

        # Always search in sent folder
        full_query = f"in:sent {query}".strip()

        results = (
            service.users()
            .messages()
            .list(userId="me", q=full_query, maxResults=max_results)
            .execute()
        )

        return results.get("messages", [])

    def get_thread_messages(self, user: User, thread_id: str) -> list[dict]:
        """
        Get all messages in a Gmail thread

        Args:
            user: User object
            thread_id: Gmail thread ID

        Returns:
            List of full message objects in the thread
        """
        credentials = self.get_credentials(user)
        service = build("gmail", "v1", credentials=credentials)

        try:
            thread = (
                service.users().threads().get(userId="me", id=thread_id, format="full").execute()
            )
            return thread.get("messages", [])
        except Exception:
            # Return empty list if thread not found or error
            return []
