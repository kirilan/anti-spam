from celery import current_task
from datetime import datetime, timedelta
from typing import Dict, List
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.models.deletion_request import DeletionRequest, RequestStatus
from app.models.broker_response import BrokerResponse, ResponseType
from app.services.email_scanner import EmailScanner
from app.services.gmail_service import GmailService
from app.services.response_detector import ResponseDetector
from app.services.response_matcher import ResponseMatcher
from app.services.broker_service import BrokerService


def _parse_email_date(date_str: str):
    """Parse email date string to datetime"""
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(date_str) if date_str else None
    except Exception:
        return None


@celery_app.task(bind=True)
def scan_inbox_task(self, user_id: str, days_back: int = 90, max_emails: int = 100):
    """
    Background task to scan user's inbox for data broker emails.

    Updates task state with progress:
    - STARTED: Task began
    - PROGRESS: Includes processed/total counts
    - SUCCESS: Returns scan results
    - FAILURE: Error details
    """
    db = SessionLocal()

    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Update state to show we're starting
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': max_emails,
                'status': 'Starting email scan...'
            }
        )

        # Create scanner and run scan
        scanner = EmailScanner(db)
        scans = scanner.scan_inbox(user, days_back=days_back, max_emails=max_emails)

        # Count results
        broker_count = sum(1 for s in scans if s.is_broker_email)

        return {
            'status': 'completed',
            'total_scanned': len(scans),
            'broker_emails_found': broker_count,
            'user_id': user_id
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise

    finally:
        db.close()


@celery_app.task(bind=True)
def scan_for_responses_task(self, user_id: str, days_back: int = 7):
    """
    Background task to scan for broker responses to deletion requests.

    Args:
        user_id: User ID to scan responses for
        days_back: Number of days to look back for responses (default: 7)

    Returns:
        Dict with scan results including responses found and requests updated
    """
    import logging
    logger = logging.getLogger(__name__)
    db = SessionLocal()

    try:
        logger.info(f"Starting response scan for user {user_id}")
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Update state
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': 0,
                'status': 'Scanning for broker responses...'
            }
        )

        # Initialize services
        gmail_service = GmailService()
        response_detector = ResponseDetector()
        response_matcher = ResponseMatcher(db)
        broker_service = BrokerService(db)

        # Get user's sent deletion requests
        sent_requests = (
            db.query(DeletionRequest)
            .filter(
                DeletionRequest.user_id == user_id,
                DeletionRequest.status == RequestStatus.SENT
            )
            .all()
        )

        if not sent_requests:
            return {
                'status': 'completed',
                'responses_found': 0,
                'requests_updated': 0,
                'message': 'No sent deletion requests to scan for'
            }

        # Build list of broker domains to search
        broker_ids = {req.broker_id for req in sent_requests}
        broker_domains = set()

        for broker_id in broker_ids:
            broker = broker_service.get_broker_by_id(str(broker_id))
            if broker and broker.domains:
                broker_domains.update(broker.domains)

        if not broker_domains:
            return {
                'status': 'completed',
                'responses_found': 0,
                'requests_updated': 0,
                'message': 'No broker domains to scan'
            }

        # Build Gmail query for emails from broker domains
        # Search for emails received after the oldest sent request
        logger.info(f"Building search query for {len(broker_domains)} broker domains")
        oldest_sent = min(req.sent_at for req in sent_requests if req.sent_at)
        after_date = oldest_sent.strftime('%Y/%m/%d') if oldest_sent else (
            (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        )

        # Query: from any broker domain, after the sent date, in inbox
        domain_queries = ' OR '.join(f'from:@{domain}' for domain in broker_domains)
        query = f'({domain_queries}) after:{after_date} in:inbox'
        logger.info(f"Gmail query: {query}")

        # Fetch messages
        logger.info("Fetching messages from Gmail API")
        messages = gmail_service.search_messages(user, query, max_results=50)
        logger.info(f"Found {len(messages)} messages to process")

        responses_created = 0
        requests_updated = 0

        # Process each message
        for idx, msg_data in enumerate(messages):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': idx + 1,
                    'total': len(messages),
                    'status': f'Processing response {idx + 1} of {len(messages)}'
                }
            )

            gmail_message_id = msg_data.get('id')

            # Skip if already processed
            existing = (
                db.query(BrokerResponse)
                .filter(BrokerResponse.gmail_message_id == gmail_message_id)
                .first()
            )
            if existing:
                continue

            # Extract email details using proper header parsing
            headers = gmail_service.get_message_headers(msg_data)
            sender = headers.get('from', '')
            subject = headers.get('subject', '')
            date_str = headers.get('date', '')
            thread_id = msg_data.get('threadId')

            # Get email body
            body = gmail_service._extract_body(msg_data.get('payload', {}))

            # Detect response type
            response_type, confidence = response_detector.detect_response_type(subject, body)

            # Create BrokerResponse record
            broker_response = BrokerResponse(
                user_id=user_id,
                gmail_message_id=gmail_message_id,
                gmail_thread_id=thread_id,
                sender_email=sender,
                subject=subject,
                body_text=body[:5000] if body else None,  # Limit body length
                received_date=_parse_email_date(date_str),
                response_type=response_type,
                confidence_score=confidence
            )

            # Match to deletion request
            request_id, matched_by = response_matcher.match_response_to_request(broker_response)

            if request_id:
                broker_response.deletion_request_id = request_id
                broker_response.matched_by = matched_by

                # Auto-update request status if confidence is high enough
                if confidence >= 0.6:
                    request = db.query(DeletionRequest).filter(
                        DeletionRequest.id == request_id
                    ).first()

                    if request and request.status == RequestStatus.SENT:
                        if response_type == ResponseType.CONFIRMATION:
                            request.status = RequestStatus.CONFIRMED
                            request.confirmed_at = datetime.now()
                            requests_updated += 1
                        elif response_type == ResponseType.REJECTION:
                            request.status = RequestStatus.REJECTED
                            request.rejected_at = datetime.now()
                            requests_updated += 1

            # Mark as processed
            broker_response.is_processed = True
            broker_response.processed_at = datetime.now()

            # Save to database
            db.add(broker_response)
            responses_created += 1

        # Commit all changes
        db.commit()

        logger.info(f"Response scan completed: {responses_created} responses, {requests_updated} requests updated")
        return {
            'status': 'completed',
            'responses_found': responses_created,
            'requests_updated': requests_updated,
            'sent_requests_scanned': len(sent_requests),
            'user_id': user_id
        }

    except Exception as e:
        logger.error(f"Response scan failed for user {user_id}: {type(e).__name__}: {str(e)}", exc_info=True)
        error_msg = f"{type(e).__name__}: {str(e)}"
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg}
        )
        # Return error dict instead of raising to avoid Celery serialization issues
        return {
            'status': 'failed',
            'error': error_msg,
            'user_id': user_id
        }

    finally:
        db.close()


@celery_app.task(bind=True)
def scan_all_users_for_responses(self):
    """
    Background task to scan all users with sent deletion requests for new broker responses.
    This task is scheduled to run daily via Celery Beat.

    Returns:
        Dict with summary of users scanned and tasks triggered
    """
    db = SessionLocal()

    try:
        # Get all users with sent deletion requests
        users_with_sent = (
            db.query(User.id)
            .join(DeletionRequest, DeletionRequest.user_id == User.id)
            .filter(DeletionRequest.status == RequestStatus.SENT)
            .distinct()
            .all()
        )

        total_scanned = 0
        tasks_triggered = []

        for (user_id,) in users_with_sent:
            # Trigger scan for each user asynchronously
            result = scan_for_responses_task.delay(str(user_id), days_back=7)
            tasks_triggered.append({
                'user_id': str(user_id),
                'task_id': result.id
            })
            total_scanned += 1

        return {
            'status': 'completed',
            'users_scanned': total_scanned,
            'tasks_triggered': len(tasks_triggered),
            'task_details': tasks_triggered
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise

    finally:
        db.close()
