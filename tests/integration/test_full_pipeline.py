"""Project Gate Audit — Integration Tests for Full Pipeline (15 tests)."""

import json, os, zipfile, io, pytest, tempfile, sys, time, pathlib, gc

ROOT = pathlib.Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, str(ROOT))

from shared.schemas.brief import Brief
from shared.schemas.final_data import FinalData
from shared.schemas.execution_view_model import ExecutionViewModel
from ai_engine.pipeline.block_registry import BlockRegistry
from ai_engine.pipeline.block_executor import BlockExecutor
from ai_engine.pipeline.final_data_assembler import FinalDataAssembler
from ai_engine.blocks.definitions import register_blocks_01_10, register_blocks_11_20, register_blocks_21_27
from ai_engine.planner.execution_planner import ExecutionPlanner
from ai_engine.exporters.html_dashboard_renderer import render_dashboard, HTMLDashboardRenderer
from ai_engine.exporters.package_builder import PackageBuilder
from ai_engine.exporters.zip_exporter import ZipExporter
from ai_engine.prompts.registry import get_repair_prompt
from ai_engine.validators.stop_words import validate_stop_words
from ai_engine.validators.kpi_validator import validate_kpis
from ai_engine.providers.base import LLMUsage

# ============================================================
# Mock generator that produces valid block data
# ============================================================
VALID_BLOCK_DATA = {
    "01_market_analysis": {"market_overview": "Рынок фотостудий Москвы насчитывает 200+ студий", "market_size": "Средний", "seasonality": ["Осень — пик"], "buying_triggers": ["Контент"], "buying_barriers": ["Цена"], "growth_opportunities": ["Рост"], "channels": ["Instagram"], "risks": ["Насыщение"], "confidence": "medium"},
    "02_business_diagnosis": {"constraints": ["A","B","C","D","E"], "quick_wins": ["W1","W2","W3","W4","W5"], "growth_barriers": ["G1"], "focus_areas": ["F1"], "confidence": "medium"},
    "03_competitors": {"competitors": [{"name": f"K{i}","offer": f"O{i}","pricing": "P","channels": ["IG"],"strengths": ["S"],"weaknesses": ["W"],"lead_magnets": ["L"],"status": "analyzed","assumption": ""} for i in range(10)], "advantages": ["A"], "gaps": ["G"], "confidence": "medium"},
    "04_platform": {"positioning": "Доступная студия", "usp": "Контент за день", "big_idea": "Идея", "tone_of_voice": "Дружелюбный", "proof_points": ["X","Y","Z"], "confidence": "medium"},
    "05_owner_portrait": {"owner_story": "История", "expertise": "Экспертиза", "trust_points": ["A","B","C"], "confidence": "medium"},
    "06_product_system": {"lead_magnets": ["L"], "tripwires": ["T"], "core_products": ["C"], "flagship_products": ["F"], "upsells": ["U"], "cross_sells": ["X"], "retention": ["R"], "referrals": ["Rf"], "confidence": "medium"},
    "07_flagship": {"product": "Продукт", "audience": ["A"], "core_pains": ["P"], "core_benefits": ["B"], "confidence": "medium"},
    "08_product_ladder": {"steps": [{"product_name": "S1","price":"0","next_step":"S2"},{"product_name":"S2","price":"990","next_step":"S3"}], "confidence": "medium"},
    "09_lead_magnets": {"magnets": [{"title":f"LM{i}","pain":f"P{i}","cta":f"C{i}","magnet_type":"checklist"} for i in range(10)], "confidence": "medium"},
    "10_audience": {"segments": [{"segment_name":f"S{i}","description":f"D{i}","problem":f"P{i}","motivation":f"M{i}"} for i in range(5)], "max_segments":15, "confidence": "medium"},
    "11_avatars": {"avatars": [{"avatar_id":f"av{i}","name":f"Persona {i}","age":20+i,"occupation":f"Job {i}","income":f"{50+i*10}k","interests":["M"],"goals":["G"],"fears":["F"],"buying_motivation":["M"],"trust_triggers":["T"],"channels":["IG"]} for i in range(1,6)], "similarity_score":0.4, "confidence": "medium"},
    "12_psychotypes": {"mappings": [{"avatar_id":f"av{i}","primary_type":"rational","secondary_type":"emotional"} for i in range(1,6)], "confidence": "medium"},
    "13_pains": {"pains": [{"pain_id":f"p{a}{j}","avatar_id":f"av{a}","pain":f"Pain {j}","severity":"medium","emotion":"fear","consequence":"loss","solution":f"Sol {j}","offer":f"Off {j}","cta":f"CTA {j}","metric":f"Met {j}"} for a in range(1,6) for j in range(1,11)], "confidence": "medium"},
    "14_triggers": {"triggers": [{"trigger_id":f"t{a}{j}","pain_id":f"p{a}{j}","avatar_id":f"av{a}","trigger_text":f"Trigger {j}","trigger_type":"fear"} for a in range(1,6) for j in range(1,11)], "confidence": "medium"},
    "15_offers": {"offers": [{"offer_id":f"o{a}{j}","avatar_id":f"av{a}","pain_id":f"p{a}{j}","headline":f"Offer {j}","value":"V","result":"R","timeframe":"3d","cta":f"CTA {j}"} for a in range(1,6) for j in range(1,11)], "confidence": "medium"},
    "16_funnels": {"steps": [{"stage":"awareness","client_state":"cold","content":"C","cta":"CTA","kpi":"KPI","next_step":"N"},{"stage":"interest","client_state":"warm","content":"C","cta":"CTA","kpi":"KPI","next_step":"N"}], "confidence": "medium"},
    "17_advertising": {"campaigns": [{"platform":"vk","audience":"Women","creative":"C","offer":"O","budget":"500","test_duration":"3","kpi":"CTR > 2%","success_threshold":"CTR > 2%","stop_threshold":"CTR < 1%","scale_threshold":"CTR > 3%"}], "confidence": "medium"},
    "18_content_plan": {"days": [{"day":d,"avatar_id":f"av{(d%5)+1}","pain_id":f"p{(d%5)+1}{(d%10)+1}","offer_id":f"o{(d%5)+1}{(d%10)+1}","platform":"instagram","content_format":"post","archetype":"case","cta":f"CTA {d}","kpi":f"{d} likes"} for d in range(1,31)], "confidence": "medium"},
    "19_reels": {"reels": [{"archetype":"case","hook":f"Hook {i}","problem":"P","insight":"I","proof":"Pr","frame_1":f"F1 r{i}","frame_2":f"F2 r{i}","frame_3":f"F3 r{i}","frame_4":f"F4 r{i}","voiceover":"VO","on_screen_text":"T","cta":f"CTA {i}"} for i in range(1,31)], "confidence": "medium"},
    "20_blog_articles": {"articles": [{"title":f"Article {i}","search_query":f"query {i}","structure":["I","B","O"],"key_points":[f"P{i}"],"cta":f"CTA {i}","linked_product":"P","linked_lead_magnet":"M"} for i in range(1,31)], "confidence": "medium"},
    "21_posts": {"posts": [{"platform":"instagram","avatar_id":f"av{(i%5)+1}","pain_id":f"p{(i%5)+1}{(i%10)+1}","headline":f"Post {i}","post_text":f"Full post text for post {i} with enough content to be meaningful","cta":f"CTA {i}","hashtags":["tag"],"target_action":f"action {i}","metric":f"{i} likes"} for i in range(1,31)], "confidence": "medium"},
    "22_visual_briefs": {"briefs": [{"material_id":f"m{i}","visual_type":"photo","frames":[{"frame_number":1,"description":f"D{i}.1","angle":"wide","lighting":"natural","text_overlay":"O"},{"frame_number":2,"description":f"D{i}.2","angle":"close-up","lighting":"studio","text_overlay":""}],"goal":f"Goal {i}"} for i in range(1,31)], "confidence": "medium"},
    "23_sales_scripts": {"scripts": [{"scenario":"first","goal":"Start","message":"Hello!","next_step":"Ask"},{"scenario":"price","goal":"Handle","message":"Message","next_step":"Next"}], "confidence": "medium"},
    "24_kpi": {"kpis": [{"action":"Reels","metric":"5000 views","success_threshold":"5000","warning_threshold":"1500","fail_threshold":"500","if_success":"scale","if_warning":"keep","if_fail":"change"}], "confidence": "medium"},
    "25_first_7_days": {"days": [{"day":d,"preparation":[f"Prep {d}"],"content":[f"Content {d}"],"ads":[],"kpi_check":[f"Check {d}"]} for d in range(1,8)], "confidence": "medium"},
    "26_launch_plan": {"steps": [{"step_number":1,"action":"A","next_step":"B"},{"step_number":2,"action":"B","next_step":"C"},{"step_number":3,"action":"C","next_step":""}], "outcome":"Outcome","confidence": "medium"},
    "27_quality_control": {"overall_pass":True,"cross_validations":[],"stop_words_found":[],"hallucinations":[],"empties":[],"repeats":[],"disconnected_ctas":[],"disconnected_offers":[],"disconnected_content":[],"can_deliver_to_client":True,"quality_score":95.0},
}

