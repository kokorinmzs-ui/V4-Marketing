"""Project CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.dependencies import get_project_service
from backend.models.project import (
    CreateProjectRequest,
    ProjectDeleteResponse,
    ProjectRecord,
    ProjectSummary,
)
from backend.services.project_service import ProjectNotFoundError, ProjectService


router = APIRouter(prefix="/projects", tags=["projects"])


def _strip_schema_version(value):
    if isinstance(value, dict):
        return {key: _strip_schema_version(item) for key, item in value.items() if key != "schema_version"}
    if isinstance(value, list):
        return [_strip_schema_version(item) for item in value]
    return value


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> dict[str, str]:
    record = project_service.create_project(payload)
    return {"project_id": record.project_id, "status": "created"}


@router.get("")
def list_projects(project_service: ProjectService = Depends(get_project_service)) -> list[dict]:
    return [
        _strip_schema_version(item.model_dump(mode="json"))
        for item in project_service.list_projects()
    ]


@router.get("/{project_id}")
def get_project(project_id: str, project_service: ProjectService = Depends(get_project_service)) -> dict:
    try:
        return _strip_schema_version(project_service.get_project(project_id).model_dump(mode="json"))
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.delete("/{project_id}")
def delete_project(project_id: str, project_service: ProjectService = Depends(get_project_service)) -> dict[str, str]:
    try:
        deleted = project_service.delete_project(project_id)
        return {"project_id": deleted.project_id, "status": deleted.status}
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.get("/{project_id}/status")
def project_status(project_id: str, project_service: ProjectService = Depends(get_project_service)) -> dict[str, int | str]:
    try:
        record = project_service.get_project(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    return {"status": record.status, "progress": record.progress}
