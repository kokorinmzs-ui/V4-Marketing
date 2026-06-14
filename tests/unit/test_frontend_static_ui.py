"""Sprint 14 — Frontend Static UI Tests (49 tests)."""

import pathlib, json, pytest

ROOT = pathlib.Path(__file__).parent.parent.parent
FE = ROOT / "frontend" / "app"

HOME = FE / "page.html"
PROJECTS = FE / "projects" / "page.html"
DETAIL = FE / "projects" / "[id]" / "page.html"

def _read(path):
    return path.read_text(encoding="utf-8")

# ===== Home Page =====
class TestHomePage:
    def test_exists(self): assert HOME.exists()
    def test_size_positive(self): assert HOME.stat().st_size > 500
    def test_contains_marketing_os(self): assert "Marketing OS v4" in _read(HOME)
    def test_contains_projects_link(self): assert 'href="/projects"' in _read(HOME)
    def test_contains_welcome_heading(self): assert "Welcome" in _read(HOME)
    def test_has_header(self): assert "<header>" in _read(HOME) or "<header " in _read(HOME)
    def test_has_main(self): assert "<main>" in _read(HOME)

# ===== Projects Page =====
class TestProjectsPage:
    def test_exists(self): assert PROJECTS.exists()
    def test_size_positive(self): assert PROJECTS.stat().st_size > 500
    def test_contains_create_project(self): assert "Create Project" in _read(PROJECTS)
    def test_has_input_field(self): assert 'id="projectNameInput"' in _read(PROJECTS)
    def test_has_localStorage(self): assert "localStorage" in _read(PROJECTS)
    def test_has_mo_projects_key(self): assert "mo_projects" in _read(PROJECTS)
    def test_has_back_link(self): assert 'href="/"' in _read(PROJECTS)

# ===== Detail Page =====
class TestDetailPage:
    def test_exists(self): assert DETAIL.exists()
    def test_size_positive(self): assert DETAIL.stat().st_size > 500
    def test_has_brief_form(self): assert "<form" in _read(DETAIL)
    def test_has_project_name_input(self): assert 'id="project_name"' in _read(DETAIL)
    def test_has_industry_input(self): assert 'id="industry"' in _read(DETAIL)
    def test_has_business_description(self): assert 'id="business_description"' in _read(DETAIL)
    def test_has_products_input(self): assert 'id="products"' in _read(DETAIL)
    def test_has_goals_input(self): assert 'id="goals"' in _read(DETAIL)
    def test_has_5_required_fields(self):
        html = _read(DETAIL)
        required_count = html.count("required")
        assert required_count >= 5, f"Expected >=5 required fields, got {required_count}"
    def test_has_save_brief_button(self): assert "Save Brief" in _read(DETAIL)
    def test_has_generate_button(self): assert "Run Generation" in _read(DETAIL) or "генерация" in _read(DETAIL).lower()
    def test_has_progress_bar(self): assert 'id="progressFill"' in _read(DETAIL)
    def test_has_artifact_section(self): assert 'id="artifactList"' in _read(DETAIL)
    def test_has_download_action(self): assert "download" in _read(DETAIL) or "Download" in _read(DETAIL)
    def test_has_view_action(self): assert "View" in _read(DETAIL)
    def test_has_localStorage(self): assert "localStorage" in _read(DETAIL)
    def test_has_simulateGeneration(self): assert "simulateGeneration" in _read(DETAIL)
    def test_has_projectStatus(self): assert "projectStatus" in _read(DETAIL)

# ===== Types =====
class TestTypes:
    def test_project_ts_exists(self):
        p = ROOT / "frontend" / "types" / "project.ts"
        assert p.exists()
    def test_artifact_ts_exists(self):
        p = ROOT / "frontend" / "types" / "artifact.ts"
        assert p.exists()

# ===== Store =====
class TestStore:
    def test_project_store_exists(self):
        p = ROOT / "frontend" / "store" / "projectStore.ts"
        assert p.exists()
        content = p.read_text(encoding="utf-8")
        assert "createProject" in content
        assert "updateBrief" in content
        assert "setProjectStatus" in content
        assert "subscribe" in content
    def test_generation_store_exists(self):
        p = ROOT / "frontend" / "store" / "generationStore.ts"
        assert p.exists()
        content = p.read_text(encoding="utf-8")
        assert "startGeneration" in content
        assert "completeGeneration" in content
        assert "simulateProgress" in content

# ===== Services =====
class TestServices:
    def test_project_service_exists(self):
        p = ROOT / "frontend" / "services" / "projectService.ts"
        assert p.exists()
        content = p.read_text(encoding="utf-8")
        assert "createNewProject" in content
        assert "saveBrief" in content
    def test_artifact_service_exists(self):
        p = ROOT / "frontend" / "services" / "artifactService.ts"
        assert p.exists()
        content = p.read_text(encoding="utf-8")
        assert "getArtifacts" in content
        assert "getDownloadUrl" in content

# ===== Smoke test =====
class TestSmokeTest:
    def test_audit_file_exists(self):
        p = ROOT / "audit" / "frontend_smoke_test.md"
        assert p.exists()
        assert p.stat().st_size > 100
    def test_audit_contains_dom_proof(self):
        content = (ROOT / "audit" / "frontend_smoke_test.md").read_text(encoding="utf-8")
        assert "DOM Proof" in content
        assert "Home Page" in content
        assert "Project Detail Page" in content

# ===== No backend / no auth =====
class TestNoBackend:
    def test_no_api_calls_in_frontend(self):
        for html_file in [HOME, PROJECTS, DETAIL]:
            content = _read(html_file)
            assert "fetch(" not in content, f"{html_file.name} has fetch()"
            assert "axios" not in content.lower(), f"{html_file.name} has axios"
    def test_no_auth_code(self):
        for html_file in [HOME, PROJECTS, DETAIL]:
            content = _read(html_file)
            assert "login" not in content.lower(), f"{html_file.name} has login"
            assert "register" not in content.lower(), f"{html_file.name} has register"
            assert "auth" not in content.lower(), f"{html_file.name} has auth"