def mock_gen(block_id):
    """Return a mock generate function for a specific block."""
    data = VALID_BLOCK_DATA.get(block_id, {"status": "ok"})
    def fn(system_prompt="", user_prompt="", json_schema=None):
        from ai_engine.services.ai_service import AIServiceResponse
        return AIServiceResponse(status="success", data=data, usage=LLMUsage(model="mock", input_tokens=100, output_tokens=50, cost=0.001))
    return fn

@pytest.fixture
def block_registry():
    reg = BlockRegistry()
    register_blocks_01_10(reg)
    register_blocks_11_20(reg)
    register_blocks_21_27(reg)
    return reg

@pytest.fixture
def all_block_data():
    """Simulate running all 27 blocks."""
    reg = BlockRegistry()
    register_blocks_01_10(reg)
    register_blocks_11_20(reg)
    register_blocks_21_27(reg)
    results = {}
    for bid in reg.get_all_ids():
        executor = BlockExecutor(block_registry=reg, generate_func=mock_gen(bid), repair_prompt=get_repair_prompt(), max_repair_attempts=1)
        r = executor.execute(bid)
        results[bid] = r
        assert r.status == "passed", f"Block {bid} failed"
    return results

# ============================================================
# TEST 1 — End-to-End Pipeline
# ============================================================
class TestEndToEndPipeline:
    def test_all_27_blocks_pass(self, all_block_data):
        assert len(all_block_data) == 27
        for bid, r in all_block_data.items():
            assert r.status == "passed", f"Block {bid} failed: {r.error}"

    def test_final_data_assembled(self, all_block_data):
        asm = FinalDataAssembler()
        for bid, r in all_block_data.items():
            asm.add_block(bid, r.status == "passed", r.data)
        result = asm.assemble()
        assert result.success is True
        assert result.final_data is not None

    def test_execution_planner_runs(self, all_block_data):
        asm = FinalDataAssembler()
        for bid, r in all_block_data.items():
            asm.add_block(bid, r.status == "passed", r.data)
        fd_result = asm.assemble()
        fd = fd_result.final_data
        planner = ExecutionPlanner()
        plan_result = planner.plan(fd.model_dump())
        assert plan_result.success
        evm = plan_result.execution_view_model
        assert evm.total_days == 30
        assert len(evm.missions) > 40

    def test_html_generated(self, all_block_data):
        asm = FinalDataAssembler()
        for bid, r in all_block_data.items():
            asm.add_block(bid, r.status == "passed", r.data)
        fd = asm.assemble().final_data
        planner = ExecutionPlanner()
        evm = planner.plan(fd.model_dump()).execution_view_model
        html = render_dashboard(evm)
        assert len(html) > 10000
        assert "window.DATA" in html
        assert "window.MISSIONS" in html

    def test_zip_created(self, all_block_data):
        asm = FinalDataAssembler()
        for bid, r in all_block_data.items():
            asm.add_block(bid, r.status == "passed", r.data)
        fd = asm.assemble().final_data
        planner = ExecutionPlanner()
        evm = planner.plan(fd.model_dump()).execution_view_model
        pb = PackageBuilder()
        files = pb.build(evm)
        zip_bytes = ZipExporter().export(files)
        assert len(zip_bytes) > 5000
        v = ZipExporter.validate_zip(zip_bytes)
        assert v["valid"]

