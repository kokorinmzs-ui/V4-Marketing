"""Generation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_generation_service
from backend.services.generation_service import GenerationService
from backend.services.project_service import ProjectNotFoundError


router = APIRouter(prefix="/projects/{project_id}", tags=["generation"])


@router.post("/generate")
def generate_project(
    project_id: str,
    generation_service: GenerationService = Depends(get_generation_service),
) -> dict[str, object]:
    try:
        result = generation_service.generate(project_id)
        return {
            "project_id": result["project_id"],
            "status": result["status"],
            "llm_summary": result.get("llm_summary", {}),
        }
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
