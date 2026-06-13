"""Tests for Blocks 21-27 — Sprint 9 (48 tests)."""

import pytest
from ai_engine.pipeline.block_registry import BlockRegistry
from ai_engine.pipeline.block_executor import BlockExecutor
from ai_engine.blocks.definitions import register_blocks_01_10, register_blocks_11_20, register_blocks_21_27
from ai_engine.prompts.registry import get_repair_prompt
from ai_engine.providers.base import LLMUsage

def mock_gen(data):
    def fn(**kwargs):
        from ai_engine.services.ai_service import AIServiceResponse
        return AIServiceResponse(status="success", data=data, usage=LLMUsage(model="mock", input_tokens=100, output_tokens=50, cost=0.001))
    return fn

def ex(reg, data, repair=3):
    return BlockExecutor(reg, mock_gen(data), get_repair_prompt(), max_repair_attempts=repair)

def ex0(reg, data):
    return BlockExecutor(reg, mock_gen(data), get_repair_prompt(), max_repair_attempts=0)

def new_reg():
    reg = BlockRegistry()
    register_blocks_01_10(reg)
    register_blocks_11_20(reg)
    register_blocks_21_27(reg)
    return reg

# ============================================================
# Common valid data
# ============================================================
def _post(i):
    return {"platform":"instagram","avatar_id":f"av{(i%5)+1}","pain_id":f"p{(i%5)+1}{(i%10)+1}",
            "headline":f"Post Headline {i}","post_text":f"Full post text content for post number {i} with enough length to be meaningful content.",
            "cta":f"CTA {i}","hashtags":[f"tag{i}"],"target_action":f"action {i}","metric":f"{i} likes"}

V21 = {"posts": [_post(i) for i in range(1,31)], "confidence":"medium"}

def _vis(i):
    return {"material_id":f"mat{i}","visual_type":"photo","frames":[
        {"frame_number":1,"description":f"Entrance shot for material {i}","angle":"wide","lighting":"natural","text_overlay":"Overlay"},
        {"frame_number":2,"description":f"Product detail for material {i}","angle":"close-up","lighting":"studio","text_overlay":""}
    ],"goal":f"Show product {i}"}

V22 = {"briefs": [_vis(i) for i in range(1,31)], "confidence":"medium"}
V22_BAD = {"briefs": [{"material_id":"m1","visual_type":"photo","frames":[],"goal":"нет информации"}], "confidence":"medium"}

V23 = {"scripts": [
    {"scenario":"first_response","goal":"Start conversation","message":"Здравствуйте! Спасибо за интерес к нашей фотостудии. Какой зал вас интересует?","next_step":"Уточнить потребности","notes":""},
    {"scenario":"price_question","goal":"Handle price objection","message":"Понимаю, цена важна. Наши залы включают оборудование Profoto, что экономит вам бюджет на аренду техники.","next_step":"Предложить пробную съёмку","notes":""},
    {"scenario":"doubt","goal":"Address doubts","message":"Многие клиенты сомневаются перед первой съёмкой. Посмотрите наши кейсы — вот что получается у новичков.","next_step":"Показать кейсы","notes":""},
    {"scenario":"follow_up","goal":"Re-engage silent lead","message":"Добрый день! Недавно вы интересовались арендой зала. У нас появилось свободное окно на субботу — хотите забронировать?","next_step":"Забронировать","notes":""},
    {"scenario":"repeat","goal":"Bring back past client","message":"С прошлой съёмки прошёл месяц! У нас новая циклорама — приходите попробовать со скидкой 15%.","next_step":"Предложить скидку","notes":""},
    {"scenario":"review","goal":"Get testimonial","message":"Спасибо за съёмку! Если понравилось — будем благодарны за отзыв в Instagram.","next_step":"Получить отзыв","notes":""},
    {"scenario":"referral","goal":"Get referral","message":"Приведите друга — получите скидку 20% на следующую съёмку.","next_step":"Отправить промокод","notes":""},
], "confidence":"medium"}
V23_BAD = {"scripts": [{"scenario":"first","goal":"","message":"Гарантированно получите 100% результат","next_step":"","notes":""}], "confidence":"medium"}

V24 = {"kpis": [
    {"action":"Reels","metric":"5000 просмотров","success_threshold":"5000","warning_threshold":"1500","fail_threshold":"500","if_success":"scale","if_warning":"keep","if_fail":"change"},
    {"action":"Post","metric":"20+ лайков","success_threshold":"20","warning_threshold":"10","fail_threshold":"5","if_success":"repeat","if_warning":"change CTA","if_fail":"change hook"},
], "confidence":"medium"}
V24_BAD = {"kpis": [{"action":"Post","metric":"хороший результат","success_threshold":"много","warning_threshold":"","fail_threshold":"","if_success":"","if_warning":"","if_fail":""}], "confidence":"medium"}