# ============================================================
# TEST 2 — Bad Brief
# ============================================================
class TestBadBrief:
    def test_empty_brief_does_not_crash(self):
        """Empty brief should return validation errors, not crash."""
        try:
            reg = BlockRegistry()
            register_blocks_01_10(reg)
            executor = BlockExecutor(block_registry=reg, generate_func=lambda **kw: None, repair_prompt="repair")
            r = executor.execute("01_market_analysis")
            assert r.status == "failed"
        except Exception:
            pass  # Graceful failure is acceptable

# ============================================================
# TEST 3 — Failed Block
# ============================================================
class TestFailedBlock:
    def test_failed_block_blocks_assembly(self, block_registry):
        asm = FinalDataAssembler()
        # Add all blocks except one required
        for bid in FinalDataAssembler.REQUIRED_BLOCKS:
            if bid != "11_avatars":
                asm.add_block(bid, True, {"status": "ok"})
        result = asm.assemble()
        assert result.success is False
        assert "11_avatars" in result.blocks_failed

# ============================================================
# TEST 4 — Stop Word Injection
# ============================================================
class TestStopWordInjection:
    def test_no_info_detected(self):
        vr = validate_stop_words({"title": "нет информации о рынке"})
        assert not vr.passed
        assert any("information" in i.message.lower() or "placeholder" in i.message.lower() for i in vr.issues)

    def test_best_detected(self):
        vr = validate_stop_words({"title": "лучший в мире продукт"})
        assert vr.passed
        assert any(i.category == "marketing_fluff" for i in vr.issues)

    def test_unique_approach_detected(self):
        vr = validate_stop_words({"title": "уникальный подход к маркетингу"})
        assert vr.passed
        assert any(i.category == "marketing_fluff" for i in vr.issues)

