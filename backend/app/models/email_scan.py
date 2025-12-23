import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text, Uuid

from app.database import Base


class EmailScan(Base):
    __tablename__ = "email_scans"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    broker_id = Column(Uuid, ForeignKey("data_brokers.id"), nullable=True, index=True)

    # Gmail details
    gmail_message_id = Column(String, nullable=False, unique=True, index=True)
    gmail_thread_id = Column(String, nullable=True, index=True)  # Thread grouping
    email_direction = Column(String, nullable=False, default="received")  # 'sent' or 'received'
    sender_email = Column(String, nullable=False)
    sender_domain = Column(String, nullable=False, index=True)
    recipient_email = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    received_date = Column(DateTime, nullable=True)

    # Classification
    is_broker_email = Column(Boolean, default=False)
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    classification_notes = Column(Text, nullable=True)

    # Email preview
    body_preview = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
