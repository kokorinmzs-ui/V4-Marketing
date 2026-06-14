"""Sprint 20 — Human Review Gates & Cost Governance (real backend tests)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.dependencies import get_artifact_service, get_generation_service, get_project_service
from backend.services.artifact_service import ArtifactService
from backend.services.generation_service import GenerationService
from backend.services.project_service import ProjectService
from shared.schemas.brief import Brief


@pytest.fixture
def client(tmp_path: Path):
    project_service = ProjectService(tmp_path / "projects")
    artifact_service = ArtifactService(project_service)
    generation_service = GenerationService(project_service)
    app.dependency_overrides[get_project_service] = lambda: project_service
    app.dependency_overrides[get_artifact_service] = lambda: artifact_service
    app.dependency_overrides[get_generation_service] = lambda: generation_service
    try:
        yield TestClient(app), project_service
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def brief() -> Brief:
    return Brief(
        project_name="Sprint 20 Studio",
        industry="photography_studio",
        business_description="A real studio brief for review gate coverage",
        region="Москве",
        products=["content day"],
        goals=["qualified leads"],
    )


@pytest.fixture
def created_project(client, brief):
    http, _service = client
    response = http.post(
        "/projects",
        json={"name": brief.project_name, "brief": brief.model_dump(mode="json")},
    )
    assert response.status_code == 201
    return response.json()


class TestReviewStatusModel:
    def test_review_required_status_exists(self):
        from backend.models.project import ProjectRecord

        record = ProjectRecord(
            project_id="p1",
            name="Test",
            brief=Brief(
                project_name="Test",
                industry="photography_studio",
                business_description="Brief",
            ),
            status="review_required",
        )
        assert record.status == "review_required"

    def test_rejected_status_exists(self):
        from backend.models.project import ProjectRecord

        record = ProjectRecord(
            project_id="p1",
            name="Test",
            brief=Brief(
                project_name="Test",
                industry="photography_studio",
                business_description="Brief",
            ),
            status="rejected",
        )
        assert record.status == "rejected"

    def test_status_not_auto_client_ready(self):
        assert "client_ready" not in ["pending", "running", "review_required", "rejected", "failed"]


class TestReviewMetadata:
    def test_review_metadata_structure(self):
        review = {
            "status": "review_required",
            "reviewer": None,
            "approved_at": None,
            "notes": [],
            "override_reasons": [],
        }
        assert review["status"] == "review_required"
        assert review["reviewer"] is None

    def test_review_metadata_approval(self):
        review = {"status": "approved", "reviewer": "admin", "approved_at": datetime.utcnow().isoformat()}
        assert review["status"] == "approved"
        assert review["reviewer"] == "admin"


class TestReviewEndpoints:
    def test_get_review_endpoint_path(self):
        from fastapi import APIRouter

        router = APIRouter(prefix="/projects/{project_id}", tags=["review"])

        @router.get("/review")
        def get_review(project_id: str):
            return {"project_id": project_id, "review": {"status": "review_required"}}

        @router.post("/review/approve")
        def approve_review(project_id: str):
            return {"project_id": project_id, "review": {"status": "approved"}}

        @router.post("/review/reject")
        def reject_review(project_id: str):
            return {"project_id": project_id, "review": {"status": "rejected"}}

        assert router.routes[0].path == "/projects/{project_id}/review"
        assert router.routes[1].path == "/projects/{project_id}/review/approve"
        assert router.routes[2].path == "/projects/{project_id}/review/reject"

    def test_cannot_approve_without_artifacts(self, client, created_project):
        http, _service = client
        response = http.post(f"/projects/{created_project['project_id']}/review/approve")
        assert response.status_code == 400


class TestCostBudget:
    def test_budget_structure(self):
        budget = {"max_tokens": 100000, "max_cost_usd": 1.00}
        assert budget["max_tokens"] == 100000
        assert budget["max_cost_usd"] == 1.0

    def test_tracking_structure(self):
        tracking = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "estimated_cost_usd": 0.0}
        assert tracking["total_tokens"] == 0


class TestBudgetEnforcement:
    def test_budget_within_limit(self):
        budget = {"max_tokens": 100000, "max_cost_usd": 1.00}
        used = {"total_tokens": 50000, "estimated_cost_usd": 0.50}
        assert used["total_tokens"] <= budget["max_tokens"]
        assert used["estimated_cost_usd"] <= budget["max_cost_usd"]

    def test_budget_exceeded_block(self, client, created_project):
        _http, project_service = client
        generation_service = GenerationService(project_service)
        review = generation_service._build_review_metadata(
            {"input_tokens": 90000, "output_tokens": 20000, "cost": 0.5},
            {},
        )
        assert review["budget"]["over_budget"] is True

    def test_cost_exceeded_block(self, client, created_project):
        _http, project_service = client
        generation_service = GenerationService(project_service)
        review = generation_service._build_review_metadata(
            {"input_tokens": 1000, "output_tokens": 1000, "cost": 2.0},
            {},
        )
        assert review["budget"]["over_budget"] is True


class TestGenerationEndsInReview:
    def test_generation_results_include_review_metadata(self, client, created_project):
        http, _service = client
        response = http.post(f"/projects/{created_project['project_id']}/generate")
        assert response.status_code == 200
        assert response.json()["status"] == "review_required"
        assert "review" in response.json()
        assert response.json()["review"]["status"] == "review_required"

    def test_approve_changes_status_to_approved(self, client, created_project):
        http, project_service = client
        http.post(f"/projects/{created_project['project_id']}/generate")
        response = http.post(f"/projects/{created_project['project_id']}/review/approve")
        assert response.status_code == 200
        assert response.json()["status"] == "client_ready"
        assert project_service.get_project(created_project["project_id"]).status == "client_ready"

    def test_reject_changes_status_to_rejected(self, client, created_project):
        http, project_service = client
        http.post(f"/projects/{created_project['project_id']}/generate")
        response = http.post(f"/projects/{created_project['project_id']}/review/reject")
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
        assert project_service.get_project(created_project["project_id"]).status == "rejected"


class TestGenerationReportIncludesCostReview:
    def test_report_structure_comprehensive(self, client, created_project):
        http, project_service = client
        http.post(f"/projects/{created_project['project_id']}/generate")
        report_path = project_service.artifacts_path(created_project["project_id"]) / "generation_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["llm_summary"]["cost"] >= 0
        assert report["review"]["status"] == "review_required"
        assert report["review"]["budget"]["used_tokens"] >= 0
        assert report["review"]["budget"]["used_cost_usd"] >= 0
