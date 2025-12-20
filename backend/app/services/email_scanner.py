from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
import base64

from app.models.user import User
from app.models.email_scan import EmailScan
from app.services.gmail_service import GmailService
from app.services.broker_service import BrokerService
from app.services.broker_detector import BrokerDetector


class EmailScanner:
    def __init__(self, db: Session):
        self.db = db
        self.gmail_service = GmailService()
        self.broker_service = BrokerService(db)
        self.detector = BrokerDetector()

    def scan_inbox(
        self,
        user: User,
        days_back: int = 1,
        max_emails: int = 100
    ) -> List[EmailScan]:
        """Scan user's Gmail inbox for data broker emails"""

        # Get all known brokers
        all_brokers = self.broker_service.get_all_brokers()

        # Calculate date range
        after_date = datetime.now() - timedelta(days=days_back)
        after_str = after_date.strftime('%Y/%m/%d')

        # Query Gmail for recent emails
        query = f'after:{after_str}'

        try:
            messages = self.gmail_service.list_messages(user, query, max_emails)
        except Exception as e:
            raise Exception(f"Failed to fetch emails: {str(e)}")

        scans = []

        for message_ref in messages:
            message_id = message_ref['id']

            # Check if we've already scanned this email
            existing = self.db.query(EmailScan).filter(
                EmailScan.gmail_message_id == message_id
            ).first()

            if existing:
                scans.append(existing)
                continue

            # Fetch full message
            try:
                message = self.gmail_service.get_message(user, message_id)
                headers = self.gmail_service.get_message_headers(message)

                # Extract email details
                sender = headers.get('from', '')
                recipient = headers.get('to', '')
                subject = headers.get('subject', '')
                date_str = headers.get('date', '')

                # Parse sender email
                sender_email = self._extract_email(sender)
                sender_domain = self.detector.extract_domain_from_email(sender_email)

                # Parse recipient email
                recipient_email = self._extract_email(recipient) if recipient else None

                # Extract body
                body_html, body_text = self._extract_body(message)

                # Detect if broker email
                broker, confidence, notes = self.detector.detect_broker(
                    sender_email,
                    sender_domain,
                    subject,
                    body_html,
                    body_text,
                    all_brokers
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
                    sender_email=sender_email,
                    sender_domain=sender_domain,
                    recipient_email=recipient_email,
                    subject=subject,
                    received_date=received_date,
                    is_broker_email=broker is not None or confidence > 0.5,
                    confidence_score=confidence,
                    classification_notes=notes,
                    body_preview=body_preview
                )

                self.db.add(scan)
                scans.append(scan)

            except Exception as e:
                print(f"Error processing message {message_id}: {str(e)}")
                continue

        # Update user's last scan timestamp
        user.last_scan_at = datetime.now()

        self.db.commit()
        return scans

    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header"""
        import re
        match = re.search(r'[\w\.-]+@[\w\.-]+', from_header)
        if match:
            return match.group(0)
        return from_header

    def _extract_body(self, message: Dict) -> tuple[str, str]:
        """Extract HTML and text body from Gmail message"""
        body_html = ""
        body_text = ""

        def parse_parts(parts):
            nonlocal body_html, body_text
            for part in parts:
                mime_type = part.get('mimeType', '')

                if mime_type == 'text/plain' and 'data' in part.get('body', {}):
                    body_text = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8', errors='ignore')

                elif mime_type == 'text/html' and 'data' in part.get('body', {}):
                    body_html = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8', errors='ignore')

                if 'parts' in part:
                    parse_parts(part['parts'])

        if 'payload' in message:
            payload = message['payload']

            # Single part message
            if 'body' in payload and 'data' in payload['body']:
                mime_type = payload.get('mimeType', '')
                if mime_type == 'text/plain':
                    body_text = base64.urlsafe_b64decode(
                        payload['body']['data']
                    ).decode('utf-8', errors='ignore')
                elif mime_type == 'text/html':
                    body_html = base64.urlsafe_b64decode(
                        payload['body']['data']
                    ).decode('utf-8', errors='ignore')

            # Multi-part message
            if 'parts' in payload:
                parse_parts(payload['parts'])

        return body_html, body_text

    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date string"""
        from email.utils import parsedate_to_datetime
        try:
            return parsedate_to_datetime(date_str)
        except:
            return datetime.now()
