"""Filesystem-backed project storage service."""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from backend.models.project import (
    CreateProjectRequest,
    ProjectDeleteResponse,
    ProjectRecord,
    ProjectSummary,
)
from shared.schemas.brief import Brief


class ProjectNotFoundError(FileNotFoundError):
    pass


class ProjectService:
    def __init__(self, storage_root: Path | str | None = None):
        self.root = Path(storage_root) if storage_root else Path.cwd() / "storage" / "projects"
        self.root.mkdir(parents=True, exist_ok=True)

    def create_project(self, payload: CreateProjectRequest) -> ProjectRecord:
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        brief = payload.brief.model_copy(update={"project_id": project_id})
        now = datetime.now(timezone.utc)
        record = ProjectRecord(
            project_id=project_id,
            name=payload.name.strip(),
            brief=brief,
            status="pending",
            progress=0,
            created_at=now,
            updated_at=now,
        )
        self._write_project(record)
        self._write_json(self.project_path(project_id) / "brief.json", brief.model_dump(mode="json"))
        return record

    def list_projects(self) -> list[ProjectSummary]:
        summaries: list[ProjectSummary] = []
        for path in sorted(self.root.glob("*/project.json")):
            try:
                record = ProjectRecord.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            summaries.append(
                ProjectSummary(
                    project_id=record.project_id,
                    name=record.name,
                    status=record.status,
                    progress=record.progress,
                    created_at=record.created_at,
                )
            )
        summaries.sort(key=lambda item: item.created_at, reverse=True)
        return summaries

    def get_project(self, project_id: str) -> ProjectRecord:
        path = self.project_file(project_id)
        if not path.exists():
            raise ProjectNotFoundError(project_id)
        return ProjectRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def delete_project(self, project_id: str) -> ProjectDeleteResponse:
        path = self.project_path(project_id)
        if not path.exists():
            raise ProjectNotFoundError(project_id)
        shutil.rmtree(path)
        return ProjectDeleteResponse(project_id=project_id, status="deleted")

    def update_project(
        self,
        project_id: str,
        *,
        status: str | None = None,
        progress: int | None = None,
        last_error: str | None = None,
        artifacts_ready: bool | None = None,
    ) -> ProjectRecord:
        record = self.get_project(project_id)
        update_payload: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
        if status is not None:
            update_payload["status"] = status
        if progress is not None:
            update_payload["progress"] = progress
        if last_error is not None:
            update_payload["last_error"] = last_error
        if artifacts_ready is not None and artifacts_ready:
            update_payload["last_error"] = None
        record = record.model_copy(update=update_payload)
        self._write_project(record)
        return record

    def set_status(self, project_id: str, status: str, progress: int, last_error: str | None = None) -> ProjectRecord:
        return self.update_project(project_id, status=status, progress=progress, last_error=last_error)

    def project_path(self, project_id: str) -> Path:
        return self.root / project_id

    def project_file(self, project_id: str) -> Path:
        return self.project_path(project_id) / "project.json"

    def artifacts_path(self, project_id: str) -> Path:
        path = self.project_path(project_id) / "artifacts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_bundle(self, project_id: str, filename: str, content: bytes | str) -> Path:
        target = self.artifacts_path(project_id) / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        return target

    def read_bundle_file(self, project_id: str, filename: str) -> bytes:
        target = self.safe_artifact_path(project_id, filename)
        return target.read_bytes()

    def safe_artifact_path(self, project_id: str, filename: str) -> Path:
        if not filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid artifact name")
        project_root = self.project_path(project_id)
        if not project_root.exists():
            raise ProjectNotFoundError(project_id)
        artifacts_root = self.artifacts_path(project_id).resolve()
        target = (artifacts_root / filename).resolve()
        root = artifacts_root
        if root not in target.parents and target != root:
            raise ValueError("Artifact path escape detected")
        if not target.exists():
            raise FileNotFoundError(filename)
        return target

    def _write_project(self, record: ProjectRecord) -> None:
        path = self.project_path(record.project_id)
        path.mkdir(parents=True, exist_ok=True)
        self._write_json(self.project_file(record.project_id), record.model_dump(mode="json"))

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
