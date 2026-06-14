"""Live Block 01 — Market Analysis via DeepSeek API."""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
from typing import Any

ROOT = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(ROOT))

ENV_PATH = ROOT / ".env"
if not ENV_PATH.exists():
    print("❌ .env file not found. Copy .env.example → .env and add your API key.")
    sys.exit(1)

for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")

api_key = os.environ.get("DEEPSEEK_API_KEY", "")
if not api_key or api_key == "sk-your-deepseek-key":
    print("❌ DEEPSEEK_API_KEY not set. Edit .env with your real key.")
    sys.exit(1)

from ai_engine.providers.base import ProviderConfig
from ai_engine.providers.deepseek import DeepSeekProvider
from ai_engine.prompts.registry import get_block_prompt
from ai_engine.validators.content_quality import ContentQualityValidator
from ai_engine.validators.schema_validator import SchemaValidator
from ai_engine.validators.stop_words import StopWordsValidator
from shared.schemas.blocks import MarketAnalysis

BRIEF = {
    "project_name": "Фотостудия Воздух",
    "industry": "Фотостудии",
    "business_description": "Аренда фотостудий в Москве. 7 залов, оборудование Profoto, циклорама. Работаем с 2018 года.",
}

STRICT_FIELDS = [
    "market_overview",
    "market_size",
    "seasonality",
    "buying_triggers",
    "buying_barriers",
    "growth_opportunities",
    "channels",
    "risks",
    "confidence",
]


def normalize_market_analysis(payload: Any) -> dict[str, Any]:
    data = payload
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    if not isinstance(data, dict):
        data = {}

    def as_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    confidence = data.get("confidence", "medium")
    if isinstance(confidence, dict):
        confidence = confidence.get("level") or confidence.get("value") or "medium"
    confidence = str(confidence).lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"

    market_overview = data.get("market_overview")
    if not isinstance(market_overview, str):
        market_overview = ""

    market_size = data.get("market_size")
    if isinstance(market_size, dict):
        market_size = market_size.get("summary") or market_size.get("label") or ""
    if not isinstance(market_size, str):
        market_size = ""

    return {
        "market_overview": market_overview,
        "market_size": market_size,
        "seasonality": as_list(data.get("seasonality")),
        "buying_triggers": as_list(data.get("buying_triggers")),
        "buying_barriers": as_list(data.get("buying_barriers")),
        "growth_opportunities": as_list(data.get("growth_opportunities")),
        "channels": as_list(data.get("channels")),
        "risks": as_list(data.get("risks")),
        "confidence": confidence,
    }


print("=" * 60)
print("LIVE BLOCK 01 SMOKE TEST — Market Analysis via DeepSeek")
print("=" * 60)

provider = DeepSeekProvider(
    ProviderConfig(
        api_key=api_key,
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        timeout_seconds=float(os.environ.get("AI_ENGINE_TIMEOUT", "120")),
    )
)
print("✅ Provider: DeepSeek")
print(f"   Model: {os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')}")

prompt = get_block_prompt("01_market_analysis") or ""
strict_prompt = (
    f"{prompt}\n\n"
    "Return ONLY valid JSON with EXACTLY these keys and types:\n"
    "{\n"
    '  "market_overview": string,\n'
    '  "market_size": string,\n'
    '  "seasonality": string[],\n'
    '  "buying_triggers": string[],\n'
    '  "buying_barriers": string[],\n'
    '  "growth_opportunities": string[],\n'
    '  "channels": string[],\n'
    '  "risks": string[],\n'
    '  "confidence": "high"|"medium"|"low"\n'
    "}\n"
    "Do not add extra keys. Do not nest objects. Do not output markdown."
)
print(f"✅ Prompt: {len(prompt)} chars")

t0 = time.perf_counter()
response = provider.generate(
    system_prompt=strict_prompt,
    user_prompt=f"Analyze this brief and return structured JSON:\n{json.dumps(BRIEF, ensure_ascii=False)}",
    json_schema=MarketAnalysis.model_json_schema(),
)
elapsed = time.perf_counter() - t0

