"""Tests for Blocks 01-10 — Sprint 7 (21 tests)."""

import pytest
from ai_engine.pipeline.block_registry import BlockRegistry, BlockDefinition
from ai_engine.pipeline.block_executor import BlockExecutor
from ai_engine.pipeline.dependency_graph import build_marketing_os_dependency_graph
from ai_engine.blocks.definitions import register_blocks_01_10
from ai_engine.repair.repair_loop import RepairLoop
from ai_engine.prompts.registry import get_repair_prompt
from ai_engine.validators.stop_words import validate_stop_words
from ai_engine.validators.content_quality import validate_content_quality
from ai_engine.validators.base import ValidationSeverity
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
    return reg

# ============================================================
# Registration
# ============================================================
class TestBlocksRegistration:
    def test_registry_contains_10_blocks(self):
        assert len(new_reg()) == 10
    def test_all_blocks_have_validators(self):
        r = new_reg()
        for bid in r.get_all_ids():
            assert len(r.get(bid).validators) >= 2
    def test_dependency_graph_order_01_10(self):
        g = build_marketing_os_dependency_graph()
        order = g.topological_order()
        assert order.index("01_market_analysis") < order.index("10_audience")

# ============================================================
# Valid data
# ============================================================
V01 = {"market_overview":"Рынок растёт","market_size":"Средний","seasonality":["Осень"],"buying_triggers":["Контент"],"buying_barriers":["Цена"],"growth_opportunities":["Рост"],"channels":["IG"],"risks":["Насыщение"],"confidence":"medium"}
V02 = {"constraints":["Нет контента","Нет CRM","Слабый оффер","Нет воронки","Нет повторов"],"quick_wins":["Запустить IG","Создать лид-магнит","Настроить VK","Сделать сайт","Внедрить CRM"],"growth_barriers":["Воронка","Оффер","Повторы"],"focus_areas":["Контент","Лиды"],"confidence":"medium"}
V03 = {"competitors":[{"name":f"K{i}","offer":f"O{i}","pricing":f"P{i}","channels":["IG"],"strengths":["S"],"weaknesses":["W"],"lead_magnets":["L"],"status":"analyzed","assumption":""} for i in range(1,11)],"advantages":["Сервис"],"gaps":["Новички"],"confidence":"medium"}
V04 = {"positioning":"Доступная студия","usp":"Контент за день","big_idea":"Контент без границ","tone_of_voice":"Дружелюбный","proof_points":["7 залов","100+ отзывов","Profoto"],"confidence":"medium"}
V05 = {"owner_story":"Основатель в 2018","expertise":"Коммерческая съёмка","trust_points":["10 лет","100+ клиентов","Преподаватель"],"confidence":"medium"}
V06 = {"lead_magnets":["Чек-лист"],"content_magnets":["Гайд"],"tripwires":["Пробная"],"core_products":["Аренда"],"flagship_products":["Полный день"],"upsells":["Оборудование"],"cross_sells":["Визаж"],"retention":["Абонемент"],"referrals":["Скидка"]}
V07 = {"product":"Аренда зала","audience":["Мейкеры"],"core_pains":["Нет зала"],"core_benefits":["7 залов"],"confidence":"medium"}
V08 = {"steps":[{"product_name":"Чек-лист","price":"0","next_step":"Пробная"},{"product_name":"Пробная","price":"990","next_step":"Аренда"},{"product_name":"Аренда","price":"2000","next_step":"Полный день"}],"confidence":"medium"}
V09 = {"magnets":[{"title":f"LM {i}","pain":f"Pain {i}","cta":f"CTA {i}","magnet_type":"checklist"} for i in range(1,11)],"confidence":"medium"}
V10 = {"segments":[{"segment_name":f"Сегмент {i}","description":f"Описание {i}","problem":f"Проблема {i}","motivation":f"Мотивация {i}"} for i in range(1,6)],"max_segments":15,"confidence":"medium"}