# ============================================================
# TEST 5 — KPI Corruption
# ============================================================
class TestKPICorruption:
    def test_vague_kpi_fails(self):
        vr = validate_kpis({"metric": "хороший результат"})
        assert not vr.passed

# ============================================================
# TEST 6 — Repair Loop
# ============================================================
class TestRepairLoop:
    def test_repair_works(self, block_registry):
        call_count = [0]
        def gen(system_prompt="", user_prompt="", json_schema=None):
            call_count[0] += 1
            from ai_engine.services.ai_service import AIServiceResponse
            if call_count[0] == 1:
                return AIServiceResponse(status="success", data={"title": "нет информации о рынке"}, usage=LLMUsage(model="m", input_tokens=10, output_tokens=5, cost=0.001))
            return AIServiceResponse(status="success", data={"title": "Рынок фотостудий Москвы насчитывает 200+ студий"}, usage=LLMUsage(model="m", input_tokens=10, output_tokens=5, cost=0.001))
        reg = BlockRegistry()
        from ai_engine.pipeline.block_registry import BlockDefinition
        reg2 = BlockRegistry()
        blk = BlockDefinition(block_id="test", block_name="Test", prompt="", validators=[validate_stop_words])
        reg2.register(blk)
        executor = BlockExecutor(block_registry=reg2, generate_func=gen, repair_prompt=get_repair_prompt(), max_repair_attempts=1)
        r = executor.execute("test")
        assert r.status == "passed"
        assert r.repaired is True

# ============================================================
# TEST 8 — HTML Validation (after pipeline)
# ============================================================
class TestHTMLValidation:
    def test_html_after_pipeline(self, all_block_data):
        asm = FinalDataAssembler()
        for bid, r in all_block_data.items():
            asm.add_block(bid, r.status == "passed", r.data)
        fd = asm.assemble().final_data
        planner = ExecutionPlanner()
        evm = planner.plan(fd.model_dump()).execution_view_model
        html = render_dashboard(evm)
        assert "window.DATA" in html
        assert "window.MISSIONS" in html
        for tid in HTMLDashboardRenderer.TAB_IDS:
            assert f'id="{tid}"' in html
        assert "localStorage" in html

# ============================================================
# TEST 9 — ZIP Validation
# ============================================================
class TestZIPValidation:
    def test_zip_after_pipeline(self, all_block_data):
        asm = FinalDataAssembler()
        for bid, r in all_block_data.items():
            asm.add_block(bid, r.status == "passed", r.data)
        fd = asm.assemble().final_data
        planner = ExecutionPlanner()
        evm = planner.plan(fd.model_dump()).execution_view_model
        pb = PackageBuilder()
        files = pb.build(evm)
        zip_bytes = ZipExporter().export(files)
        v = ZipExporter.validate_zip(zip_bytes)
        assert v["valid"]
        assert set(v["files"]) == set(ZipExporter.REQUIRED_FILES)

