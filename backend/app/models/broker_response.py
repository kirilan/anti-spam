from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Float, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from app.database import Base


class ResponseType(str, enum.Enum):
    """Type of response received from broker"""
    CONFIRMATION = "confirmation"  # Data deleted
    REJECTION = "rejection"  # Unable to delete, no records found, etc.
    ACKNOWLEDGMENT = "acknowledgment"  # Request received, processing
    REQUEST_INFO = "request_info"  # Need more information to verify identity
    UNKNOWN = "unknown"  # Unable to classify


class BrokerResponse(Base):
    """Model for tracking broker responses to deletion requests"""
    __tablename__ = "broker_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    deletion_request_id = Column(UUID(as_uuid=True), ForeignKey('deletion_requests.id'), nullable=True, index=True)

    # Gmail metadata
    gmail_message_id = Column(String, nullable=False, unique=True, index=True)
    gmail_thread_id = Column(String, nullable=True, index=True)

    # Email content
    sender_email = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    body_text = Column(Text, nullable=True)
    received_date = Column(DateTime, nullable=True)

    # Classification
    response_type = Column(
        Enum(ResponseType, values_callable=lambda x: [e.value for e in x]),
        default=ResponseType.UNKNOWN,
        nullable=False
    )
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    matched_by = Column(String, nullable=True)  # How we matched to deletion request

    # Processing metadata
    is_processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="broker_responses")
    deletion_request = relationship("DeletionRequest", back_populates="broker_responses")

    def __repr__(self):
        return f"<BrokerResponse {self.id} {self.response_type.value} from {self.sender_email}>"