# ============================================================
# Success
# ============================================================
class TestSuccess:
    def test_01(self): assert ex(new_reg(), V01).execute("01_market_analysis").status == "passed"
    def test_02(self): assert ex(new_reg(), V02).execute("02_business_diagnosis").status == "passed"
    def test_03(self): assert ex(new_reg(), V03).execute("03_competitors").status == "passed"
    def test_04(self): assert ex(new_reg(), V04).execute("04_platform").status == "passed"
    def test_05(self): assert ex(new_reg(), V05).execute("05_owner_portrait").status == "passed"
    def test_06(self): assert ex(new_reg(), V06).execute("06_product_system").status == "passed"
    def test_07(self): assert ex(new_reg(), V07).execute("07_flagship").status == "passed"
    def test_08(self): assert ex(new_reg(), V08).execute("08_product_ladder").status == "passed"
    def test_09(self): assert ex(new_reg(), V09).execute("09_lead_magnets").status == "passed"
    def test_10(self): assert ex(new_reg(), V10).execute("10_audience").status == "passed"

# ============================================================
# Stop words
# ============================================================
class TestStopWords:
    def test_01(self): assert ex0(new_reg(), {**V01,"market_overview":"нет информации"}).execute("01_market_analysis").status == "failed"
    def test_03_placeholder(self):
        bad = {"competitors":[{**V03["competitors"][0],"offer":"нет информации"}],"advantages":[],"gaps":[],"confidence":"low"}
        assert ex0(new_reg(), bad).execute("03_competitors").status == "failed"
    def test_03_not_found(self):
        bad = {"competitors":[{"name":"K","offer":"не найдено","pricing":"","channels":[],"strengths":[],"weaknesses":[],"lead_magnets":[],"status":"analyzed","assumption":""}],"advantages":[],"gaps":[],"confidence":"low"}
        assert ex0(new_reg(), bad).execute("03_competitors").status == "failed"
    def test_04_fluff(self):
        bad = {"positioning":"нет информации","usp":"","big_idea":"","tone_of_voice":"","proof_points":[],"confidence":"medium"}
        assert ex0(new_reg(), bad).execute("04_platform").status == "failed"
    def test_10(self):
        bad = {"segments":[{"segment_name":"S1","description":"нет информации","problem":"P","motivation":"M"}],"max_segments":15,"confidence":"medium"}
        assert ex0(new_reg(), bad).execute("10_audience").status == "failed"

# ============================================================
# Repair
# ============================================================
class TestRepair:
    def test_01(self):
        cnt=[0]
        def g(**kwargs):
            cnt[0]+=1
            from ai_engine.services.ai_service import AIServiceResponse
            if cnt[0]==1:
                return AIServiceResponse(status="success", data={**V01,"market_overview":"нет информации"}, usage=LLMUsage(model="m",input_tokens=10,output_tokens=5,cost=0.001))
            return AIServiceResponse(status="success", data=V01, usage=LLMUsage(model="m",input_tokens=10,output_tokens=5,cost=0.001))
        r = BlockExecutor(new_reg(), g, get_repair_prompt(), max_repair_attempts=1).execute("01_market_analysis")
        assert r.status == "passed"
        assert r.repaired is True

# ============================================================
# Structural
# ============================================================
class TestStructural:
    def test_03_10_competitors(self):
        r = ex(new_reg(), V03).execute("03_competitors")
        assert len(r.data["competitors"]) == 10
    def test_06_product_roles(self):
        r = ex(new_reg(), V06).execute("06_product_system")
        for k in ["lead_magnets","tripwires","core_products","flagship_products","upsells","cross_sells","retention","referrals"]:
            assert len(r.data.get(k,[])) >= 1, f"Missing {k}"
    def test_09_10_magnets(self):
        r = ex(new_reg(), V09).execute("09_lead_magnets")
        assert len(r.data["magnets"]) >= 10
    def test_10_5_segments(self):
        r = ex(new_reg(), V10).execute("10_audience")
        assert len(r.data["segments"]) >= 5