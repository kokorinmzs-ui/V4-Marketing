"""Sprint 16 Diversity Audit — 3 niches × live DeepSeek with marker propagation."""
import json, os, sys, time, pathlib, itertools, re

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
from ai_engine.pipeline.schema_normalizer import normalize
from ai_engine.planner.execution_planner import ExecutionPlanner
from ai_engine.exporters.html_dashboard_renderer import render_dashboard
from shared.schemas.blocks import MarketAnalysis, Audience, AvatarSet, Pains, Offers

BRIEFS = {
    "photo_studio": {
        "project_name": "Фотостудия Воздух",
        "industry": "Фотостудии",
        "business_description": "Аренда фотостудий в Москве. 7 залов, Profoto, циклорама. Работаем с 2018 года. PHOTO_UNIQUE_MARKER_777",
        "target_audience": "Content makers, bloggers, marketers",
        "products": "Аренда зала (2000₽/час), full day (15000₽), оборудование",
        "channels": "Instagram, VK, Telegram, Яндекс.Карты",
        "goals": "80% загрузка залов, 30+ лидов в месяц",
        "region": "Москва",
        "budget": "30000"
    },
    "dental_clinic": {
        "project_name": "Стоматология Белый Клык",
        "industry": "Стоматология",
        "business_description": "Частная стоматология в СПб. 5 кабинетов, микроскоп, имплантация. Работаем с 2015. DENTAL_UNIQUE_MARKER_888",
        "target_audience": "Adults 25-55, families with children, elderly",
        "products": "Caries treatment (5000₽), implantation (80000₽), children's dentistry",
        "channels": "Instagram, VK, 2ГИС, Яндекс.Карты",
        "goals": "50+ primary patients/month, loyalty program, repeat visits",
        "region": "Санкт-Петербург",
        "budget": "50000"
    },
    "b2b_service": {
        "project_name": "B2B Маркетинг Сервис",
        "industry": "B2B Маркетинг",
        "business_description": "Агентство B2B маркетинга. Лидогенерация, email-маркетинг, контент-стратегия. 10+ клиентов. B2B_UNIQUE_MARKER_999",
        "target_audience": "IT companies, industrial enterprises, SaaS products",
        "products": "Marketing audit (25000₽), lead generation (50000₽/mo), content marketing",
        "channels": "LinkedIn, Telegram, cold email, conferences",
        "goals": "5 new contracts/quarter, own lead funnel, brand awareness",
        "region": "Москва / Россия",
        "budget": "100000"
    }
}

CHAIN = [
    ("01_market_analysis", MarketAnalysis, "Market Analysis"),
    ("10_audience", Audience, "Audience Analysis"),
    ("11_avatars", AvatarSet, "Avatars"),
    ("13_pains", Pains, "Pains"),
    ("15_offers", Offers, "Offers"),
]

cfg = ProviderConfig(api_key=api_key, model="deepseek-chat",
                     base_url=os.environ.get("DEEPSEEK_BASE_URL","https://api.deepseek.com/v1"))
provider = DeepSeekProvider(cfg)
sw = StopWordsValidator()
cq = ContentQualityValidator()
AUDIT = ROOT / "audit"
AUDIT.mkdir(exist_ok=True)

all_results = {}


def find_marker(brief: dict) -> str:
    for value in brief.values():
        if isinstance(value, str) and "MARKER" in value:
            return value
    return "NONE"


def stringify_payload(payload) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    try:
        return json.dumps(payload, ensure_ascii=False)
    except TypeError:
        return str(payload)


def contains_marker(payload, marker: str) -> bool:
    if not marker or marker == "NONE":
        return False
    return marker in stringify_payload(payload)


def extract_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(filter(None, (extract_text(item) for item in value.values())))
    if isinstance(value, (list, tuple, set)):
        return " ".join(filter(None, (extract_text(item) for item in value)))
    return str(value)

