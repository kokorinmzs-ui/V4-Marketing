"""Package Builder — assembles all client package content files."""

from __future__ import annotations

import html as html_lib
import json
from datetime import datetime, timezone

from shared.schemas.execution_view_model import ExecutionViewModel
from ai_engine.exporters.html_dashboard_renderer import render_dashboard


class PackageBuilder:
    """Assembles all content files for the client delivery ZIP."""

    def __init__(self):
        self._generated_at = datetime.now(timezone.utc).isoformat()

    def build(self, evm: ExecutionViewModel) -> dict[str, str]:
        files = {}
        files["01-README.txt"] = self._build_readme(evm)
        files["02-EXECUTION-DASHBOARD.html"] = render_dashboard(evm)
        files["03-CONTENT-LIBRARY.html"] = self._build_content_library(evm)
        files["04-SALES-SCRIPTS.html"] = self._build_sales_scripts(evm)
        files["05-KPI-GUIDE.html"] = self._build_kpi_guide(evm)
        files["06-PROJECT-METADATA.json"] = self._build_metadata(evm)
        return files

    def _build_readme(self, evm: ExecutionViewModel) -> str:
        return f"""=== {self._esc(evm.project.name)} — Marketing OS Client Package ===
Generated: {self._generated_at}
Version: 4.0

WHAT IS THIS PACKAGE?
This is your complete 30-day marketing execution system.
Open 02-EXECUTION-DASHBOARD.html in any browser to start.

FILES INCLUDED:
  02-EXECUTION-DASHBOARD.html — Your main dashboard with daily missions
  03-CONTENT-LIBRARY.html    — All content: posts, Reels, articles
  04-SALES-SCRIPTS.html      — Ready-to-use sales scripts and CTAs
  05-KPI-GUIDE.html          — Key metrics and success thresholds
  06-PROJECT-METADATA.json   — Technical overview of this package

HOW TO USE:
  1. Open 02-EXECUTION-DASHBOARD.html in your browser
  2. Follow today's missions
  3. Click "Done" when complete — your progress saves automatically
  4. Work offline — no internet needed after opening

QUESTIONS?
Contact your marketing consultant.
"""

    def _build_content_library(self, evm: ExecutionViewModel) -> str:
        tasks = evm.content_tasks
        items = ""
        for t in tasks:
            items += f"""<div class="item">
<h3>{self._esc(t.title)}</h3>
<div class="meta">Day {t.day} | {self._esc(t.content_format.value if t.content_format else "post")}</div>
<div class="ready-text">{self._esc(t.ready_text)}</div>
<div class="cta"><strong>CTA:</strong> {self._esc(t.cta)}</div>
</div>
"""
        return f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Content Library — {self._esc(evm.project.name)}</title>
<style>
body{{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px;background:#f5f7fa}}
h1{{color:#1a1a2e}}
.item{{background:#fff;border-radius:8px;padding:16px;margin-bottom:12px;box-shadow:0 2px 6px rgba(0,0,0,.05)}}
.item h3{{margin:0 0 6px}}
.meta{{font-size:12px;color:#888;margin-bottom:8px}}
.ready-text{{background:#f0f4ff;padding:12px;border-radius:6px;white-space:pre-wrap;margin:8px 0}}
.cta{{color:#4caf50;font-weight:600}}
</style></head>
<body>
<h1>{self._esc(evm.project.name)} — Content Library</h1>
<p>{len(tasks)} content items</p>
{items}
</body></html>"""

    def _build_sales_scripts(self, evm: ExecutionViewModel) -> str:
        tasks = evm.sales_tasks
        items = ""
        for t in tasks:
            items += f"""<div class="item">
<h3>{self._esc(t.scenario)}</h3>
<div class="meta">Day {t.day}</div>
<p class="message">{self._esc(t.message)}</p>
<div class="next"><strong>Next:</strong> {self._esc(t.next_step)}</div>
</div>
"""
        return f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sales Scripts — {self._esc(evm.project.name)}</title>
<style>
body{{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px;background:#f5f7fa}}
h1{{color:#1a1a2e}}
.item{{background:#fff;border-radius:8px;padding:16px;margin-bottom:12px;box-shadow:0 2px 6px rgba(0,0,0,.05)}}
.item h3{{margin:0 0 6px}}
.meta{{font-size:12px;color:#888;margin-bottom:8px}}
.message{{font-size:15px;line-height:1.5}}
.next{{color:#2196f3;font-weight:600;margin-top:8px}}
</style></head>
<body>
<h1>{self._esc(evm.project.name)} — Sales Scripts</h1>
<p>{len(tasks)} scripts</p>
{items}
</body></html>"""

    def _build_kpi_guide(self, evm: ExecutionViewModel) -> str:
        kpis = evm.kpi_tasks
        items = ""
        for k in kpis:
            items += f"""<div class="item">
<h3>{self._esc(k.action)}</h3>
<div class="metric"><strong>Metric:</strong> {self._esc(k.metric)}</div>
<div class="thresholds">
<div class="success">✅ Success: {self._esc(k.success_threshold)}</div>
<div class="warning">⚠ Warning: {self._esc(k.warning_threshold)}</div>
<div class="fail">❌ Fail: {self._esc(k.fail_threshold)}</div>
</div>
</div>
"""
        return f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KPI Guide — {self._esc(evm.project.name)}</title>
<style>
body{{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px;background:#f5f7fa}}
h1{{color:#1a1a2e}}
.item{{background:#fff;border-radius:8px;padding:16px;margin-bottom:12px;box-shadow:0 2px 6px rgba(0,0,0,.05)}}
.item h3{{margin:0 0 6px}}
.metric{{font-size:14px;margin-bottom:8px}}
.thresholds{{font-size:13px}}
.success{{color:#4caf50}}
.warning{{color:#ff9800}}
.fail{{color:#f44336}}
</style></head>
<body>
<h1>{self._esc(evm.project.name)} — KPI Guide</h1>
<p>{len(kpis)} KPI metrics</p>
{items}
</body></html>"""

    def _build_metadata(self, evm: ExecutionViewModel) -> str:
        meta = {
            "project_name": evm.project.name,
            "generated_at": self._generated_at,
            "version": "4.0",
            "missions_count": len(evm.missions),
            "content_count": len(evm.content_tasks),
            "ads_count": len(evm.ads_tasks),
            "sales_count": len(evm.sales_tasks),
            "total_days": evm.total_days,
            "current_day": evm.project.current_day,
        }
        return json.dumps(meta, ensure_ascii=False, indent=2)

    @staticmethod
    def _esc(s: str) -> str:
        if not s:
            return ""
        return html_lib.escape(str(s), quote=True)
