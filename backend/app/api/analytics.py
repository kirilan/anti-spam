from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/stats")
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get overall statistics for a user

    Returns total requests, status breakdown, success rate, and average response time
    """
    service = AnalyticsService(db)
    return service.get_user_stats(str(current_user.id))


@router.get("/broker-ranking")
def get_broker_ranking(
    user_id: str | None = Query(
        None, description="User ID (optional, admin can query other users)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """
    Get broker compliance ranking

    Shows brokers sorted by success rate and response time.
    If user_id is provided, shows ranking based on that user's requests only.
    """
    if not user_id:
        user_id = str(current_user.id)

    service = AnalyticsService(db)
    return service.get_broker_compliance_ranking(user_id)


@router.get("/timeline")
def get_timeline(
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """
    Get timeline data for requests sent and confirmations received

    Returns daily counts for the specified time period
    """
    service = AnalyticsService(db)
    return service.get_timeline_data(str(current_user.id), days)


@router.get("/response-distribution")
def get_response_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """
    Get distribution of broker response types

    Shows count of each response type (confirmation, rejection, acknowledgment, etc.)
    """
    service = AnalyticsService(db)
    return service.get_response_type_distribution(str(current_user.id))
