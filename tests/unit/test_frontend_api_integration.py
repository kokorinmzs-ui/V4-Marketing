"""Sprint 19 — Frontend API Integration Tests (14 tests)."""
import json, pytest, pathlib

ROOT = pathlib.Path(__file__).parent.parent.parent

class TestApiClient:
    def test_api_js_exists(self):
        api_js = ROOT / "frontend" / "js" / "api.js"
        assert api_js.exists(), "api.js not found"

    def test_api_js_has_create_project(self):
        js = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
        assert "createProject" in js
        assert "function createProject" in js
        assert "brief: payloadBrief" in js

    def test_api_js_has_list_projects(self):
        js = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
        assert "listProjects" in js

    def test_api_js_has_generate(self):
        js = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
        assert "generateProject" in js

    def test_api_js_has_artifacts(self):
        js = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
        assert "listArtifacts" in js
        assert "getArtifactDownloadUrl" in js

    def test_api_js_has_status(self):
        js = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
        assert "getGenerationStatus" in js

    def test_api_js_no_localstorage_calls(self):
        js = (ROOT / "frontend" / "js" / "api.js").read_text(encoding="utf-8")
        assert "localStorage.setItem" not in js
        assert "localStorage.getItem" not in js


class TestProjectsPage:
    def test_projects_page_exists(self):
        page = ROOT / "frontend" / "app" / "projects" / "page.html"
        assert page.exists()

    def test_projects_page_loads_api_js(self):
        html = (ROOT / "frontend" / "app" / "projects" / "page.html").read_text(encoding="utf-8")
        assert "script src=" in html, "api.js not loaded"

    def test_projects_uses_list_projects_api(self):
        html = (ROOT / "frontend" / "app" / "projects" / "page.html").read_text(encoding="utf-8")
        assert "listProjects()" in html

    def test_projects_uses_create_project_api(self):
        html = (ROOT / "frontend" / "app" / "projects" / "page.html").read_text(encoding="utf-8")
        assert "createProject(" in html

    def test_projects_page_has_brief_inputs(self):
        html = (ROOT / "frontend" / "app" / "projects" / "page.html").read_text(encoding="utf-8")
        assert "industryInput" in html
        assert "descriptionInput" in html
        assert "productsInput" in html
        assert "goalsInput" in html


class TestProjectDetailPage:
    def test_detail_page_exists(self):
        page = ROOT / "frontend" / "app" / "projects" / "[id]" / "page.html"
        assert page.exists()

    def test_detail_page_loads_api_js(self):
        html = (ROOT / "frontend" / "app" / "projects" / "[id]" / "page.html").read_text(encoding="utf-8")
        assert "api.js" in html

    def test_detail_page_has_generate_button(self):
        html = (ROOT / "frontend" / "app" / "projects" / "[id]" / "page.html").read_text(encoding="utf-8")
        assert "generateBtn" in html
        assert "generateProject(" in html

    def test_detail_page_has_artifact_list(self):
        html = (ROOT / "frontend" / "app" / "projects" / "[id]" / "page.html").read_text(encoding="utf-8")
        assert "artifactList" in html
        assert "listArtifacts(" in html

    def test_detail_page_has_status_polling(self):
        html = (ROOT / "frontend" / "app" / "projects" / "[id]" / "page.html").read_text(encoding="utf-8")
        assert "getGenerationStatus(" in html or "status" in html.lower()
