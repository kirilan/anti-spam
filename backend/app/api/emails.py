from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.email_scan import EmailScan as EmailScanModel
from app.schemas.email import ScanRequest, ScanResult, EmailScan
from app.services.email_scanner import EmailScanner

router = APIRouter()


@router.post("/scan", response_model=ScanResult)
def scan_emails(
    user_id: str,
    request: ScanRequest = ScanRequest(),
    db: Session = Depends(get_db)
):
    """Scan user's Gmail inbox for data broker emails"""

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is authenticated
    if not user.encrypted_access_token:
        raise HTTPException(status_code=401, detail="User not authenticated with Gmail")

    # Scan inbox
    scanner = EmailScanner(db)

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

        return ScanResult(
            message="Inbox scan completed",
            total_scanned=len(scans),
            broker_emails_found=broker_emails,
            scans=scan_responses
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/scans", response_model=List[EmailScan])
def get_scans(
    user_id: str,
    broker_only: bool = False,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """Get email scan results for a user"""

    query = db.query(EmailScanModel).filter(EmailScanModel.user_id == user_id)

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
