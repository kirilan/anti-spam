from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class AiSettingsUpdate(BaseModel):
    api_key: Optional[str] = Field(default=None)
    model: Optional[str] = None


class AiSettingsStatus(BaseModel):
    has_key: bool
    updated_at: Optional[datetime] = None
    model: str
    available_models: List[str] = Field(default_factory=list)


class AiResponseClassification(BaseModel):
    response_id: str
    response_type: Literal[
        "confirmation",
        "rejection",
        "acknowledgment",
        "request_info",
        "unknown",
    ]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    rationale: Optional[str] = None


class AiThreadClassification(BaseModel):
    model: str
    responses: List[AiResponseClassification]


class AiClassifyResult(BaseModel):
    request_id: str
    updated_responses: int
    status_updated: bool
    request_status: str
    model: str
    ai_output: AiThreadClassification
