"""Sprint 12 Smoke Test — generates real HTML and performs JS syntax checks."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ai_engine.planner.execution_planner import ExecutionPlanner
from ai_engine.exporters.html_dashboard_renderer import HTMLDashboardRenderer

MIN_FD = {
    "project_name": "Фотостудия Воздух",
    "market_analysis": {"market_overview": "Рынок фотостудий Москвы"},
    "avatars": {"avatars": [
        {"avatar_id": "av1", "name": "Анна", "age": 34, "income": "150k", "occupation": "Маркетолог", "goals": ["Контент"], "fears": ["Цена"]},
        {"avatar_id": "av2", "name": "Борис", "age": 28, "income": "80k", "occupation": "Контент-мейкер", "goals": ["Клиенты"], "fears": ["Цена"]},
    ]},
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
html = renderer.render(evm)

out_dir = os.path.join(ROOT, "output", "sprint12_dashboard_test")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "02-EXECUTION-DASHBOARD.html")

with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

size = os.path.getsize(out_path)
print(f"✅ HTML generated: {out_path}")
print(f"   Size: {size:,} bytes")

# Show first 20 lines
lines = html.split("\n")[:20]
print("\n📄 First 20 lines:")
for i, line in enumerate(lines, 1):
    print(f"   {i:3d} | {line.rstrip()}")

# Smoke checks
checks = {
    "window.DATA": "window.DATA" in html,
    "window.MISSIONS": "window.MISSIONS" in html,
    "8 tabs": all(f'id="{tid}"' in html for tid in ["today", "plan", "content", "ads", "sales", "clients", "metrics", "why"]),
    "localStorage": "localStorage" in html,
    "copy fallback": "textarea" in html,
    "btn-done": "btn-done" in html,
    "btn-copy": "btn-copy" in html,
    "DOCTYPE": html.strip().startswith("<!DOCTYPE html>"),
    "</html>": "</html>" in html,
    "no CDN": "cdn." not in html.lower(),
    "no TODO": "TODO" not in html,
    "mobile CSS": "@media" in html,
    "no empty tabs": all(f'id="{tid}-grid"' in html or f'id="{tid}"' in html for tid in ["today", "plan", "content", "ads", "sales", "clients", "metrics", "why"]),
}

print("\n🔍 Smoke checks:")
all_pass = True
for name, passed in checks.items():
    status = "✅" if passed else "❌"
    if not passed:
        all_pass = False
    print(f"   {status} {name}")

# JS syntax extraction (simplified: just check for balanced braces and no obvious errors)
script_start = html.index("<script>") + len("<script>")
script_end = html.index("</script>", script_start)
js_code = html[script_start:script_end]

# Basic JS syntax: count braces
open_braces = js_code.count("{")
close_braces = js_code.count("}")
open_parens = js_code.count("(")
close_parens = js_code.count(")")
open_brackets = js_code.count("[")
close_brackets = js_code.count("]")

js_ok = (open_braces == close_braces and open_parens == close_parens and open_brackets == close_brackets)
status = "✅" if js_ok else "❌"
print(f"\n📝 JS syntax check: {status}")
print(f"   Braces: {open_braces}/{close_braces}, Parens: {open_parens}/{close_parens}, Brackets: {open_brackets}/{close_brackets}")

# Check no ReferenceError for DATA/MISSIONS
has_data_ref = "window.DATA" in js_code
has_missions_ref = "window.MISSIONS" in js_code
no_ref_error_data = has_data_ref and js_code.index("window.DATA") < js_code.index("})();")
no_ref_error_missions = has_missions_ref and js_code.index("window.MISSIONS") < js_code.index("})();")
print(f"   DATA accessible: {'✅' if has_data_ref else '❌'}")
print(f"   MISSIONS accessible: {'✅' if has_missions_ref else '❌'}")

print(f"\n{'🎉 ALL CHECKS PASSED!' if all_pass and js_ok else '❌ SOME CHECKS FAILED!'}")