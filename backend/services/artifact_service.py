"""Artifact filesystem service."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from backend.models.project import ArtifactInfo
from backend.services.project_service import ProjectNotFoundError, ProjectService


@dataclass
class ArtifactReadResult:
    path: Path
    mime_type: str


class ArtifactService:
    def __init__(self, project_service: ProjectService):
        self.project_service = project_service

    def list_artifacts(self, project_id: str) -> list[ArtifactInfo]:
        project_root = self.project_service.project_path(project_id)
        if not project_root.exists():
            raise ProjectNotFoundError(project_id)
        artifacts_dir = self.project_service.artifacts_path(project_id)
        if not artifacts_dir.exists():
            return []
        items: list[ArtifactInfo] = []
        for path in sorted(artifacts_dir.iterdir()):
            if path.is_file():
                stat = path.stat()
                items.append(
                    ArtifactInfo(
                        name=path.name,
                        size=stat.st_size,
                        modified_at=None,
                    )
                )
        return items

    def get_artifact_path(self, project_id: str, artifact_name: str) -> Path:
        return self.project_service.safe_artifact_path(project_id, artifact_name)

    def get_artifact_read_result(self, project_id: str, artifact_name: str) -> ArtifactReadResult:
        path = self.get_artifact_path(project_id, artifact_name)
        mime_type, _ = mimetypes.guess_type(path.name)
        return ArtifactReadResult(path=path, mime_type=mime_type or "application/octet-stream")
