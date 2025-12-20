import json
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.email_scan import EmailScan as EmailScanModel
from app.models.activity_log import ActivityLog
from app.models.activity_log import ActivityType
from app.schemas.email import (
    ScanRequest,
    ScanResult,
    EmailScan,
    EmailScanPage,
    ScanHistoryEntry,
    ScanHistoryPage,
)
from app.services.email_scanner import EmailScanner
from app.services.activity_log_service import ActivityLogService
from app.dependencies.auth import get_current_user
from app.config import settings
from app.services.rate_limiter import rate_limiter

router = APIRouter()


def _parse_scan_history(activity: ActivityLog) -> ScanHistoryEntry:
    details = activity.details or ""
    source = "manual"
    scan_type = "email"
    days_back = None
    max_emails = None
    total_scanned = None
    broker_emails_found = None
    sent_requests_scanned = None
    responses_found = None
    responses_updated = None
    requests_updated = None

    if activity.activity_type == ActivityType.RESPONSE_SCANNED:
        scan_type = "responses"

    try:
        parsed = json.loads(details) if details else {}
        if isinstance(parsed, dict):
            source = parsed.get("source") or source
            scan_type = parsed.get("scan_type") or scan_type
            days_back = parsed.get("days_back")
            max_emails = parsed.get("max_emails")
            total_scanned = parsed.get("total_scanned")
            broker_emails_found = parsed.get("broker_emails_found")
            sent_requests_scanned = parsed.get("sent_requests_scanned")
            responses_found = parsed.get("responses_found")
            responses_updated = parsed.get("responses_updated")
            requests_updated = parsed.get("requests_updated")
    except json.JSONDecodeError:
        match = re.search(r"Days back:\s*(\d+),\s*Max emails:\s*(\d+)", details)
        if match:
            days_back = int(match.group(1))
            max_emails = int(match.group(2))
        response_match = re.search(r"Sent requests scanned:\s*(\d+),\s*Days back:\s*(\d+)", details)
        if response_match:
            sent_requests_scanned = int(response_match.group(1))
            days_back = days_back or int(response_match.group(2))

    message_match = re.search(r"Email scan completed:\s*(\d+)\s*emails scanned,\s*(\d+)\s*broker", activity.message)
    if message_match:
        total_scanned = total_scanned or int(message_match.group(1))
        broker_emails_found = broker_emails_found or int(message_match.group(2))

    response_message_match = re.search(
        r"Response scan completed:\s*(\d+)\s*new responses,\s*(\d+)\s*re-classified,\s*(\d+)\s*requests updated",
        activity.message,
    )
    if response_message_match:
        responses_found = responses_found or int(response_message_match.group(1))
        responses_updated = responses_updated or int(response_message_match.group(2))
        requests_updated = requests_updated or int(response_message_match.group(3))

    return ScanHistoryEntry(
        id=str(activity.id),
        performed_at=activity.created_at,
        scan_type=scan_type,
        source=source,
        days_back=days_back,
        max_emails=max_emails,
        total_scanned=total_scanned,
        broker_emails_found=broker_emails_found,
        sent_requests_scanned=sent_requests_scanned,
        responses_found=responses_found,
        responses_updated=responses_updated,
        requests_updated=requests_updated,
        message=activity.message,
    )


