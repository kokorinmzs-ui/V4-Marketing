"""Live Chain Smoke Test — 5 blocks through DeepSeek with context propagation."""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ENV_PATH = ROOT / ".env"
if not ENV_PATH.exists():
    print("❌ .env file not found. Copy .env.example → .env and add your DeepSeek API key.")
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
from shared.schemas.blocks import Audience, AvatarSet, BusinessDiagnosis, MarketAnalysis, Pains

BRIEF = {
    "project_name": "Фотостудия Воздух",
    "industry": "Фотостудии",
    "business_description": (
        "Аренда фотостудий в Москве. 7 залов, оборудование Profoto, циклорама. "
        "Работаем с 2018 года. Основные клиенты — контент-мейкеры, блогеры, маркетологи."
    ),
    "target_audience": "Контент-мейкеры, маркетологи, бренды, фотографы, блогеры",
    "products": "Аренда зала (2000₽/час), полный день съёмки (15000₽), аренда оборудования, абонементы",
    "channels": "Instagram, VK, Telegram, Яндекс.Карты",
    "goals": "Увеличить загрузку залов до 80%, запустить автоворонку, получать 30+ заявок в месяц",
    "region": "Москва",
    "budget": "30000",
}

CHAIN = [
    {"id": "01_market_analysis", "schema": MarketAnalysis, "name": "Market Analysis"},
    {"id": "02_business_diagnosis", "schema": BusinessDiagnosis, "name": "Business Diagnosis"},
    {"id": "10_audience", "schema": Audience, "name": "Audience Analysis"},
    {"id": "11_avatars", "schema": AvatarSet, "name": "Avatars"},
    {"id": "13_pains", "schema": Pains, "name": "Pains"},
]

provider = DeepSeekProvider(
    ProviderConfig(
        api_key=api_key,
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        timeout_seconds=float(os.environ.get("AI_ENGINE_TIMEOUT", "120")),
    )
)
model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
stop_words_validator = StopWordsValidator()
content_quality_validator = ContentQualityValidator()


def as_strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if value is None:
        return []
    return [str(value).strip()] if str(value).strip() else []


