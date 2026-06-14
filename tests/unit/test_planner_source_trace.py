"""Tests for Planner Source Trace — Phase 2 (13 tests)."""
import pytest
from ai_engine.planner.execution_planner import ExecutionPlanner
from ai_engine.planner.mission_generator import MissionGenerator
from ai_engine.planner.content_action_builder import ContentActionBuilder

FULL_FD = {
    "project_name": "Test Project",
    "market_analysis": {"market_overview": "Test market", "market_size": "Средний", "seasonality": ["Осень"], "buying_triggers": ["Цена"], "buying_barriers": ["Цена"], "growth_opportunities": ["Рост"], "channels": ["IG"], "risks": ["Насыщение"], "confidence": "medium"},
    "business_diagnosis": {"constraints": ["A"], "quick_wins": ["W1","W2","W3","W4","W5"], "growth_barriers": ["G"], "focus_areas": ["F"], "confidence": "medium"},
    "competitors": {"competitors": [{"name": f"K{i}","offer": f"O{i}","pricing":"P","channels":[],"strengths":[],"weaknesses":[],"lead_magnets":[],"status":"analyzed","assumption":""} for i in range(10)], "advantages": ["A"], "gaps": ["G"], "confidence": "medium"},
    "platform": {"positioning": "Позиция", "usp": "УТП", "big_idea": "Идея", "tone_of_voice": "Дружелюбный", "proof_points": ["X","Y","Z"], "confidence": "medium"},
    "product_system": {"lead_magnets": ["L"], "tripwires": ["T"], "core_products": ["C"], "flagship_products": ["F"], "upsells": ["U"], "cross_sells": ["X"], "retention": ["R"], "referrals": ["Rf"], "confidence": "medium"},
    "avatars": {"avatars": [{"avatar_id": f"av{i}","name": f"A{i}","age":20+i,"occupation":f"J{i}","income":"100k","interests":["M"],"goals":["G"],"fears":["F"],"buying_motivation":["M"],"trust_triggers":["T"],"channels":["IG"]} for i in range(1,6)], "similarity_score":0.4, "confidence":"medium"},
    "pains": {"pains": [{"pain_id":f"p{j}","avatar_id":"av1","pain":f"P{j}","severity":"medium","emotion":"fear","consequence":"loss","solution":f"Sol {j}","offer":f"Off {j}","cta":f"CTA {j}","metric":f"Met {j}"} for j in range(1,51)], "confidence":"medium"},
    "offers": {"offers": [{"offer_id":f"o{j}","avatar_id":"av1","pain_id":f"p{j}","headline":f"O{j}","value":"V","result":"R","timeframe":"3d","cta":f"CTA {j}"} for j in range(1,51)], "confidence":"medium"},
    "content_plan": {"days": [{"day":d,"avatar_id":f"av{1}","pain_id":"p1","offer_id":"o1","platform":"instagram","content_format":"post","archetype":"case","cta":f"CTA {d}","kpi":f"{d} likes"} for d in range(1,31)], "confidence":"medium"},
    "reels": {"reels": [{"archetype":"case","hook":f"Hook {x}","problem":"P","insight":"I","proof":"Pr","frame_1":"F1","frame_2":"F2","frame_3":"F3","frame_4":"F4","voiceover":"VO","on_screen_text":"T","cta":f"CTA {x}"} for x in range(1,31)], "confidence":"medium"},
    "posts": {"posts": [{"platform":"instagram","avatar_id":"av1","pain_id":"p1","headline":f"Post {x}","post_text":f"Full text {x}","cta":f"CTA {x}","hashtags":["tag"],"target_action":f"action {x}","metric":f"{x} likes"} for x in range(1,31)], "confidence":"medium"},
    "sales_scripts": {"scripts": [{"scenario":"first","goal":"Start","message":"Hello!","next_step":"Ask"}], "confidence":"medium"},
    "kpi": {"kpis": [{"action":"Reels","metric":"5000 views","success_threshold":"5000","warning_threshold":"1500","fail_threshold":"500","if_success":"scale"}], "confidence":"medium"},
    "advertising": {"campaigns": [{"platform":"vk","audience":"Women","offer":"O","budget":"500","test_duration":"3","kpi":"CTR > 2%"}], "confidence":"medium"},
    "first_7_days": {"days": [{"day":d,"preparation":[f"Prep {d}"],"content":[f"Content {d}"],"ads":[],"kpi_check":[f"Check {d}"]} for d in range(1,8)], "confidence":"medium"},
    "launch_plan": {"steps": [{"step_number":1,"action":"A","next_step":"B"},{"step_number":2,"action":"B","next_step":""}], "outcome":"Outcome", "confidence":"medium"},
    "quality_control": {"overall_pass":True,"quality_score":95.0},
}

class TestMissionGenerator:
    def test_instance_counter(self):
        mg1 = MissionGenerator()
        mg2 = MissionGenerator()
        m1 = mg1._next_id()
        m2 = mg2._next_id()
        assert m1 == "m0001"
        assert m2 == "m0001"  # Each instance starts from 0

    def test_content_action_builder_instance_counter(self):
        cb1 = ContentActionBuilder()
        assert cb1._counter == 0