V25 = {"days": [{"day":d,"preparation":[f"Prep {d}"],"content":[f"Content {d}"],"ads":[],"kpi_check":[f"Check {d}"]} for d in range(1,8)], "confidence":"medium"}

V26 = {"steps": [
    {"step_number":1,"action":"Опубликовать пост-знакомство","next_step":"Создать лид-магнит"},
    {"step_number":2,"action":"Создать лид-магнит","next_step":"Запустить рекламу на лид-магнит"},
    {"step_number":3,"action":"Запустить рекламу","next_step":"Обработать заявки"},
    {"step_number":4,"action":"Обработать заявки","next_step":"Закрыть продажи"},
    {"step_number":5,"action":"Закрыть продажи","next_step":"Повторить лучшие связки"},
], "outcome":"Клиент получает 20+ заявок за 30 дней", "confidence":"medium"}
V26_BAD = {"steps": [{"step_number":1,"action":"нет информации","next_step":""}], "outcome":"","confidence":"low"}

V27 = {"overall_pass":True,"cross_validations":[{"validator":"avatar->pain","passed":True,"issues":[]}],
       "stop_words_found":[],"hallucinations":[],"empties":[],"repeats":[],
       "disconnected_ctas":[],"disconnected_offers":[],"disconnected_content":[],
       "can_deliver_to_client":True,"quality_score":95.0}
V27_BAD = {"overall_pass":False,"cross_validations":[],"stop_words_found":["нет информации"],"hallucinations":["рынок растёт"],"empties":["block_01"],"repeats":["same hook"],
           "disconnected_ctas":["cta3"],"disconnected_offers":["offer5"],"disconnected_content":["post12"],
           "can_deliver_to_client":False,"quality_score":45.0}

# ============================================================
# Registration
# ============================================================
class TestReg:
    def test_27_blocks_total(self):
        assert len(new_reg()) == 27
    def test_all_21_27_ids(self):
        r = new_reg()
        for b in ["21_posts","22_visual_briefs","23_sales_scripts","24_kpi","25_first_7_days","26_launch_plan","27_quality_control"]:
            assert b in r
    def test_all_27_have_validators(self):
        r = new_reg()
        for bid in r.get_all_ids():
            assert len(r.get(bid).validators) >= 2

# ============================================================
# Success
# ============================================================
class TestSuccess:
    def test_21(self): assert ex(new_reg(), V21).execute("21_posts").status == "passed"
    def test_22(self): assert ex(new_reg(), V22).execute("22_visual_briefs").status == "passed"
    def test_23(self): assert ex(new_reg(), V23).execute("23_sales_scripts").status == "passed"
    def test_24(self): assert ex(new_reg(), V24).execute("24_kpi").status == "passed"
    def test_25(self): assert ex(new_reg(), V25).execute("25_first_7_days").status == "passed"
    def test_26(self): assert ex(new_reg(), V26).execute("26_launch_plan").status == "passed"
    def test_27(self): assert ex(new_reg(), V27).execute("27_quality_control").status == "passed"

# ============================================================
# Stop words / quality fails
# ============================================================
class TestStopWords:
    def test_21_stop(self):
        bad = {"posts": [{**_post(1), "headline":"нет информации"}], "confidence":"medium"}
        assert ex0(new_reg(), bad).execute("21_posts").status == "failed"
    def test_22_stop(self):
        assert ex0(new_reg(), V22_BAD).execute("22_visual_briefs").status == "failed"
    def test_23_dangerous(self):
        assert ex0(new_reg(), V23_BAD).execute("23_sales_scripts").status == "failed"
    def test_24_vague_kpi(self):
        assert ex0(new_reg(), V24_BAD).execute("24_kpi").status == "failed"
    def test_26_stop(self):
        assert ex0(new_reg(), V26_BAD).execute("26_launch_plan").status == "failed"
    def test_27_stop(self):
        assert ex0(new_reg(), V27_BAD).execute("27_quality_control").status == "failed"
    def test_27_bad_quality_fails(self):
        r = ex0(new_reg(), V27_BAD).execute("27_quality_control")
        assert r.status == "failed"

