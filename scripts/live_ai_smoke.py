"""Lightweight live AI smoke check.

Checks env wiring and, when API keys are available, performs a single
small AIService call to confirm a real provider returns structured JSON.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_engine.services.ai_service import AIService, AIServiceConfig  # noqa: E402

AUDIT = ROOT / "audit"


def _env_flag(name: str) -> bool:
    return bool((os.getenv(name) or "").strip())


def _build_report() -> dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "env": {
            "PIPELINE_LLM_MODE": os.getenv("PIPELINE_LLM_MODE", ""),
            "PRIMARY_LLM_PROVIDER": os.getenv("PRIMARY_LLM_PROVIDER", ""),
            "FALLBACK_LLM_PROVIDER": os.getenv("FALLBACK_LLM_PROVIDER", ""),
            "DEEPSEEK_API_KEY_exists": _env_flag("DEEPSEEK_API_KEY"),
            "OPENAI_API_KEY_exists": _env_flag("OPENAI_API_KEY"),
        },
        "live_ready": False,
        "reason": "",
        "status": "pending",
        "provider_used": "mock",
        "model_used": "mock",
        "tokens": {"input": 0, "output": 0, "total": 0},
        "cost": 0.0,
        "response": {},
    }


def run_smoke(audit_dir: Path | None = None) -> dict[str, Any]:
    audit_root = Path(audit_dir) if audit_dir else AUDIT
    audit_root.mkdir(parents=True, exist_ok=True)

    report = _build_report()
    has_keys = report["env"]["DEEPSEEK_API_KEY_exists"] or report["env"]["OPENAI_API_KEY_exists"]
    if not has_keys:
        report["live_ready"] = False
        report["reason"] = "no_api_keys"
        report["status"] = "no_api_keys"
        _write_reports(audit_root, report)
        return report

    config = AIServiceConfig()
    service = AIService(config)
    result = service.generate(
        system_prompt=(
            "You are a strict marketing-and-architecture assistant. "
            "Return only valid JSON for a tiny smoke test."
        ),
        user_prompt=(
            "Return a minimal JSON object with keys status, provider_used, "
            "model_used, tokens, cost, and a short note."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "provider_used": {"type": "string"},
                "model_used": {"type": "string"},
                "tokens": {"type": "object"},
                "cost": {"type": "number"},
                "note": {"type": "string"},
            },
            "required": ["status", "provider_used", "model_used", "tokens", "cost"],
        },
    )

    if result.status != "success":
        report["live_ready"] = False
        report["reason"] = result.error or "ai_service_error"
        report["status"] = "error"
        report["provider_used"] = result.provider_used or "mock"
        report["model_used"] = result.model_used or "mock"
        _write_reports(audit_root, report)
        return report

    report["live_ready"] = True
    report["reason"] = "ok"
    report["status"] = "ok"
    report["provider_used"] = result.provider_used or config.primary_provider
    report["model_used"] = result.model_used or config.deepseek_model or config.openai_model
    report["tokens"] = {
        "input": result.usage.input_tokens,
        "output": result.usage.output_tokens,
        "total": result.usage.total_tokens(),
    }
    report["cost"] = result.usage.cost
    report["response"] = {
        "status": "ok",
        "provider_used": report["provider_used"],
        "model_used": report["model_used"],
    }
    _write_reports(audit_root, report)
    return report


def _write_reports(audit_root: Path, report: dict[str, Any]) -> None:
    json_path = audit_root / "live_ai_smoke_report.json"
    md_path = audit_root / "live_ai_smoke_report.md"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Live AI Smoke Report",
        "",
        f"- live_ready: {str(report['live_ready']).lower()}",
        f"- status: {report['status']}",
        f"- reason: {report['reason']}",
        f"- provider_used: {report['provider_used']}",
        f"- model_used: {report['model_used']}",
        f"- input_tokens: {report['tokens']['input']}",
        f"- output_tokens: {report['tokens']['output']}",
        f"- total_tokens: {report['tokens']['total']}",
        f"- cost: {report['cost']}",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    report = run_smoke()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