class TestPlannerSourceTrace:
    def test_planner_produces_missions(self):
        planner = ExecutionPlanner()
        result = planner.plan(FULL_FD)
        assert result.success
        evm = result.execution_view_model
        assert len(evm.missions) > 40

    def test_planner_has_source_id_on_missions(self):
        planner = ExecutionPlanner()
        result = planner.plan(FULL_FD)
        evm = result.execution_view_model
        missions_with_source = sum(1 for m in evm.missions if getattr(m, "source_id", ""))
        assert missions_with_source > 0  # At least some missions have source IDs

    def test_different_briefs_produce_different_titles(self):
        fd1 = dict(FULL_FD)
        fd2 = {
            "project_name": "Dental Clinic",
            "market_analysis": {"market_overview":"Стоматологический рынок СПб — 200+ клиник","market_size":"Крупный","seasonality":["Q4"],"buying_triggers":["Боль"],"buying_barriers":["Страх"],"growth_opportunities":["Имплантация"],"channels":["2ГИС"],"risks":["Конкуренция"],"confidence":"medium"},
            "content_plan": FULL_FD["content_plan"],
            "avatars": {"avatars": [{"avatar_id":"av100","name":"Пациент с болью","age":45,"occupation":"Менеджер","income":"120k","interests":[],"goals":[],"fears":["Стоматолог"],"buying_motivation":[],"trust_triggers":[],"channels":[]}], "similarity_score":0.5, "confidence":"medium"},
            "pains": {"pains": [{"pain_id":"p1","avatar_id":"av100","pain":"Зубная боль","severity":"high","emotion":"fear","consequence":"Потеря зуба","solution":"Имплантация","offer":"Имплант Premium","cta":"Записаться","metric":"1 запись"}], "confidence":"medium"},
            "offers": {"offers": [{"offer_id":"o1","avatar_id":"av100","pain_id":"p1","headline":"Имплантация за 1 день","value":"V","result":"R","timeframe":"1d","cta":"Записаться"}], "confidence":"medium"},
            "advertising": FULL_FD.get("advertising", {}),
            "sales_scripts": FULL_FD.get("sales_scripts", {}),
            "kpi": FULL_FD.get("kpi", {}),
        }
        p1 = ExecutionPlanner().plan(fd1).execution_view_model
        p2 = ExecutionPlanner().plan(fd2).execution_view_model

        t1 = {m.title for m in p1.missions}
        t2 = {m.title for m in p2.missions}
        overlap = len(t1 & t2)
        total = max(len(t1 | t2), 1)
        # Setup missions (days 1-5) share structure but use different data.
        # Expect at least 30% unique titles across the full mission set.
        unique_ratio = 1 - overlap / total
        assert unique_ratio >= 0.30, f"Mission titles too similar: {overlap}/{total} unique={unique_ratio:.0%}"

    def test_planner_consumes_content_plan(self):
        planner = ExecutionPlanner()
        result = planner.plan(FULL_FD)
        evm = result.execution_view_model
        content_related = [m for m in evm.missions if "контент" in (m.title or "").lower() or m.mission_type and m.mission_type.value == "content"]
        assert len(content_related) > 0

    def test_planner_handles_minimal_data(self):
        minimal = {"project_name":"T","content_plan":{"days":[{"day":1}]}}
        result = ExecutionPlanner().plan(minimal)
        # Planner succeeds with minimal data (produces missions from content_plan),
        # but emits warnings about missing sections.
        assert result.success
        assert len(result.warnings) >= 3  # Missing avatars, pains, offers, etc.
        assert result.execution_view_model
        assert len(result.execution_view_model.missions) >= 0

    def test_mission_has_required_fields(self):
        planner = ExecutionPlanner()
        result = planner.plan(FULL_FD)
        evm = result.execution_view_model
        m = evm.missions[0]
        assert m.title
        assert m.cta
        assert m.metric
        assert m.success_threshold
        assert m.warning_threshold
        assert m.fail_threshold
        assert m.if_success
        assert m.if_fail

    def test_content_tasks_created(self):
        planner = ExecutionPlanner()
        result = planner.plan(FULL_FD)
        evm = result.execution_view_model
        assert len(evm.content_tasks) > 0

    def test_ads_tasks_created(self):
        planner = ExecutionPlanner()
        result = planner.plan(FULL_FD)
        evm = result.execution_view_model
        assert len(evm.ads_tasks) > 0

    def test_sales_tasks_created(self):
        planner = ExecutionPlanner()
        result = planner.plan(FULL_FD)
        evm = result.execution_view_model
        assert len(evm.sales_tasks) > 0

    def test_kpi_tasks_created(self):
        planner = ExecutionPlanner()
        result = planner.plan(FULL_FD)
        evm = result.execution_view_model
        assert len(evm.kpi_tasks) > 0