for niche, brief in BRIEFS.items():
    print(f"\n{'='*60}")
    print(f"DIVERSITY AUDIT: {niche}")
    marker = find_marker(brief)
    print(f"  Marker: {marker}")
    print(f"{'='*60}")

    context = {"brief": brief}
    block_results = []
    t_start = time.perf_counter()

    for bid, schema_cls, name in CHAIN:
        print(f"  [{bid}] {name}...", end=" ")
        prompt = get_block_prompt(bid)
        ctx_json = json.dumps(context, ensure_ascii=False, indent=2)
        user_prompt = f"Use context and return JSON for this block.\n\n## CONTEXT\n{ctx_json}"

        resp = provider.generate(system_prompt=prompt, user_prompt=user_prompt)
        data = resp.data
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        data = normalize(bid, data)

        sv = SchemaValidator(schema_cls)
        schema_ok = sv.validate(data if isinstance(data, dict) else {})
        sw_ok = sw.validate(data if isinstance(data, dict) else {})
        cq_ok = cq.validate(data if isinstance(data, dict) else {})

        block_results.append({
            "block_id": bid, "schema_passed": schema_ok.passed, "stopwords_passed": sw_ok.passed,
            "content_quality_passed": cq_ok.passed, "cq_score": cq_ok.score,
            "tokens_in": resp.usage.input_tokens, "tokens_out": resp.usage.output_tokens,
            "cost": resp.usage.cost, "time_sec": 0,
            "provider_used": getattr(resp.usage, "model", "deepseek"),
            "model_used": getattr(resp.usage, "model", "deepseek-chat"),
        })

        status = "✅" if schema_ok.passed else "❌"
        print(f"{status} | {resp.usage.input_tokens}/{resp.usage.output_tokens}tok | ${resp.usage.cost:.6f} | schema={schema_ok.passed} cq={cq_ok.score}")
        context[bid] = data

    # Build flat FinalData dict for planner
    fd = {
        "project_name": brief["project_name"],
        "avatars": context.get("11_avatars", {}),
        "pains": context.get("13_pains", {}),
        "offers": context.get("15_offers", {}),
        "audience": context.get("10_audience", {}),
        "market_analysis": context.get("01_market_analysis", {}),
        "platform": {}, "product_system": {}, "funnels": {},
        "advertising": {}, "content_plan": {}, "reels": {},
        "posts": {}, "sales_scripts": {}, "kpi": {},
        "launch_plan": {}, "quality_control": {},
        "business_diagnosis": {}, "competitors": {},
        "owner_portrait": {}, "flagship": {}, "product_ladder": {},
        "lead_magnets": {}, "psychotypes": {}, "triggers": {},
        "blog_articles": {}, "visual_briefs": {},
        "first_7_days": {},
    }
    planner = ExecutionPlanner()
    plan_result = planner.plan(fd)
    evm = plan_result.execution_view_model
    html = render_dashboard(evm) if evm else ""
    final_data_dump = json.loads(json.dumps(fd, ensure_ascii=False))
    evm_dump = evm.model_dump(mode="json") if evm else {}

    total_time = time.perf_counter() - t_start
    total_cost = sum(b["cost"] for b in block_results)

    # Extract key metrics
    missions = evm.missions if evm else []
    mission_titles = [m.title for m in missions]
    mission_ctas = [getattr(m, "cta", "") for m in missions if getattr(m, "cta", "")]
    mission_hooks = [getattr(m, "hook", "") for m in missions if getattr(m, "hook", "")]
    mission_ready_texts = [getattr(m, "ready_text", "") for m in missions if getattr(m, "ready_text", "")]
    marker_hits = {
        "final_data": contains_marker(final_data_dump, marker),
        "execution_view_model": contains_marker(evm_dump, marker),
        "html": contains_marker(html, marker),
    }
    all_results[niche] = {
        "marker": marker,
        "market_overview": context.get("01_market_analysis", {}).get("market_overview", "")[:100],
        "segments_count": len(context.get("10_audience", {}).get("segments", [])),
        "avatars_count": len(context.get("11_avatars", {}).get("avatars", [])),
        "pains_count": len(context.get("13_pains", {}).get("pains", [])),
        "offers_count": len(context.get("15_offers", {}).get("offers", [])),
        "missions_count": len(missions),
        "mission_titles": mission_titles,
        "ctas": mission_ctas,
        "hooks": mission_hooks,
        "ready_texts": mission_ready_texts,
        "total_tokens": sum(b["tokens_in"]+b["tokens_out"] for b in block_results),
        "total_cost": total_cost,
        "total_time_sec": round(total_time, 1),
        "html_size": len(html.encode("utf-8")) if html else 0,
        "marker_hits": marker_hits,
        "provider_used": "deepseek",
        "model_used": "deepseek-chat",
        "final_data": final_data_dump,
        "execution_view_model": evm_dump,
        "html": html,
        "blocks": block_results,
    }

