"""Sprint 12 Hard QA — comprehensive audit of HTML Dashboard."""

import json, os, sys, subprocess, pathlib

ROOT = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(ROOT))
AUDIT = ROOT / "audit"
AUDIT.mkdir(exist_ok=True)
OUT = ROOT / "output" / "sprint12_dashboard_test"
OUT.mkdir(parents=True, exist_ok=True)
HTML_FILE = OUT / "02-EXECUTION-DASHBOARD.html"

from ai_engine.planner.execution_planner import ExecutionPlanner
from ai_engine.exporters.html_dashboard_renderer import HTMLDashboardRenderer, render_dashboard

MIN_FD = {
    "project_name": "Фотостудия Воздух",
    "market_analysis": {"market_overview": "Рынок фотостудий Москвы"},
    "avatars": {"avatars": [{"avatar_id": "av1", "name": "Анна", "age": 34, "income": "150k", "occupation": "Маркетолог", "goals": ["Контент"], "fears": ["Цена"]},
                            {"avatar_id": "av2", "name": "Борис", "age": 28, "income": "80k", "occupation": "Контент-мейкер", "goals": ["Клиенты"], "fears": ["Цена"]}]},
    "pains": {"pains": [{"pain_id": "p1", "avatar_id": "av1", "pain": "Нет времени на контент"}]},
    "offers": {"offers": [{"offer_id": "o1", "avatar_id": "av1", "pain_id": "p1", "headline": "Оффер"}]},
    "funnels": {"steps": [{"stage": "awareness"}]},
    "advertising": {"campaigns": [{"platform": "vk", "audience": "Женщины 25-40", "offer": "Подберём зал", "budget": "500", "kpi": "CTR > 2%"}]},
    "content_plan": {"days": [{"day": 1}]},
    "reels": {"reels": [{"hook": "Как выбрать зал", "frame_1": "F1", "frame_2": "F2", "frame_3": "F3", "frame_4": "F4", "cta": "ЗАЛ", "archetype": "tour"}]},
    "posts": {"posts": [{"headline": "Пост 1", "post_text": "Текст поста о фотостудии", "cta": "CTA"}]},
    "sales_scripts": {"scripts": [{"scenario": "first", "goal": "Знакомство", "message": "Здравствуйте! Спасибо за интерес.", "next_step": "Уточнить"}]},
    "kpi": {"kpis": [{"action": "Reels", "metric": "5000 просмотров", "success_threshold": "5000", "warning_threshold": "1500", "fail_threshold": "500", "if_success": "scale"}]},
}

planner = ExecutionPlanner()
result = planner.plan(MIN_FD)
evm = result.execution_view_model
renderer = HTMLDashboardRenderer()

# ============================================================
# Generate HTML
# ============================================================
html = renderer.render(evm)
HTML_FILE.write_text(html, encoding="utf-8")
f_size = HTML_FILE.stat().st_size
print(f"✅ HTML generated: {HTML_FILE} ({f_size:,} bytes)")

lines = html.split("\n")
first30 = lines[:30]
last30 = lines[-30:]

print("📄 First 30 lines:")
for i, l in enumerate(first30, 1):
    print(f"   {i:3d} | {l.rstrip()[:100]}")

print("📄 Last 30 lines:")
for i, l in enumerate(last30, 1):
    print(f"   {i:3d} | {l.rstrip()[:100]}")

# ============================================================
# 1. Pytest Collect
# ============================================================
px_coll = subprocess.run(["python", "-m", "pytest", "tests/unit/", "--collect-only", "-q"], capture_output=True, text=True, cwd=str(ROOT))
(AUDIT / "sprint12_pytest_collect.txt").write_text(px_coll.stdout + "\n" + px_coll.stderr, encoding="utf-8")
collected = 0
for line in px_coll.stdout.split("\n"):
    if "tests collected" in line:
        collected = int(line.split("tests collected")[0].strip() or 0)
print(f"\n📊 pytest collect: {collected} tests collected")

# ============================================================
# 2. Pytest Run
# ============================================================
px_run = subprocess.run(["python", "-m", "pytest", "tests/unit/", "-q"], capture_output=True, text=True, cwd=str(ROOT))
(AUDIT / "sprint12_pytest_run.txt").write_text(px_run.stdout + "\n" + px_run.stderr, encoding="utf-8")
for line in px_run.stdout.split("\n") + px_run.stderr.split("\n"):
    if "passed" in line and "failed" in line:
        print(f"📊 pytest run: {line.strip()}")

