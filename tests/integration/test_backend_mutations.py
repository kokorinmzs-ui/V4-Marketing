"""Mutation-proof integration tests for the Sprint 15 backend API."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.dependencies import get_artifact_service, get_generation_service, get_project_service
from backend.services.artifact_service import ArtifactService
from backend.services.generation_service import GenerationService
from backend.services.project_service import ProjectService
from shared.schemas.brief import Brief


def make_brief(name: str = "Mutation Project") -> Brief:
    return Brief(
        project_name=name,
        industry="photography_studio",
        business_description="Mutation test brief",
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
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_mutation_a_create_project_requires_brief(client):
    response = client.post("/projects", json={"name": "Broken"})
    assert response.status_code == 422


def test_mutation_b_status_missing_project_returns_404(client):
    response = client.get("/projects/missing/status")
    assert response.status_code == 404


def test_mutation_c_artifacts_missing_project_returns_404(client):
    response = client.get("/projects/missing/artifacts")
    assert response.status_code == 404


def test_mutation_d_download_path_escape_rejected(client):
    created = client.post("/projects", json={"name": "Escape", "brief": make_brief("Escape").model_dump(mode="json")})
    assert created.status_code == 201
    project_id = created.json()["project_id"]
    response = client.get(f"/projects/{project_id}/download/../secret.txt")
    assert response.status_code in {400, 404}


def test_mutation_e_generate_missing_project_returns_404(client):
    response = client.post("/projects/missing/generate")
    assert response.status_code == 404
