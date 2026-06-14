"""Generation endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

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
            "review": result.get("review", {}),
            "files": result.get("files", []),
        }
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.get("/run/stream")
def stream_generation(
    project_id: str,
    mode: str = Query("auto", pattern="^(auto|live|replay|mock)$"),
    generation_service: GenerationService = Depends(get_generation_service),
):
    def event_stream():
        try:
            for event in generation_service.stream_run(project_id, mode=mode):
                yield _format_sse(event)
        except ProjectNotFoundError as exc:
            yield _format_sse({"event": "run_failed", "project_id": project_id, "error": "Project not found"})
        except Exception as exc:  # pragma: no cover - transport fallback
            yield _format_sse({"event": "run_failed", "project_id": project_id, "error": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _format_sse(payload: dict[str, object]) -> str:
    event_name = str(payload.get("event", "message"))
    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {event_name}\ndata: {data}\n\n"
