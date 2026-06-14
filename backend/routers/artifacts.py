"""Artifact endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from backend.dependencies import get_artifact_service
from backend.services.artifact_service import ArtifactService
from backend.services.project_service import ProjectNotFoundError


router = APIRouter(prefix="/projects/{project_id}", tags=["artifacts"])


@router.get("/artifacts")
def list_artifacts(
    project_id: str,
    artifact_service: ArtifactService = Depends(get_artifact_service),
) -> list[dict]:
    try:
        return [item.model_dump(mode="json", exclude={"schema_version"}) for item in artifact_service.list_artifacts(project_id)]
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.get("/download/{artifact_name}")
def download_artifact(
    project_id: str,
    artifact_name: str,
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    try:
        artifact = artifact_service.get_artifact_read_result(project_id, artifact_name)
        return FileResponse(path=artifact.path, media_type=artifact.mime_type, filename=artifact.path.name)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Artifact not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
