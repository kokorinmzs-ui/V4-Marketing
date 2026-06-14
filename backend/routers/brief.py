"""Brief endpoints — CRUD for project brief."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_project_service
from backend.services.project_service import ProjectNotFoundError, ProjectService

router = APIRouter(prefix="/projects/{project_id}", tags=["brief"])


@router.get("/brief")
def get_brief(project_id: str, project_service: ProjectService = Depends(get_project_service)):
    try:
        project = project_service.get_project(project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")

    brief_path = project_service.project_path(project_id) / "brief.json"
    if not brief_path.exists():
        return {"project_id": project_id, "brief": None}

    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    return {"project_id": project_id, "brief": brief}


@router.put("/brief")
def update_brief(project_id: str, brief: dict, project_service: ProjectService = Depends(get_project_service)):
    try:
        project_service.get_project(project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")

    brief_path = project_service.project_path(project_id) / "brief.json"
    brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"project_id": project_id, "brief": brief, "status": "saved"}