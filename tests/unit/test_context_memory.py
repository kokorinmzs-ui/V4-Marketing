"""Tests for ContextMemory — Sprint 16-D (12 tests)."""
import pytest
from ai_engine.pipeline.context_memory import ContextMemory

CM = ContextMemory()

class TestContextMemory:
    def test_empty_returns_empty(self):
        m = CM.build({}, "10")
        assert isinstance(m, dict)

    def test_market_summary(self):
        m = CM.build({"01_market_analysis": {"market_overview": "Рынок Москвы", "market_size": "Средний", "channels": ["IG"]}}, "10")
        assert "market_summary" in m

    def test_constraints_preserved(self):
        m = CM.build({"02_business_diagnosis": {"constraints": ["A","B","C","D"], "quick_wins": ["Q1","Q2","Q3","Q4"], "focus_areas": ["F1","F2","F3"]}}, "10")
        assert len(m.get("constraints", [])) <= 3

    def test_competitors_count(self):
        m = CM.build({"03_competitors": {"competitors": [{"name": f"K{i}"} for i in range(10)]}}, "10")
        assert m.get("competitors_count") == 10
        assert len(m.get("top_competitors", [])) <= 3

    def test_platform_fields(self):
        m = CM.build({"04_platform": {"positioning": "A", "usp": "B", "tone_of_voice": "C"}}, "10")
        assert m.get("positioning") == "A"
        assert m.get("usp") == "B"

    def test_product_keys(self):
        m = CM.build({"06_product_system": {"lead_magnets": ["L1","L2"], "tripwires": ["T1"], "core_products": []}}, "10")
        assert "product_lead_magnets" in m

    def test_avatar_ids_preserved(self):
        avs = {"avatars": [{"avatar_id": f"av{i}", "name": f"N{i}", "occupation": "Job", "fears": ["f1","f2"]} for i in range(1, 6)]}
        m = CM.build({"11_avatars": avs}, "15")
        assert "avatar_ids" in m
        assert len(m["avatar_ids"]) == 5

    def test_pain_offer_maps(self):
        m = CM.build({
            "13_pains": {"pains": [{"pain_id": "p1", "avatar_id": "av1"}]},
            "15_offers": {"offers": [{"offer_id": "o1", "pain_id": "p1"}]}
        }, "15")
        assert m.get("pains_count") == 1
        assert m.get("offers_count") == 1

    def test_truncation_triggers(self):
        big = {"13_pains": {"pains": [{"pain_id": f"p{i:04d}", "avatar_id": "av1"} for i in range(200)]}}
        m = CM.build(big, "15")
        assert isinstance(m, dict)
        assert len(str(m)) < 5000

    def test_blob_size_limit(self):
        huge_data = {f"{i:02d}_block": {"data": "x" * 2000} for i in range(1, 20)}
        m = CM.build(huge_data, "15")
        assert len(str(m)) < 6000

    def test_ad_campaigns_count(self):
        m = CM.build({"17_advertising": {"campaigns": [{"platform":"vk"}, {"platform":"tg"}]}}, "15")
        assert m.get("ad_campaigns") == 2

    def test_content_plan_days(self):
        m = CM.build({"18_content_plan": {"days": list(range(30))}}, "15")
        assert m.get("content_plan_days") == 30