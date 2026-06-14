"""Live Chain 10 Blocks — Sprint 16-B: 01→02→03→04→06→10→11→13→14→15 via DeepSeek."""
import json, os, sys, time, pathlib

ROOT = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(ROOT))

env_path = ROOT / ".env"
if not env_path.exists():
    print("❌ .env file not found")
    sys.exit(1)

for line in env_path.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip('"').strip("'")

api_key = os.environ.get("DEEPSEEK_API_KEY", "")
if not api_key or api_key == "sk-your-deepseek-key":
    print("❌ DEEPSEEK_API_KEY not set")
    sys.exit(1)

from ai_engine.providers.deepseek import DeepSeekProvider
from ai_engine.providers.base import ProviderConfig
from ai_engine.prompts.registry import get_block_prompt
from ai_engine.validators.schema_validator import SchemaValidator
from ai_engine.validators.stop_words import StopWordsValidator
from ai_engine.validators.content_quality import ContentQualityValidator
from shared.schemas.blocks import (
    MarketAnalysis, BusinessDiagnosis, CompetitorAnalysis,
    MarketingPlatform, ProductSystem, Audience,
    AvatarSet, Pains, Triggers, Offers,
)

BRIEF = {
    "project_name": "Фотостудия Воздух",
    "industry": "Фотостудии",
    "business_description": "Аренда фотостудий в Москве. 7 залов, оборудование Profoto, циклорама. Работаем с 2018 года.",
    "target_audience": "Контент-мейкеры, маркетологи, бренды, фотографы, блогеры",
    "products": "Аренда зала (2000₽/час), полный день съёмки (15000₽), аренда оборудования",
    "channels": "Instagram, VK, Telegram, Яндекс.Карты",
    "goals": "Увеличить загрузку залов до 80%, запустить автоворонку, получать 30+ заявок в месяц",
    "region": "Москва",
    "budget": "30000",
}

CHAIN = [
    ("01_market_analysis", MarketAnalysis, "Market Analysis"),
    ("02_business_diagnosis", BusinessDiagnosis, "Business Diagnosis"),
    ("03_competitors", CompetitorAnalysis, "Competitors"),
    ("04_platform", MarketingPlatform, "Marketing Platform"),
    ("06_product_system", ProductSystem, "Product System"),
    ("10_audience", Audience, "Audience Analysis"),
    ("11_avatars", AvatarSet, "Avatars"),
    ("13_pains", Pains, "Pains"),
    ("14_triggers", Triggers, "Triggers"),
    ("15_offers", Offers, "Offers"),
]

cfg = ProviderConfig(api_key=api_key, model=os.environ.get("DEEPSEEK_MODEL","deepseek-chat"),
                     base_url=os.environ.get("DEEPSEEK_BASE_URL","https://api.deepseek.com/v1"))
provider = DeepSeekProvider(cfg)
model = os.environ.get("DEEPSEEK_MODEL","deepseek-chat")
sw = StopWordsValidator()
cq = ContentQualityValidator()

results = []
context = {"brief": BRIEF}
total_start = time.perf_counter()

print("=" * 70)
print("LIVE CHAIN 10 BLOCKS — Sprint 16-B")
print(f"Provider: DeepSeek | Model: {model}")
print("=" * 70)

