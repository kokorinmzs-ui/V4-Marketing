"""Tests for FinalDataAssembler and Cross-Validation — Sprint 10 (25 tests)."""

import pytest
from ai_engine.pipeline.final_data_assembler import FinalDataAssembler, AssemblyResult
from ai_engine.validators.base import ValidationSeverity

# ============================================================
# Helpers: minimal valid data for each required block
# ============================================================
def _mk_all_valid():
    """Return dict of all 19 required blocks with valid linked data."""
    return {
        "01_market_analysis": {"market_overview":"R","market_size":"M","seasonality":[],"buying_triggers":[],"buying_barriers":[],"growth_opportunities":[],"channels":[],"risks":[],"confidence":"medium"},
        "02_business_diagnosis": {"constraints":["A"],"quick_wins":["B","C","D","E","F"],"growth_barriers":["G"],"focus_areas":["H"],"confidence":"medium"},
        "03_competitors": {"competitors":[{"name":f"K{i}","offer":f"O{i}","pricing":"P","channels":[],"strengths":[],"weaknesses":[],"lead_magnets":[],"status":"analyzed","assumption":""} for i in range(10)],"advantages":[],"gaps":[],"confidence":"medium"},
        "04_platform": {"positioning":"A","usp":"B","big_idea":"C","tone_of_voice":"D","proof_points":["X","Y","Z"],"confidence":"medium"},
        "10_audience": {"segments":[{"segment_name":"S1","description":"D","problem":"P","motivation":"M"}],"max_segments":15,"confidence":"medium"},
        "11_avatars": {"avatars":[{"avatar_id":"av1","name":"Anna","age":34,"occupation":"J","income":"100k","interests":[],"goals":["G"],"fears":["F"],"buying_motivation":[],"trust_triggers":[],"channels":[]},{"avatar_id":"av2","name":"Bob","age":28,"occupation":"J","income":"80k","interests":[],"goals":["G"],"fears":["F"],"buying_motivation":[],"trust_triggers":[],"channels":[]}],"similarity_score":0.3,"confidence":"medium"},
        "13_pains": {"pains":[{"pain_id":"p1","avatar_id":"av1","pain":"Pain 1","severity":"medium","emotion":"fear","consequence":"loss","solution":"Solve","offer":"Offer","cta":"CTA","metric":"Metric"},{"pain_id":"p2","avatar_id":"av2","pain":"Pain 2","severity":"medium","emotion":"fear","consequence":"loss","solution":"Solve","offer":"Offer","cta":"CTA","metric":"Metric"}],"confidence":"medium"},
        "14_triggers": {"triggers":[{"trigger_id":"t1","pain_id":"p1","avatar_id":"av1","trigger_text":"Trigger 1","trigger_type":"fear"},{"trigger_id":"t2","pain_id":"p2","avatar_id":"av2","trigger_text":"Trigger 2","trigger_type":"benefit"}],"confidence":"medium"},
        "15_offers": {"offers":[{"offer_id":"o1","avatar_id":"av1","pain_id":"p1","headline":"Offer 1","value":"Value","result":"Result","timeframe":"3d","cta":"CTA"},{"offer_id":"o2","avatar_id":"av2","pain_id":"p2","headline":"Offer 2","value":"Value","result":"Result","timeframe":"3d","cta":"CTA"}],"confidence":"medium"},
        "16_funnels": {"steps":[{"stage":"awareness","client_state":"cold","content":"Post","cta":"CTA","kpi":"KPI","next_step":"next"}],"confidence":"medium"},
        "17_advertising": {"campaigns":[{"platform":"vk","audience":"Women","creative":"Cre","offer":"Off","budget":"500","test_duration":"3","kpi":"CTR > 2%","success_threshold":"CTR > 2%","stop_threshold":"CTR < 1%","scale_threshold":"CTR > 3%"}],"confidence":"medium"},
        "18_content_plan": {"days":[{"day":1,"avatar_id":"av1","pain_id":"p1","offer_id":"o1","platform":"instagram","content_format":"post","archetype":"case","cta":"CTA","kpi":"KPI"}],"confidence":"medium"},
        "19_reels": {"reels":[{"archetype":"case","hook":"Hook","problem":"P","insight":"I","proof":"Pr","frame_1":"f1","frame_2":"f2","frame_3":"f3","frame_4":"f4","voiceover":"VO","on_screen_text":"T","cta":"CTA"}],"confidence":"medium"},
        "21_posts": {"posts":[{"platform":"instagram","avatar_id":"av1","pain_id":"p1","headline":"Head","post_text":"Text text text text text","cta":"CTA","hashtags":[],"target_action":"act","metric":"10 likes"}],"confidence":"medium"},
        "23_sales_scripts": {"scripts":[{"scenario":"first","goal":"Start","message":"Hello!","next_step":"Ask"}],"confidence":"medium"},
        "24_kpi": {"kpis":[{"action":"Reels","metric":"views","success_threshold":"5000","warning_threshold":"1500","fail_threshold":"500","if_success":"scale","if_warning":"keep","if_fail":"change"}],"confidence":"medium"},
        "25_first_7_days": {"days":[{"day":1,"preparation":["P"],"content":[],"ads":[],"kpi_check":[]}],"confidence":"medium"},
        "26_launch_plan": {"steps":[{"step_number":1,"action":"A","next_step":"B"},{"step_number":2,"action":"B","next_step":"C"},{"step_number":3,"action":"C","next_step":""}],"outcome":"Outcome","confidence":"medium"},
        "27_quality_control": {"overall_pass":True,"cross_validations":[],"stop_words_found":[],"hallucinations":[],"empties":[],"repeats":[],"disconnected_ctas":[],"disconnected_offers":[],"disconnected_content":[],"can_deliver_to_client":True,"quality_score":95.0},
    }

