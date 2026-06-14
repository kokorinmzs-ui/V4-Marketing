from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_engine.services.ai_service import AIServiceResponse
from scripts.live_ai_smoke import run_smoke


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_env_missing_does_not_fail(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PIPELINE_LLM_MODE", raising=False)
    report = run_smoke(tmp_path)
    assert report["live_ready"] is False
    assert report["reason"] == "no_api_keys"
    assert report["provider_used"] == "mock"
    assert (tmp_path / "live_ai_smoke_report.json").exists()
    assert (tmp_path / "live_ai_smoke_report.md").exists()


def test_report_created_in_mock_fallback_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    report = run_smoke(tmp_path)
    data = _read_json(tmp_path / "live_ai_smoke_report.json")
    assert data["status"] == "no_api_keys"
    assert data["provider_used"] == "mock"
    assert report["live_ready"] is False


def test_mock_mode_is_explicitly_marked(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("PIPELINE_LLM_MODE", "deterministic")
    report = run_smoke(tmp_path)
    assert report["provider_used"] == "mock"
    assert report["model_used"] == "mock"


def test_live_mode_requires_provider_and_model(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("PRIMARY_LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("FALLBACK_LLM_PROVIDER", "openai")

    import scripts.live_ai_smoke as smoke_module

    monkeypatch.setattr(
        smoke_module.AIService,
        "generate",
        lambda self, system_prompt, user_prompt="", json_schema=None: AIServiceResponse(
            status="success",
            data={"status": "ok"},
            provider_used="deepseek",
            model_used="deepseek-chat",
        ),
    )

    report = run_smoke(tmp_path)
    assert report["live_ready"] is True
    assert report["provider_used"] == "deepseek"
    assert report["model_used"] == "deepseek-chat"
    data = _read_json(tmp_path / "live_ai_smoke_report.json")
    assert data["provider_used"] == "deepseek"
    assert data["model_used"] == "deepseek-chat"
