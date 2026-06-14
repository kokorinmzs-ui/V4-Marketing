"""Sprint 16 — Golden Briefs Audit: run 10 briefs through the backend pipeline."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import sys
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(ROOT))

from backend.models.project import CreateProjectRequest
from backend.services.generation_service import GenerationService
from backend.services.project_service import ProjectService
from shared.schemas.brief import Brief


AUDIT = ROOT / "audit"
AUDIT.mkdir(exist_ok=True)
BRIEFS_DIR = ROOT / "tests" / "golden" / "briefs"
BRIEF_FILES = sorted(f for f in BRIEFS_DIR.glob("*.json"))


def print_line(message: str) -> None:
    print(message)


def normalize_brief_payload(payload: dict[str, object]) -> dict[str, object]:
    normalized = dict(payload)
    products = normalized.get("products")
    if isinstance(products, str):
        normalized["products"] = [item.strip() for item in products.split(",") if item.strip()]

    goals = normalized.get("goals")
    if isinstance(goals, str):
        normalized["goals"] = [item.strip() for item in goals.split(",") if item.strip()]

    budget = normalized.get("budget")
    if isinstance(budget, str):
        digits = "".join(ch for ch in budget if ch.isdigit())
        normalized["budget"] = {"amount": int(digits) if digits else 0}

    return normalized


temp_root = Path(tempfile.mkdtemp(prefix="sprint16_golden_", dir=str(ROOT)))
project_service = ProjectService(temp_root / "storage" / "projects")
generation_service = GenerationService(project_service)

results: list[dict[str, object]] = []

try:
    for brief_path in BRIEF_FILES:
        t0 = time.perf_counter()
        brief_data = json.loads(brief_path.read_text(encoding="utf-8"))
        brief_data = normalize_brief_payload(brief_data)
        brief = Brief.model_validate(brief_data)
        project = project_service.create_project(
            CreateProjectRequest(name=brief.project_name, brief=brief)
        )

        result = generation_service.generate(project.project_id)
        artifacts_dir = project_service.artifacts_path(project.project_id)
        final_data = json.loads((artifacts_dir / "final_data.json").read_text(encoding="utf-8"))
        evm = json.loads((artifacts_dir / "execution_view_model.json").read_text(encoding="utf-8"))
        dashboard = (artifacts_dir / "dashboard.html").read_text(encoding="utf-8")
        zip_bytes = (artifacts_dir / "client-package.zip").read_bytes()
        elapsed = round(time.perf_counter() - t0, 3)

        row = {
            "project_name": brief.project_name,
            "industry": brief.industry,
            "status": result.get("status", "failed"),
            "llm_mode": result.get("llm_summary", {}).get("mode", ""),
            "live_enabled": result.get("llm_summary", {}).get("live_enabled", False),
            "providers": result.get("llm_summary", {}).get("providers", []),
            "models": result.get("llm_summary", {}).get("models", []),
            "final_data_size": len(json.dumps(final_data, ensure_ascii=False)),
            "evm_size": len(json.dumps(evm, ensure_ascii=False)),
            "dashboard_size": len(dashboard.encode("utf-8")),
            "zip_size": len(zip_bytes),
            "missions_count": len(evm.get("missions", [])),
            "content_count": len(evm.get("content_tasks", [])),
            "ads_count": len(evm.get("ads_tasks", [])),
            "sales_count": len(evm.get("sales_tasks", [])),
            "quality_score": final_data.get("quality_control", {}).get("quality_score", 0),
            "warnings": [],
            "time_sec": elapsed,
        }
        results.append(row)
        print_line(
            f"  {brief.project_name}: {row['status']} in {row['time_sec']}s "
            f"(mode={row['llm_mode']}, live={row['live_enabled']}, models={row['models'][:2]})"
        )

    report = {
        "golden_briefs": results,
        "total": len(results),
        "passed": sum(1 for row in results if row["status"] == "completed"),
    }
    (AUDIT / "golden_briefs_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print_line(f"\n✅ audit/golden_briefs_report.json — {report['passed']}/{report['total']} passed")

    md = []
    md.append("# GOLDEN BRIEFS REPORT")
    md.append("")
    md.append("| # | Project | Industry | Status | Missions | Days | Quality | Time |")
    md.append("|---|---------|----------|--------|----------|------|---------|------|")
    for index, row in enumerate(results, 1):
        md.append(
            f"| {index} | {row['project_name']} | {row['industry']} | {row['status']} | "
            f"{row['missions_count']} | 30 | {row['quality_score']} | {row['time_sec']}s |"
        )
    md.append("")
    md.append(f"**Total: {report['passed']}/{report['total']} passed**")
    (AUDIT / "GOLDEN_BRIEFS_REPORT.md").write_text("\n".join(md), encoding="utf-8")
    print_line("✅ audit/GOLDEN_BRIEFS_REPORT.md created")
finally:
    shutil.rmtree(temp_root, ignore_errors=True)