for i, (bid, schema_cls, name) in enumerate(CHAIN):
    print(f"\n[{i+1}/10] Block {bid} — {name}")
    prompt = get_block_prompt(bid)
    context_json = json.dumps(context, ensure_ascii=False, indent=2)[:8000]
    user_prompt = f"Use the provided context and return structured JSON for this block.\n\n## CONTEXT\n{context_json}"

    t0 = time.perf_counter()
    response = provider.generate(system_prompt=prompt, user_prompt=user_prompt)
    elapsed = time.perf_counter() - t0

    data = response.data
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    sv = SchemaValidator(schema_cls)
    schema_ok = sv.validate(data if isinstance(data, dict) else {})
    sw_result = sw.validate(data if isinstance(data, dict) else {})
    cq_result = cq.validate(data if isinstance(data, dict) else {})

    all_pass = schema_ok.passed and sw_result.passed and cq_result.passed
    status_icon = "✅" if all_pass else "❌"

    print(f"    {status_icon} {'PASS' if all_pass else 'FAIL'} | {elapsed:.1f}s | {response.usage.input_tokens}/{response.usage.output_tokens} tok | ${response.usage.cost:.6f}")
    if not schema_ok.passed:
        print(f"       Schema: {[i.message for i in schema_ok.issues[:2]]}")
    if not sw_result.passed:
        print(f"       StopWords: issues found")
    if not cq_result.passed:
        print(f"       ContentQ: score={cq_result.score}")

    results.append({
        "block_id": bid, "name": name, "status": "passed" if all_pass else "failed",
        "tokens_in": response.usage.input_tokens, "tokens_out": response.usage.output_tokens,
        "cost": response.usage.cost, "time_sec": round(elapsed, 2),
        "schema_passed": schema_ok.passed, "stopwords_passed": sw_result.passed,
        "content_quality_passed": cq_result.passed, "content_quality_score": cq_result.score,
        "data_keys": list(data.keys()) if isinstance(data, dict) else [],
    })

    context[bid] = data

total_time = time.perf_counter() - total_start
total_cost = sum(r["cost"] for r in results)
all_passed = all(r["status"] == "passed" for r in results)

print(f"\n{'='*70}")
print(f"RESULT: {'ALL PASSED ✅' if all_passed else 'SOME FAILED ❌'}")
print(f"Time: {total_time:.0f}s | Cost: ${total_cost:.6f}")

# Context propagation proof
print(f"\nContext propagation:")
print(f"  01→02: market_size={'✅' if context.get('01_market_analysis',{}).get('market_size') else '❌'}")
print(f"  02→03→04: competitors={len(context.get('03_competitors',{}).get('competitors',[]))}, platform={'✅' if context.get('04_platform',{}).get('positioning') else '❌'}")
print(f"  06→10: product_system filled={'✅' if context.get('06_product_system',{}).get('lead_magnets') else '❌'}")
print(f"  11→13→14→15: avatars={len(context.get('11_avatars',{}).get('avatars',[]))}, pains={len(context.get('13_pains',{}).get('pains',[]))}, triggers={len(context.get('14_triggers',{}).get('triggers',[]))}, offers={len(context.get('15_offers',{}).get('offers',[]))}")

# Save JSON + MD
AUDIT = ROOT / "audit"
AUDIT.mkdir(exist_ok=True)
summary = {"provider":"deepseek","model":model,"chain":"01→02→03→04→06→10→11→13→14→15",
           "total_time_sec": round(total_time,1), "total_cost": total_cost, "all_passed": all_passed,
           "blocks": results}
(AUDIT / "live_chain_10_blocks.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

md = f"""# Live Chain 10 Blocks — Sprint 16-B

**Provider:** DeepSeek | **Model:** {model}

## Results
| # | Block | Status | Time | Tokens | Cost | Schema | SW | CQ |
|---|-------|--------|------|--------|------|--------|----|----|
"""
for r in results:
    s, sw_s, cq_s = "✅" if r["schema_passed"] else "❌", "✅" if r["stopwords_passed"] else "❌", "✅" if r["content_quality_passed"] else "❌"
    md += f"| {r['block_id']} | {r['name']} | {r['status']} | {r['time_sec']}s | {r['tokens_in']}/{r['tokens_out']} | ${r['cost']:.6f} | {s} | {sw_s} | {cq_s} |\n"

md += f"""
**Total:** {total_time:.0f}s | ${total_cost:.6f} | {'PASSED ✅' if all_passed else 'FAILED ❌'}

## Context propagation
- 01→02→03→04→06→10→11→13→14→15
- competitors: {len(context.get('03_competitors',{}).get('competitors',[]))}
- avatars: {len(context.get('11_avatars',{}).get('avatars',[]))}
- pains: {len(context.get('13_pains',{}).get('pains',[]))}
- offers: {len(context.get('15_offers',{}).get('offers',[]))}
"""
(AUDIT / "live_chain_10_blocks.md").write_text(md, encoding="utf-8")
print(f"\nReports: audit/live_chain_10_blocks.json + .md")