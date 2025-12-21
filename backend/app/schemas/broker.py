import re
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# Valid broker categories
VALID_CATEGORIES = [
    "data_aggregator",
    "people_search",
    "marketing",
    "credit_bureau",
    "background_check",
    "other",
]


class BrokerBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    domains: Annotated[list[str], Field(min_length=1, max_length=50)]
    privacy_email: str | None = Field(None, max_length=255)
    opt_out_url: str | None = Field(None, max_length=2048)
    category: str | None = Field(None, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or whitespace only")
        if re.search(r"[<>\"']", v):
            raise ValueError("Name contains invalid characters")
        return v

    @field_validator("domains")
    @classmethod
    def validate_domains(cls, v: list[str]) -> list[str]:
        validated = []
        for domain in v:
            domain = domain.strip().lower()
            if not domain:
                continue
            if not re.match(
                r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$",
                domain,
            ):
                raise ValueError(f"Invalid domain format: {domain}")
            if len(domain) > 253:
                raise ValueError(f"Domain too long: {domain}")
            validated.append(domain)
        if not validated:
            raise ValueError("At least one valid domain is required")
        return validated

    @field_validator("privacy_email")
    @classmethod
    def validate_privacy_email(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if not v:
            return None
        if not re.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("opt_out_url")
    @classmethod
    def validate_opt_out_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if not v:
            return None
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}")
        return v


class BrokerCreate(BrokerBase):
    pass


class Broker(BrokerBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrokerSyncResult(BaseModel):
    message: str
    brokers_added: int
    total_brokers: int
