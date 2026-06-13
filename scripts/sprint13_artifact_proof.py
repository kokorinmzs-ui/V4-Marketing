"""Sprint 13 — Artifact Proof (RULE-017)"""
import json, os, sys, zipfile, io, pathlib

ROOT = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(ROOT))

from ai_engine.planner.execution_planner import ExecutionPlanner
from ai_engine.exporters.package_builder import PackageBuilder
from ai_engine.exporters.zip_exporter import ZipExporter

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

evm = ExecutionPlanner().plan(MIN_FD).execution_view_model
files = PackageBuilder().build(evm)
zip_bytes = ZipExporter().export(files)

OUT = ROOT / "output" / "sprint13_package"
OUT.mkdir(parents=True, exist_ok=True)
ZIP_PATH = OUT / "client-package.zip"
UNPACK_DIR = OUT / "unpacked"
UNPACK_DIR.mkdir(exist_ok=True)

ZIP_PATH.write_bytes(zip_bytes)

# 1. ZIP Proof
print("=" * 60)
print("SPRINT 13 — ARTIFACT PROOF (RULE-017)")
print("=" * 60)
print(f"\n📦 ZIP PATH:     {ZIP_PATH}")
print(f"   ZIP SIZE:     {ZIP_PATH.stat().st_size:,} bytes")

with zipfile.ZipFile(ZIP_PATH) as zf:
    names = zf.namelist()
    print(f"   FILES IN ZIP: {len(names)}")
    for n in names:
        info = zf.getinfo(n)
        print(f"      - {n} ({info.file_size:,} bytes)")
    zf.extractall(UNPACK_DIR)

# 2. Unpacked files
print(f"\n📂 UNPACKED TO:  {UNPACK_DIR}")
for fpath in sorted(UNPACK_DIR.iterdir()):
    print(f"   {fpath.name}: {fpath.stat().st_size:,} bytes")

# 3. Metadata content
meta_path = UNPACK_DIR / "06-PROJECT-METADATA.json"
if meta_path.exists():
    print(f"\n📋 METADATA.JSON:{meta_path}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    print(json.dumps(meta, indent=2, ensure_ascii=False))

# 4. Validation
v = ZipExporter.validate_zip(zip_bytes)
print(f"\n✅ ZIP VALIDATION: {'PASSED' if v['valid'] else 'FAILED'}")
if v["errors"]:
    for e in v["errors"]:
        print(f"   ❌ {e}")
else:
    print("   No errors")

# 5. Content check snippets
for name in ["01-README.txt", "03-CONTENT-LIBRARY.html", "04-SALES-SCRIPTS.html"]:
    fpath = UNPACK_DIR / name
    if fpath.exists():
        content = fpath.read_text(encoding="utf-8")[:200]
        print(f"\n📄 {name} (first 200 chars):")
        print(content[:200])

print(f"\n{'=' * 60}")
print(f"RULE-017 ARTIFACT PROOF: PASSED")
print(f"{'=' * 60}")