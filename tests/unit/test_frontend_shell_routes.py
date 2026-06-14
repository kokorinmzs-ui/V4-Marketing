"""Smoke tests for the restored frontend shell."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import app


ROOT = Path(__file__).resolve().parents[2]
client = TestClient(app)


class TestShellRoutes:
    def test_home_route(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Главный экран оператора" in response.text

    def test_projects_route(self):
        response = client.get("/app/projects")
        assert response.status_code == 200
        assert "Проекты" in response.text

    def test_workspace_route(self):
        response = client.get("/app/projects/demo")
        assert response.status_code == 200
        assert "Project workspace" in response.text or "workspace" in response.text.lower()

    def test_run_route(self):
        response = client.get("/app/projects/demo/run")
        assert response.status_code == 200
        assert "Проработка проекта" in response.text

    def test_brief_routes(self):
        assert client.get("/app/brief/new").status_code == 200
        assert client.get("/app/brief/upload").status_code == 200
        assert client.get("/app/brief/template").status_code == 200

    def test_stage_routes(self):
        assert client.get("/app/projects/demo/brief").status_code == 200
        assert client.get("/app/projects/demo/analysis").status_code == 200
        assert client.get("/app/projects/demo/planning").status_code == 200
        assert client.get("/app/projects/demo/review").status_code == 200
        assert client.get("/app/projects/demo/delivery").status_code == 200
        assert client.get("/app/projects/demo/artifacts").status_code == 200

    def test_css_served(self):
        response = client.get("/css/styles.css")
        assert response.status_code == 200
        assert ".app-shell" in response.text

    def test_js_served(self):
        response = client.get("/js/api.js")
        assert response.status_code == 200
        assert "function createProject" in response.text


class TestShellFiles:
    def test_home_file_exists(self):
        assert (ROOT / "frontend" / "app" / "page.html").exists()

    def test_projects_file_exists(self):
        assert (ROOT / "frontend" / "app" / "projects" / "page.html").exists()

    def test_workspace_file_exists(self):
        assert (ROOT / "frontend" / "app" / "projects" / "[id]" / "page.html").exists()

    def test_run_file_exists(self):
        assert (ROOT / "frontend" / "app" / "projects" / "[id]" / "run.html").exists()

    def test_all_html_pages_include_css_and_js(self):
        html_files = [
            ROOT / "frontend" / "app" / "page.html",
            ROOT / "frontend" / "app" / "projects" / "page.html",
            ROOT / "frontend" / "app" / "projects" / "[id]" / "page.html",
            ROOT / "frontend" / "app" / "projects" / "[id]" / "run.html",
            ROOT / "frontend" / "app" / "brief" / "new" / "page.html",
            ROOT / "frontend" / "app" / "brief" / "upload" / "page.html",
            ROOT / "frontend" / "app" / "brief" / "template" / "page.html",
            ROOT / "frontend" / "app" / "projects" / "[id]" / "brief" / "page.html",
            ROOT / "frontend" / "app" / "projects" / "[id]" / "analysis" / "page.html",
            ROOT / "frontend" / "app" / "projects" / "[id]" / "planning" / "page.html",
            ROOT / "frontend" / "app" / "projects" / "[id]" / "review" / "page.html",
            ROOT / "frontend" / "app" / "projects" / "[id]" / "delivery" / "page.html",
            ROOT / "frontend" / "app" / "projects" / "[id]" / "artifacts" / "page.html",
        ]

        for path in html_files:
            text = path.read_text(encoding="utf-8")
            assert '/css/styles.css' in text
            assert '/js/api.js' in text