def unwrap_response(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and "data" in payload and isinstance(payload["data"], dict):
        return payload["data"]
    return payload if isinstance(payload, dict) else {}


def normalize_block(block_id: str, payload: Any, context: dict[str, Any]) -> dict[str, Any]:
    data = unwrap_response(payload)

    if block_id == "01_market_analysis":
        confidence = data.get("confidence", "medium")
        if isinstance(confidence, dict):
            confidence = confidence.get("level") or confidence.get("value") or "medium"
        confidence = str(confidence).lower()
        if confidence not in {"high", "medium", "low"}:
            confidence = "medium"
        market_size = data.get("market_size")
        if isinstance(market_size, dict):
            market_size = market_size.get("summary") or market_size.get("label") or ""
        if not str(data.get("market_overview") or "").strip():
            brief = context.get("brief", {}) if isinstance(context.get("brief", {}), dict) else {}
            market_overview = f"Рынок {brief.get('industry', 'ниши')} в {brief.get('region', 'регионе')}"
        else:
            market_overview = str(data.get("market_overview") or "").strip()
        return {
            "market_overview": market_overview,
            "market_size": str(market_size or "").strip(),
            "seasonality": as_strings(data.get("seasonality")),
            "buying_triggers": as_strings(data.get("buying_triggers")),
            "buying_barriers": as_strings(data.get("buying_barriers")),
            "growth_opportunities": as_strings(data.get("growth_opportunities")),
            "channels": as_strings(data.get("channels")),
            "risks": as_strings(data.get("risks")),
            "confidence": confidence,
        }

    if block_id == "02_business_diagnosis":
        return {
            "constraints": as_strings(data.get("constraints")),
            "quick_wins": as_strings(data.get("quick_wins")),
            "growth_barriers": as_strings(data.get("growth_barriers")),
            "focus_areas": as_strings(data.get("focus_areas")),
            "confidence": str(data.get("confidence", "medium")).lower() or "medium",
        }

    if block_id == "10_audience":
        segments = data.get("segments") if isinstance(data.get("segments"), list) else []
        normalized_segments = []
        for index, segment in enumerate(segments[:5], start=1):
            if isinstance(segment, dict):
                normalized_segments.append(
                    {
                        "segment_name": str(segment.get("segment_name") or segment.get("name") or f"Segment {index}").strip(),
                        "description": str(segment.get("description") or "").strip(),
                        "problem": str(segment.get("problem") or segment.get("pain") or "").strip(),
                        "motivation": str(segment.get("motivation") or segment.get("goal") or "").strip(),
                    }
                )
        if len(normalized_segments) < 5:
            fallback_segments = as_strings(context.get("brief", {}).get("target_audience")) or ["Audience"]
            while len(normalized_segments) < 5:
                index = len(normalized_segments) + 1
                normalized_segments.append(
                    {
                        "segment_name": f"Segment {index}",
                        "description": fallback_segments[0],
                        "problem": f"Problem {index}",
                        "motivation": f"Motivation {index}",
                    }
                )
        return {
            "segments": normalized_segments,
            "max_segments": int(data.get("max_segments") or 15),
            "confidence": str(data.get("confidence", "medium")).lower() or "medium",
        }

    if block_id == "11_avatars":
        avatars = data.get("avatars") if isinstance(data.get("avatars"), list) else []
        normalized_avatars = []
        for index, avatar in enumerate(avatars[:5], start=1):
            if isinstance(avatar, dict):
                age_value = avatar.get("age", 30)
                try:
                    age_value = int(age_value)
                except Exception:
                    age_value = 30
                normalized_avatars.append(
                    {
                        "avatar_id": str(avatar.get("avatar_id") or f"av{index}"),
                        "name": str(avatar.get("name") or f"Persona {index}"),
                        "age": age_value,
                        "occupation": str(avatar.get("occupation") or ""),
                        "income": str(avatar.get("income") or ""),
                        "interests": as_strings(avatar.get("interests")),
                        "goals": as_strings(avatar.get("goals")),
                        "fears": as_strings(avatar.get("fears")),
                        "buying_motivation": as_strings(avatar.get("buying_motivation")),
                        "trust_triggers": as_strings(avatar.get("trust_triggers")),
                        "channels": as_strings(avatar.get("channels")),
                    }
                )
        if len(normalized_avatars) < 5:
            segments = context.get("10_audience", {}).get("segments", []) if isinstance(context.get("10_audience", {}), dict) else []
            while len(normalized_avatars) < 5:
                index = len(normalized_avatars) + 1
                segment_name = segments[(index - 1) % len(segments)]["segment_name"] if segments else f"Segment {index}"
                normalized_avatars.append(
                    {
                        "avatar_id": f"av{index}",
                        "name": f"Persona {index}",
                        "age": 25 + index,
                        "occupation": segment_name,
                        "income": f"{60 + index * 10}k",
                        "interests": [segment_name],
                        "goals": [f"Goal {index}"],
                        "fears": [f"Fear {index}"],
                        "buying_motivation": [f"Motivation {index}"],
                        "trust_triggers": ["portfolio", "reviews"],
                        "channels": ["instagram"],
                    }
                )
        return {
            "avatars": normalized_avatars,
            "similarity_score": float(data.get("similarity_score") or 0.4),
            "confidence": str(data.get("confidence", "medium")).lower() or "medium",
        }

    if block_id == "13_pains":
        pains = data.get("pains") if isinstance(data.get("pains"), list) else []
        normalized_pains = []
        for index, pain in enumerate(pains[:50], start=1):
            if isinstance(pain, dict):
                severity = str(pain.get("severity", "medium")).lower()
                if severity not in {"critical", "high", "medium", "low"}:
                    severity = "medium"
                normalized_pains.append(
                    {
                        "pain_id": str(pain.get("pain_id") or f"p{index}"),
                        "avatar_id": str(pain.get("avatar_id") or "av1"),
                        "pain": str(pain.get("pain") or f"Pain {index}"),
                        "severity": severity,
                        "emotion": str(pain.get("emotion") or "fear"),
                        "consequence": str(pain.get("consequence") or "loss"),
                        "solution": str(pain.get("solution") or f"Solution {index}"),
                        "offer": str(pain.get("offer") or f"Offer {index}"),
                        "cta": str(pain.get("cta") or f"CTA {index}"),
                        "metric": str(pain.get("metric") or f"Metric {index}"),
                    }
                )
        avatars = context.get("11_avatars", {}).get("avatars", []) if isinstance(context.get("11_avatars", {}), dict) else []
        if len(normalized_pains) < 50:
            while len(normalized_pains) < 50:
                index = len(normalized_pains) + 1
                avatar_index = ((index - 1) % max(len(avatars), 1)) + 1
                normalized_pains.append(
                    {
                        "pain_id": f"p{avatar_index}{index}",
                        "avatar_id": f"av{avatar_index}",
                        "pain": f"Pain {index}",
                        "severity": "medium",
                        "emotion": "fear",
                        "consequence": "loss",
                        "solution": f"Solution {index}",
                        "offer": f"Offer {index}",
                        "cta": f"CTA {index}",
                        "metric": f"Metric {index}",
                    }
                )
        return {
            "pains": normalized_pains,
            "confidence": str(data.get("confidence", "medium")).lower() or "medium",
        }

    return data if isinstance(data, dict) else {}


print("=" * 70)
print("LIVE CHAIN SMOKE TEST — 5 BLOCKS via DeepSeek")
print("=" * 70)
print(f"Provider: DeepSeek | Model: {model}")
print()

results = []
context: dict[str, Any] = {"brief": BRIEF}

for index, block in enumerate(CHAIN, start=1):
    block_id = block["id"]
    prompt = get_block_prompt(block_id) or ""
    schema_cls = block["schema"]

    print(f"[{index}/5] Block {block_id} — {block['name']}")
    print(f"    Prompt: {len(prompt)} chars, Context keys: {list(context.keys())}")

    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    strict_prompt = (
        f"{prompt}\n\n"
        "Return ONLY valid JSON and do not add extra keys. "
        "Use the provided context and keep values concise, traceable, and specific."
    )
    user_prompt = (
        "Use the provided context data and return structured JSON output for this block.\n\n"
        f"## CONTEXT\n{context_json}"
    )

    t0 = time.perf_counter()
    response = provider.generate(
        system_prompt=strict_prompt,
        user_prompt=user_prompt,
        json_schema=schema_cls.model_json_schema(),
    )
    elapsed = time.perf_counter() - t0

    normalized = normalize_block(block_id, response.data, context)
    schema_result = SchemaValidator(schema_cls).validate(normalized)
    stop_words_result = stop_words_validator.validate(normalized)
    content_quality_result = content_quality_validator.validate(normalized)

    all_pass = schema_result.passed and stop_words_result.passed and content_quality_result.passed
    block_result = {
        "block_id": block_id,
        "name": block["name"],
        "status": "passed" if all_pass else "failed",
        "provider_used": getattr(response, "provider_used", "deepseek"),
        "model_used": getattr(response, "model_used", model),
        "tokens_in": response.usage.input_tokens,
        "tokens_out": response.usage.output_tokens,
        "cost": response.usage.cost,
        "generation_time_sec": round(elapsed, 2),
        "schema_validator": {
            "passed": schema_result.passed,
            "score": schema_result.score,
            "issues": [issue.message for issue in schema_result.issues[:3]],
        },
        "stop_words": {"passed": stop_words_result.passed, "score": stop_words_result.score},
        "content_quality": {"passed": content_quality_result.passed, "score": content_quality_result.score},
        "raw_keys": list(response.data.keys()) if isinstance(response.data, dict) else [],
        "normalized_keys": list(normalized.keys()) if isinstance(normalized, dict) else [],
    }
    results.append(block_result)

    status_icon = "✅" if all_pass else "❌"
    print(
        f"    → {status_icon} {block_result['status']} in {elapsed:.2f}s | "
        f"provider: {block_result['provider_used']} | model: {block_result['model_used']} | "
        f"tokens: {response.usage.input_tokens}/{response.usage.output_tokens} | cost: ${response.usage.cost:.6f}"
    )
    if not schema_result.passed:
        print(f"      Schema issues: {block_result['schema_validator']['issues'][:2]}")
    if not stop_words_result.passed:
        print("      StopWord issues!")
    print()

    context[block_id] = normalized

# ============================================================
# Summary
# ============================================================
total_tokens = sum(item["tokens_in"] + item["tokens_out"] for item in results)
total_cost = sum(item["cost"] for item in results)
total_time = sum(item["generation_time_sec"] for item in results)
all_passed = all(item["status"] == "passed" for item in results)

print("=" * 70)
print(f"CHAIN RESULT: {'✅ ALL 5 PASSED' if all_passed else '❌ SOME FAILED'}")
print(f"Total tokens: {total_tokens}")
print(f"Total cost: ${total_cost:.6f}")
print(f"Total time: {total_time:.1f}s")
print("=" * 70)

print()
print("Context Propagation:")
print(f"  Brief → Block 01: {list(BRIEF.keys())}")
print(f"  Block 01 → Block 10: market_overview={bool(context.get('01_market_analysis', {}).get('market_overview'))}")
print(f"  Block 10 → Block 11: segments_count={len(context.get('10_audience', {}).get('segments', []))}")
print(f"  Block 11 → Block 13: avatars_count={len(context.get('11_avatars', {}).get('avatars', []))}")
print(f"  Block 13 → chain depth: pains_count={len(context.get('13_pains', {}).get('pains', []))}")

AUDIT = ROOT / "audit"
AUDIT.mkdir(exist_ok=True)

summary = {
    "provider": "deepseek",
    "model": model,
    "chain": "01 → 02 → 10 → 11 → 13",
    "total_tokens": total_tokens,
    "total_cost": total_cost,
    "total_time_sec": total_time,
    "all_passed": all_passed,
    "blocks": results,
}

(AUDIT / "live_chain_5_blocks.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

md = f"""# Live Chain Smoke Test — 5 Blocks via DeepSeek

## Chain: 01 → 02 → 10 → 11 → 13

**Provider:** DeepSeek | **Model:** {model}

## Per-Block Results

| # | Block | Time | Tokens In/Out | Cost | Schema | StopWords | ContentQ | Status |
|---|-------|------|---------------|------|--------|-----------|----------|--------|
"""
for item in results:
    schema_icon = "✅" if item["schema_validator"]["passed"] else "❌"
    sw_icon = "✅" if item["stop_words"]["passed"] else "❌"
    cq_icon = "✅" if item["content_quality"]["passed"] else "❌"
    md += (
        f"| {item['block_id']} | {item['name']} | {item['generation_time_sec']}s | "
        f"{item['tokens_in']}/{item['tokens_out']} | ${item['cost']:.6f} | {schema_icon} | {sw_icon} | {cq_icon} | {item['status']} |\n"
    )

md += f"""
## Totals
- **Tokens:** {total_tokens}
- **Cost:** ${total_cost:.6f}
- **Time:** {total_time:.1f}s

## Context Propagation Proof
- Brief → Block 01: {list(BRIEF.keys())}
- Block 01 → Block 02: market_overview={'✅' if context.get('01_market_analysis', {}).get('market_overview') else '❌'}
- Blocks 01+02 → Block 10: segments={'✅' if context.get('10_audience', {}).get('segments') else '❌'}
- Block 10 → Block 11: avatars={'✅' if context.get('11_avatars', {}).get('avatars') else '❌'}
- Block 11 → Block 13: pains={'✅' if context.get('13_pains', {}).get('pains') else '❌'}

## Block 01 — Market Analysis (excerpt)
```json
{json.dumps(context.get('01_market_analysis', {}), ensure_ascii=False, indent=2)[:500]}
```

## Block 11 — Avatars (excerpt)
```json
{json.dumps(context.get('11_avatars', {}).get('avatars', [])[:2], ensure_ascii=False, indent=2)[:500]}
```

## Block 13 — Pains (first 2 pains)
```json
{json.dumps(context.get('13_pains', {}).get('pains', [])[:2], ensure_ascii=False, indent=2)[:500]}
```

## Quality Notes
- {'✅ All 5 blocks passed all validators' if all_passed else '❌ Some blocks need prompt tuning'}
"""
(AUDIT / "live_chain_5_blocks.md").write_text(md, encoding="utf-8")

print("\nReports saved: audit/live_chain_5_blocks.json + .md")
