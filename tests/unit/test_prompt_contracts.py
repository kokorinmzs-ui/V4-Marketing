"""Unit tests for Prompt Contracts — verifies every prompt meets structural requirements."""

import pytest

from ai_engine.prompts.registry import (
    get_all_block_prompts,
    get_master_system_prompt,
    get_repair_prompt,
    get_execution_planner_prompt,
)


class TestMasterSystemPrompt:
    def test_contains_key_rules(self):
        prompt = get_master_system_prompt()
        assert "JSON" in prompt
        assert "маркетинговую воду" in prompt.lower() or "marketing water" in prompt.lower()
        assert "halluci" in prompt.lower()
        assert "галлюцина" in prompt.lower() or "halluci" in prompt.lower()
        assert "пустых совет" in prompt.lower() or "empty advice" in prompt.lower() or "пустые совет" in prompt.lower()
        assert "27 блок" in prompt.lower() or "27 block" in prompt.lower() or "клиент" in prompt.lower()

    def test_has_version(self):
        from ai_engine.prompts.system.master_system_prompt import VERSION
        assert VERSION == "1.0.0"


class TestRepairPrompt:
    def test_contains_fix_only_rule(self):
        prompt = get_repair_prompt()
        text_lower = prompt.lower()
        assert "исправь только ошибк" in text_lower or "fix only" in text_lower or "только ошибочны" in text_lower

    def test_contains_no_rewrite_rule(self):
        prompt = get_repair_prompt()
        text_lower = prompt.lower()
        assert "не переписыва" in text_lower or "do not rewrite" in text_lower or "не переписывай" in text_lower

    def test_requires_json_output(self):
        prompt = get_repair_prompt()
        assert "JSON" in prompt or "json" in prompt.lower()

    def test_has_version(self):
        from ai_engine.prompts.repair.repair_prompt import VERSION
        assert VERSION == "1.0.0"


class TestExecutionPlannerPrompt:
    def test_contains_final_data(self):
        prompt = get_execution_planner_prompt()
        assert "final_data" in prompt.lower()

    def test_contains_execution_view_model(self):
        prompt = get_execution_planner_prompt()
        assert "execution_view_model" in prompt.lower()

    def test_no_re_analysis_rule(self):
        prompt = get_execution_planner_prompt()
        text_lower = prompt.lower()
        assert "не анализиров" in text_lower or "not to analyze" in text_lower or "not analyze" in text_lower or "do not analyze" in text_lower

    def test_forbidden_words_included(self):
        prompt = get_execution_planner_prompt()
        assert "запрещен" in prompt.lower() or "forbidden" in prompt.lower()

    def test_output_structure_mentioned(self):
        prompt = get_execution_planner_prompt()
        assert "missions" in prompt.lower()
        assert "days" in prompt.lower() or "30" in prompt

    def test_has_version(self):
        from ai_engine.prompts.execution.execution_planner_prompt import VERSION
        assert VERSION == "1.0.0"


class TestAllBlockPrompts:
    def test_all_27_have_json_mention(self):
        prompts = get_all_block_prompts()
        for block_id, prompt_text in prompts.items():
            assert "JSON" in prompt_text or "json" in prompt_text.lower(), (
                f"Block {block_id}: no JSON mention"
            )

    def test_all_27_have_forbidden_section(self):
        prompts = get_all_block_prompts()
        for block_id, prompt_text in prompts.items():
            text_lower = prompt_text.lower()
            assert "запрещен" in text_lower or "forbidden" in text_lower, (
                f"Block {block_id}: no forbidden section"
            )

    def test_all_27_have_output_section(self):
        prompts = get_all_block_prompts()
        for block_id, prompt_text in prompts.items():
            text_lower = prompt_text.lower()
            assert "выход" in text_lower or "output" in text_lower, (
                f"Block {block_id}: no output section"
            )

    def test_all_27_have_quality_rules_section(self):
        prompts = get_all_block_prompts()
        for block_id, prompt_text in prompts.items():
            text_lower = prompt_text.lower()
            assert "quality" in text_lower, (
                f"Block {block_id}: no quality section"
            )

    def test_all_27_have_version(self):
        import importlib
        slugs = [
            "market_analysis", "business_diagnosis", "competitors",
            "platform", "owner_portrait", "product_system", "flagship",
            "product_ladder", "lead_magnets", "audience",
            "avatars", "psychotypes", "pains", "triggers", "offers",
            "funnels", "advertising", "content_plan", "reels",
            "blog_articles", "posts", "visual_briefs", "sales_scripts",
            "kpi", "first_7_days", "launch_plan", "quality_control",
        ]
        for i, slug in enumerate(slugs, start=1):
            module_name = f"ai_engine.prompts.blocks.block_{i:02d}_{slug}_prompt"
            mod = importlib.import_module(module_name)
            assert hasattr(mod, "VERSION"), f"Missing VERSION in {module_name}"

    def test_all_27_have_PROMPT_constant(self):
        import importlib
        slugs = [
            "market_analysis", "business_diagnosis", "competitors",
            "platform", "owner_portrait", "product_system", "flagship",
            "product_ladder", "lead_magnets", "audience",
            "avatars", "psychotypes", "pains", "triggers", "offers",
            "funnels", "advertising", "content_plan", "reels",
            "blog_articles", "posts", "visual_briefs", "sales_scripts",
            "kpi", "first_7_days", "launch_plan", "quality_control",
        ]
        for i, slug in enumerate(slugs, start=1):
            module_name = f"ai_engine.prompts.blocks.block_{i:02d}_{slug}_prompt"
            mod = importlib.import_module(module_name)
            # Each module has a BLOCK_XX_XXXXXXXX_PROMPT constant
            has_prompt = any(
                name.endswith("_PROMPT") for name in dir(mod)
            )
            assert has_prompt, f"Missing PROMPT constant in {module_name}"