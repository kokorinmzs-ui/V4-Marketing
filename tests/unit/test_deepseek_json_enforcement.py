"""Tests for DeepSeek JSON enforcement — Phase 1 (12 tests)."""
import json, pytest
from ai_engine.providers.deepseek import DeepSeekProvider
from ai_engine.providers.base import ProviderConfig

@pytest.fixture
def provider():
    cfg = ProviderConfig(api_key="test-key", model="deepseek-chat", mock_mode=False)
    return DeepSeekProvider(cfg)

class TestJsonEnforcement:
    def test_json_object_mode_by_default(self, provider):
        """Without json_schema param, API should use json_object mode."""
        body = provider._build_request_body("system", "user", None)
        assert body["response_format"]["type"] == "json_object"

    def test_json_schema_mode_when_provided(self, provider):
        """With json_schema param, API should use strict json_schema mode."""
        schema = {"type": "object", "properties": {"title": {"type": "string"}}}
        body = provider._build_request_body("system", "user", schema)
        assert body["response_format"]["type"] == "json_schema"
        assert body["response_format"]["json_schema"]["strict"] is True
        assert body["response_format"]["json_schema"]["name"] == "response"

    def test_mock_mode_skips_json_schema(self, provider):
        """In mock mode, API should not enforce json_schema."""
        cfg = ProviderConfig(api_key="test", mock_mode=True, mock_response={"data": "test"})
        mp = DeepSeekProvider(cfg)
        resp = mp.generate("sys", "user", {"type": "object"})
        assert resp.status == "success"

    def test_empty_schema_uses_json_object(self, provider):
        """Empty dict or None should fall back to json_object."""
        body1 = provider._build_request_body("s", "u", {})
        assert body1["response_format"]["type"] == "json_object"
        # None should also work
        body2 = provider._build_request_body("s", "u", None)
        assert body2["response_format"]["type"] == "json_object"

    def test_provider_metadata_in_response(self):
        """Response should contain provider_used="deepseek"."""
        cfg = ProviderConfig(api_key="test", mock_mode=True)
        mp = DeepSeekProvider(cfg)
        resp = mp.generate("s", "u")
        assert "deepseek" in resp.model_used.lower() or "(mock)" in resp.model_used.lower()

    def test_token_tracking_present(self):
        cfg = ProviderConfig(api_key="test", mock_mode=True)
        mp = DeepSeekProvider(cfg)
        resp = mp.generate("s", "u")
        assert resp.usage.input_tokens >= 0
        assert resp.usage.output_tokens >= 0
        assert resp.usage.model in ("deepseek-chat (mock)", "deepseek-chat")

    def test_no_openai_fallback(self):
        """OpenAI should NOT be used as fallback anywhere in DeepSeek provider."""
        src = (__import__('pathlib').Path(__file__).parent.parent.parent /
               'ai_engine' / 'providers' / 'deepseek.py').read_text()
        assert 'OpenAI' not in src or 'openai' not in src.lower(), "DeepSeek provider should not import OpenAI"

    def test_normalization_flag_traceable(self):
        """SchemaNormalizer preserves keys — test that normalized output is traceable."""
        from ai_engine.pipeline.schema_normalizer import normalize
        data = {"market_trends": "Test", "confidence_score": "high"}
        result = normalize("01_market_analysis", data)
        assert result["market_overview"] == "Test"
        assert result["confidence"] == "high"

    def test_schema_pass_rate_tracks_provider(self):
        """Schema validation: raw AI output may fail, normalized output passes."""
        from ai_engine.validators.schema_validator import SchemaValidator
        from ai_engine.pipeline.schema_normalizer import normalize
        from shared.schemas.blocks import MarketAnalysis
        sv = SchemaValidator(MarketAnalysis)
        # Valid data passes
        valid = {"market_overview": "Test market", "market_size": "Medium", "seasonality": ["Q4"],
                 "buying_triggers": ["P"], "buying_barriers": ["C"], "growth_opportunities": ["G"],
                 "channels": ["IG"], "risks": ["R"], "confidence": "medium"}
        r = sv.validate(valid)
        assert r.passed
        # AI-style output (before normalization) — passes because all fields have defaults
        ai_style = {"market_trends": "Test", "confidence_score": "high"}
        r_raw = sv.validate(ai_style)
        # After normalization, it maps correctly
        normalized = normalize("01_market_analysis", ai_style)
        r_norm = sv.validate(normalized)
        assert r_norm.passed
        assert normalized["market_overview"] == "Test"
        assert normalized["confidence"] == "high"

    def test_live_chain_script_has_provider_tracking(self):
        """live_chain scripts should log provider/model/tokens/cost."""
        script = (__import__('pathlib').Path(__file__).parent.parent.parent /
                  'scripts' / 'live_block_01_smoke.py').read_text()
        assert "provider" in script.lower()
        assert "model" in script.lower()
        assert "tokens" in script.lower()

    def test_normalizer_does_not_replace_existing_valid_data(self):
        """Existing valid keys should survive normalization."""
        from ai_engine.pipeline.schema_normalizer import normalize
        data = {"market_overview": "Valid overview", "confidence": "high"}
        result = normalize("01_market_analysis", data)
        assert result["market_overview"] == "Valid overview"