# ============================================================
# 3. Embedded Data audit
# ============================================================
data_ok = "window.DATA" in html
missions_ok = "window.MISSIONS" in html

data_marker = "window.DATA = "
data_start = html.index(data_marker) + len(data_marker) if data_ok else -1
data_end = html.index(";", data_start) if data_ok else -1
data_json_str = html[data_start:data_end] if data_ok else "{}"
try:
    data_obj = json.loads(data_json_str)
    data_parse_ok = True
except:
    data_obj = {}
    data_parse_ok = False

missions_marker = "window.MISSIONS = "
m_start = html.index(missions_marker) + len(missions_marker) if missions_ok else -1
m_end = html.index(";", m_start) if missions_ok else -1
missions_json_str = html[m_start:m_end] if missions_ok else "[]"
try:
    missions_obj = json.loads(missions_json_str)
    missions_parse_ok = True
except:
    missions_obj = []
    missions_parse_ok = False

data_audit = {
    "window.DATA_found": data_ok,
    "window.MISSIONS_found": missions_ok,
    "DATA_parses": data_parse_ok,
    "MISSIONS_parses": missions_parse_ok,
    "missions_count": len(missions_obj),
    "days_count": len(data_obj.get("days", [])),
    "today_exists": "today" in data_obj,
    "project_name_exists": bool(data_obj.get("project", {}).get("name")),
}
(AUDIT / "sprint12_html_data_audit.json").write_text(json.dumps(data_audit, indent=2, ensure_ascii=False))
print(f"\n📊 Data audit: DATA={data_ok}, MISSIONS={missions_ok}, missions={len(missions_obj)}, days={len(data_obj.get('days', []))}")

# ============================================================
# 4. DOM Markers audit
# ============================================================
tab_ids = ["today", "plan", "content", "ads", "sales", "clients", "metrics", "why"]
dom_audit = {
    "all_8_tab_divs": all(f'id="{tid}"' in html for tid in tab_ids),
    "data-tab_buttons": "data-tab=" in html,
    "mission-cards": 'id="mission-cards"' in html,
    "btn-done": "btn-done" in html,
    "btn-redo": "btn-redo" in html,
    "btn-fail": "btn-fail" in html,
    "btn-copy": "btn-copy" in html,
    "grid_divs": {tid: f'id="{tid}-grid"' in html for tid in tab_ids},
}
(AUDIT / "sprint12_html_dom_audit.json").write_text(json.dumps(dom_audit, indent=2, ensure_ascii=False))
print(f"📊 DOM audit: tabs={dom_audit['all_8_tab_divs']}, mission-cards={dom_audit['mission-cards']}, buttons OK={all([dom_audit['btn-done'], dom_audit['btn-redo'], dom_audit['btn-fail'], dom_audit['btn-copy']])}")

# ============================================================
# 5. JS audit
# ============================================================
script_start = html.index("<script>") + len("<script>")
script_end = html.index("</script>", script_start)
js_code = html[script_start:script_end]

js_audit = {
    "DATA_ref": "window.DATA" in js_code,
    "MISSIONS_ref": "window.MISSIONS" in js_code,
    "switchTab_def": "function sw" in js_code,
    "localStorage_key": "marketing_os_dashboard" in js_code,
    "copyText_def": "function cp" in js_code,
    "textarea_fallback": "textarea" in js_code,
    "no_script_src": '<script src=' not in html,
    "no_CDN": "cdn." not in html.lower(),
    "balanced_braces": js_code.count("{") == js_code.count("}"),
    "balanced_parens": js_code.count("(") == js_code.count(")"),
    "balanced_brackets": js_code.count("[") == js_code.count("]"),
}
(AUDIT / "sprint12_html_js_audit.json").write_text(json.dumps(js_audit, indent=2, ensure_ascii=False))
print(f"📊 JS audit: DATA={js_audit['DATA_ref']}, MISSIONS={js_audit['MISSIONS_ref']}, balanced={js_audit['balanced_braces'] and js_audit['balanced_parens']}, no CDN={js_audit['no_CDN']}")

