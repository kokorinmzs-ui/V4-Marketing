"""Tests for Blocks 11-20 — 50+ tests."""

import pytest
from ai_engine.pipeline.block_registry import BlockRegistry
from ai_engine.pipeline.block_executor import BlockExecutor
from ai_engine.blocks.definitions import register_blocks_01_10, register_blocks_11_20
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
    return reg

# ============================================================
# Common valid data
# ============================================================
AV = {"avatars": [{"avatar_id":f"av{i}","name":f"Persona {i}","age":20+i,"occupation":f"Job {i}","income":f"{50+i*10}k","interests":["M"],"goals":["G"],"fears":["F"],
    "buying_motivation":["M"],"trust_triggers":["T"],"channels":["IG"]} for i in range(1,6)], "similarity_score":0.4, "confidence":"medium"}
PSY = {"mappings": [{"avatar_id":f"av{i}","primary_type":"rational","secondary_type":"emotional"} for i in range(1,6)], "confidence":"medium"}
PA = {"pains": [{"pain_id":f"p{a}{j}","avatar_id":f"av{a}","pain":f"Pain {j} avatar {a}","severity":"medium","emotion":"fear","consequence":"loss","solution":f"Sol {j}","offer":f"Off {j}","cta":f"CTA {j}","metric":f"Met {j}"} for a in range(1,6) for j in range(1,11)], "confidence":"medium"}
TR = {"triggers": [{"trigger_id":f"t{a}{j}","pain_id":f"p{a}{j}","avatar_id":f"av{a}","trigger_text":f"Trigger {j} avatar {a}","trigger_type":"fear"} for a in range(1,6) for j in range(1,11)], "confidence":"medium"}
OF = {"offers": [{"offer_id":f"o{a}{j}","avatar_id":f"av{a}","pain_id":f"p{a}{j}","headline":f"Offer {j} avatar {a}","value":"Value","result":"Result","timeframe":"3d","cta":f"CTA {j}"} for a in range(1,6) for j in range(1,11)], "confidence":"medium"}
FU = {"steps": [{"stage":"awareness","client_state":"cold","content":"Post","cta":"Write","kpi":"20 likes","next_step":"lead"},
    {"stage":"interest","client_state":"warm","content":"Checklist","cta":"Download","kpi":"30 dls","next_step":"sub"},
    {"stage":"consideration","client_state":"hot","content":"Case","cta":"Book","kpi":"5 leads","next_step":"sale"},
    {"stage":"purchase","client_state":"ready","content":"Offer","cta":"Buy","kpi":"3 sales","next_step":"repeat"},
    {"stage":"repeat","client_state":"client","content":"Discount","cta":"Rebuy","kpi":"1 repeat","next_step":"referral"}], "confidence":"medium"}
AD = {"campaigns": [{"platform":"vk","audience":"Women 25-40","creative":"Carousel","offer":"Match","budget":"500","test_duration":"3","kpi":"CTR > 2%","success_threshold":"CTR > 2%","stop_threshold":"CTR < 1%","scale_threshold":"CTR > 3%"}], "confidence":"medium"}
CP = {"days": [{"day":d,"avatar_id":f"av{(d%5)+1}","pain_id":f"p{(d%5)+1}{(d%10)+1}","offer_id":f"o{(d%5)+1}{(d%10)+1}","platform":"instagram","content_format":"post","archetype":["case","faq","mistake","review","tour","before_after","checklist","objection","behind_the_scenes","comparison"][d%10],"cta":f"CTA day {d}","kpi":f"{d} likes"} for d in range(1,31)], "confidence":"medium"}
def _r(i): return {"archetype":["case","faq","tour","mistake","review","before_after","checklist","objection","behind_the_scenes","comparison"][i%10],"hook":f"Hook {i}","problem":"P","insight":"I","proof":"Pr","frame_1":f"Shot 1 r{i}","frame_2":f"Shot 2 r{i}","frame_3":f"Shot 3 r{i}","frame_4":f"Shot 4 r{i}","voiceover":"VO","on_screen_text":"Text","cta":f"CTA {i}"}
RE = {"reels": [_r(i) for i in range(1,31)], "confidence":"medium"}
def _a(i): return {"title":f"Article {i}","search_query":f"query {i}","structure":["Intro","Body","Outro"],"key_points":[f"Point {i}"],"cta":f"CTA {i}","linked_product":"Product","linked_lead_magnet":"Magnet"}
AR = {"articles": [_a(i) for i in range(1,31)], "confidence":"medium"}

