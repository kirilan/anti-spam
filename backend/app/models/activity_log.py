import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text, Uuid
from sqlalchemy import Enum as SQLEnum

from app.database import Base


class ActivityType(str, enum.Enum):
    """Types of activities to log"""

    REQUEST_CREATED = "request_created"
    REQUEST_SENT = "request_sent"
    RESPONSE_RECEIVED = "response_received"
    RESPONSE_SCANNED = "response_scanned"
    EMAIL_SCANNED = "email_scanned"
    BROKER_DETECTED = "broker_detected"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, nullable=False, index=True)

    # Activity details
    activity_type = Column(
        SQLEnum(ActivityType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    message = Column(String, nullable=False)  # User-friendly message
    details = Column(Text, nullable=True)  # Additional context (JSON string)

    # Related entities (optional)
    broker_id = Column(Uuid, nullable=True, index=True)
    deletion_request_id = Column(Uuid, nullable=True, index=True)
    response_id = Column(Uuid, nullable=True, index=True)
    email_scan_id = Column(Uuid, nullable=True, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