print(f"\n⏱ Generation time: {elapsed:.2f}s")
print(f"   Status: {response.status}")
print(f"   Tokens: {response.usage.input_tokens} in / {response.usage.output_tokens} out")
print(f"   Cost: ${response.usage.cost:.6f}")

raw_data = response.data
normalized_data = normalize_market_analysis(raw_data)

print(f"\n📄 Raw data keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else type(raw_data).__name__}")
print(f"   Normalized keys: {list(normalized_data.keys())}")

schema_validator = SchemaValidator(MarketAnalysis)
schema_result = schema_validator.validate(normalized_data)
stop_words_result = StopWordsValidator().validate(normalized_data)
content_quality_result = ContentQualityValidator().validate(normalized_data)

print("\n🔍 Validation Results:")
print(f"   SchemaValidator: {'✅ PASS' if schema_result.passed else '❌ FAIL'}")
print(f"   StopWords:      {'✅ PASS' if stop_words_result.passed else '❌ FAIL'}")
print(f"   ContentQuality: {'✅ PASS' if content_quality_result.passed else '❌ FAIL'}")

if not schema_result.passed:
    for issue in schema_result.issues[:5]:
        print(f"     - {issue.message}")
if not stop_words_result.passed:
    for issue in stop_words_result.issues[:5]:
        print(f"     - {issue.message}")
if not content_quality_result.passed:
    for issue in content_quality_result.issues[:5]:
        print(f"     - {issue.message}")

audit = ROOT / "audit"
audit.mkdir(exist_ok=True)

result = {
    "provider": "deepseek",
    "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
    "tokens_in": response.usage.input_tokens,
    "tokens_out": response.usage.output_tokens,
    "cost": response.usage.cost,
    "generation_time_sec": round(elapsed, 2),
    "block": "01_market_analysis",
    "brief": BRIEF,
    "strict_fields": STRICT_FIELDS,
    "raw_data": raw_data,
    "data": normalized_data,
    "schema_validation": {"passed": schema_result.passed, "score": schema_result.score, "issues": len(schema_result.issues)},
    "stop_words_validation": {"passed": stop_words_result.passed, "score": stop_words_result.score, "issues": len(stop_words_result.issues)},
    "content_quality_validation": {"passed": content_quality_result.passed, "score": content_quality_result.score, "issues": len(content_quality_result.issues)},
}

(audit / "live_block_01_market_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

md = f"""# Live Block 01 — Market Analysis via DeepSeek

## Provider Info
- **Provider:** DeepSeek
- **Model:** {result['model']}
- **Tokens:** {result['tokens_in']} in / {result['tokens_out']} out
- **Cost:** ${result['cost']:.6f}
- **Generation Time:** {elapsed:.2f}s

## Validation Results
- **SchemaValidator:** {'✅ PASS' if schema_result.passed else '❌ FAIL'} (score: {schema_result.score})
- **StopWordsValidator:** {'✅ PASS' if stop_words_result.passed else '❌ FAIL'} (score: {stop_words_result.score})
- **ContentQualityValidator:** {'✅ PASS' if content_quality_result.passed else '❌ FAIL'} (score: {content_quality_result.score})

## Normalized JSON output
```json
{json.dumps(normalized_data, ensure_ascii=False, indent=2)[:2000]}
```

## Quality Notes
- {'✅ All validators passed' if all([schema_result.passed, stop_words_result.passed, content_quality_result.passed]) else '❌ Some validators failed'}
"""
(audit / "live_block_01_market_analysis.md").write_text(md, encoding="utf-8")

all_pass = schema_result.passed and stop_words_result.passed and content_quality_result.passed
print(f"\n{'=' * 60}")
print(f"LIVE TEST: {'PASSED ✅' if all_pass else 'FAILED ❌'}")
print("Reports: audit/live_block_01_market_analysis.json + .md")
print(f"{'=' * 60}")
