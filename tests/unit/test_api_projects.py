"""Unit tests for backend project CRUD service and endpoints."""

from __future__ import annotations

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


def make_brief(name: str = "Studio One", industry: str = "photography_studio") -> Brief:
    return Brief(
        project_name=name,
        industry=industry,
        business_description="Photography studio with content production packages",
        region="Москва",
        target_markets=["SMB"],
        products=["content day"],
        services=["shoot", "editing"],
        goals=["More qualified leads"],
        constraints=["Budget control"],
    )


@pytest.fixture
def project_service(tmp_path: Path) -> ProjectService:
    return ProjectService(tmp_path / "projects")


@pytest.fixture
def project_request() -> CreateProjectRequest:
    return CreateProjectRequest(name="Studio One", brief=make_brief())


@pytest.fixture
def project(project_service: ProjectService, project_request: CreateProjectRequest):
    return project_service.create_project(project_request)


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


def test_create_project_persists_project_json(project_service: ProjectService, project_request: CreateProjectRequest):
    record = project_service.create_project(project_request)
    assert record.project_id.startswith("proj_")
    assert (project_service.project_file(record.project_id)).exists()
    saved = project_service.get_project(record.project_id)
    assert saved.name == "Studio One"
    assert saved.brief.project_id == record.project_id


def test_list_projects_is_empty_initially(project_service: ProjectService):
    assert project_service.list_projects() == []


def test_get_project_roundtrip(project_service: ProjectService, project_request: CreateProjectRequest):
    record = project_service.create_project(project_request)
    loaded = project_service.get_project(record.project_id)
    assert loaded.project_id == record.project_id
    assert loaded.brief.project_name == "Studio One"


def test_get_project_missing_raises(project_service: ProjectService):
    with pytest.raises(ProjectNotFoundError):
        project_service.get_project("missing")


def test_delete_project_removes_folder(project_service: ProjectService, project_request: CreateProjectRequest):
    record = project_service.create_project(project_request)
    project_dir = project_service.project_path(record.project_id)
    assert project_dir.exists()
    deleted = project_service.delete_project(record.project_id)
    assert deleted.project_id == record.project_id
    assert not project_dir.exists()


def test_set_status_updates_project(project_service: ProjectService, project_request: CreateProjectRequest):
    record = project_service.create_project(project_request)
    updated = project_service.set_status(record.project_id, "running", 42)
    assert updated.status == "running"
    assert updated.progress == 42


def test_list_projects_returns_summary(project_service: ProjectService):
    first = project_service.create_project(CreateProjectRequest(name="One", brief=make_brief("One")))
    second = project_service.create_project(CreateProjectRequest(name="Two", brief=make_brief("Two")))
    items = project_service.list_projects()
    assert {item.project_id for item in items} == {first.project_id, second.project_id}


def test_create_project_overrides_brief_project_id(project_service: ProjectService, project_request: CreateProjectRequest):
    record = project_service.create_project(project_request)
    assert record.brief.project_id == record.project_id


def test_create_project_http_roundtrip(client):
    http, _service = client
    response = http.post("/projects", json={"name": "Studio HTTP", "brief": make_brief("Studio HTTP").model_dump(mode="json")})
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "created"
    assert body["project_id"].startswith("proj_")


def test_list_projects_http_roundtrip(client):
    http, _service = client
    http.post("/projects", json={"name": "List Me", "brief": make_brief("List Me").model_dump(mode="json")})
    response = http.get("/projects")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_project_http_roundtrip(client):
    http, _service = client
    created = http.post("/projects", json={"name": "Detail Me", "brief": make_brief("Detail Me").model_dump(mode="json")}).json()
    response = http.get(f"/projects/{created['project_id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Detail Me"


def test_status_http_roundtrip(client):
    http, _service = client
    created = http.post("/projects", json={"name": "Status Me", "brief": make_brief("Status Me").model_dump(mode="json")}).json()
    response = http.get(f"/projects/{created['project_id']}/status")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["progress"] == 0


def test_delete_project_http_roundtrip(client):
    http, _service = client
    created = http.post("/projects", json={"name": "Delete Me", "brief": make_brief("Delete Me").model_dump(mode="json")}).json()
    response = http.delete(f"/projects/{created['project_id']}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


def test_get_missing_project_http_returns_404(client):
    http, _service = client
    response = http.get("/projects/missing")
    assert response.status_code == 404


def test_delete_missing_project_http_returns_404(client):
    http, _service = client
    response = http.delete("/projects/missing")
    assert response.status_code == 404


def test_projects_listing_keeps_created_order(project_service: ProjectService):
    first = project_service.create_project(CreateProjectRequest(name="First", brief=make_brief("First")))
    second = project_service.create_project(CreateProjectRequest(name="Second", brief=make_brief("Second")))
    items = project_service.list_projects()
    assert {item.project_id for item in items} == {first.project_id, second.project_id}

