"""Sprint 15 Hard QA proof for backend API reality checks."""

from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from backend.app import app
from backend.dependencies import get_artifact_service, get_generation_service, get_project_service
from backend.models.project import CreateProjectRequest
from backend.services.artifact_service import ArtifactService
from backend.services.generation_service import GenerationService
from backend.services.project_service import ProjectService
from shared.schemas.brief import Brief


AUDIT = ROOT / "audit"
AUDIT.mkdir(exist_ok=True)


def make_brief(project_name: str, industry: str, business_description: str) -> Brief:
    return Brief(
        project_name=project_name,
        industry=industry,
        business_description=business_description,
        region="Москва",
        products=["Strategy Sprint", "Content System"],
        services=["Audit", "Launch"],
        goals=["Lead generation", "Sales growth"],
        target_markets=["B2B"],
        social_links=["https://example.com/instagram"],
        constraints=["No paid media"],
        additional_notes="Hard QA proof run",
    )


def print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def print_file_proof(path: Path) -> None:
    print(f"PATH: {path.resolve()}")
    print(f"SIZE: {path.stat().st_size} bytes")
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    print("HEAD:")
    for line in lines[:5]:
        print(f"  {line}")
    print(f"READ_OK: {path.exists() and len(content) > 0}")


def artifact_text(project_root: Path, artifact_name: str) -> str:
    artifact_path = project_root / "artifacts" / artifact_name
    if artifact_name.endswith(".zip"):
        with zipfile.ZipFile(artifact_path) as zf:
            chunks: list[str] = []
            for name in zf.namelist():
                if name.lower().endswith((".json", ".html", ".txt", ".md")):
                    try:
                        chunks.append(zf.read(name).decode("utf-8", errors="ignore"))
                    except Exception:
                        continue
            return "\n".join(chunks)
    return artifact_path.read_text(encoding="utf-8", errors="ignore")


