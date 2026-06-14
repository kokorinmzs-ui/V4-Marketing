"""FastAPI application entrypoint for Sprint 15 backend API."""

from __future__ import annotations

from fastapi import FastAPI

from backend.routers.artifacts import router as artifacts_router
from backend.routers.generation import router as generation_router
from backend.routers.health import router as health_router
from backend.routers.projects import router as projects_router
from backend.routers.review import router as review_router


app = FastAPI(title="Marketing OS v4 Backend API", version="15.0.0")

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(generation_router)
app.include_router(artifacts_router)
app.include_router(review_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "Marketing OS v4 Backend API"}

