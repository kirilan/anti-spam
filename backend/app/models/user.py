import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from cryptography.fernet import Fernet

from app.database import Base
from app.config import settings


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    google_id = Column(String, unique=True, nullable=False)

    # Encrypted OAuth tokens
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    encrypted_gemini_api_key = Column(Text, nullable=True)
    gemini_key_updated_at = Column(DateTime, nullable=True)
    gemini_model = Column(String, nullable=True)

    # Scanner metadata
    last_scan_at = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    broker_responses = relationship("BrokerResponse", back_populates="user")

    def encrypt_token(self, token: str) -> str:
        """Encrypt a token using Fernet encryption"""
        fernet = Fernet(settings.encryption_key.encode())
        return fernet.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token using Fernet encryption"""
        fernet = Fernet(settings.encryption_key.encode())
        return fernet.decrypt(encrypted_token.encode()).decode()

    def set_access_token(self, token: str):
        """Set encrypted access token"""
        self.encrypted_access_token = self.encrypt_token(token)

    def set_refresh_token(self, token: str):
        """Set encrypted refresh token"""
        self.encrypted_refresh_token = self.encrypt_token(token)

    def get_access_token(self) -> str:
        """Get decrypted access token"""
        if self.encrypted_access_token:
            return self.decrypt_token(self.encrypted_access_token)
        return None

    def get_refresh_token(self) -> str:
        """Get decrypted refresh token"""
        if self.encrypted_refresh_token:
            return self.decrypt_token(self.encrypted_refresh_token)
        return None

    def set_gemini_api_key(self, api_key: str):
        """Set encrypted Gemini API key"""
        self.encrypted_gemini_api_key = self.encrypt_token(api_key)
        self.gemini_key_updated_at = datetime.utcnow()

    def clear_gemini_api_key(self):
        """Remove stored Gemini API key"""
        self.encrypted_gemini_api_key = None
        self.gemini_key_updated_at = datetime.utcnow()

    def get_gemini_api_key(self) -> str:
        """Get decrypted Gemini API key"""
        if self.encrypted_gemini_api_key:
            return self.decrypt_token(self.encrypted_gemini_api_key)
        return None
