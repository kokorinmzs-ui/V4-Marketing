"""Service dependencies for FastAPI."""

from __future__ import annotations

from functools import lru_cache

from backend.services.artifact_service import ArtifactService
from backend.services.generation_service import GenerationService
from backend.services.project_service import ProjectService


@lru_cache(maxsize=1)
def get_project_service() -> ProjectService:
    return ProjectService()


@lru_cache(maxsize=1)
def get_artifact_service() -> ArtifactService:
    return ArtifactService(get_project_service())


@lru_cache(maxsize=1)
def get_generation_service() -> GenerationService:
    return GenerationService(get_project_service())

