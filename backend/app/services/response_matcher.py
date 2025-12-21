"""
Response Matcher Service
Matches broker email responses to deletion requests
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.broker_response import BrokerResponse
from app.models.deletion_request import DeletionRequest
from app.services.broker_service import BrokerService


class ResponseMatcher:
    """Matches broker responses to deletion requests using various strategies"""

    def __init__(self, db: Session):
        self.db = db
        self.broker_service = BrokerService(db)

    def match_response_to_request(self, response: BrokerResponse) -> tuple[str | None, str | None]:
        """
        Match a broker response to a deletion request

        Args:
            response: BrokerResponse object to match

        Returns:
            Tuple of (deletion_request_id, matched_by_method)
            Returns (None, None) if no match found
        """
        # Strategy 1: Gmail thread_id match (highest confidence)
        if response.gmail_thread_id:
            match = self._match_by_thread_id(response)
            if match:
                return (str(match.id), "thread_id")

        # Strategy 2: Subject line + sender domain match (medium confidence)
        match = self._match_by_subject_and_sender(response)
        if match:
            return (str(match.id), "subject_sender")

        # Strategy 3: Sender domain + time window match (lower confidence)
        match = self._match_by_domain_and_time(response)
        if match:
            return (str(match.id), "domain_time")

        return (None, None)

    def _match_by_thread_id(self, response: BrokerResponse) -> DeletionRequest | None:
        """
        Match response by Gmail thread ID

        This is the most reliable method since Gmail keeps related emails
        in the same thread.
        """
        return (
            self.db.query(DeletionRequest)
            .filter(
                DeletionRequest.user_id == response.user_id,
                DeletionRequest.gmail_thread_id == response.gmail_thread_id,
                DeletionRequest.gmail_thread_id.isnot(None),
            )
            .first()
        )

    def _match_by_subject_and_sender(self, response: BrokerResponse) -> DeletionRequest | None:
        """
        Match response by subject line keywords and sender domain

        Looks for:
        1. Sender domain matches broker domain
        2. Subject contains keywords like "re:", "deletion", "data", etc.
        """
        # Extract sender domain
        sender_domain = self._extract_domain(response.sender_email)
        if not sender_domain:
            return None

        # Find broker by domain
        broker = self.broker_service.get_broker_by_domain(sender_domain)
        if not broker:
            return None

        # Check if subject suggests it's a reply to deletion request
        subject = (response.subject or "").lower()
        reply_keywords = [
            "re:",
            "deletion",
            "data",
            "privacy",
            "opt-out",
            "unsubscribe",
            "gdpr",
            "ccpa",
        ]

        if not any(kw in subject for kw in reply_keywords):
            return None

        # Find sent deletion request for this broker
        # Look for requests sent in the last 90 days
        cutoff_date = datetime.now() - timedelta(days=90)

        return (
            self.db.query(DeletionRequest)
            .filter(
                DeletionRequest.user_id == response.user_id,
                DeletionRequest.broker_id == broker.id,
                DeletionRequest.status == "sent",
                DeletionRequest.sent_at >= cutoff_date,
            )
            .order_by(DeletionRequest.sent_at.desc())
            .first()
        )

    def _match_by_domain_and_time(self, response: BrokerResponse) -> DeletionRequest | None:
        """
        Match response by sender domain and time window

        Less reliable - matches if:
        1. Sender domain matches broker domain
        2. Request was sent within the last 90 days
        3. No other responses already matched to this request
        """
        # Extract sender domain
        sender_domain = self._extract_domain(response.sender_email)
        if not sender_domain:
            return None

        # Find broker by domain
        broker = self.broker_service.get_broker_by_domain(sender_domain)
        if not broker:
            return None

        # Find sent deletion request for this broker without existing responses
        cutoff_date = datetime.now() - timedelta(days=90)

        # Get requests that don't already have responses
        requests_with_responses = (
            self.db.query(BrokerResponse.deletion_request_id)
            .filter(BrokerResponse.deletion_request_id.isnot(None))
            .distinct()
        )

        return (
            self.db.query(DeletionRequest)
            .filter(
                DeletionRequest.user_id == response.user_id,
                DeletionRequest.broker_id == broker.id,
                DeletionRequest.status == "sent",
                DeletionRequest.sent_at >= cutoff_date,
                ~DeletionRequest.id.in_(requests_with_responses),
            )
            .order_by(DeletionRequest.sent_at.desc())
            .first()
        )

    def _extract_domain(self, email: str) -> str | None:
        """Extract domain from email address"""
        if not email or "@" not in email:
            return None

        try:
            # Handle email format: "Name <email@domain.com>" or "email@domain.com"
            if "<" in email and ">" in email:
                email = email.split("<")[1].split(">")[0]

            return email.split("@")[1].lower().strip()
        except (IndexError, AttributeError):
            return None
