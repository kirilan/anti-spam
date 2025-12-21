from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.broker import Broker, BrokerCreate, BrokerSyncResult
from app.services.broker_service import BrokerService

router = APIRouter()


@router.get("/", response_model=list[Broker])
def list_brokers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all data brokers"""
    service = BrokerService(db)
    brokers = service.get_all_brokers()

    return [
        Broker(
            id=str(broker.id),
            name=broker.name,
            domains=broker.domains,
            privacy_email=broker.privacy_email,
            opt_out_url=broker.opt_out_url,
            category=broker.category,
            created_at=broker.created_at,
            updated_at=broker.updated_at,
        )
        for broker in brokers
    ]


@router.get("/{broker_id}", response_model=Broker)
def get_broker(
    broker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific broker by ID"""
    service = BrokerService(db)
    broker = service.get_broker_by_id(broker_id)

    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")

    return Broker(
        id=str(broker.id),
        name=broker.name,
        domains=broker.domains,
        privacy_email=broker.privacy_email,
        opt_out_url=broker.opt_out_url,
        category=broker.category,
        created_at=broker.created_at,
        updated_at=broker.updated_at,
    )


@router.post("/", response_model=Broker, status_code=201)
def create_broker(
    broker_data: BrokerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new data broker"""
    service = BrokerService(db)
    try:
        broker = service.create_broker(broker_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return Broker(
        id=str(broker.id),
        name=broker.name,
        domains=broker.domains,
        privacy_email=broker.privacy_email,
        opt_out_url=broker.opt_out_url,
        category=broker.category,
        created_at=broker.created_at,
        updated_at=broker.updated_at,
    )


@router.post("/sync", response_model=BrokerSyncResult)
def sync_brokers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Sync brokers from JSON file to database"""
    service = BrokerService(db)

    try:
        count = service.load_brokers_from_json()
        total = len(service.get_all_brokers())

        return BrokerSyncResult(
            message="Successfully synced brokers", brokers_added=count, total_brokers=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync brokers: {str(e)}")