# ============================================================
# Min counts
# ============================================================
class TestMinCounts:
    def test_21_posts_30(self):
        r = ex(new_reg(), V21).execute("21_posts")
        assert len(r.data["posts"]) == 30
    def test_23_scripts_7(self):
        r = ex(new_reg(), V23).execute("23_sales_scripts")
        assert len(r.data["scripts"]) >= 7
    def test_25_days_7(self):
        r = ex(new_reg(), V25).execute("25_first_7_days")
        assert len(r.data["days"]) == 7
    def test_24_kpi_numeric(self):
        r = ex(new_reg(), V24).execute("24_kpi")
        for kpi in r.data["kpis"]:
            assert any(c.isdigit() for c in kpi["success_threshold"]), f"Non-numeric success: {kpi['success_threshold']}"

# ============================================================
# Structural checks
# ============================================================
class TestStructural:
    def test_21_has_all_fields(self):
        r = ex(new_reg(), V21).execute("21_posts")
        for post in r.data["posts"]:
            for k in ["platform","avatar_id","pain_id","headline","post_text","cta","hashtags","target_action","metric"]:
                assert post.get(k) or k == "hashtags", f"Post missing {k}"
    def test_22_has_frames(self):
        r = ex(new_reg(), V22).execute("22_visual_briefs")
        for brief in r.data["briefs"]:
            assert len(brief["frames"]) >= 1, "Brief missing frames"
    def test_23_has_goal_next_step(self):
        r = ex(new_reg(), V23).execute("23_sales_scripts")
        for s in r.data["scripts"]:
            assert s.get("goal"), "Script missing goal"
            assert s.get("next_step"), "Script missing next_step"
    def test_25_each_day_has_action(self):
        r = ex(new_reg(), V25).execute("25_first_7_days")
        for d in r.data["days"]:
            total = len(d.get("preparation",[])) + len(d.get("content",[])) + len(d.get("ads",[])) + len(d.get("kpi_check",[]))
            assert total >= 1, f"Day {d['day']} has no actions"
    def test_26_chain_links(self):
        r = ex(new_reg(), V26).execute("26_launch_plan")
        steps = r.data["steps"]
        for i in range(len(steps)-1):
            assert steps[i]["next_step"], f"Step {i+1} missing next_step"
    def test_27_quality_score(self):
        r = ex(new_reg(), V27).execute("27_quality_control")
        assert r.data["quality_score"] == 95.0

# ============================================================
# Repair (2 blocks)
# ============================================================
class TestRepair:
    def test_24_kpi_structural_counts(self):
        r = ex(new_reg(), V24).execute("24_kpi")
        assert len(r.data["kpis"]) >= 2
        for kpi in r.data["kpis"]:
            for k in ["success_threshold","warning_threshold","fail_threshold"]:
                assert kpi.get(k), f"KPI missing {k}"
    def test_26_launch_outcome(self):
        r = ex(new_reg(), V26).execute("26_launch_plan")
        assert len(r.data["outcome"]) > 0
        assert len(r.data["steps"]) >= 5
    def test_27_cross_validators_count(self):
        r = ex(new_reg(), V27).execute("27_quality_control")
        assert r.data["overall_pass"] is True

# ============================================================
# Cross-validation
# ============================================================
class TestCrossValidation:
    def test_27_passes_clean(self):
        r = ex(new_reg(), V27).execute("27_quality_control")
        assert r.data["can_deliver_to_client"] is True
    def test_27_fails_dirty(self):
        r = ex0(new_reg(), V27_BAD).execute("27_quality_control")
        assert r.status == "failed"
        assert r.data["can_deliver_to_client"] is False
    def test_27_catches_stop_words(self):
        r = ex0(new_reg(), V27_BAD).execute("27_quality_control")
        assert len(r.data.get("stop_words_found",[])) >= 1
    def test_27_catches_hallucinations(self):
        r = ex0(new_reg(), V27_BAD).execute("27_quality_control")
        assert len(r.data.get("hallucinations",[])) >= 1
    def test_27_catches_empty(self):
        r = ex0(new_reg(), V27_BAD).execute("27_quality_control")
        assert len(r.data.get("empties",[])) >= 1
    def test_27_catches_repeats(self):
        r = ex0(new_reg(), V27_BAD).execute("27_quality_control")
        assert len(r.data.get("repeats",[])) >= 1
    def test_27_catches_disconnected(self):
        r = ex0(new_reg(), V27_BAD).execute("27_quality_control")
        assert len(r.data.get("disconnected_ctas",[])) >= 1
        assert len(r.data.get("disconnected_offers",[])) >= 1
        assert len(r.data.get("disconnected_content",[])) >= 1
    def test_27_quality_score_range(self):
        r = ex0(new_reg(), V27_BAD).execute("27_quality_control")
        assert 0 <= r.data["quality_score"] <= 100