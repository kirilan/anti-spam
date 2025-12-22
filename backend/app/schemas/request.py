import re
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# Valid frameworks for deletion requests
VALID_FRAMEWORKS = ["GDPR", "CCPA", "GDPR/CCPA"]

# Valid status values
VALID_STATUSES = ["pending", "sent", "confirmed", "rejected"]


class DeletionRequestCreate(BaseModel):
    broker_id: Annotated[str, Field(min_length=36, max_length=36)]
    framework: str = Field(default="GDPR/CCPA", max_length=20)

    @field_validator("broker_id")
    @classmethod
    def validate_broker_id(cls, v: str) -> str:
        # Validate UUID format
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        if not re.match(uuid_pattern, v.lower()):
            raise ValueError("Invalid broker ID format")
        return v

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in [f.upper() for f in VALID_FRAMEWORKS]:
            raise ValueError(f"Invalid framework. Must be one of: {', '.join(VALID_FRAMEWORKS)}")
        return v


class DeletionRequestUpdate(BaseModel):
    status: Annotated[str, Field(min_length=1, max_length=20)]
    notes: str | None = Field(None, max_length=1000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
        return v

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        return v if v else None


class DeletionRequest(BaseModel):
    id: str
    user_id: str
    broker_id: str
    status: str
    generated_email_subject: str | None = None
    generated_email_body: str | None = None
    sent_at: datetime | None = None
    confirmed_at: datetime | None = None
    rejected_at: datetime | None = None
    notes: str | None = None
    gmail_sent_message_id: str | None = None
    gmail_thread_id: str | None = None
    send_attempts: int
    last_send_error: str | None = None
    next_retry_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    warning: str | None = None

    class Config:
        from_attributes = True


class EmailPreview(BaseModel):
    subject: str
    body: str
    to_email: str | None = None
    broker_name: str


class ThreadEmail(BaseModel):
    """Email in a deletion request thread"""

    id: str
    gmail_message_id: str
    gmail_thread_id: str | None = None
    sender_email: str
    recipient_email: str | None = None
    subject: str | None = None
    body_preview: str | None = None
    direction: str  # 'sent' or 'received'
    received_date: datetime | None = None
    response_type: str | None = None
    confidence_score: float | None = None

    class Config:
        from_attributes = True
