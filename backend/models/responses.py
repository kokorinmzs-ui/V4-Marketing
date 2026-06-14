"""Small response models for API endpoints."""

from __future__ import annotations

from pydantic import Field

from shared.schemas.base import MarketingOSBaseModel
from backend.models.project import ArtifactInfo


class HealthResponse(MarketingOSBaseModel):
    status: str = Field(default="ok")


class StatusPayload(MarketingOSBaseModel):
    status: str = Field(...)
    progress: int = Field(..., ge=0, le=100)


class DeletePayload(MarketingOSBaseModel):
    project_id: str = Field(...)
    status: str = Field(default="deleted")


class GeneratePayload(MarketingOSBaseModel):
    project_id: str = Field(...)
    status: str = Field(default="completed")


class ArtifactListPayload(MarketingOSBaseModel):
    artifacts: list[ArtifactInfo] = Field(default_factory=list)

