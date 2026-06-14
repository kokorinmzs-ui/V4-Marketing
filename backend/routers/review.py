"""Review endpoints — human-in-the-loop approval workflow."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_project_service
from backend.services.project_service import ProjectNotFoundError, ProjectService

router = APIRouter(prefix="/projects/{project_id}", tags=["review"])


@router.get("/review")
def get_review(project_id: str, project_service: ProjectService = Depends(get_project_service)):
    """Get review metadata for a project."""
    try:
        project = project_service.get_project(project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")

    review_path = project_service.artifacts_path(project_id) / "generation_report.json"
    if not review_path.exists():
        return {"project_id": project_id, "review": {"status": "not_generated"}}

    report = json.loads(review_path.read_text(encoding="utf-8"))
    review = report.get("review", {"status": project.status})
    return {"project_id": project_id, "review": review}


@router.post("/review/approve")
def approve_review(project_id: str, project_service: ProjectService = Depends(get_project_service)):
    """Approve generated artifacts — mark as client_ready."""
    try:
        project = project_service.get_project(project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status not in ("review_required", "draft_generated", "completed"):
        raise HTTPException(status_code=400, detail=f"Project in status '{project.status}' cannot be approved")

    artifacts_dir = project_service.artifacts_path(project_id)
    if not artifacts_dir.exists() or not any(artifacts_dir.iterdir()):
        raise HTTPException(status_code=400, detail="No artifacts found — generate first")

    project_service.set_status(project_id, "client_ready", 100)

    report_path = artifacts_dir / "generation_report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["review"] = {
            "status": "approved",
            "reviewer": "system",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "notes": report.get("review", {}).get("notes", []),
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"project_id": project_id, "status": "client_ready", "review": {"status": "approved"}}


@router.post("/review/reject")
def reject_review(project_id: str, project_service: ProjectService = Depends(get_project_service)):
    """Reject generated artifacts."""
    try:
        project = project_service.get_project(project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")

    project_service.set_status(project_id, "rejected", 100)

    report_path = project_service.artifacts_path(project_id) / "generation_report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["review"] = {
            "status": "rejected",
            "reviewer": "system",
            "approved_at": None,
            "notes": report.get("review", {}).get("notes", []),
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"project_id": project_id, "status": "rejected", "review": {"status": "rejected"}}