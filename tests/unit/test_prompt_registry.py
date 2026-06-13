"""Unit tests for Prompt Registry."""

import pytest

from ai_engine.prompts.registry import (
    get_block_prompt,
    get_all_block_prompts,
    get_block_prompt_list,
    check_all_block_prompts_exist,
    get_master_system_prompt,
    get_repair_prompt,
    get_execution_planner_prompt,
)


class TestRegistryFunctions:
    def test_all_27_block_prompts_exist(self):
        ok, missing = check_all_block_prompts_exist()
        assert ok is True, f"Missing block prompts: {missing}"

    def test_get_all_block_prompts_returns_27(self):
        all_prompts = get_all_block_prompts()
        assert len(all_prompts) == 27

    def test_get_block_prompt_list_returns_27_sorted(self):
        ids = get_block_prompt_list()
        assert len(ids) == 27
        assert ids == sorted(ids)

    def test_get_block_prompt_known_id(self):
        prompt = get_block_prompt("01_market_analysis")
        assert prompt is not None
        assert "Анализ ниши" in prompt

    def test_get_block_prompt_unknown_id(self):
        prompt = get_block_prompt("99_nonexistent")
        assert prompt is None

    def test_get_block_prompt_last_block(self):
        prompt = get_block_prompt("27_quality_control")
        assert prompt is not None
        assert "Контроль качества" in prompt

    def test_get_master_system_prompt(self):
        prompt = get_master_system_prompt()
        assert "Senior Marketing Strategist" in prompt
        assert "JSON" in prompt

    def test_get_repair_prompt(self):
        prompt = get_repair_prompt()
        assert "исправь только ошибки" in prompt.lower() or "только ошибки" in prompt.lower() or "fix only" in prompt.lower()

    def test_get_execution_planner_prompt(self):
        prompt = get_execution_planner_prompt()
        assert "final_data" in prompt.lower()
        assert "execution_view_model" in prompt.lower()


class TestBlockPromptsContent:
    def test_every_prompt_has_version(self):
        import importlib
        for i in range(1, 28):
            block_id = f"{i:02d}"
            slugs = [
                "market_analysis", "business_diagnosis", "competitors",
                "platform", "owner_portrait", "product_system", "flagship",
                "product_ladder", "lead_magnets", "audience",
                "avatars", "psychotypes", "pains", "triggers", "offers",
                "funnels", "advertising", "content_plan", "reels",
                "blog_articles", "posts", "visual_briefs", "sales_scripts",
                "kpi", "first_7_days", "launch_plan", "quality_control",
            ]
            slug = slugs[i - 1]
            module_name = f"ai_engine.prompts.blocks.block_{block_id}_{slug}_prompt"
            mod = importlib.import_module(module_name)
            assert hasattr(mod, "VERSION"), f"Missing VERSION in {module_name}"

    def test_every_prompt_has_PROMPT_constant(self):
        prompts = get_all_block_prompts()
        for block_id, prompt_text in prompts.items():
            assert isinstance(prompt_text, str), f"Prompt {block_id} is not a string"
            assert len(prompt_text) > 100, f"Prompt {block_id} too short ({len(prompt_text)} chars)"