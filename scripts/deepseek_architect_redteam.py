"""DeepSeek architect red-team smoke test.

Asks the model to review the system like a senior architect + marketer and
returns a strict JSON report for local inspection.
"""

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

AUDIT = ROOT / "audit"
AUDIT.mkdir(exist_ok=True)

MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

SYSTEM_PROMPT = """
You are a senior software architect, principal engineer, and top-tier marketing strategist.
Your job is to review the Marketing OS v4 system like a ruthless expert.

Rules:
- Be specific and concrete.
- Call out architectural, code, prompt, and product risks.
- Do not be vague or generic.
- If you infer something, say it is an inference.
- Use JSON only.

Return this schema exactly:
{
  "overall_verdict": "string",
  "readiness_level": "prototype|demo|client_ready|production_ready",
  "top_architecture_risks": [
    {
      "risk": "string",
      "severity": "critical|high|medium|low",
      "why_it_matters": "string",
      "evidence": "string",
      "fix": "string"
    }
  ],
  "top_code_risks": [
    {
      "risk": "string",
      "severity": "critical|high|medium|low",
      "why_it_matters": "string",
      "evidence": "string",
      "fix": "string"
    }
  ],
  "top_prompt_risks": [
    {
      "risk": "string",
      "severity": "critical|high|medium|low",
      "why_it_matters": "string",
      "evidence": "string",
      "fix": "string"
    }
  ],
  "live_ai_assessment": {
    "is_acting_like_real_strategist": true,
    "is_only_template_filling": false,
    "strengths": ["string"],
    "weaknesses": ["string"],
    "recommendations": ["string"]
  },
  "minimum_changes_needed": ["string"],
  "commercial_assessment": {
    "can_sell_now": true,
    "best_customer_type": "string",
    "main_sales_risk": "string"
  }
}
""".strip()

USER_PROMPT = """
Review the Marketing OS v4 codebase as a production candidate.

Project context:
- It turns briefs into marketing strategy, execution view models, HTML dashboards, and ZIP packages.
- DeepSeek is primary provider; OpenAI is fallback.
- The pipeline includes 27 blocks, validators, final data assembly, execution planner, HTML renderer, and ZIP exporter.
- Live AI smoke tests already proved DeepSeek works; now assess whether the overall architecture is trustworthy and commercially useful.

Focus on:
1. Architectural risks
2. Code-level risks
3. Prompt-engineering risks
4. Where the system is too mocked/deterministic
5. Where the system is too loose for live use
6. Whether DeepSeek is acting like a real strategist or only filling templates
7. Minimum changes needed to feel expert-level, not toy-level
8. Commercial viability

Do not be polite.
Do not give generic advice.
Return valid JSON only.
""".strip()


def main() -> int:
    provider = DeepSeekProvider(
        ProviderConfig(
            api_key=api_key,
            model=MODEL,
            base_url=BASE_URL,
            timeout_seconds=float(os.environ.get("AI_ENGINE_TIMEOUT", "120")),
        )
    )

    print("=" * 72)
    print("DEEPSEEK ARCHITECT RED-TEAM SMOKE")
    print("=" * 72)
    print(f"Provider: deepseek | Model: {MODEL}")
    print()

    t0 = time.perf_counter()
    response = provider.generate(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        json_schema={
            "type": "object",
            "properties": {
                "overall_verdict": {"type": "string"},
                "readiness_level": {"type": "string"},
                "top_architecture_risks": {"type": "array"},
                "top_code_risks": {"type": "array"},
                "top_prompt_risks": {"type": "array"},
                "live_ai_assessment": {"type": "object"},
                "minimum_changes_needed": {"type": "array"},
                "commercial_assessment": {"type": "object"},
            },
            "required": [
                "overall_verdict",
                "readiness_level",
                "top_architecture_risks",
                "top_code_risks",
                "top_prompt_risks",
                "live_ai_assessment",
                "minimum_changes_needed",
                "commercial_assessment",
            ],
        },
    )
    elapsed = round(time.perf_counter() - t0, 2)

    report: dict[str, Any] = {
        "provider": "deepseek",
        "model": MODEL,
        "status": response.status,
        "provider_used": getattr(response, "provider_used", "deepseek"),
        "model_used": getattr(response, "model_used", MODEL),
        "tokens_in": response.usage.input_tokens,
        "tokens_out": response.usage.output_tokens,
        "cost": response.usage.cost,
        "elapsed_sec": elapsed,
        "raw": response.data,
    }

    json_path = AUDIT / "deepseek_architect_redteam.json"
    md_path = AUDIT / "deepseek_architect_redteam.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# DeepSeek Architect Red-Team Smoke",
        "",
        f"- Provider: `deepseek`",
        f"- Model: `{MODEL}`",
        f"- Status: `{response.status}`",
        f"- Provider used: `{getattr(response, 'provider_used', 'deepseek')}`",
        f"- Model used: `{getattr(response, 'model_used', MODEL)}`",
        f"- Tokens: `{response.usage.input_tokens}` in / `{response.usage.output_tokens}` out",
        f"- Cost: `${response.usage.cost:.6f}`",
        f"- Elapsed: `{elapsed}s`",
        "",
        "## Verdict",
        "```json",
        json.dumps(response.data, ensure_ascii=False, indent=2)[:6000],
        "```",
    ]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print()
    print(f"Reports saved: {json_path.relative_to(ROOT)} + {md_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