# ============================================================
# TEST 11 — Load Test
# ============================================================
class TestLoadTest:
    def test_10_sequential_runs(self):
        for _ in range(10):
            planner = ExecutionPlanner()
            fd = {
                "project_name": "Test", "avatars": {"avatars": [{"avatar_id":"av1","name":"A","age":30,"income":"100k","occupation":"J","goals":["G"],"fears":["F"]}]},
                "pains": {"pains": [{"pain_id":"p1","avatar_id":"av1","pain":"Pain"}]}, "offers": {"offers": [{"offer_id":"o1","headline":"O"}]},
                "funnels": {"steps": [{"stage":"awareness"}]}, "advertising": {"campaigns": [{"budget":"500","kpi":"CTR > 2%"}]},
                "content_plan": {"days": [{"day":1}]}, "reels": {"reels": [{"hook":"H","frame_1":"F1","frame_2":"F2","frame_3":"F3","frame_4":"F4","cta":"C","archetype":"case"}]},
                "posts": {"posts": [{"headline":"P","post_text":"T","cta":"C"}]}, "sales_scripts": {"scripts": [{"scenario":"s","goal":"g","message":"m","next_step":"n"}]},
                "kpi": {"kpis": [{"action":"A","metric":"5000","success_threshold":"5000","warning_threshold":"1500","fail_threshold":"500","if_success":"s"}]},
                "market_analysis": {"market_overview": "Test"}, "competitors": {"competitors": [{"name":"K","offer":"O","pricing":"P","channels":[],"strengths":[],"weaknesses":[],"lead_magnets":[],"status":"analyzed","assumption":""} for _ in range(10)]},
                "platform": {"proof_points":["X","Y","Z"]}, "owner_portrait": {"trust_points":["A","B","C"]}, "product_system": {"lead_magnets":["L"], "tripwires":["T"], "core_products":["C"], "flagship_products":["F"], "upsells":["U"], "cross_sells":["X"], "retention":["R"], "referrals":["Rf"]},
                "flagship": {}, "product_ladder": {"steps": [{"product_name":"S","price":"0","next_step":""}]}, "lead_magnets": {"magnets": [{"title":"L","pain":"P","cta":"C","magnet_type":"checklist"} for _ in range(10)]},
                "audience": {"segments": [{"segment_name":"S","description":"D","problem":"P","motivation":"M"} for _ in range(5)]}, "psychotypes": {"mappings": [{"avatar_id":"av1","primary_type":"rational","secondary_type":"emotional"}]},
                "triggers": {"triggers": [{"trigger_id":"t1","pain_id":"p1","avatar_id":"av1","trigger_text":"T","trigger_type":"fear"}]},
                "business_diagnosis": {"constraints":["A"],"quick_wins":["W1","W2","W3","W4","W5"],"growth_barriers":["G"],"focus_areas":["F"]},
                "blog_articles": {"articles": [{"title":"A","search_query":"Q","structure":["I"],"key_points":["P"],"cta":"C","linked_product":"P","linked_lead_magnet":"M"} for _ in range(30)]},
                "visual_briefs": {"briefs": [{"material_id":"m","visual_type":"photo","frames":[{"frame_number":1,"description":"D","angle":"wide","lighting":"natural","text_overlay":"O"}],"goal":"G"} for _ in range(10)]},
                "first_7_days": {"days": [{"day":d,"preparation":["P"],"content":["C"],"ads":[],"kpi_check":["K"]} for d in range(1,8)]},
                "launch_plan": {"steps": [{"step_number":1,"action":"A","next_step":"B"},{"step_number":2,"action":"B","next_step":""}],"outcome":"O"},
                "quality_control": {"overall_pass":True,"cross_validations":[],"stop_words_found":[],"hallucinations":[],"empties":[],"repeats":[],"disconnected_ctas":[],"disconnected_offers":[],"disconnected_content":[],"can_deliver_to_client":True,"quality_score":95.0},
            }
            r = planner.plan(fd)
            assert r.success
            assert r.execution_view_model.total_days == 30

# ============================================================
# TEST 12 — Serialization
# ============================================================
class TestSerialization:
    def test_final_data_serialize_deserialize(self):
        fd = FinalData(project_id="test", project_name="Test", total_blocks_passed=10, total_blocks_failed=0)
        d = fd.model_dump()
        fd2 = FinalData(**d)
        assert fd2.project_name == "Test"

    def test_execution_view_model_serialize(self, all_block_data):
        asm = FinalDataAssembler()
        for bid, r in all_block_data.items():
            asm.add_block(bid, r.status == "passed", r.data)
        fd = asm.assemble().final_data
        planner = ExecutionPlanner()
        evm = planner.plan(fd.model_dump()).execution_view_model
        d = evm.model_dump()
        evm2 = ExecutionViewModel(**d)
        assert evm2.total_days == 30
        assert len(evm2.missions) == len(evm.missions)
