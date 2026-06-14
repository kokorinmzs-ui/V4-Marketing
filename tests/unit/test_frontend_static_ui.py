"""Static frontend proof tests for Sprint 14-A."""

from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
AUDIT = ROOT / "audit"

HOME = FRONTEND / "app" / "page.html"
PROJECTS = FRONTEND / "app" / "projects" / "page.html"
DETAIL = FRONTEND / "app" / "projects" / "[id]" / "page.html"
SMOKE = AUDIT / "frontend_smoke_test.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(path: Path, *needles: str) -> None:
    text = read(path)
    for needle in needles:
        assert needle in text, f"{path} is missing {needle!r}"


def assert_not_contains(path: Path, *needles: str) -> None:
    text = read(path)
    for needle in needles:
        assert needle not in text, f"{path} unexpectedly contains {needle!r}"


# A. Files
def test_home_page_exists():
    assert HOME.exists()


def test_projects_page_exists():
    assert PROJECTS.exists()


def test_project_detail_page_exists():
    assert DETAIL.exists()


def test_frontend_smoke_report_exists():
    assert SMOKE.exists()


# B. Home
def test_home_contains_marketing_os_title():
    assert_contains(HOME, "Marketing OS v4")


def test_home_contains_projects_link():
    assert_contains(HOME, 'href="/projects"')


def test_home_has_no_login_form():
    assert_not_contains(HOME, "login", "sign in", "password")


def test_home_has_no_payment_text():
    assert_not_contains(HOME, "payment", "checkout", "subscribe", "billing")


# C. Projects
def test_projects_contains_create_project_ui():
    assert_contains(PROJECTS, "Create Project", "projectNameInput", "createBtn")


def test_projects_contains_project_name_input():
    assert_contains(PROJECTS, 'id="projectNameInput"', 'placeholder="Enter project name..."')


def test_projects_contains_project_list_container():
    assert_contains(PROJECTS, 'id="projectsList"')


def test_projects_contains_create_button():
    assert_contains(PROJECTS, 'id="createBtn"', "Create Project")


def test_projects_uses_localstorage():
    assert_contains(PROJECTS, "localStorage", 'mo_projects')


def test_projects_has_navigation_to_detail_page():
    assert_contains(PROJECTS, '<a href="/projects/', "p.id")


# D. Detail
def test_detail_contains_brief_form():
    assert_contains(DETAIL, 'id="briefForm"')


def test_detail_contains_required_project_name_field():
    assert_contains(DETAIL, 'id="project_name"', "required")


def test_detail_contains_required_industry_field():
    assert_contains(DETAIL, 'id="industry"', "required")


def test_detail_contains_required_business_description_field():
    assert_contains(DETAIL, 'id="business_description"', "required")


def test_detail_contains_required_products_field():
    assert_contains(DETAIL, 'id="products"', "required")


def test_detail_contains_required_goals_field():
    assert_contains(DETAIL, 'id="goals"', "required")


def test_detail_contains_generate_button():
    assert_contains(DETAIL, 'id="generateBtn"', "Run Generation")


def test_detail_contains_progress_bar():
    assert_contains(DETAIL, 'class="progress-bar"')


def test_detail_contains_progress_fill():
    assert_contains(DETAIL, 'id="progressFill"')


def test_detail_contains_generation_status():
    assert_contains(DETAIL, "Generating...", "completed", "draft")


def test_detail_contains_artifact_list():
    assert_contains(DETAIL, 'id="artifactList"')


def test_detail_contains_download_zip_action():
    assert_contains(DETAIL, "client-package.zip", "Download")


def test_detail_contains_dashboard_preview_action():
    assert_contains(DETAIL, "dashboard.html", "View")


# E. Artifact proof
def test_detail_contains_client_package_zip():
    assert_contains(DETAIL, "client-package.zip")


def test_detail_contains_dashboard_html():
    assert_contains(DETAIL, "dashboard.html")


def test_detail_contains_final_data_json():
    assert_contains(DETAIL, "final_data.json")


def test_detail_contains_execution_view_model_json():
    assert_contains(DETAIL, "execution_view_model.json")


# F. Architecture
def test_no_auth_strings_in_frontend():
    assert_not_contains(HOME, "auth", "login", "signup")
    assert_not_contains(PROJECTS, "auth", "login", "signup")
    assert_not_contains(DETAIL, "auth", "login", "signup")


def test_no_payment_strings_in_frontend():
    assert_not_contains(HOME, "payment", "billing", "checkout")
    assert_not_contains(PROJECTS, "payment", "billing", "checkout")
    assert_not_contains(DETAIL, "payment", "billing", "checkout")


def test_no_backend_api_dependency():
    assert_not_contains(HOME, "/api/", "fetch(", "axios", "backend")
    assert_not_contains(PROJECTS, "/api/", "fetch(", "axios", "backend")
    assert_not_contains(DETAIL, "/api/", "fetch(", "axios", "backend")


def test_mock_generation_is_explicitly_marked():
    assert_contains(DETAIL, "Mock generation is enabled for Sprint 14-A")
    assert "Mock project service" in read(ROOT / "frontend" / "services" / "projectService.ts")
    assert "Mock artifact service" in read(ROOT / "frontend" / "services" / "artifactService.ts")


# G. Smoke report
def test_smoke_report_mentions_home_page():
    assert_contains(SMOKE, "Home Page", "frontend/app/page.html")


def test_smoke_report_mentions_projects_page():
    assert_contains(SMOKE, "Projects Page", "frontend/app/projects/page.html")


def test_smoke_report_mentions_project_detail_page():
    assert_contains(SMOKE, "Project Detail Page", "frontend/app/projects/[id]/page.html")


def test_smoke_report_mentions_artifacts():
    assert_contains(SMOKE, "client-package.zip", "dashboard.html", "final_data.json", "execution_view_model.json")


def test_smoke_report_mentions_mock_generation():
    assert_contains(SMOKE, "Mock generation", "Mock generation flow", "mock generation")


# Extra proof
def test_frontend_file_count():
    assert len(list(FRONTEND.rglob("*"))) >= 10


def test_frontend_pages_are_static_html():
    assert HOME.suffix == ".html"
    assert PROJECTS.suffix == ".html"
    assert DETAIL.suffix == ".html"


def test_project_detail_has_project_id_logic():
    assert_contains(DETAIL, "projectId", "window.location.pathname")


def test_project_detail_has_render_artifacts():
    assert_contains(DETAIL, "renderArtifacts", "artifactList")


def test_project_store_exists():
    assert (FRONTEND / "store" / "projectStore.ts").exists()


def test_generation_store_exists():
    assert (FRONTEND / "store" / "generationStore.ts").exists()


def test_artifact_service_exists():
    assert (FRONTEND / "services" / "artifactService.ts").exists()


def test_project_service_exists():
    assert (FRONTEND / "services" / "projectService.ts").exists()


def test_types_exist():
    assert (FRONTEND / "types" / "project.ts").exists()
    assert (FRONTEND / "types" / "artifact.ts").exists()