@router.post("/scan", response_model=ScanResult)
def scan_emails(
    request: ScanRequest = ScanRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scan user's Gmail inbox for data broker emails"""

    # Get user
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is authenticated
    if not user.encrypted_access_token:
        raise HTTPException(status_code=401, detail="User not authenticated with Gmail")

    # Scan inbox
    scanner = EmailScanner(db)
    activity_service = ActivityLogService(db)

    # Enforce per-user scan limits
    limit_result = rate_limiter.check_limit(
        user_id=str(user.id),
        action="email_scan",
        limit=settings.email_scan_rate_limit,
        window_seconds=settings.email_scan_rate_window_seconds,
    )
    if not limit_result.allowed:
        activity_service.log_activity(
            user_id=str(user.id),
            activity_type=ActivityType.WARNING,
            message="Email scan blocked by rate limit",
            details=f"Limit {settings.email_scan_rate_limit} per {settings.email_scan_rate_window_seconds}s",
        )
        raise HTTPException(
            status_code=429,
            detail=f"Email scan limit reached. Try again in {limit_result.retry_after} seconds.",
            headers={"Retry-After": str(limit_result.retry_after)},
        )

    try:
        scans = scanner.scan_inbox(
            user,
            days_back=request.days_back,
            max_emails=request.max_emails
        )

        # Convert to response schema
        scan_responses = [
            EmailScan(
                id=str(scan.id),
                user_id=str(scan.user_id),
                broker_id=str(scan.broker_id) if scan.broker_id else None,
                gmail_message_id=scan.gmail_message_id,
                sender_email=scan.sender_email,
                sender_domain=scan.sender_domain,
                subject=scan.subject,
                received_date=scan.received_date,
                is_broker_email=scan.is_broker_email,
                confidence_score=scan.confidence_score,
                classification_notes=scan.classification_notes,
                body_preview=scan.body_preview,
                created_at=scan.created_at
            )
            for scan in scans
        ]

        # Count broker emails
        broker_emails = sum(1 for scan in scans if scan.is_broker_email)

        # Log activity
        activity_service.log_activity(
            user_id=str(user.id),
            activity_type=ActivityType.EMAIL_SCANNED,
            message=f"Email scan completed: {len(scans)} emails scanned, {broker_emails} broker emails found",
            details=json.dumps(
                {
                    "scan_type": "email",
                    "source": "manual",
                    "days_back": request.days_back,
                    "max_emails": request.max_emails,
                    "total_scanned": len(scans),
                    "broker_emails_found": broker_emails,
                },
                ensure_ascii=True,
            ),
        )

        # Log each detected broker
        for scan in scans:
            if scan.is_broker_email and scan.broker_id:
                activity_service.log_activity(
                    user_id=str(user.id),
                    activity_type=ActivityType.BROKER_DETECTED,
                    message=f"Detected broker email from {scan.sender_email}",
                    details=f"Subject: {scan.subject}, Confidence: {scan.confidence_score}",
                    broker_id=str(scan.broker_id),
                    email_scan_id=str(scan.id)
                )

        return ScanResult(
            message="Inbox scan completed",
            total_scanned=len(scans),
            broker_emails_found=broker_emails,
            scans=scan_responses
        )

    except Exception as e:
        # Log error
        activity_service.log_activity(
            user_id=str(user.id),
            activity_type=ActivityType.ERROR,
            message=f"Email scan failed",
            details=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/scans", response_model=List[EmailScan])
def get_scans(
    broker_only: bool = False,
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get email scan results for a user"""

    query = db.query(EmailScanModel).filter(EmailScanModel.user_id == current_user.id)

    if broker_only:
        query = query.filter(EmailScanModel.is_broker_email == True)

    # Cap limit at 2000 for performance
    limit = min(limit, 2000)

    scans = query.order_by(EmailScanModel.received_date.desc()).limit(limit).all()

    return [
        EmailScan(
            id=str(scan.id),
            user_id=str(scan.user_id),
            broker_id=str(scan.broker_id) if scan.broker_id else None,
            gmail_message_id=scan.gmail_message_id,
            sender_email=scan.sender_email,
            sender_domain=scan.sender_domain,
            subject=scan.subject,
            received_date=scan.received_date,
            is_broker_email=scan.is_broker_email,
            confidence_score=scan.confidence_score,
            classification_notes=scan.classification_notes,
            body_preview=scan.body_preview,
            created_at=scan.created_at
        )
        for scan in scans
    ]


@router.get("/scans/paged", response_model=EmailScanPage)
def get_scans_paged(
    broker_only: bool = False,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated email scan results for a user"""
    query = db.query(EmailScanModel).filter(EmailScanModel.user_id == current_user.id)

    if broker_only:
        query = query.filter(EmailScanModel.is_broker_email == True)

    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    total = query.count()
    scans = (
        query.order_by(EmailScanModel.received_date.desc(), EmailScanModel.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return EmailScanPage(
        items=[
            EmailScan(
                id=str(scan.id),
                user_id=str(scan.user_id),
                broker_id=str(scan.broker_id) if scan.broker_id else None,
                gmail_message_id=scan.gmail_message_id,
                sender_email=scan.sender_email,
                sender_domain=scan.sender_domain,
                subject=scan.subject,
                received_date=scan.received_date,
                is_broker_email=scan.is_broker_email,
                confidence_score=scan.confidence_score,
                classification_notes=scan.classification_notes,
                body_preview=scan.body_preview,
                created_at=scan.created_at,
            )
            for scan in scans
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/scan-history", response_model=ScanHistoryPage)
def get_scan_history(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated scan history for a user"""
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    base_query = db.query(ActivityLog).filter(
        ActivityLog.user_id == current_user.id,
        ActivityLog.activity_type.in_([ActivityType.EMAIL_SCANNED, ActivityType.RESPONSE_SCANNED]),
    )

    total = base_query.count()
    activities = (
        base_query.order_by(ActivityLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return ScanHistoryPage(
        items=[_parse_scan_history(activity) for activity in activities],
        total=total,
        limit=limit,
        offset=offset,
    )