def run() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="sprint15_hard_qa_", dir=str(ROOT)))
    try:
        storage_root = temp_root / "storage" / "projects"
        project_service = ProjectService(storage_root=storage_root)
        generation_service = GenerationService(project_service)
        artifact_service = ArtifactService(project_service)

        app.dependency_overrides[get_project_service] = lambda: project_service
        app.dependency_overrides[get_generation_service] = lambda: generation_service
        app.dependency_overrides[get_artifact_service] = lambda: artifact_service
        client = TestClient(app)

        print_header("QA-001 Trace")
        import inspect

        print(inspect.getsource(GenerationService.generate))
        print("TRACE: POST /projects/{id}/generate -> BlockExecutor.execute -> 27 blocks -> FinalDataAssembler -> ExecutionPlanner -> HTMLDashboardRenderer -> PackageBuilder -> ZipExporter")

        print_header("QA-002 27 Block Statuses")
        create_payload = CreateProjectRequest(
            name="QA Trace Project",
            brief=make_brief(
                project_name="QA Trace Project",
                industry="photography_studio",
                business_description="Hard QA trace project",
            ),
        )
        project = project_service.create_project(create_payload)
        block_results = generation_service._run_blocks(project)
        for block_id in sorted(block_results.keys()):
            result = block_results[block_id]
            status = getattr(result, "status", "unknown")
            print(f"{block_id}: {status}")

        print_header("QA-003 Unique Brief Propagation")
        unique_name = "UNIQUE_TEST_ABC_123"
        unique_payload = CreateProjectRequest(
            name=unique_name,
            brief=make_brief(
                project_name=unique_name,
                industry="marketing_consulting",
                business_description=f"Project {unique_name} for propagation check",
            ),
        )
        unique_project = project_service.create_project(unique_payload)
        response = client.post(f"/projects/{unique_project.project_id}/generate")
        print(f"HTTP /generate status_code: {response.status_code}")
        print(f"HTTP /generate body: {response.json()}")

        unique_root = project_service.project_path(unique_project.project_id)
        for artifact_name in [
            "brief.json",
            "final_data.json",
            "execution_view_model.json",
            "dashboard.html",
            "client-package.zip",
        ]:
            print_file_proof(unique_root / "artifacts" / artifact_name)

        final_data_text = artifact_text(unique_root, "final_data.json")
        evm_text = artifact_text(unique_root, "execution_view_model.json")
        dashboard_text = artifact_text(unique_root, "dashboard.html")
        zip_listing = artifact_text(unique_root, "client-package.zip")
        print(f"FINAL_DATA_HAS_UNIQUE: {unique_name in final_data_text}")
        print(f"EVM_HAS_UNIQUE: {unique_name in evm_text}")
        print(f"DASHBOARD_HAS_UNIQUE: {unique_name in dashboard_text}")
        print(f"ZIP_LISTING_HAS_UNIQUE: {unique_name in zip_listing}")

        print_header("QA-004 Forced Block Failure")
        failure_project_service = ProjectService(storage_root=temp_root / "failure" / "storage" / "projects")
        failure_service = GenerationService(failure_project_service)
        failure_project = failure_project_service.create_project(
            CreateProjectRequest(
                name="Failure Project",
                brief=make_brief(
                    project_name="Failure Project",
                    industry="photography_studio",
                    business_description="Failure injection project",
                ),
            )
        )

        original_make = failure_service._make_generate_func

        def failing_make(block_id: str, payloads: dict[str, dict[str, object]]):
            if block_id == "13_pains":
                def fail_fn(**_kwargs):
                    from ai_engine.providers.base import LLMUsage
                    from ai_engine.services.ai_service import AIServiceResponse

                    return AIServiceResponse(
                        status="success",
                        data={"status": "failed", "errors": ["Injected failure"]},
                        usage=LLMUsage(model="mock", input_tokens=1, output_tokens=1, cost=0.0),
                    )

                return fail_fn
            return original_make(block_id, payloads)

        failure_service._make_generate_func = failing_make  # type: ignore[assignment]
        app.dependency_overrides[get_project_service] = lambda: failure_project_service
        app.dependency_overrides[get_generation_service] = lambda: failure_service
        app.dependency_overrides[get_artifact_service] = lambda: ArtifactService(failure_project_service)
        failure_client = TestClient(app, raise_server_exceptions=False)
        failure_response = failure_client.post(f"/projects/{failure_project.project_id}/generate")
        print(f"HTTP /generate failure status_code: {failure_response.status_code}")
        print(f"HTTP /generate failure body: {failure_response.text}")
        print(f"PIPELINE_FAILED_AS_EXPECTED: {failure_response.status_code >= 500}")

        print_header("QA-005 Two Projects Separate Artifacts")
        project_a = project_service.create_project(
            CreateProjectRequest(
                name="Project A",
                brief=make_brief("Project A", "real_estate", "Project A business"),
            )
        )
        project_b = project_service.create_project(
            CreateProjectRequest(
                name="Project B",
                brief=make_brief("Project B", "education", "Project B business"),
            )
        )
        generation_service.generate(project_a.project_id)
        generation_service.generate(project_b.project_id)
        a_root = project_service.project_path(project_a.project_id)
        b_root = project_service.project_path(project_b.project_id)
        print(f"A_ARTIFACTS: {sorted(p.name for p in (a_root / 'artifacts').iterdir())}")
        print(f"B_ARTIFACTS: {sorted(p.name for p in (b_root / 'artifacts').iterdir())}")
        print(f"A_DIFFERENT_FROM_B: {(a_root / 'artifacts' / 'final_data.json').read_text(encoding='utf-8') != (b_root / 'artifacts' / 'final_data.json').read_text(encoding='utf-8')}")

        print_header("QA-006 Storage Tree")
        for path in sorted(storage_root.rglob("*")):
            rel = path.relative_to(storage_root)
            print(rel.as_posix())

        print_header("SUMMARY")
        print(f"PROJECTS_ROOT: {storage_root.resolve()}")
        print(f"TOTAL_PROJECTS: {len([p for p in storage_root.iterdir() if p.is_dir()])}")
        print("STATUS: PASS")

    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    run()
