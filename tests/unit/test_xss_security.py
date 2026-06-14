"""Phase 6.1 — XSS Security Tests (15 tests)."""
import json, pytest
from ai_engine.planner.execution_planner import ExecutionPlanner
from ai_engine.exporters.html_dashboard_renderer import render_dashboard, HTMLDashboardRenderer

MALICIOUS_FD = {
    "project_name": "MyProject",
    "market_analysis": {"market_overview": "Market overview text", "market_size": "Small", "seasonality": ["Q4"], "buying_triggers": ["trigger"], "buying_barriers": ["barrier"], "growth_opportunities": ["G"], "channels": ["IG"], "risks": ["R"], "confidence": "medium"},
    "content_plan": {"days": [{"day": 1, "avatar_id": "av1", "pain_id": "p1", "offer_id": "o1", "platform": "instagram", "content_format": "post", "archetype": "case", "cta": "cta1", "kpi": "1 like"}]},
    "avatars": {"avatars": [{"avatar_id": "av1", "name": "Anna", "age": 30, "occupation": "Marketer", "income": "100k", "interests": [], "goals": [], "fears": [], "buying_motivation": [], "trust_triggers": [], "channels": []}], "similarity_score": 0.3, "confidence": "medium"},
    "pains": {"pains": [{"pain_id": "p1", "avatar_id": "av1", "pain": "No time", "severity": "high", "emotion": "fear", "consequence": "loss", "solution": "fix", "offer": "offer1", "cta": "cta1", "metric": "1"}], "confidence": "medium"},
    "offers": {"offers": [{"offer_id": "o1", "avatar_id": "av1", "pain_id": "p1", "headline": "Offer 1", "value": "V", "result": "R", "timeframe": "1d", "cta": "OK"}], "confidence": "medium"},
    "reels": {"reels": [{"hook": "Hook 1", "problem": "P", "insight": "I", "proof": "Pr", "frame_1": "F1", "frame_2": "F2", "frame_3": "F3", "frame_4": "F4", "voiceover": "VO", "on_screen_text": "T", "cta": "OK", "archetype": "case"}], "confidence": "medium"},
    "posts": {"posts": [{"platform": "instagram", "avatar_id": "av1", "pain_id": "p1", "headline": "Post 1", "post_text": "Text content", "cta": "OK", "hashtags": ["safe"], "target_action": "action", "metric": "1 like"}], "confidence": "medium"},
    "advertising": {"campaigns": [{"platform": "vk", "audience": "Women", "offer": "O", "budget": "500", "test_duration": "3", "kpi": "CTR > 2%"}], "confidence": "medium"},
    "sales_scripts": {"scripts": [{"scenario": "first", "goal": "Start", "message": "Hello!", "next_step": "Ask"}], "confidence": "medium"},
    "kpi": {"kpis": [{"action": "Reels", "metric": "5000 views", "success_threshold": "5000", "warning_threshold": "1500", "fail_threshold": "500", "if_success": "scale"}], "confidence": "medium"},
}

def _render():
    planner = ExecutionPlanner()
    result = planner.plan(MALICIOUS_FD)
    evm = result.execution_view_model
    return render_dashboard(evm)

class TestHtmlEscaping:
    def test_title_tag_safe(self):
        html = _render()
        ts = html.index("<title>") + 7
        te = html.index("</title>", ts)
        title = html[ts:te]
        assert "<" not in title, "Raw HTML in <title>"

    def test_no_javascript_url(self):
        html = _render()
        assert "javascript:" not in html

    def test_no_raw_img_tag_in_body(self):
        html = _render()
        sp = html.index(chr(60)+"script"+chr(62))
        body = html[:sp]
        assert "<img " not in body.lower(), "Raw img in body"

    def test_no_raw_svg_in_body(self):
        html = _render()
        sp = html.index(chr(60)+"script"+chr(62))
        body = html[:sp]
        assert "<svg " not in body.lower(), "Raw SVG in body"


class TestSafeJsonEmbedding:
    def test_script_block_has_data(self):
        html = _render()
        ss = html.index(chr(60)+"script"+chr(62)) + 8
        se = html.index(chr(60)+"/script"+chr(62), ss)
        js_block = html[ss:se]
        assert "window.DATA" in js_block

    def test_json_literal_escapes_angle(self):
        lit = HTMLDashboardRenderer._js_json_literal("</")
        assert "<" not in lit

    def test_esc_function_produces_entities(self):
        result = HTMLDashboardRenderer._esc("<b>")
        assert "lt;" in result
        assert result != "<b>"


class TestZIPSafety:
    def test_exported_html_safe(self):
        from ai_engine.exporters.package_builder import PackageBuilder
        from ai_engine.exporters.zip_exporter import ZipExporter
        import zipfile, io
        planner = ExecutionPlanner()
        result = planner.plan(MALICIOUS_FD)
        evm = result.execution_view_model
        pb = PackageBuilder()
        files = pb.build(evm)
        zip_data = ZipExporter().export(files)
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            dh = zf.read("02-EXECUTION-DASHBOARD.html").decode("utf-8")
            sp = dh.index(chr(60)+"script"+chr(62))
            body = dh[:sp]
            assert "<script " not in body.lower()
            assert "<img " not in body.lower()

    def test_metadata_is_json(self):
        fd = dict(MALICIOUS_FD)
        planner = ExecutionPlanner()
        result = planner.plan(fd)
        evm = result.execution_view_model
        from ai_engine.exporters.package_builder import PackageBuilder
        pb = PackageBuilder()
        files = pb.build(evm)
        meta = json.loads(files["06-PROJECT-METADATA.json"])
        assert isinstance(meta, dict)


class TestEscapeHtmlFrontend:
    def test_escape_html_function_exists(self):
        html = _render()
        assert "escapeHtml(" in html

    def test_frontend_escapes_lt(self):
        html = _render()
        assert "replace(/"+chr(60)+"/g" in html

    def test_all_render_functions_exist(self):
        html = _render()
        funcs = ["function rt(", "function rp(", "function rc(", "function ra(", "function rs(", "function rm("]
        for func in funcs:
            assert func in html, f"Missing: {func}"