# Save per-niche results
for niche, data in all_results.items():
    (AUDIT / f"diversity_{niche}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# Diversity analysis
def similarity_score(list1, list2):
    if not list1 or not list2: return 0.0
    set1, set2 = set(str(x)[:50] for x in list1), set(str(x)[:50] for x in list2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

niches = list(all_results.keys())
report_lines = []
report_lines.append("# Sprint 16 Diversity Audit Report\n")
report_lines.append("## Executive Summary\n")
report_lines.append(f"Date: {time.strftime('%Y-%m-%d %H:%M')} | Provider: DeepSeek | Model: deepseek-chat\n")

report_lines.append("## Brief Propagation\n")
report_lines.append("| Brief | Marker | FinalData | EVM | HTML | Segments | Avatars | Pains | Offers | Missions | HTML Size |")
report_lines.append("|-------|--------|-----------|-----|------|----------|---------|-------|--------|----------|-----------|")
for n, d in all_results.items():
    hits = d.get("marker_hits", {})
    report_lines.append(
        f"| {n} | {d['marker'][:30]} | {hits.get('final_data', False)} | {hits.get('execution_view_model', False)} | {hits.get('html', False)} | "
        f"{d['segments_count']} | {d['avatars_count']} | {d['pains_count']} | {d['offers_count']} | {d['missions_count']} | {d['html_size']:,} |"
    )

report_lines.append("\n## Output Diversity\n")
report_lines.append("| Metric | photo_studio | dental_clinic | b2b_service |")
report_lines.append("|--------|-------------|---------------|-------------|")
for key in ["segments_count", "avatars_count", "pains_count", "offers_count", "missions_count"]:
    vals = [str(all_results[n].get(key, "?")) for n in niches]
    report_lines.append(f"| {key} | {' | '.join(vals)} |")

report_lines.append("\n## Similarity Audit\n")
pairs = list(itertools.combinations(niches, 2))
for n1, n2 in pairs:
    sim_titles = similarity_score(all_results[n1].get("mission_titles", []), all_results[n2].get("mission_titles", []))
    sim_ctas = similarity_score(all_results[n1].get("ctas", []), all_results[n2].get("ctas", []))
    sim_hooks = similarity_score(all_results[n1].get("hooks", []), all_results[n2].get("hooks", []))
    report_lines.append(f"- **{n1} vs {n2}**: title_sim={sim_titles:.2%}, cta_sim={sim_ctas:.2%}, hook_sim={sim_hooks:.2%}")

# Unique ratios
all_titles = []
all_ctas = []
all_hooks = []
all_ready_texts = []
for d in all_results.values():
    all_titles.extend(d.get("mission_titles", []))
    all_ctas.extend(d.get("ctas", []))
    all_hooks.extend(d.get("hooks", []))
    all_ready_texts.extend(d.get("ready_texts", []))
unique_title_ratio = len(set(str(t)[:60] for t in all_titles)) / max(len(all_titles), 1)
unique_cta_ratio = len(set(str(c)[:40] for c in all_ctas)) / max(len(all_ctas), 1)
unique_hook_ratio = len(set(str(h)[:60] for h in all_hooks)) / max(len(all_hooks), 1)
unique_ready_ratio = len(set(str(r)[:80] for r in all_ready_texts)) / max(len(all_ready_texts), 1)
report_lines.append(f"\n- **Title unique ratio:** {unique_title_ratio:.2%}")
report_lines.append(f"- **CTA unique ratio:** {unique_cta_ratio:.2%}")
report_lines.append(f"- **Hook unique ratio:** {unique_hook_ratio:.2%}")
report_lines.append(f"- **Ready text unique ratio:** {unique_ready_ratio:.2%}")

report_lines.append(f"\n## Schema Audit\n")
for n, d in all_results.items():
    blocks = d.get("blocks", [])
    passed = sum(1 for b in blocks if b["schema_passed"])
    report_lines.append(f"- **{n}**: {passed}/{len(blocks)} schema passed")

diversity_pass = (
    unique_title_ratio >= 0.70
    and unique_cta_ratio >= 0.70
    and unique_hook_ratio >= 0.70
    and unique_ready_ratio >= 0.70
)
report_lines.append(f"\n## Final Verdict\n")
report_lines.append(f"- Pipeline Stability: PASS (all 3 niches completed)")
report_lines.append(
    f"- AI Diversity: {'PASS' if diversity_pass else 'FAIL'} "
    f"(title_unique={unique_title_ratio:.0%}, cta_unique={unique_cta_ratio:.0%}, "
    f"hook_unique={unique_hook_ratio:.0%}, ready_unique={unique_ready_ratio:.0%})"
)
report_lines.append(f"- Ready for next stage: {'YES' if diversity_pass else 'NO'}")

report_payload = {
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "provider": "DeepSeek",
    "model": "deepseek-chat",
    "results": all_results,
    "diversity": {
        "unique_title_ratio": unique_title_ratio,
        "unique_cta_ratio": unique_cta_ratio,
        "unique_hook_ratio": unique_hook_ratio,
        "unique_ready_ratio": unique_ready_ratio,
        "passed": diversity_pass,
    },
    "pipeline_stability": True,
    "final_verdict": "YES" if diversity_pass else "NO",
}
(AUDIT / "DIVERSITY_AUDIT_REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")
(AUDIT / "DIVERSITY_AUDIT_REPORT.json").write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n✅ Diversity audit complete: audit/DIVERSITY_AUDIT_REPORT.md + audit/DIVERSITY_AUDIT_REPORT.json")