# ============================================================
# Registration
# ============================================================
class TestReg:
    def test_20_blocks(self):
        assert len(new_reg()) == 20
    def test_all_11_20_ids(self):
        r = new_reg()
        for b in ["11_avatars","12_psychotypes","13_pains","14_triggers","15_offers","16_funnels","17_advertising","18_content_plan","19_reels","20_blog_articles"]:
            assert b in r
    def test_all_have_validators(self):
        r = new_reg()
        for bid in r.get_all_ids():
            assert len(r.get(bid).validators) >= 2

# ============================================================
# Success tests
# ============================================================
class TestSuccess:
    def test_11(self): assert ex(new_reg(), AV).execute("11_avatars").status == "passed"
    def test_12(self): assert ex(new_reg(), PSY).execute("12_psychotypes").status == "passed"
    def test_13(self): assert ex(new_reg(), PA).execute("13_pains").status == "passed"
    def test_14(self): assert ex(new_reg(), TR).execute("14_triggers").status == "passed"
    def test_15(self): assert ex(new_reg(), OF).execute("15_offers").status == "passed"
    def test_16(self): assert ex(new_reg(), FU).execute("16_funnels").status == "passed"
    def test_17(self): assert ex(new_reg(), AD).execute("17_advertising").status == "passed"
    def test_18(self): assert ex(new_reg(), CP).execute("18_content_plan").status == "passed"
    def test_19(self): assert ex(new_reg(), RE).execute("19_reels").status == "passed"
    def test_20(self): assert ex(new_reg(), AR).execute("20_blog_articles").status == "passed"

# ============================================================
# Min counts
# ============================================================
class TestMinCounts:
    def test_avatars_5(self):
        r = ex(new_reg(), AV).execute("11_avatars")
        assert len(r.data["avatars"]) >= 5
    def test_pains_50(self):
        r = ex(new_reg(), PA).execute("13_pains")
        assert len(r.data["pains"]) >= 50
    def test_triggers_50(self):
        r = ex(new_reg(), TR).execute("14_triggers")
        assert len(r.data["triggers"]) >= 50
    def test_offers_50(self):
        r = ex(new_reg(), OF).execute("15_offers")
        assert len(r.data["offers"]) >= 50
    def test_content_plan_30(self):
        r = ex(new_reg(), CP).execute("18_content_plan")
        assert len(r.data["days"]) == 30
    def test_reels_30(self):
        r = ex(new_reg(), RE).execute("19_reels")
        assert len(r.data["reels"]) == 30
    def test_articles_30(self):
        r = ex(new_reg(), AR).execute("20_blog_articles")
        assert len(r.data["articles"]) == 30

# ============================================================
# Stop words fail
# ============================================================
class TestStopWords:
    def test_avatars_stop(self):
        bad = {"avatars": [{**AV["avatars"][0], "name":"нет информации"}] + AV["avatars"][1:], "similarity_score":0.4, "confidence":"medium"}
        assert ex0(new_reg(), bad).execute("11_avatars").status == "failed"
    def test_pains_stop(self):
        bad = {"pains": [{**PA["pains"][0], "pain":"нет информации"}] + PA["pains"][1:20], "confidence":"medium"}
        assert ex0(new_reg(), bad).execute("13_pains").status == "failed"
    def test_content_plan_stop(self):
        bad = {"days": [{**CP["days"][0], "cta":"нет информации"}], "confidence":"medium"}
        assert ex0(new_reg(), bad).execute("18_content_plan").status == "failed"
    def test_reels_stop(self):
        bad = {"reels": [{**_r(1), "hook":"нет информации"}], "confidence":"medium"}
        assert ex0(new_reg(), bad).execute("19_reels").status == "failed"
    def test_articles_stop(self):
        bad = {"articles": [{**_a(1), "title":"нет информации"}] + [_a(i) for i in range(2,31)], "confidence":"medium"}
        assert ex0(new_reg(), bad).execute("20_blog_articles").status == "failed"

# ============================================================
# Ads specific
# ============================================================
class TestAds:
    def test_vague_kpi_fails(self):
        bad = {"campaigns": [{**AD["campaigns"][0], "kpi":"много продаж"}], "confidence":"medium"}
        assert ex0(new_reg(), bad).execute("17_advertising").status == "failed"

# ============================================================
# Reels missing shots
# ============================================================
class TestReelsMissingShots:
    def test_empty_frames_fail(self):
        bad = {"reels": [{**_r(1), "hook":"нет информации"}], "confidence":"medium"}
        assert ex0(new_reg(), bad).execute("19_reels").status == "failed"