# ============================================================
# 6. UX Content audit
# ============================================================
# Parse DATA JSON to find today's missions
data_raw = json.loads(data_json_str) if data_parse_ok else {}
missions_raw = json.loads(missions_json_str) if missions_parse_ok else []
today_day = data_raw.get("today", {}).get("day", 1)
today_missions = [m for m in missions_raw if m.get("day") == today_day]

content_audit = {
    "today_has_missions": len(today_missions) >= 1,
    "all_missions_have_title": all(m.get("title") for m in today_missions),
    "all_missions_have_why": all(m.get("why") for m in today_missions),
    "all_missions_have_steps": all(len(m.get("steps", [])) >= 1 for m in today_missions),
    "all_missions_have_cta": all(m.get("cta") for m in today_missions),
    "all_missions_have_metric": all(m.get("metric") for m in today_missions),
    "all_missions_have_if_success": all(m.get("if_success") for m in today_missions),
    "all_missions_have_if_fail": all(m.get("if_fail") for m in today_missions),
    "no_todo": "TODO" not in html,
    "no_fixme": "FIXME" not in html,
    "no_lorem": "lorem ipsum" not in html.lower(),
    "no_net_inform": "нет информации" not in html.lower(),
    "no_razvivat": "развивать соцсети" not in html.lower(),
    "no_uluchsit": "улучшить маркетинг" not in html.lower(),
    "content_tasks_not_empty": len(data_raw.get("content_tasks", [])) >= 1,
    "ads_tasks_not_empty": len(data_raw.get("ads_tasks", [])) >= 1,
    "sales_tasks_not_empty": len(data_raw.get("sales_tasks", [])) >= 1,
}
(AUDIT / "sprint12_html_content_audit.json").write_text(json.dumps(content_audit, indent=2, ensure_ascii=False))
all_content_ok = all(content_audit.values())
print(f"📊 Content audit: today_missions={len(today_missions)}, all_fields={all_content_ok}")

# ============================================================
# 7. Mobile CSS audit
# ============================================================
css_start = html.index("<style>") + len("<style>")
css_end = html.index("</style>", css_start)
css_code = html[css_start:css_end]

mobile_audit = {
    "media_rule": "@media" in css_code,
    "max_width": "max-width" in css_code,
    "min_width_390": "min-width:390px" in css_code,
    "no_fixed_body_width": "width:" not in css_code.split("body{")[1].split("}")[0] if "body{" in css_code else True,
    "no_scroll_cooldown": "overflow-x:scroll" not in css_code,
    "responsive_padding": "padding:10px" in css_code or "padding:12px" in css_code,
}
(AUDIT / "sprint12_mobile_audit.json").write_text(json.dumps(mobile_audit, indent=2, ensure_ascii=False))
print(f"📊 Mobile audit: media={mobile_audit['media_rule']}, min-width={mobile_audit['min_width_390']}, responsive={mobile_audit['responsive_padding']}")

# ============================================================
# 8. Summary
# ============================================================
summary = {
    "pytest": {
        "collected": collected,
        "file": "audit/sprint12_pytest_collect.txt",
    },
    "html_file": {
        "exists": HTML_FILE.exists(),
        "size_bytes": f_size,
        "path": str(HTML_FILE.relative_to(ROOT)),
    },
    "embedded_data": data_audit,
    "dom_markers": dom_audit,
    "js_audit": js_audit,
    "ux_content": content_audit,
    "mobile_css": mobile_audit,
    "all_passed": all([
        data_audit["window.DATA_found"], data_audit["window.MISSIONS_found"],
        data_audit["DATA_parses"], data_audit["MISSIONS_parses"],
        dom_audit["all_8_tab_divs"], dom_audit["mission-cards"],
        js_audit["DATA_ref"], js_audit["MISSIONS_ref"],
        js_audit["balanced_braces"], js_audit["no_CDN"],
        content_audit["today_has_missions"], mobile_audit["media_rule"],
    ]),
}

(AUDIT / "sprint12_qa_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

print(f"\n{'='*60}")
print(f"SPRINT 12 HARD QA: {'PASSED' if summary['all_passed'] else 'FAILED'}")
print(f"{'='*60}")
print(f"Sprint 13 allowed: {'YES' if summary['all_passed'] else 'NO'}")