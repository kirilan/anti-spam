import json
import os
import uuid

from sqlalchemy.orm import Session

from app.models.data_broker import DataBroker
from app.schemas.broker import BrokerCreate


class BrokerService:
    def __init__(self, db: Session):
        self.db = db

    def load_brokers_from_json(self) -> int:
        """Load data brokers from JSON file into database"""
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "data_brokers.json"
        )

        with open(json_path) as f:
            data = json.load(f)

        count = 0
        for broker_data in data["brokers"]:
            # Check if broker already exists
            existing = (
                self.db.query(DataBroker).filter(DataBroker.name == broker_data["name"]).first()
            )

            if existing:
                # Update existing broker
                existing.domains = broker_data["domains"]
                existing.privacy_email = broker_data.get("privacy_email")
                existing.opt_out_url = broker_data.get("opt_out_url")
                existing.category = broker_data.get("category")
            else:
                # Create new broker
                broker = DataBroker(
                    name=broker_data["name"],
                    domains=broker_data["domains"],
                    privacy_email=broker_data.get("privacy_email"),
                    opt_out_url=broker_data.get("opt_out_url"),
                    category=broker_data.get("category"),
                )
                self.db.add(broker)
                count += 1

        self.db.commit()
        return count

    def get_all_brokers(self) -> list[DataBroker]:
        """Get all data brokers"""
        return self.db.query(DataBroker).order_by(DataBroker.name).all()

    def get_broker_by_domain(self, domain: str) -> DataBroker:
        """Find broker by domain"""
        brokers = self.db.query(DataBroker).all()

        for broker in brokers:
            if domain in broker.domains or any(d in domain for d in broker.domains):
                return broker

        return None

    def get_broker_by_id(self, broker_id: str) -> DataBroker | None:
        """Get broker by ID"""
        try:
            broker_uuid = uuid.UUID(broker_id) if isinstance(broker_id, str) else broker_id
        except ValueError:
            return None
        return self.db.query(DataBroker).filter(DataBroker.id == broker_uuid).first()

    def find_broker_by_domain(self, domain: str) -> DataBroker | None:
        """Alias for get_broker_by_domain for backwards compatibility"""
        return self.get_broker_by_domain(domain)

    def create_broker(self, broker_data: BrokerCreate) -> DataBroker:
        """Create a new broker record"""
        normalized_domains = [
            domain.strip().lower() for domain in broker_data.domains if domain and domain.strip()
        ]

        if not normalized_domains:
            raise ValueError("At least one valid domain is required")

        existing = (
            self.db.query(DataBroker).filter(DataBroker.name == broker_data.name.strip()).first()
        )

        if existing:
            raise ValueError("Broker with this name already exists")

        broker = DataBroker(
            name=broker_data.name.strip(),
            domains=normalized_domains,
            privacy_email=broker_data.privacy_email.strip() if broker_data.privacy_email else None,
            opt_out_url=broker_data.opt_out_url.strip() if broker_data.opt_out_url else None,
            category=broker_data.category.strip() if broker_data.category else None,
        )

        self.db.add(broker)
        self.db.commit()
        self.db.refresh(broker)
        return broker
