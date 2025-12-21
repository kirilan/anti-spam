from datetime import datetime, timedelta

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.activity_log import ActivityType
from app.models.broker_response import BrokerResponse, ResponseType
from app.models.deletion_request import DeletionRequest, RequestStatus
from app.models.user import User
from app.services.activity_log_service import ActivityLogService
from app.services.broker_service import BrokerService
from app.services.email_scanner import EmailScanner
from app.services.gmail_service import GmailService
from app.services.response_detector import ResponseDetector
from app.services.response_matcher import ResponseMatcher


def _parse_email_date(date_str: str):
    """Parse email date string to datetime"""
    from email.utils import parsedate_to_datetime

    try:
        return parsedate_to_datetime(date_str) if date_str else None
    except Exception:
        return None


@celery_app.task(bind=True, max_retries=2)
def scan_inbox_task(self, user_id: str, days_back: int = 90, max_emails: int = 100):
    """
    Background task to scan user's inbox for data broker emails.

    Updates task state with progress:
    - STARTED: Task began
    - PROGRESS: Includes processed/total counts
    - SUCCESS: Returns scan results
    - FAILURE: Error details

    Retry schedule on failure:
    - 1st retry: 2 minutes
    - 2nd retry: 10 minutes
    """
    db = SessionLocal()

    # Custom retry intervals (in seconds)
    retry_intervals = [
        2 * 60,  # 2 minutes
        10 * 60,  # 10 minutes
    ]

    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Log task start
        activity_service = ActivityLogService(db)
        activity_service.log_activity(
            user_id=user_id,
            activity_type=ActivityType.INFO,
            message=f"Started email scan (last {days_back} days, max {max_emails} emails)",
        )

        # Update state to show we're starting
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": max_emails, "status": "Starting email scan..."},
        )

        # Create scanner and run scan
        scanner = EmailScanner(db)
        scans = scanner.scan_inbox(user, days_back=days_back, max_emails=max_emails)

        # Count results
        broker_count = sum(1 for s in scans if s.is_broker_email)

        # Log task completion
        activity_service.log_activity(
            user_id=user_id,
            activity_type=ActivityType.EMAIL_SCANNED,
            message=f"Email scan completed: {len(scans)} emails scanned, {broker_count} broker emails found",
            details=f"Days back: {days_back}, Max emails: {max_emails}",
        )

        return {
            "status": "completed",
            "total_scanned": len(scans),
            "broker_emails_found": broker_count,
            "user_id": user_id,
        }

    except Exception as exc:
        # Log failure and retry attempts
        retry_count = self.request.retries

        try:
            activity_service = ActivityLogService(db)

            if retry_count < len(retry_intervals):
                countdown = retry_intervals[retry_count]
                # Log retry attempt
                activity_service.log_activity(
                    user_id=user_id,
                    activity_type=ActivityType.WARNING,
                    message=f"Email scan failed, retrying in {countdown // 60} minutes (attempt {retry_count + 1}/{len(retry_intervals)})",
                    details=f"Error: {str(exc)}",
                )
                import logging

                logging.info(
                    f"Inbox scan failed, retrying in {countdown}s (attempt {retry_count + 1}/{len(retry_intervals)})"
                )
            else:
                # Log final failure
                activity_service.log_activity(
                    user_id=user_id,
                    activity_type=ActivityType.ERROR,
                    message=f"Email scan failed after {retry_count} retry attempts",
                    details=f"Error: {str(exc)}",
                )
        except Exception:
            pass  # Don't fail on logging errors

        db.close()

        # Determine retry countdown based on current retry attempt
        if retry_count < len(retry_intervals):
            countdown = retry_intervals[retry_count]
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # Max retries exceeded
            self.update_state(state="FAILURE", meta={"error": str(exc)})
            raise

    finally:
        if db:
            db.close()


