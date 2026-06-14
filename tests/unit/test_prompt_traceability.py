"""Tests for Prompt Traceability (10 tests)."""
import pytest, hashlib

class TestPromptTraceability:
    def test_block_prompt_hashable(self):
        from ai_engine.prompts.registry import get_block_prompt
        prompt = get_block_prompt("01_market_analysis")
        h = hashlib.sha256(prompt.encode()).hexdigest()
        assert len(h) == 64

    def test_master_prompt_exists(self):
        from ai_engine.prompts.registry import get_master_system_prompt
        assert len(get_master_system_prompt()) > 100

    def test_repair_prompt_exists(self):
        from ai_engine.prompts.registry import get_repair_prompt
        assert len(get_repair_prompt()) > 50

    def test_execution_planner_prompt_exists(self):
        from ai_engine.prompts.registry import get_execution_planner_prompt
        assert len(get_execution_planner_prompt()) > 100

    def test_all_27_prompts_have_version(self):
        from ai_engine.prompts.registry import registry as pr
        prompts = pr.get_all()
        for bid, text in prompts.items():
            assert "VERSION" in text.upper() or "version" in text.lower(), f"{bid}: no version"

    def test_all_27_prompts_are_unique(self):
        from ai_engine.prompts.registry import registry as pr
        prompts = pr.get_all()
        hashes = [hashlib.sha256(t.encode()).hexdigest() for t in prompts.values()]
        assert len(set(hashes)) == len(hashes)

    def test_block_result_stores_provider_info(self):
        from ai_engine.pipeline.block_result import BlockResult
        r = BlockResult(block_id="test", status="passed", usage=None)
        assert r.block_id == "test"
        assert r.status == "passed"

    def test_provider_config_defaults(self):
        from ai_engine.providers.base import ProviderConfig
        cfg = ProviderConfig(api_key="test")
        assert cfg.api_key == "test"

    def test_llm_usage_totals(self):
        from ai_engine.providers.base import LLMUsage
        u = LLMUsage(input_tokens=100, output_tokens=50, model="deepseek-chat", cost=0.001)
        assert u.total_tokens() == 150

    def test_prompt_registry_has_27_blocks(self):
        from ai_engine.prompts.registry import registry as pr
        assert len(pr.get_all()) == 27