from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DeletionRequestCreate(BaseModel):
    broker_id: str
    framework: str = "GDPR/CCPA"


class DeletionRequestUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class DeletionRequest(BaseModel):
    id: str
    user_id: str
    broker_id: str
    status: str
    generated_email_subject: Optional[str] = None
    generated_email_body: Optional[str] = None
    sent_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    notes: Optional[str] = None
    gmail_sent_message_id: Optional[str] = None
    gmail_thread_id: Optional[str] = None
    send_attempts: int
    last_send_error: Optional[str] = None
    next_retry_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    warning: Optional[str] = None

    class Config:
        from_attributes = True


class EmailPreview(BaseModel):
    subject: str
    body: str
    to_email: Optional[str] = None
    broker_name: str
