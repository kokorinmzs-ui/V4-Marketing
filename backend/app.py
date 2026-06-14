"""FastAPI application entrypoint for Marketing OS v4."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.routers.artifacts import router as artifacts_router
from backend.routers.brief import router as brief_router
from backend.routers.generation import router as generation_router
from backend.routers.health import router as health_router
from backend.routers.projects import router as projects_router
from backend.routers.review import router as review_router

app = FastAPI(title="Marketing OS v4 Backend API", version="24.1.0")

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_APP = ROOT / "frontend" / "app"
FRONTEND_JS = ROOT / "frontend" / "js"
FRONTEND_CSS = ROOT / "frontend" / "css"

app.mount("/js", StaticFiles(directory=FRONTEND_JS), name="js")
app.mount("/css", StaticFiles(directory=FRONTEND_CSS), name="css")

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(brief_router)
app.include_router(generation_router)
app.include_router(review_router)
app.include_router(artifacts_router)


def _read_html(*parts: str) -> str:
    return (FRONTEND_APP.joinpath(*parts)).read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def home_page() -> str:
    return _read_html("page.html")


@app.get("/app/projects", response_class=HTMLResponse, include_in_schema=False)
def projects_page() -> str:
    return _read_html("projects", "page.html")


@app.get("/app/projects/{project_id}", response_class=HTMLResponse, include_in_schema=False)
def project_detail_page(project_id: str) -> str:
    return _read_html("projects", "[id]", "page.html")


@app.get("/app/projects/{project_id}/run", response_class=HTMLResponse, include_in_schema=False)
def project_run_page(project_id: str) -> str:
    return _read_html("projects", "[id]", "run.html")


@app.get("/app/brief/new", response_class=HTMLResponse, include_in_schema=False)
def brief_new_page() -> str:
    return _read_html("brief", "new", "page.html")


@app.get("/app/brief/upload", response_class=HTMLResponse, include_in_schema=False)
def brief_upload_page() -> str:
    return _read_html("brief", "upload", "page.html")


@app.get("/app/brief/template", response_class=HTMLResponse, include_in_schema=False)
def brief_template_page() -> str:
    return _read_html("brief", "template", "page.html")


@app.get("/app/projects/{project_id}/brief", response_class=HTMLResponse, include_in_schema=False)
def project_brief_page(project_id: str) -> str:
    return _read_html("projects", "[id]", "brief", "page.html")


@app.get("/app/projects/{project_id}/analysis", response_class=HTMLResponse, include_in_schema=False)
def project_analysis_page(project_id: str) -> str:
    return _read_html("projects", "[id]", "analysis", "page.html")


@app.get("/app/projects/{project_id}/planning", response_class=HTMLResponse, include_in_schema=False)
def project_planning_page(project_id: str) -> str:
    return _read_html("projects", "[id]", "planning", "page.html")


@app.get("/app/projects/{project_id}/review", response_class=HTMLResponse, include_in_schema=False)
def project_review_page(project_id: str) -> str:
    return _read_html("projects", "[id]", "review", "page.html")


@app.get("/app/projects/{project_id}/delivery", response_class=HTMLResponse, include_in_schema=False)
def project_delivery_page(project_id: str) -> str:
    return _read_html("projects", "[id]", "delivery", "page.html")


@app.get("/app/projects/{project_id}/artifacts", response_class=HTMLResponse, include_in_schema=False)
def project_artifacts_page(project_id: str) -> str:
    return _read_html("projects", "[id]", "artifacts", "page.html")