def _add_all(asm, data):
    for bid, d in data.items():
        asm.add_block(bid, True, d)

# ============================================================
# Test Successful Assembly
# ============================================================
class TestSuccessfulAssembly:
    def test_all_blocks_passed(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble()
        assert result.success is True
        assert result.final_data is not None
        assert len(result.errors) == 0
        assert len(result.blocks_failed) == 0

    def test_final_data_has_correct_fields(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble()
        fd = result.final_data
        assert fd.market_analysis is not None
        assert fd.avatars is not None
        assert fd.pains is not None
        assert fd.offers is not None
        assert fd.total_blocks_passed > 0

    def test_cross_validators_count(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble()
        assert len(result.cross_validation_results) >= 16


# ============================================================
# Test Failed Assembly (missing required blocks)
# ============================================================
class TestFailedAssembly:
    def test_one_required_block_failed(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        del data["11_avatars"]  # Avatars missing
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is False
        assert "11_avatars" in result.blocks_failed

    def test_multiple_required_blocks_failed(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        del data["13_pains"]
        del data["15_offers"]
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is False
        assert len(result.blocks_failed) >= 2
        assert "13_pains" in result.blocks_failed

    def test_blocks_passed_not_filled(self):
        asm = FinalDataAssembler()
        result = asm.assemble()
        assert result.success is False
        assert len(result.blocks_failed) >= len(FinalDataAssembler.REQUIRED_BLOCKS)


# ============================================================
# Cross-validator: avatar → pain
# ============================================================
class TestAvatarPain:
    def test_valid(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble()
        assert result.success is True

    def test_pain_with_unknown_avatar(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        data["13_pains"] = {"pains": [{"pain_id":"p_bad","avatar_id":"av99","pain":"P","severity":"high","emotion":"f","consequence":"c","solution":"s","offer":"o","cta":"c","metric":"m"}], "confidence":"medium"}
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is False
        assert any("av99" in e for e in result.errors)


# ============================================================
# Cross-validator: pain → offer
# ============================================================
class TestPainOffer:
    def test_valid(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble()
        assert result.success is True

    def test_offer_with_unknown_pain(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        data["15_offers"] = {"offers": [{"offer_id":"o_bad","avatar_id":"av1","pain_id":"p99","headline":"H","value":"V","result":"R","timeframe":"3d","cta":"CTA"}], "confidence":"medium"}
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is False
        assert any("p99" in e for e in result.errors)


# ============================================================
# Cross-validator: offer → CTA
# ============================================================
class TestOfferCTA:
    def test_valid(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble()
        assert result.success is True

    def test_offer_missing_cta(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        data["15_offers"] = {"offers": [{"offer_id":"o1","avatar_id":"av1","pain_id":"p1","headline":"H","value":"V","result":"R","timeframe":"3d","cta":""}], "confidence":"medium"}
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is False


# ============================================================
# Cross-validator: content → avatar
# ============================================================
class TestContentAvatar:
    def test_valid(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble()
        assert result.success is True

    def test_content_unknown_avatar_warns(self):
        """content→avatar is WARNING, so assembly still succeeds"""
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        data["18_content_plan"] = {"days": [{"day":1,"avatar_id":"av99","pain_id":"p1","offer_id":"o1","platform":"instagram","content_format":"post","archetype":"case","cta":"CTA","kpi":"KPI"}], "confidence":"medium"}
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is True  # WARNING doesn't block
        assert any("content→avatar" in vr.validator_name for vr in result.cross_validation_results)

    def test_content_unknown_offer_warns(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        data["18_content_plan"] = {"days": [{"day":1,"avatar_id":"av1","pain_id":"p1","offer_id":"o99","platform":"instagram","content_format":"post","archetype":"case","cta":"CTA","kpi":"KPI"}], "confidence":"medium"}
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is True
        assert any("content→offer" in vr.validator_name for vr in result.cross_validation_results)


# ============================================================
# Cross-validator: ads → audience
# ============================================================
class TestAdsAudience:
    def test_valid(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble()
        assert result.success is True

    def test_ads_missing_audience(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        data["17_advertising"] = {"campaigns": [{"platform":"vk","audience":"","creative":"C","offer":"O","budget":"500","test_duration":"3","kpi":"CTR > 2%","success_threshold":"CTR > 2%","stop_threshold":"CTR < 1%","scale_threshold":"CTR > 3%"}], "confidence":"medium"}
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is False


# ============================================================
# Cross-validator: posts → linkage
# ============================================================
class TestPostsLinkage:
    def test_post_with_unknown_offer_fails(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        data["21_posts"] = {"posts": [{"platform":"instagram","offer_id":"o99","avatar_id":"av1","pain_id":"p1","headline":"Head","post_text":"Text text text text text","cta":"CTA","hashtags":[],"target_action":"act","metric":"10 likes"}], "confidence":"medium"}
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is False

    def test_strict_mode_requires_optional_blocks(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble(strict=True)
        assert result.success is False
        assert "05_owner_portrait" in result.blocks_failed


# ============================================================
# Cross-validator: KPI → action
# ============================================================
class TestKPIAction:
    def test_valid(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble()
        assert result.success is True

    def test_kpi_missing_action(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        data["24_kpi"] = {"kpis": [{"action":"","metric":"views","success_threshold":"5000","warning_threshold":"1500","fail_threshold":"500","if_success":"s","if_warning":"w","if_fail":"f"}], "confidence":"medium"}
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is False


# ============================================================
# Cross-validator: launch chain broken
# ============================================================
class TestLaunchChain:
    def test_valid(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble()
        assert result.success is True

    def test_launch_missing_next_step(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        data["26_launch_plan"] = {"steps": [{"step_number":1,"action":"A","next_step":""}], "outcome":"O","confidence":"medium"}
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is False

    def test_launch_too_few_steps(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        data["26_launch_plan"] = {"steps": [{"step_number":1,"action":"A","next_step":""}], "outcome":"O","confidence":"medium"}
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is False  # Only 1 step, next_step empty


# ============================================================
# Cross-validator: pain → trigger
# ============================================================
class TestPainTrigger:
    def test_valid(self):
        asm = FinalDataAssembler()
        _add_all(asm, _mk_all_valid())
        result = asm.assemble()
        assert result.success is True

    def test_trigger_unknown_pain(self):
        asm = FinalDataAssembler()
        data = _mk_all_valid()
        data["14_triggers"] = {"triggers": [{"trigger_id":"t_bad","pain_id":"p99","avatar_id":"av1","trigger_text":"T","trigger_type":"fear"}], "confidence":"medium"}
        _add_all(asm, data)
        result = asm.assemble()
        assert result.success is False