@celery_app.task(bind=True, max_retries=2)
def scan_for_responses_task(self, user_id: str, days_back: int = 7):
    """
    Background task to scan for broker responses to deletion requests.

    Args:
        user_id: User ID to scan responses for
        days_back: Number of days to look back for responses (default: 7)

    Returns:
        Dict with scan results including responses found and requests updated

    Retry schedule on failure:
    - 1st retry: 2 minutes
    - 2nd retry: 10 minutes
    """
    import logging

    logger = logging.getLogger(__name__)
    db = SessionLocal()

    # Custom retry intervals (in seconds)
    retry_intervals = [
        2 * 60,  # 2 minutes
        10 * 60,  # 10 minutes
    ]

    try:
        logger.info(f"Starting response scan for user {user_id}")
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Log task start
        activity_service = ActivityLogService(db)
        activity_service.log_activity(
            user_id=user_id,
            activity_type=ActivityType.INFO,
            message=f"Started scanning for broker responses (last {days_back} days)",
        )

        # Update state
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 0, "status": "Scanning for broker responses..."},
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
                DeletionRequest.user_id == user_id, DeletionRequest.status == RequestStatus.SENT
            )
            .all()
        )

        if not sent_requests:
            return {
                "status": "completed",
                "responses_found": 0,
                "requests_updated": 0,
                "message": "No sent deletion requests to scan for",
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
                "status": "completed",
                "responses_found": 0,
                "requests_updated": 0,
                "message": "No broker domains to scan",
            }

        # Build Gmail query for emails from broker domains
        # Search for emails received after the oldest sent request
        logger.info(f"Building search query for {len(broker_domains)} broker domains")
        oldest_sent = min(req.sent_at for req in sent_requests if req.sent_at)
        after_date = (
            oldest_sent.strftime("%Y/%m/%d")
            if oldest_sent
            else ((datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d"))
        )

        # Query: from any broker domain, after the sent date, in inbox
        domain_queries = " OR ".join(f"from:@{domain}" for domain in broker_domains)
        query = f"({domain_queries}) after:{after_date} in:inbox"
        logger.info(f"Gmail query: {query}")

        # Fetch messages
        logger.info("Fetching messages from Gmail API")
        messages = gmail_service.search_messages(user, query, max_results=50)
        logger.info(f"Found {len(messages)} messages to process")

        responses_created = 0
        responses_updated = 0
        requests_updated = 0

        # Process each message
        for idx, msg_data in enumerate(messages):
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": idx + 1,
                    "total": len(messages),
                    "status": f"Processing response {idx + 1} of {len(messages)}",
                },
            )

            gmail_message_id = msg_data.get("id")

            # Check if already processed
            existing = (
                db.query(BrokerResponse)
                .filter(BrokerResponse.gmail_message_id == gmail_message_id)
                .first()
            )

            # Extract email details using proper header parsing
            headers = gmail_service.get_message_headers(msg_data)
            sender = headers.get("from", "")
            subject = headers.get("subject", "")
            date_str = headers.get("date", "")
            thread_id = msg_data.get("threadId")

            # Get email body
            body = gmail_service._extract_body(msg_data.get("payload", {}))

            # Detect response type
            response_type, confidence = response_detector.detect_response_type(subject, body)

            # Update existing response or create new one
            if existing:
                # Re-classify existing response with updated keywords
                broker_response = existing
                broker_response.response_type = response_type
                broker_response.confidence_score = confidence
                responses_updated += 1
                logger.info(
                    f"Re-classified existing response {existing.id}: {response_type.value} ({confidence})"
                )
            else:
                # Create new BrokerResponse record
                broker_response = BrokerResponse(
                    user_id=user_id,
                    gmail_message_id=gmail_message_id,
                    gmail_thread_id=thread_id,
                    sender_email=sender,
                    subject=subject,
                    body_text=body[:5000] if body else None,  # Limit body length
                    received_date=_parse_email_date(date_str),
                    response_type=response_type,
                    confidence_score=confidence,
                )
                db.add(broker_response)
                responses_created += 1

            # Match to deletion request (for both new and updated responses)
            request_id, matched_by = response_matcher.match_response_to_request(broker_response)

            if request_id:
                broker_response.deletion_request_id = request_id
                broker_response.matched_by = matched_by

                # Auto-update request status if confidence is high enough
                if confidence >= 0.6:
                    request = (
                        db.query(DeletionRequest).filter(DeletionRequest.id == request_id).first()
                    )

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

        # Commit all changes
        db.commit()

        logger.info(
            f"Response scan completed: {responses_created} new, {responses_updated} re-classified, {requests_updated} requests updated"
        )

        # Log task completion
        activity_service.log_activity(
            user_id=user_id,
            activity_type=ActivityType.RESPONSE_SCANNED,
            message=f"Response scan completed: {responses_created} new responses, {responses_updated} re-classified, {requests_updated} requests updated",
            details=f"Sent requests scanned: {len(sent_requests)}, Days back: {days_back}",
        )

        return {
            "status": "completed",
            "responses_found": responses_created,
            "responses_updated": responses_updated,
            "requests_updated": requests_updated,
            "sent_requests_scanned": len(sent_requests),
            "user_id": user_id,
        }

    except Exception as exc:
        logger.error(
            f"Response scan failed for user {user_id}: {type(exc).__name__}: {str(exc)}",
            exc_info=True,
        )
        error_msg = f"{type(exc).__name__}: {str(exc)}"

        # Log failure and retry attempts
        retry_count = self.request.retries

        try:
            activity_service = ActivityLogService(db)

            if retry_count < len(retry_intervals):
                countdown = retry_intervals[retry_count]
                # Log retry attempt
                activity_service.log_activity(
                    user_id=user_id,
                    activity_type=ActivityType.WARNING,
                    message=f"Response scan failed, retrying in {countdown // 60} minutes (attempt {retry_count + 1}/{len(retry_intervals)})",
                    details=error_msg,
                )
                logger.info(
                    f"Retrying in {countdown}s (attempt {retry_count + 1}/{len(retry_intervals)})"
                )
            else:
                # Log final failure
                activity_service.log_activity(
                    user_id=user_id,
                    activity_type=ActivityType.ERROR,
                    message=f"Response scan failed after {retry_count} retry attempts",
                    details=error_msg,
                )
        except Exception:
            pass  # Don't fail on logging errors

        db.close()

        # Determine retry countdown based on current retry attempt
        if retry_count < len(retry_intervals):
            countdown = retry_intervals[retry_count]
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # Max retries exceeded
            self.update_state(state="FAILURE", meta={"error": error_msg})
            # Return error dict instead of raising to avoid Celery serialization issues
            return {"status": "failed", "error": error_msg, "user_id": user_id}

    finally:
        if db:
            db.close()


