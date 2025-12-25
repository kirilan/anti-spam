import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app modules
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMmJ5dGVzISE=")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENVIRONMENT", "test")

from app.database import Base, get_db
from app.main import app
from app.models.activity_log import ActivityLog, ActivityType
from app.models.broker_response import BrokerResponse, ResponseType
from app.models.data_broker import DataBroker
from app.models.deletion_request import DeletionRequest, RequestStatus
from app.models.user import User

# Test database engine (SQLite in-memory)
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override"""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        google_id="google-123",
        encrypted_access_token="encrypted-token",
        encrypted_refresh_token="encrypted-refresh",
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin test user"""
    user = User(
        email="admin@example.com",
        google_id="google-admin-123",
        encrypted_access_token="encrypted-token",
        encrypted_refresh_token="encrypted-refresh",
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_broker(db: Session) -> DataBroker:
    """Create a test data broker"""
    broker = DataBroker(
        name="Test Broker",
        domains=["testbroker.com", "test-broker.net"],
        privacy_email="privacy@testbroker.com",
        opt_out_url="https://testbroker.com/opt-out",
        category="people_search",
    )
    db.add(broker)
    db.commit()
    db.refresh(broker)
    return broker


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Generate auth headers for test user"""
    from app.dependencies.auth import create_access_token

    token = create_access_token(
        subject=str(test_user.id),
        email=test_user.email,
        is_admin=test_user.is_admin,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict:
    """Generate auth headers for admin user"""
    from app.dependencies.auth import create_access_token

    token = create_access_token(
        subject=str(admin_user.id),
        email=admin_user.email,
        is_admin=admin_user.is_admin,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_deletion_request(db: Session, test_user: User, test_broker: DataBroker) -> DeletionRequest:
    """Create a test deletion request"""
    from datetime import datetime

    request = DeletionRequest(
        user_id=test_user.id,
        broker_id=test_broker.id,
        status=RequestStatus.PENDING,
        source="manual",
        generated_email_subject="Data Deletion Request",
        generated_email_body="Please delete my data.",
        created_at=datetime.utcnow(),
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@pytest.fixture
def sent_deletion_request(db: Session, test_user: User, test_broker: DataBroker) -> DeletionRequest:
    """Create a sent deletion request with Gmail tracking"""
    from datetime import datetime

    request = DeletionRequest(
        user_id=test_user.id,
        broker_id=test_broker.id,
        status=RequestStatus.SENT,
        source="manual",
        generated_email_subject="Data Deletion Request",
        generated_email_body="Please delete my data.",
        sent_at=datetime.utcnow(),
        gmail_sent_message_id="msg-123",
        gmail_thread_id="thread-123",
        created_at=datetime.utcnow(),
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@pytest.fixture
def test_broker_response(
    db: Session, test_user: User, sent_deletion_request: DeletionRequest
) -> BrokerResponse:
    """Create a test broker response"""
    from datetime import datetime

    response = BrokerResponse(
        user_id=test_user.id,
        deletion_request_id=sent_deletion_request.id,
        gmail_message_id="response-msg-123",
        gmail_thread_id="thread-123",
        sender_email="privacy@testbroker.com",
        subject="Re: Data Deletion Request",
        body_text="Your data has been deleted.",
        received_date=datetime.utcnow(),
        response_type=ResponseType.CONFIRMATION,
        confidence_score=0.95,
        matched_by="thread_id",
        is_processed=True,
        processed_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    return response


@pytest.fixture
def test_activity_log(db: Session, test_user: User) -> ActivityLog:
    """Create a test activity log entry"""
    from datetime import datetime

    activity = ActivityLog(
        user_id=test_user.id,
        activity_type=ActivityType.EMAIL_SCANNED,
        message="Scanned inbox and found 5 broker emails",
        details='{"count": 5}',
        created_at=datetime.utcnow(),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@pytest.fixture
def multiple_deletion_requests(
    db: Session, test_user: User, test_broker: DataBroker
) -> list[DeletionRequest]:
    """Create multiple deletion requests with various statuses for analytics testing"""
    from datetime import datetime, timedelta

    requests = []
    statuses = [
        RequestStatus.PENDING,
        RequestStatus.SENT,
        RequestStatus.SENT,
        RequestStatus.CONFIRMED,
        RequestStatus.CONFIRMED,
        RequestStatus.CONFIRMED,
        RequestStatus.REJECTED,
    ]

    for i, status in enumerate(statuses):
        created_at = datetime.utcnow() - timedelta(days=i)
        request = DeletionRequest(
            user_id=test_user.id,
            broker_id=test_broker.id,
            status=status,
            source="manual" if i % 2 == 0 else "auto_discovered",
            generated_email_subject=f"Data Deletion Request {i}",
            generated_email_body=f"Please delete my data. Request #{i}",
            created_at=created_at,
            sent_at=created_at if status != RequestStatus.PENDING else None,
            confirmed_at=created_at if status == RequestStatus.CONFIRMED else None,
            rejected_at=created_at if status == RequestStatus.REJECTED else None,
        )
        db.add(request)
        requests.append(request)

    db.commit()
    for r in requests:
        db.refresh(r)
    return requests


@pytest.fixture
def multiple_broker_responses(
    db: Session, test_user: User, multiple_deletion_requests: list[DeletionRequest]
) -> list[BrokerResponse]:
    """Create multiple broker responses for analytics testing"""
    from datetime import datetime

    responses = []
    response_types = [
        ResponseType.CONFIRMATION,
        ResponseType.CONFIRMATION,
        ResponseType.REJECTION,
        ResponseType.ACKNOWLEDGMENT,
        ResponseType.ACTION_REQUIRED,
    ]

    for i, (rtype, request) in enumerate(
        zip(response_types, multiple_deletion_requests[1:6], strict=False)
    ):
        response = BrokerResponse(
            user_id=test_user.id,
            deletion_request_id=request.id,
            gmail_message_id=f"response-msg-{i}",
            gmail_thread_id=f"thread-{i}",
            sender_email="privacy@testbroker.com",
            subject=f"Re: Data Deletion Request {i}",
            body_text=f"Response body {i}",
            received_date=datetime.utcnow(),
            response_type=rtype,
            confidence_score=0.9,
            matched_by="thread_id",
            is_processed=True,
            processed_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        db.add(response)
        responses.append(response)

    db.commit()
    for r in responses:
        db.refresh(r)
    return responses
