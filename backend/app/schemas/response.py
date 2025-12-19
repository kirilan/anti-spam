from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class BrokerResponseBase(BaseModel):
    gmail_message_id: str
    gmail_thread_id: Optional[str] = None
    sender_email: str
    subject: Optional[str] = None
    body_text: Optional[str] = None
    received_date: Optional[datetime] = None
    response_type: str  # 'confirmation', 'rejection', 'acknowledgment', 'request_info', 'unknown'
    confidence_score: Optional[float] = None
    matched_by: Optional[str] = None


class BrokerResponse(BrokerResponseBase):
    id: str
    user_id: str
    deletion_request_id: Optional[str] = None
    is_processed: bool
    processed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanResponsesRequest(BaseModel):
    days_back: int = 7


ResponseTypeLiteral = Literal[
    "confirmation",
    "rejection",
    "acknowledgment",
    "request_info",
    "unknown",
]


class ClassifyResponseRequest(BaseModel):
    response_type: ResponseTypeLiteral
    confidence_score: Optional[float] = None
    deletion_request_id: Optional[str] = None