@celery_app.task(bind=True, max_retries=3)
def scan_all_users_for_responses(self):
    """
    Background task to scan all users with sent deletion requests for new broker responses.
    This task is scheduled to run daily via Celery Beat.

    Retry schedule on failure:
    - 1st retry: 15 minutes
    - 2nd retry: 1 hour
    - 3rd retry: 4 hours

    Returns:
        Dict with summary of users scanned and tasks triggered
    """
    db = SessionLocal()

    # Custom retry intervals (in seconds)
    retry_intervals = [
        15 * 60,  # 15 minutes
        60 * 60,  # 1 hour
        4 * 60 * 60,  # 4 hours
    ]

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
            user_id_str = str(user_id)

            # Log that we're triggering scan for this user
            try:
                activity_service = ActivityLogService(db)
                activity_service.log_activity(
                    user_id=user_id_str,
                    activity_type=ActivityType.INFO,
                    message="Daily automated response scan started",
                )
            except Exception:
                pass  # Don't fail on logging errors

            # Trigger scan for each user asynchronously
            result = scan_for_responses_task.delay(user_id_str, days_back=7)
            tasks_triggered.append({"user_id": user_id_str, "task_id": result.id})
            total_scanned += 1

        return {
            "status": "completed",
            "users_scanned": total_scanned,
            "tasks_triggered": len(tasks_triggered),
            "task_details": tasks_triggered,
        }

    except Exception as exc:
        db.close()

        # Determine retry countdown based on current retry attempt
        retry_count = self.request.retries
        if retry_count < len(retry_intervals):
            countdown = retry_intervals[retry_count]
            import logging

            logging.info(
                f"Daily scan failed, retrying in {countdown}s ({countdown / 60} min) - attempt {retry_count + 1}/{len(retry_intervals)}"
            )

            # Retry with custom countdown
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # Max retries exceeded
            import logging

            logging.error(f"Daily scan failed after {retry_count} retries: {str(exc)}")
            self.update_state(state="FAILURE", meta={"error": str(exc)})
            raise

    finally:
        if db:
            db.close()
