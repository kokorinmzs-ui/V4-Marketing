"""SSE run stream endpoint tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.dependencies import get_artifact_service, get_generation_service, get_project_service
from backend.services.artifact_service import ArtifactService
from backend.services.generation_service import GenerationService
from backend.services.project_service import ProjectService


@pytest.fixture()
def client(tmp_path: Path):
    project_service = ProjectService(tmp_path / "projects")
    artifact_service = ArtifactService(project_service)
    generation_service = GenerationService(project_service)
    app.dependency_overrides[get_project_service] = lambda: project_service
    app.dependency_overrides[get_artifact_service] = lambda: artifact_service
    app.dependency_overrides[get_generation_service] = lambda: generation_service
    try:
        with TestClient(app) as test_client:
            yield test_client, project_service
    finally:
        app.dependency_overrides.clear()


def _prepare_project(test_client: TestClient, project_service: ProjectService) -> str:
    response = test_client.post(
        "/projects",
        json={
            "name": "Stream Project",
            "brief": {
                "project_name": "Stream Project",
                "industry": "photography",
                "business_description": "Studio",
                "products": ["shoot"],
                "goals": ["grow"],
            },
        },
    )
    assert response.status_code == 201
    record = response.json()
    project_service.write_bundle(
        record["project_id"],
        "generation_report.json",
        json.dumps(
            {
                "project_id": record["project_id"],
                "status": "review_required",
                "llm_summary": {
                    "mode": "replay",
                    "input_tokens": 10,
                    "output_tokens": 20,
                    "cost": 0.001,
                },
                "review": {"status": "review_required", "notes": ["Replay mode"]},
                "block_results": [
                    {
                        "block_id": "01_market_analysis",
                        "block_name": "Market analysis",
                        "status": "passed",
                        "preview": "Market overview ready",
                        "provider_used": "deepseek",
                        "model_used": "deepseek-chat",
                        "elapsed_seconds": 0.2,
                        "repaired": False,
                    },
                    {
                        "block_id": "04_platform",
                        "block_name": "Platform",
                        "status": "normalized",
                        "preview": "Positioning normalized",
                        "provider_used": "deepseek",
                        "model_used": "deepseek-chat",
                        "elapsed_seconds": 0.3,
                        "repaired": True,
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
    )
    return record["project_id"]


def test_run_stream_replay_endpoint_returns_sse(client):
    test_client, project_service = client
    project_id = _prepare_project(test_client, project_service)

    with test_client.stream("GET", f"/projects/{project_id}/run/stream?mode=replay") as response:
        body = "".join(chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk for chunk in response.iter_bytes())

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "").lower()
    assert "event: run_start" in body
    assert "event: block_start" in body
    assert "event: block_update" in body
    assert "event: block_normalized" in body
    assert "event: run_complete" in body


def test_run_stream_mock_mode_returns_mock_events(client):
    test_client, project_service = client
    project_id = _prepare_project(test_client, project_service)

    with test_client.stream("GET", f"/projects/{project_id}/run/stream?mode=mock") as response:
        body = "".join(chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk for chunk in response.iter_bytes())

    assert response.status_code == 200
    assert "event: run_start" in body
    assert '"run_mode": "mock"' in body
    assert "event: run_complete" in body
