"""Unit tests for backend artifact service."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.dependencies import get_artifact_service, get_generation_service, get_project_service
from backend.models.project import CreateProjectRequest
from backend.services.artifact_service import ArtifactService
from backend.services.generation_service import GenerationService
from backend.services.project_service import ProjectNotFoundError, ProjectService
from shared.schemas.brief import Brief


def make_brief(name: str = "Artifacts Project") -> Brief:
    return Brief(
        project_name=name,
        industry="photography_studio",
        business_description="Project for artifact testing",
        region="Москва",
        products=["content day"],
        goals=["Generate artifacts"],
    )


@pytest.fixture
def project_service(tmp_path: Path) -> ProjectService:
    return ProjectService(tmp_path / "projects")


@pytest.fixture
def artifact_service(project_service: ProjectService) -> ArtifactService:
    return ArtifactService(project_service)


@pytest.fixture
def generated_project(project_service: ProjectService):
    project = project_service.create_project(CreateProjectRequest(name="Artifacts Project", brief=make_brief()))
    GenerationService(project_service).generate(project.project_id)
    return project_service, project


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


def test_list_artifacts_returns_all_files(generated_project, artifact_service: ArtifactService):
    project_service, project = generated_project
    artifacts = artifact_service.list_artifacts(project.project_id)
    names = {artifact.name for artifact in artifacts}
    assert {"brief.json", "final_data.json", "execution_view_model.json", "dashboard.html", "client-package.zip"}.issubset(names)


def test_list_artifacts_returns_positive_sizes(generated_project, artifact_service: ArtifactService):
    _service, project = generated_project
    artifacts = artifact_service.list_artifacts(project.project_id)
    assert all(artifact.size > 0 for artifact in artifacts)


def test_get_artifact_path_resolves_inside_project(generated_project, artifact_service: ArtifactService):
    _service, project = generated_project
    path = artifact_service.get_artifact_path(project.project_id, "dashboard.html")
    assert path.name == "dashboard.html"
    assert str(path).endswith("dashboard.html")


def test_get_artifact_path_rejects_traversal(generated_project, artifact_service: ArtifactService):
    _service, project = generated_project
    with pytest.raises(ValueError):
        artifact_service.get_artifact_path(project.project_id, "../secret.txt")


def test_missing_artifact_raises(generated_project, artifact_service: ArtifactService):
    _service, project = generated_project
    with pytest.raises(FileNotFoundError):
        artifact_service.get_artifact_path(project.project_id, "missing.json")


def test_missing_project_raises(artifact_service: ArtifactService):
    with pytest.raises(ProjectNotFoundError):
        artifact_service.list_artifacts("missing")


def test_artifacts_http_roundtrip(client):
    http, _service = client
    created = http.post("/projects", json={"name": "Artifacts HTTP", "brief": make_brief("Artifacts HTTP").model_dump(mode="json")}).json()
    http.post(f"/projects/{created['project_id']}/generate")
    response = http.get(f"/projects/{created['project_id']}/artifacts")
    assert response.status_code == 200
    body = response.json()
    assert any(item["name"] == "dashboard.html" for item in body)


def test_download_dashboard_html_http_roundtrip(client):
    http, _service = client
    created = http.post("/projects", json={"name": "Download HTTP", "brief": make_brief("Download HTTP").model_dump(mode="json")}).json()
    http.post(f"/projects/{created['project_id']}/generate")
    response = http.get(f"/projects/{created['project_id']}/download/dashboard.html")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Download HTTP" in response.text


def test_download_zip_http_roundtrip(client):
    http, _service = client
    created = http.post("/projects", json={"name": "Zip HTTP", "brief": make_brief("Zip HTTP").model_dump(mode="json")}).json()
    http.post(f"/projects/{created['project_id']}/generate")
    response = http.get(f"/projects/{created['project_id']}/download/client-package.zip")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/")
    assert response.content


def test_download_final_data_contains_project_name(client):
    http, _service = client
    created = http.post("/projects", json={"name": "Final Data HTTP", "brief": make_brief("Final Data HTTP").model_dump(mode="json")}).json()
    http.post(f"/projects/{created['project_id']}/generate")
    response = http.get(f"/projects/{created['project_id']}/download/final_data.json")
    assert response.status_code == 200
    data = json.loads(response.text)
    assert data["project_name"] == "Final Data HTTP"


def test_download_missing_project_returns_404(client):
    http, _service = client
    response = http.get("/projects/missing/download/dashboard.html")
    assert response.status_code == 404


def test_download_missing_artifact_returns_404(client):
    http, _service = client
    created = http.post("/projects", json={"name": "Missing Artifact", "brief": make_brief("Missing Artifact").model_dump(mode="json")}).json()
    response = http.get(f"/projects/{created['project_id']}/download/dashboard.html")
    assert response.status_code == 404
