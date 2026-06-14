"""Integration tests for the backend REST API."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.dependencies import get_artifact_service, get_generation_service, get_project_service
from backend.services.artifact_service import ArtifactService
from backend.services.generation_service import GenerationService
from backend.services.project_service import ProjectService
from shared.schemas.brief import Brief


def make_brief(name: str) -> Brief:
    return Brief(
        project_name=name,
        industry="photography_studio",
        business_description="Integration test business",
        region="Москва",
        products=["content day"],
        goals=["Generate pipeline"],
    )


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


def create_project(http: TestClient, name: str = "Integration Project") -> dict:
    response = http.post("/projects", json={"name": name, "brief": make_brief(name).model_dump(mode="json")})
    assert response.status_code == 201
    return response.json()


def test_health_endpoint(client):
    http, _service = client
    response = http.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint(client):
    http, _service = client
    response = http.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Marketing OS v4 Backend API"


def test_create_and_get_project(client):
    http, _service = client
    created = create_project(http, "Read Me")
    response = http.get(f"/projects/{created['project_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Read Me"
    assert body["status"] == "pending"


def test_list_projects_endpoint(client):
    http, _service = client
    create_project(http, "Project A")
    create_project(http, "Project B")
    response = http.get("/projects")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_generate_status_artifacts_flow(client):
    http, project_service = client
    created = create_project(http, "Flow Project")
    project_id = created["project_id"]
    generate_response = http.post(f"/projects/{project_id}/generate")
    assert generate_response.status_code == 200
    assert generate_response.json()["status"] == "review_required"
    assert generate_response.json()["review"]["status"] == "review_required"

    status_response = http.get(f"/projects/{project_id}/status")
    assert status_response.status_code == 200
    assert status_response.json() == {"status": "review_required", "progress": 90}

    artifacts_response = http.get(f"/projects/{project_id}/artifacts")
    assert artifacts_response.status_code == 200
    artifacts = artifacts_response.json()
    assert len(artifacts) >= 5
    assert any(artifact["name"] == "dashboard.html" for artifact in artifacts)


def test_download_generated_files(client):
    http, _service = client
    created = create_project(http, "Download Flow")
    project_id = created["project_id"]
    http.post(f"/projects/{project_id}/generate")

    dashboard = http.get(f"/projects/{project_id}/download/dashboard.html")
    assert dashboard.status_code == 200
    assert "Download Flow" in dashboard.text

    zip_response = http.get(f"/projects/{project_id}/download/client-package.zip")
    assert zip_response.status_code == 200
    assert zipfile.is_zipfile(Path(client[1].artifacts_path(project_id) / "client-package.zip"))
    assert zip_response.content


def test_review_approve_flow(client):
    http, project_service = client
    created = create_project(http, "Review Flow")
    project_id = created["project_id"]
    http.post(f"/projects/{project_id}/generate")
    approve = http.post(f"/projects/{project_id}/review/approve")
    assert approve.status_code == 200
    assert approve.json()["status"] == "client_ready"
    assert project_service.get_project(project_id).status == "client_ready"


def test_review_reject_flow(client):
    http, project_service = client
    created = create_project(http, "Reject Flow")
    project_id = created["project_id"]
    http.post(f"/projects/{project_id}/generate")
    reject = http.post(f"/projects/{project_id}/review/reject")
    assert reject.status_code == 200
    assert reject.json()["status"] == "rejected"
    assert project_service.get_project(project_id).status == "rejected"


def test_delete_project_endpoint(client):
    http, _service = client
    created = create_project(http, "Delete Flow")
    project_id = created["project_id"]
    response = http.delete(f"/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert http.get(f"/projects/{project_id}").status_code == 404


def test_generate_missing_project_returns_404(client):
    http, _service = client
    response = http.post("/projects/missing/generate")
    assert response.status_code == 404


def test_artifacts_after_generate_are_physical(client):
    http, project_service = client
    created = create_project(http, "Physical Proof")
    project_id = created["project_id"]
    http.post(f"/projects/{project_id}/generate")
    artifacts_dir = project_service.artifacts_path(project_id)
    for filename in ["brief.json", "final_data.json", "execution_view_model.json", "dashboard.html", "client-package.zip"]:
        path = artifacts_dir / filename
        assert path.exists()
        assert path.stat().st_size > 0


def test_download_endpoints_return_correct_content(client):
    http, _service = client
    created = create_project(http, "Content Proof")
    project_id = created["project_id"]
    http.post(f"/projects/{project_id}/generate")

    final_data = http.get(f"/projects/{project_id}/download/final_data.json")
    assert json.loads(final_data.text)["project_name"] == "Content Proof"

    evm = http.get(f"/projects/{project_id}/download/execution_view_model.json")
    assert evm.status_code == 200
    assert "missions" in evm.text
