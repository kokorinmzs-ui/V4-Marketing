"""HTML Dashboard Renderer — generates offline 02-EXECUTION-DASHBOARD.html."""

from __future__ import annotations

import json

from shared.schemas.execution_view_model import ExecutionViewModel
from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity


class RendererError(Exception):
    pass


class HTMLDashboardRenderer:

    TAB_IDS = ["today", "plan", "content", "ads", "sales", "clients", "metrics", "why"]
    TAB_NAMES = {
        "today": "Сегодня", "plan": "30 дней", "content": "Контент",
        "ads": "Реклама", "sales": "Продажи", "clients": "Клиенты",
        "metrics": "Метрики", "why": "Почему",
    }

    CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fa;color:#1a1a2e;min-width:390px;line-height:1.5}
header{background:#1a1a2e;color:#fff;padding:16px;position:sticky;top:0;z-index:10}
header h1{font-size:20px;margin-bottom:4px}
header .info{font-size:13px;opacity:.8}
.progress-bar{background:#e0e0e0;border-radius:8px;height:12px;margin:12px 0;overflow:hidden}
.progress-bar div{background:#4caf50;height:100%;border-radius:8px;transition:width .3s}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:8px 0;font-size:13px}
.stats span{background:rgba(255,255,255,.15);border-radius:6px;padding:4px 10px}
nav.tabs{display:flex;overflow-x:auto;gap:2px;background:#fff;border-bottom:2px solid #e0e0e0;position:sticky;top:88px;z-index:9}
nav.tabs button{flex-shrink:0;padding:10px 14px;border:none;background:none;font-size:13px;cursor:pointer;color:#666;border-bottom:3px solid transparent;transition:all .2s}
nav.tabs button.active{color:#1a1a2e;border-bottom-color:#4caf50;font-weight:600}
main{padding:16px;max-width:960px;margin:0 auto}
.tab-content{display:none}
.tab-content.active{display:block}
.card{background:#fff;border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.card h3{font-size:16px;margin-bottom:6px}
.card .meta{font-size:12px;color:#888;margin-bottom:8px}
.card .steps{margin:8px 0;padding-left:20px;font-size:14px}
.card .ready-text{background:#f0f4ff;padding:12px;border-radius:8px;font-size:14px;margin:8px 0;white-space:pre-wrap}
.card .kpi-row{font-size:13px;color:#555;margin:4px 0}
.card .actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.btn{padding:8px 14px;border:none;border-radius:8px;font-size:13px;cursor:pointer;font-weight:500;transition:all .2s}
.btn-done{background:#4caf50;color:#fff}
.btn-done.done{background:#388e3c}
.btn-redo{background:#ff9800;color:#fff}
.btn-fail{background:#f44336;color:#fff}
.btn-copy{background:#2196f3;color:#fff}
.no-data{text-align:center;color:#999;padding:40px}
@media(max-width:600px){main{padding:10px}.card{padding:12px}}"""

    JS = """window.DATA = DATA_PLACEHOLDER;
window.MISSIONS = MISSIONS_PLACEHOLDER;
(function(){
var K='marketing_os_dashboard_v1';
var S=JSON.parse(localStorage.getItem(K)||'{"completed":{},"failed":{},"xp":0,"streak":0}');
function save(){localStorage.setItem(K,JSON.stringify(S));}
function gs(mid){return S.completed[mid]?'done':S.failed[mid]?'failed':'pending';}
function ss(mid,st){if(st==='done'){S.completed[mid]=true;delete S.failed[mid];S.xp+=10;}else if(st==='failed'){S.failed[mid]=true;delete S.completed[mid];}else{delete S.completed[mid];delete S.failed[mid];}save();rt();}
function cp(t){if(navigator.clipboard){navigator.clipboard.writeText(t).catch(function(){fc(t);});}else{fc(t);}}
function fc(t){var ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);}
function esc(s){if(!s)return'';return String(s).replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>').replace(/"/g,'"');}
function esc_js(s){if(!s)return'';return String(s).replace(/\\\\/g,'\\\\\\\\').replace(/'/g,"\\\\'").replace(/"/g,'\\\\"').replace(/\\n/g,'\\\\n');}
function rt(){var c=document.getElementById('mission-cards');var td=window.DATA.today;var ms=window.MISSIONS.filter(function(m){return m.day===td.day;});if(!ms.length){c.innerHTML='<div class="no-data">Нет миссий</div>';return;}c.innerHTML=ms.map(function(m){var st=gs(m.mission_id);var dc=st==='done'?' done':'';return'<div class="card"><h3>'+esc(m.title)+'</h3><div class="meta">XP: '+m.xp_reward+'</div><div class="steps">'+m.steps.map(function(s){return'<li>'+esc(s)+'</li>';}).join('')+'</div>'+(m.ready_text?'<div class="ready-text">'+esc(m.ready_text)+'</div>':'')+'<div class="kpi-row">CTA: '+esc(m.cta)+' | KPI: '+esc(m.metric)+'</div><div class="actions"><button class="btn btn-done'+dc+'" onclick="ss(\\''+m.mission_id+'\\',\\'done\\')">SD</button><button class="btn btn-redo" onclick="ss(\\''+m.mission_id+'\\',\\'redo\\')">RD</button><button class="btn btn-fail" onclick="ss(\\''+m.mission_id+'\\',\\'failed\\')">FL</button>'+(m.ready_text?'<button class="btn btn-copy" onclick="cp(\\''+esc_js(m.ready_text)+'\\')">CP</button>':'')+'</div></div>';}).join('');}
function rp(){var c=document.getElementById('plan-grid');c.innerHTML=window.DATA.days.map(function(d){return'<div class="card"><h3>Day '+d.day+' - '+esc(d.phase)+'</h3><p>'+esc(d.goal)+'</p></div>';}).join('');}
function rc(){var c=document.getElementById('content-grid');var t=window.DATA.content_tasks;if(!t.length){c.innerHTML='<div class="no-data">No content</div>';return;}c.innerHTML=t.map(function(t){return'<div class="card"><h3>'+esc(t.title)+'</h3><div class="ready-text">'+esc(t.ready_text)+'</div><button class="btn btn-copy" onclick="cp(\\''+esc_js(t.ready_text)+'\\')">Copy</button></div>';}).join('');}
function ra(){var c=document.getElementById('ads-grid');var t=window.DATA.ads_tasks;if(!t.length){c.innerHTML='<div class="no-data">No ads</div>';return;}c.innerHTML=t.map(function(t){return'<div class="card"><h3>Ad Day '+t.day+'</h3><div class="meta">Budget: '+esc(t.budget)+' | KPI: '+esc(t.kpi)+'</div></div>';}).join('');}
function rs(){var c=document.getElementById('sales-grid');var t=window.DATA.sales_tasks;if(!t.length){c.innerHTML='<div class="no-data">No scripts</div>';return;}c.innerHTML=t.map(function(t){return'<div class="card"><h3>'+esc(t.scenario)+'</h3><p>'+esc(t.message)+'</p><button class="btn btn-copy" onclick="cp(\\''+esc_js(t.message)+'\\')">Copy</button></div>';}).join('');}
function rcl(){document.getElementById('clients-grid').innerHTML='<div class="no-data">Client info</div>';}
function rm(){var c=document.getElementById('metrics-grid');var k=window.DATA.kpi_tasks;if(!k||!k.length){c.innerHTML='<div class="no-data">No metrics</div>';return;}c.innerHTML=k.map(function(k){return'<div class="card"><h3>'+esc(k.action)+'</h3><div class="meta">'+esc(k.metric)+'</div></div>';}).join('');}
function rw(){document.getElementById('why-grid').innerHTML='<div class="card"><p>Built on deep marketing analysis.</p></div>';}
function sw(tabId){
document.querySelectorAll('.tab-content').forEach(function(el){el.classList.remove('active');});
document.querySelectorAll('.tabs button').forEach(function(el){el.classList.remove('active');});
var tab=document.getElementById(tabId);if(tab)tab.classList.add('active');
var btn=document.querySelector('.tabs button[data-tab="'+tabId+'"]');if(btn)btn.classList.add('active');
}
document.addEventListener('DOMContentLoaded',function(){rt();rp();rc();ra();rs();rcl();rm();rw();
document.querySelectorAll('.tabs button').forEach(function(btn){btn.addEventListener('click',function(){sw(this.dataset.tab);});});
});})();"""

    def render(self, evm: ExecutionViewModel) -> str:
        errors = self._validate(evm)
        if errors:
            raise RendererError("; ".join(e.message for e in errors))

        tabs_html = "\n".join(
            f'<button data-tab="{tid}" class="{"active" if tid == "today" else ""}">{self.TAB_NAMES[tid]}</button>'
            for tid in self.TAB_IDS
        )

        data_json = json.dumps(evm.model_dump(), ensure_ascii=False)
        missions_json = json.dumps([m.model_dump() for m in evm.missions], ensure_ascii=False)

        js = self.JS.replace("DATA_PLACEHOLDER", data_json).replace("MISSIONS_PLACEHOLDER", missions_json)

        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._esc(evm.project.name)} — Marketing OS</title>
<style>{self.CSS}</style>
</head>
<body>
<header>
<h1>{self._esc(evm.project.name)}</h1>
<div class="info">Day {evm.project.current_day} / {evm.total_days} — {self._esc(evm.project.current_phase)}</div>
<div class="stats"><span>🔥 {evm.gamification.streak} days</span><span>⭐ {evm.gamification.xp} XP</span><span>📊 {self._esc(evm.gamification.level)}</span></div>
<div class="progress-bar"><div style="width:{evm.gamification.progress_percent}%"></div></div>
</header>
<nav class="tabs">{tabs_html}</nav>
<main>
<div id="today" class="tab-content active"><h2>Today (Day {evm.today.day})</h2><p>{self._esc(evm.today.goal)}</p><div id="mission-cards"></div></div>
<div id="plan" class="tab-content"><h2>30 Day Plan</h2><div id="plan-grid"></div></div>
<div id="content" class="tab-content"><h2>Content</h2><div id="content-grid"></div></div>
<div id="ads" class="tab-content"><h2>Ads</h2><div id="ads-grid"></div></div>
<div id="sales" class="tab-content"><h2>Sales</h2><div id="sales-grid"></div></div>
<div id="clients" class="tab-content"><h2>Clients</h2><div id="clients-grid"></div></div>
<div id="metrics" class="tab-content"><h2>Metrics</h2><div id="metrics-grid"></div></div>
<div id="why" class="tab-content"><h2>Why</h2><div id="why-grid"></div></div>
</main>
<script>{js}</script>
</body>
</html>"""

    def _validate(self, evm: ExecutionViewModel) -> list[ValidationIssue]:
        issues = []
        if not evm.missions:
            issues.append(ValidationIssue(code="no_missions", message="No missions", severity=ValidationSeverity.ERROR))
        if not evm.days:
            issues.append(ValidationIssue(code="no_days", message="No days", severity=ValidationSeverity.ERROR))
        if not evm.project.name:
            issues.append(ValidationIssue(code="no_project_name", message="No project name", severity=ValidationSeverity.ERROR))
        return issues

    @staticmethod
    def _esc(text: str) -> str:
        if not text:
            return ""
        return str(text).replace("&", "&").replace("<", "<").replace(">", ">")

    def render_to_file(self, evm: ExecutionViewModel, path: str) -> int:
        html = self.render(evm)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return len(html.encode("utf-8"))


def render_dashboard(evm: ExecutionViewModel) -> str:
    return HTMLDashboardRenderer().render(evm)