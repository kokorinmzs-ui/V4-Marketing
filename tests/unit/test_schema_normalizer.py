"""Tests for SchemaNormalizer — maps live AI output keys to Pydantic schema keys."""
import pytest
from ai_engine.pipeline.schema_normalizer import normalize

class TestNormalizeMarketAnalysis:
    def test_preserves_valid_keys(self):
        data = {"market_size": "Средний", "seasonality": ["Осень"]}
        result = normalize("01_market_analysis", data)
        assert result["market_size"] == "Средний"
        assert result["seasonality"] == ["Осень"]

    def test_alias_market_trends(self):
        data = {"market_trends": "Растёт спрос на студии"}
        result = normalize("01_market_analysis", data)
        assert result["market_overview"] == "Растёт спрос на студии"

    def test_alias_price_benchmark(self):
        data = {"price_benchmark": "Конкуренты дешевле"}
        result = normalize("01_market_analysis", data)
        assert result["buying_barriers"] == "Конкуренты дешевле"

    def test_alias_key_insights(self):
        data = {"key_insights": "Ниша растёт на 15% в год"}
        result = normalize("01_market_analysis", data)
        assert result["growth_opportunities"] == "Ниша растёт на 15% в год"

    def test_confidence_score_maps(self):
        data = {"confidence_score": "high"}
        result = normalize("01_market_analysis", data)
        assert result["confidence"] == "high"

    def test_fills_missing_defaults(self):
        data = {}
        result = normalize("01_market_analysis", data)
        assert "market_overview" in result
        assert "confidence" in result

    def test_combined_alias_and_defaults(self):
        data = {"market_trends": "Тренд", "confidence_score": 0.85}
        result = normalize("01_market_analysis", data)
        assert result["market_overview"] == "Тренд"
        assert result["market_size"] == "Неизвестно"
        assert result["confidence"] == "0.85"

class TestNormalizeAvatars:
    def test_avatar_list_alias(self):
        data = {"avatar_list": [{"name": "Anna"}]}
        result = normalize("11_avatars", data)
        assert "avatars" in result
        assert result["avatars"] == [{"name": "Anna"}]

class TestNormalizePlatform:
    def test_usp_unwrapped(self):
        data = {"usp": "Контент за день"}
        result = normalize("04_platform", data)
        assert result["usp"] == "Контент за день"

class TestNormalizeTriggers:
    def test_trigger_list_alias(self):
        data = {"trigger_list": [{"trigger_text": "T"}]}
        result = normalize("14_triggers", data)
        assert "triggers" in result
        assert result["triggers"] == [{"trigger_text": "T"}]

class TestNormalizeOffers:
    def test_offer_list_alias(self):
        data = {"offer_list": [{"headline": "O"}]}
        result = normalize("15_offers", data)
        assert "offers" in result
        assert result["offers"] == [{"headline": "O"}]

class TestNonDictPassthrough:
    def test_string_passthrough(self):
        assert normalize("01_market_analysis", "not a dict") == "not a dict"

class TestUnknownBlock:
    def test_no_alias_passthrough(self):
        data = {"custom_field": "value"}
        result = normalize("99_unknown", data)
        assert result == {"custom_field": "value"}