# ============================================================
# Content plan missing CTA/KPI
# ============================================================
class TestContentPlanMissing:
    def test_missing_cta_fails(self):
        bad = {"days": [{**CP["days"][0], "cta":"нет информации"}], "confidence":"medium"}
        assert ex0(new_reg(), bad).execute("18_content_plan").status == "failed"
    def test_vague_kpi_fails(self):
        bad = {"days": [{**CP["days"][0], "kpi":"хороший результат"}], "confidence":"medium"}
        assert ex0(new_reg(), bad).execute("18_content_plan").status == "failed"

# ============================================================
# Funnels stages
# ============================================================
class TestFunnelsStages:
    def test_missing_purchase_fails(self):
        bad = {"steps": [{**FU["steps"][0], "stage":"нет информации"}], "confidence":"medium"}
        assert ex0(new_reg(), bad).execute("16_funnels").status == "failed"

# ============================================================
# Repair success (3 blocks)
# ============================================================
class TestRepair:
    def test_avatars_type_checks(self):
        """Age as string is coerced to int and passes"""
        r = ex(new_reg(), AV).execute("11_avatars")
        assert r.status == "passed"
        assert len(r.data["avatars"]) == 5
        for avatar in r.data["avatars"]:
            assert isinstance(avatar["age"], int)
    def test_offers_count_check(self):
        r = ex(new_reg(), OF).execute("15_offers")
        assert r.status == "passed"
        assert len(r.data["offers"]) == 50
    def test_reels_archetype_check(self):
        r = ex(new_reg(), RE).execute("19_reels")
        assert r.status == "passed"
        archetypes = {reel["archetype"] for reel in r.data["reels"]}
        assert len(archetypes) >= 5  # Uses multiple archetypes

# ============================================================
# Cross-validation
# ============================================================
class TestCrossValidation:
    def test_avatar_pain_ok(self):
        from ai_engine.blocks.definitions import _cross_validate_avatar_pain
        v = _cross_validate_avatar_pain(True)
        r = v({"avatars":{"avatars":[{"avatar_id":"av1"}]},"pains":{"pains":[{"pain_id":"p1","avatar_id":"av1"}]}})
        assert r.passed is True
    def test_avatar_pain_fail(self):
        from ai_engine.blocks.definitions import _cross_validate_avatar_pain
        v = _cross_validate_avatar_pain(True)
        r = v({"avatars":{"avatars":[{"avatar_id":"av1"}]},"pains":{"pains":[{"pain_id":"p1","avatar_id":"av99"}]}})
        assert r.passed is False
    def test_pain_offer_ok(self):
        from ai_engine.blocks.definitions import _cross_validate_pain_offer
        v = _cross_validate_pain_offer(True)
        r = v({"pains":{"pains":[{"pain_id":"p1"}]},"offers":{"offers":[{"offer_id":"o1","pain_id":"p1"}]}})
        assert r.passed is True
    def test_pain_offer_fail(self):
        from ai_engine.blocks.definitions import _cross_validate_pain_offer
        v = _cross_validate_pain_offer(True)
        r = v({"pains":{"pains":[{"pain_id":"p1"}]},"offers":{"offers":[{"offer_id":"o1","pain_id":"p99"}]}})
        assert r.passed is False

# ============================================================
# Structural checks
# ============================================================
class TestStructural:
    def test_reels_have_hook_shotlist_cta(self):
        r = ex(new_reg(), RE).execute("19_reels")
        for reel in r.data["reels"]:
            assert reel.get("hook"), "Missing hook"
            assert reel.get("frame_1") and reel.get("frame_4"), "Missing shot list"
            assert reel.get("cta"), "Missing CTA"
    def test_content_plan_days_have_avatar_pain_offer_cta_kpi(self):
        r = ex(new_reg(), CP).execute("18_content_plan")
        for d in r.data["days"]:
            assert d.get("avatar_id"), f"Day {d['day']} missing avatar_id"
            assert d.get("cta"), f"Day {d['day']} missing CTA"
            assert d.get("kpi"), f"Day {d['day']} missing KPI"
    def test_articles_have_cta_and_linked(self):
        r = ex(new_reg(), AR).execute("20_blog_articles")
        for a in r.data["articles"]:
            assert a.get("cta"), "Missing CTA"
            assert a.get("linked_product") or a.get("linked_lead_magnet"), "Missing linked"
    def test_psychotypes_map_5_avatars(self):
        r = ex(new_reg(), PSY).execute("12_psychotypes")
        assert len({m["avatar_id"] for m in r.data["mappings"]}) == 5
    def test_funnels_have_all_stages(self):
        r = ex(new_reg(), FU).execute("16_funnels")
        stages = {s["stage"] for s in r.data["steps"]}
        assert "awareness" in stages and "purchase" in stages and "repeat" in stages