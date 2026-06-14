"""Unit tests for backend generation service."""

from __future__ import annotations

import json
import zipfile
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


def make_brief(name: str = "Studio One") -> Brief:
    return Brief(
        project_name=name,
        industry="photography_studio",
        business_description="A studio that sells content days, reels and campaigns",
        region="Москва",
        target_markets=["SMB"],
        products=["content day"],
        services=["shoot", "editing"],
        goals=["Qualified leads"],
        constraints=["Budget control"],
    )


@pytest.fixture
def project_service(tmp_path: Path) -> ProjectService:
    return ProjectService(tmp_path / "projects")


@pytest.fixture
def generation_service(project_service: ProjectService) -> GenerationService:
    return GenerationService(project_service)


@pytest.fixture
def project(project_service: ProjectService):
    return project_service.create_project(CreateProjectRequest(name="Gen Project", brief=make_brief("Gen Project")))


@pytest.fixture
def generated_bundle(project_service: ProjectService, generation_service: GenerationService):
    project = project_service.create_project(CreateProjectRequest(name="Gen Project", brief=make_brief("Gen Project")))
    result = generation_service.generate(project.project_id)
    return project_service, project, result


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


def test_generate_creates_artifacts_on_disk(generated_bundle):
    project_service, project, _result = generated_bundle
    artifacts = project_service.artifacts_path(project.project_id)
    expected = {"brief.json", "final_data.json", "execution_view_model.json", "dashboard.html", "client-package.zip"}
    assert expected.issubset({path.name for path in artifacts.iterdir()})


def test_generate_updates_project_status(generated_bundle):
    project_service, project, _result = generated_bundle
    updated = project_service.get_project(project.project_id)
    assert updated.status == "completed"
    assert updated.progress == 100


def test_generate_writes_project_name_into_final_data(generated_bundle):
    project_service, project, _result = generated_bundle
    final_data = json.loads((project_service.artifacts_path(project.project_id) / "final_data.json").read_text(encoding="utf-8"))
    assert final_data["project_id"] == project.project_id
    assert final_data["project_name"] == "Gen Project"


def test_generate_writes_dashboard_html(generated_bundle):
    project_service, project, _result = generated_bundle
    html = (project_service.artifacts_path(project.project_id) / "dashboard.html").read_text(encoding="utf-8")
    assert "Gen Project" in html
    assert html.startswith("<!DOCTYPE html>")


def test_generate_writes_valid_zip(generated_bundle):
    project_service, project, _result = generated_bundle
    zip_bytes = (project_service.artifacts_path(project.project_id) / "client-package.zip").read_bytes()
    assert zipfile.is_zipfile(Path(project_service.artifacts_path(project.project_id) / "client-package.zip"))
    assert zip_bytes


def test_generate_returns_files_list(generated_bundle):
    _service, _project, result = generated_bundle
    assert result["status"] == "completed"
    assert "02-EXECUTION-DASHBOARD.html" in result["files"]


def test_generate_missing_project_raises(project_service: ProjectService, generation_service: GenerationService):
    with pytest.raises(ProjectNotFoundError):
        generation_service.generate("missing")


def test_generate_http_roundtrip(client):
    http, _service = client
    created = http.post("/projects", json={"name": "HTTP Gen", "brief": make_brief("HTTP Gen").model_dump(mode="json")}).json()
    response = http.post(f"/projects/{created['project_id']}/generate")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_status_after_generate_is_completed(client):
    http, _service = client
    created = http.post("/projects", json={"name": "HTTP Status", "brief": make_brief("HTTP Status").model_dump(mode="json")}).json()
    http.post(f"/projects/{created['project_id']}/generate")
    response = http.get(f"/projects/{created['project_id']}/status")
    assert response.status_code == 200
    assert response.json() == {"status": "completed", "progress": 100}


def test_generate_http_missing_project_returns_404(client):
    http, _service = client
    response = http.post("/projects/missing/generate")
    assert response.status_code == 404


def test_generation_pipeline_uses_real_artifacts_bundle(generated_bundle):
    project_service, project, _result = generated_bundle
    artifacts_dir = project_service.artifacts_path(project.project_id)
    assert (artifacts_dir / "execution_view_model.json").exists()
    assert (artifacts_dir / "final_data.json").exists()


def test_final_data_contains_pipeline_sections(generated_bundle):
    project_service, project, _result = generated_bundle
    final_data = json.loads((project_service.artifacts_path(project.project_id) / "final_data.json").read_text(encoding="utf-8"))
    assert final_data["content_plan"]["days"]
    assert final_data["sales_scripts"]["scripts"]


def test_generation_service_surfaces_nonexistent_project(project_service: ProjectService):
    generation_service = GenerationService(project_service)
    with pytest.raises(ProjectNotFoundError):
        generation_service.generate("project_missing")
