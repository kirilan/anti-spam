import base64
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.deletion_request import DeletionRequest, RequestStatus
from app.models.email_scan import EmailScan
from app.models.user import User
from app.services.broker_detector import BrokerDetector
from app.services.broker_service import BrokerService
from app.services.gmail_service import GmailService
from app.services.response_detector import ResponseDetector


class EmailScanner:
    def __init__(self, db: Session):
        self.db = db
        self.gmail_service = GmailService()
        self.broker_service = BrokerService(db)
        self.detector = BrokerDetector()
        self.response_detector = ResponseDetector()

    def scan_inbox(self, user: User, days_back: int = 90, max_emails: int = 100) -> list[EmailScan]:
        """
        Scan user's Gmail for data broker emails (both received and sent)

        This method scans:
        1. Received emails from all domains (existing functionality)
        2. Sent emails to known broker domains/privacy emails (new)
        3. Auto-creates deletion requests from ALL discovered broker emails (both sent and received)
        """

        # Get all known brokers
        all_brokers = self.broker_service.get_all_brokers()

        # Scan received emails (existing logic)
        received_scans = self._scan_received_emails(user, days_back, max_emails, all_brokers)

        # Flush to database so sent email scan can see these scans
        self.db.flush()

        # Scan sent emails to broker domains (new)
        sent_scans = self._scan_sent_broker_emails(user, days_back, max_emails, all_brokers)

        # Flush again before auto-creation
        self.db.flush()

        # Auto-create deletion requests from ALL discovered broker emails (sent + received)
        all_broker_scans = [s for s in received_scans + sent_scans if s.broker_id]
        self._auto_create_deletion_requests(user, all_broker_scans)

        # Update user's last scan timestamp
        user.last_scan_at = datetime.now()

        self.db.commit()
        return received_scans + sent_scans

    def _scan_received_emails(
        self, user: User, days_back: int, max_emails: int, all_brokers: list
    ) -> list[EmailScan]:
        """Scan received emails from Gmail inbox"""

        # Calculate date range
        after_date = datetime.now() - timedelta(days=days_back)
        after_str = after_date.strftime("%Y/%m/%d")

        # Query Gmail for recent emails
        query = f"after:{after_str}"

        try:
            messages = self.gmail_service.list_messages(user, query, max_emails)
        except Exception as e:
            raise Exception(f"Failed to fetch received emails: {str(e)}")

        scans = []

        for message_ref in messages:
            message_id = message_ref["id"]

            # Check if we've already scanned this email
            existing = (
                self.db.query(EmailScan).filter(EmailScan.gmail_message_id == message_id).first()
            )

            if existing:
                # If existing scan doesn't have a broker, try to re-match against current broker list
                # This handles the case where emails were scanned before brokers were added
                if not existing.broker_id and all_brokers:
                    broker, confidence, notes = self.detector.detect_broker(
                        existing.sender_email,
                        existing.sender_domain,
                        existing.subject or "",
                        "",  # We don't have body_html stored
                        existing.body_preview or "",
                        all_brokers,
                    )

                    if broker:
                        # Update the existing scan with broker match
                        existing.broker_id = broker.id
                        existing.is_broker_email = True
                        existing.confidence_score = confidence
                        existing.classification_notes = notes
                        print(
                            f"Re-matched email '{existing.subject[:50]}...' to broker '{broker.name}'"
                        )

                scans.append(existing)
                continue

            # Fetch full message
            try:
                message = self.gmail_service.get_message(user, message_id)
                headers = self.gmail_service.get_message_headers(message)

                # Extract email details
                sender = headers.get("from", "")
                recipient = headers.get("to", "")
                subject = headers.get("subject", "")
                date_str = headers.get("date", "")

                # Extract thread ID
                gmail_thread_id = message.get("threadId")

                # Parse sender email
                sender_email = self._extract_email(sender)
                sender_domain = self.detector.extract_domain_from_email(sender_email)

                # Parse recipient email
                recipient_email = self._extract_email(recipient) if recipient else None

                # Extract body
                body_html, body_text = self._extract_body(message)

                # Detect if broker email
                broker, confidence, notes = self.detector.detect_broker(
                    sender_email, sender_domain, subject, body_html, body_text, all_brokers
                )

                # Get body preview
                body_preview = self.detector.get_body_preview(body_html, body_text)

                # Parse date
                received_date = self._parse_date(date_str)

                # Create scan record
                scan = EmailScan(
                    user_id=user.id,
                    broker_id=broker.id if broker else None,
                    gmail_message_id=message_id,
                    gmail_thread_id=gmail_thread_id,
                    email_direction="received",
                    sender_email=sender_email,
                    sender_domain=sender_domain,
                    recipient_email=recipient_email,
                    subject=subject,
                    received_date=received_date,
                    is_broker_email=broker is not None or confidence > 0.5,
                    confidence_score=confidence,
                    classification_notes=notes,
                    body_preview=body_preview,
                )

                self.db.add(scan)
                scans.append(scan)

            except Exception as e:
                print(f"Error processing received message {message_id}: {str(e)}")
                continue

        return scans

    def _scan_sent_broker_emails(
        self, user: User, days_back: int, max_emails: int, all_brokers: list
    ) -> list[EmailScan]:
        """
        Scan sent emails to known broker domains/privacy emails

        This identifies deletion requests that were sent outside the system
        or before the system was set up.
        """

        # Calculate date range
        after_date = datetime.now() - timedelta(days=days_back)
        after_str = after_date.strftime("%Y/%m/%d")

        # Build target list (broker domains + privacy emails)
        targets = set()
        for broker in all_brokers:
            # Add all broker domains
            if broker.domains:
                for domain in broker.domains:
                    targets.add(f"@{domain}")
            # Add privacy email if specified
            if broker.privacy_email:
                targets.add(broker.privacy_email)

        if not targets:
            return []  # No brokers configured yet

        # Build Gmail query for sent emails to broker targets
        # Query: in:sent (to:@domain1.com OR to:@domain2.com OR to:privacy@...) after:date
        target_queries = " OR ".join(f"to:{t}" for t in targets)
        query = f"({target_queries}) after:{after_str}"

        try:
            messages = self.gmail_service.list_sent_messages(user, query, max_emails)
        except Exception as e:
            raise Exception(f"Failed to fetch sent emails: {str(e)}")

        scans = []

        for message_ref in messages:
            message_id = message_ref["id"]

            # Check if we've already scanned this email
            existing = (
                self.db.query(EmailScan).filter(EmailScan.gmail_message_id == message_id).first()
            )

            if existing:
                # If existing scan doesn't have a broker, try to re-match against current broker list
                # This handles the case where emails were scanned before brokers were added
                if not existing.broker_id and all_brokers:
                    broker, confidence, notes = self.detector.detect_broker(
                        existing.sender_email,
                        existing.sender_domain,
                        existing.subject or "",
                        "",  # We don't have body_html stored
                        existing.body_preview or "",
                        all_brokers,
                    )

                    if broker:
                        # Update the existing scan with broker match
                        existing.broker_id = broker.id
                        existing.is_broker_email = True
                        existing.confidence_score = confidence
                        existing.classification_notes = notes
                        print(
                            f"Re-matched email '{existing.subject[:50]}...' to broker '{broker.name}'"
                        )

                scans.append(existing)
                continue

            # Fetch full message
            try:
                message = self.gmail_service.get_message(user, message_id)
                headers = self.gmail_service.get_message_headers(message)

                # Extract email details
                sender = headers.get("from", "")
                recipient = headers.get("to", "")
                subject = headers.get("subject", "")
                date_str = headers.get("date", "")

                # Extract thread ID
                gmail_thread_id = message.get("threadId")

                # Parse sender email (should be user's email)
                sender_email = self._extract_email(sender)
                sender_domain = self.detector.extract_domain_from_email(sender_email)

                # Parse recipient email (broker contact)
                recipient_email = self._extract_email(recipient) if recipient else None
                recipient_domain = (
                    self.detector.extract_domain_from_email(recipient_email)
                    if recipient_email
                    else None
                )

                # Extract body
                body_html, body_text = self._extract_body(message)

                # Detect broker from recipient domain/email
                broker = None
                for b in all_brokers:
                    # Match by privacy email
                    if b.privacy_email and recipient_email == b.privacy_email:
                        broker = b
                        break
                    # Match by domain
                    if recipient_domain and b.domains and recipient_domain in b.domains:
                        broker = b
                        break

                # Get body preview
                body_preview = self.detector.get_body_preview(body_html, body_text)

                # Parse date
                received_date = self._parse_date(date_str)

                # Create scan record
                scan = EmailScan(
                    user_id=user.id,
                    broker_id=broker.id if broker else None,
                    gmail_message_id=message_id,
                    gmail_thread_id=gmail_thread_id,
                    email_direction="sent",
                    sender_email=sender_email,
                    sender_domain=sender_domain,
                    recipient_email=recipient_email,
                    subject=subject,
                    received_date=received_date,
                    is_broker_email=broker is not None,
                    confidence_score=1.0 if broker else 0.5,
                    classification_notes="Sent to broker domain/privacy email",
                    body_preview=body_preview,
                )

                self.db.add(scan)
                scans.append(scan)

            except Exception as e:
                print(f"Error processing sent message {message_id}: {str(e)}")
                continue

        return scans

    def _auto_create_deletion_requests(self, user: User, broker_scans: list[EmailScan]) -> None:
        """
        Auto-create deletion requests from discovered broker emails (sent or received)

        For each broker email:
        1. Check if deletion request already exists (including manually deleted ones)
        2. Skip if manually deleted (user explicitly removed it)
        3. Analyze email thread for responses
        4. Determine status based on email direction and response classification
        5. Create DeletionRequest with source='auto_discovered'
        """

        for scan in broker_scans:
            # Skip if not linked to a broker
            if not scan.broker_id:
                continue

            # Check for existing deletion request (including soft-deleted)
            existing_request = (
                self.db.query(DeletionRequest)
                .filter(
                    DeletionRequest.user_id == user.id,
                    DeletionRequest.broker_id == scan.broker_id,
                )
                .first()
            )

            if existing_request:
                # If manually deleted, respect user's decision and don't auto-recreate
                if existing_request.deleted_at is not None:
                    continue

                # Update thread_id if not already set
                if not existing_request.gmail_thread_id and scan.gmail_thread_id:
                    existing_request.gmail_thread_id = scan.gmail_thread_id
                continue

            # Determine status based on email direction
            if scan.email_direction == "sent":
                # For sent emails, analyze thread for responses
                status = self._analyze_thread_status(user, scan.gmail_thread_id, scan.received_date)
                sent_at = scan.received_date
                gmail_sent_message_id = scan.gmail_message_id
            else:
                # For received emails, analyze if this is a response to a deletion request
                # If it looks like a response, set status accordingly
                # Otherwise, mark as pending (no email sent yet by us)
                status = self._analyze_received_email_status(scan)
                sent_at = None
                gmail_sent_message_id = None

            # Create auto-discovered deletion request
            request = DeletionRequest(
                user_id=user.id,
                broker_id=scan.broker_id,
                status=status,
                source="auto_discovered",
                gmail_sent_message_id=gmail_sent_message_id,
                gmail_thread_id=scan.gmail_thread_id,
                sent_at=sent_at,
                generated_email_subject=scan.subject,
                generated_email_body=scan.body_preview,
            )

            self.db.add(request)
            self.db.flush()  # Flush to get the request ID

            # If this was a received email that looks like a response, create BrokerResponse
            if scan.email_direction == "received" and status != RequestStatus.PENDING:
                self._create_broker_response_from_scan(request, scan)

    def _create_broker_response_from_scan(self, request: DeletionRequest, scan: EmailScan) -> None:
        """
        Create a BrokerResponse record from an EmailScan

        This links the detected email to the deletion request so it appears in the thread.
        """
        from app.models.broker_response import BrokerResponse

        # Classify the response
        response_type, confidence = self.response_detector.detect_response_type(
            scan.subject or "", scan.body_preview or ""
        )

        # Create the broker response record
        response = BrokerResponse(
            user_id=request.user_id,
            deletion_request_id=request.id,
            gmail_message_id=scan.gmail_message_id,
            gmail_thread_id=scan.gmail_thread_id,
            sender_email=scan.sender_email,
            subject=scan.subject,
            body_text=scan.body_preview,
            received_date=scan.received_date,
            response_type=response_type,
            confidence_score=confidence,
            matched_by="auto_discovered",
            is_processed=True,
        )

        self.db.add(response)

    def _analyze_received_email_status(self, scan: EmailScan) -> RequestStatus:
        """
        Analyze a received broker email to determine if it's a response to a deletion request

        Uses ResponseDetector to classify the email. If it looks like a response to
        a deletion request (confirmation, rejection, etc.), returns appropriate status.
        Otherwise returns PENDING (indicating we haven't sent a request yet).
        """
        from app.models.broker_response import ResponseType

        # Analyze the email content using ResponseDetector
        response_type, confidence = self.response_detector.detect_response_type(
            scan.subject or "", scan.body_preview or ""
        )

        # If high confidence that this is a response to a deletion request
        if confidence >= 0.6:
            if response_type == ResponseType.CONFIRMATION:
                return RequestStatus.CONFIRMED
            elif response_type == ResponseType.REJECTION:
                return RequestStatus.REJECTED
            # For acknowledgment, info_request, or unknown - treat as sent
            # (implies a deletion request was sent outside the system)
            else:
                return RequestStatus.SENT

        # Low confidence or doesn't look like a response - mark as pending
        # (probably just a marketing email or notification)
        return RequestStatus.PENDING

    def _analyze_thread_status(
        self, user: User, thread_id: str | None, sent_date: datetime | None
    ) -> RequestStatus:
        """
        Analyze email thread to determine deletion request status

        Looks at received responses in the thread and classifies them:
        - CONFIRMATION response → status = CONFIRMED
        - REJECTION response → status = REJECTED
        - ACKNOWLEDGMENT/REQUEST_INFO/UNKNOWN/No responses → status = SENT
        """
        from app.models.broker_response import ResponseType

        # If no thread ID, mark as sent
        if not thread_id:
            return RequestStatus.SENT

        # Get all messages in thread
        try:
            thread_messages = self.gmail_service.get_thread_messages(user, thread_id)
        except Exception as e:
            print(f"Error fetching thread {thread_id}: {str(e)}")
            return RequestStatus.SENT

        if not thread_messages:
            return RequestStatus.SENT

        # Find received emails in thread (responses from broker)
        received_responses = []
        for message in thread_messages:
            headers = self.gmail_service.get_message_headers(message)
            sender = headers.get("from", "")
            sender_email = self._extract_email(sender)

            # Skip if this is from the user (sent email)
            if sender_email.lower() == user.email.lower():
                continue

            # This is a response from broker
            subject = headers.get("subject", "")
            body_html, body_text = self._extract_body(message)
            body_preview = self.detector.get_body_preview(body_html, body_text)

            received_responses.append({"subject": subject, "body": body_preview})

        # No responses yet - mark as sent
        if not received_responses:
            return RequestStatus.SENT

        # Analyze each response with ResponseDetector
        for response in received_responses:
            response_type, confidence = self.response_detector.detect_response_type(
                response["subject"], response["body"]
            )

            # High confidence classification
            if confidence >= 0.6:
                if response_type == ResponseType.CONFIRMATION:
                    return RequestStatus.CONFIRMED
                elif response_type == ResponseType.REJECTION:
                    return RequestStatus.REJECTED

        # Default to SENT if no clear confirmation/rejection found
        return RequestStatus.SENT

    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header"""
        import re

        match = re.search(r"[\w\.-]+@[\w\.-]+", from_header)
        if match:
            return match.group(0)
        return from_header

    def _extract_body(self, message: dict) -> tuple[str, str]:
        """Extract HTML and text body from Gmail message"""
        body_html = ""
        body_text = ""

        def parse_parts(parts):
            nonlocal body_html, body_text
            for part in parts:
                mime_type = part.get("mimeType", "")

                if mime_type == "text/plain" and "data" in part.get("body", {}):
                    body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8", errors="ignore"
                    )

                elif mime_type == "text/html" and "data" in part.get("body", {}):
                    body_html = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8", errors="ignore"
                    )

                if "parts" in part:
                    parse_parts(part["parts"])

        if "payload" in message:
            payload = message["payload"]

            # Single part message
            if "body" in payload and "data" in payload["body"]:
                mime_type = payload.get("mimeType", "")
                if mime_type == "text/plain":
                    body_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                        "utf-8", errors="ignore"
                    )
                elif mime_type == "text/html":
                    body_html = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                        "utf-8", errors="ignore"
                    )

            # Multi-part message
            if "parts" in payload:
                parse_parts(payload["parts"])

        return body_html, body_text

    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date string"""
        from email.utils import parsedate_to_datetime

        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.now()
