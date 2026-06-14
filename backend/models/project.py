"""Project API models and stored record schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from shared.schemas.base import MarketingOSBaseModel
from shared.schemas.brief import Brief


class CreateProjectRequest(MarketingOSBaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    brief: Brief = Field(...)


class ProjectRecord(MarketingOSBaseModel):
    project_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    brief: Brief = Field(...)
    status: str = Field(default="pending")
    progress: int = Field(default=0, ge=0, le=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_error: Optional[str] = Field(default=None)


class ProjectSummary(MarketingOSBaseModel):
    project_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    status: str = Field(default="pending")
    progress: int = Field(default=0, ge=0, le=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectStatusResponse(MarketingOSBaseModel):
    status: str = Field(..., description="pending|running|completed|failed")
    progress: int = Field(..., ge=0, le=100)


class ProjectDeleteResponse(MarketingOSBaseModel):
    project_id: str = Field(..., min_length=1)
    status: str = Field(default="deleted")


class ProjectCreateResponse(MarketingOSBaseModel):
    project_id: str = Field(..., min_length=1)
    status: str = Field(default="created")


class ProjectGenerateResponse(MarketingOSBaseModel):
    project_id: str = Field(..., min_length=1)
    status: str = Field(default="completed")


class ArtifactInfo(MarketingOSBaseModel):
    name: str = Field(..., min_length=1)
    size: int = Field(..., ge=0)
    modified_at: Optional[datetime] = Field(default=None)


class StoredProjectBundle(MarketingOSBaseModel):
    project: ProjectRecord
    artifacts: list[ArtifactInfo] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)
