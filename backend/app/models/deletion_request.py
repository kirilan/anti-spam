import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import relationship

from app.database import Base


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class DeletionRequest(Base):
    __tablename__ = "deletion_requests"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    broker_id = Column(Uuid, ForeignKey("data_brokers.id"), nullable=False, index=True)

    # Request details
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    source = Column(String, default='manual', nullable=False)  # 'manual' or 'auto_discovered'
    generated_email_subject = Column(String, nullable=True)
    generated_email_body = Column(Text, nullable=True)

    # Tracking
    sent_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)

    # Gmail tracking
    gmail_sent_message_id = Column(String, nullable=True, index=True)
    gmail_thread_id = Column(String, nullable=True, index=True)

    # Error tracking
    last_send_error = Column(Text, nullable=True)
    send_attempts = Column(Integer, default=0)
    next_retry_at = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    broker_responses = relationship("BrokerResponse", back_populates="deletion_request")
