"""Prompt Registry — unified access to all prompts in the library.

Usage:
    from ai_engine.prompts.registry import registry

    registry.register("01_market_analysis", BLOCK_01_MARKET_ANALYSIS_PROMPT)
    prompt = registry.get("01_market_analysis")
    all_prompts = registry.get_all()
"""

from __future__ import annotations

from typing import Any, Callable, Optional


class _PromptRegistry:
    """Thread-safe registry for block prompts.

    Uses register()/get() pattern — no if/elif chains.
    """

    def __init__(self):
        self._prompts: dict[str, str] = {}
        self._expected_slugs: list[str] = []

    def register(self, block_id: str, prompt: str) -> None:
        """Register a block prompt.

        Args:
            block_id: e.g., '01_market_analysis'
            prompt: The prompt string
        """
        self._prompts[block_id] = prompt

    def get(self, block_id: str) -> Optional[str]:
        """Get a block prompt by ID.

        Args:
            block_id: e.g., '01_market_analysis'

        Returns:
            Prompt string or None if not registered
        """
        return self._prompts.get(block_id)

    def get_all(self) -> dict[str, str]:
        """Return a copy of all registered prompts."""
        return dict(self._prompts)

    def list_ids(self) -> list[str]:
        """Return sorted list of all registered block IDs."""
        return sorted(self._prompts.keys())

    def check_complete(self, expected_slugs: list[str]) -> tuple[bool, list[str]]:
        """Check that all expected blocks are registered.

        Args:
            expected_slugs: List of expected block IDs

        Returns:
            (ok, list_of_missing_ids)
        """
        missing = [s for s in expected_slugs if s not in self._prompts]
        return len(missing) == 0, missing

    def __len__(self) -> int:
        return len(self._prompts)

    def __contains__(self, block_id: str) -> bool:
        return block_id in self._prompts


# ============================================================
# Global registry instance
# ============================================================
registry = _PromptRegistry()

# Auto-register all 27 block prompts on import
EXPECTED_SLUGS = [
    "market_analysis", "business_diagnosis", "competitors",
    "platform", "owner_portrait", "product_system", "flagship",
    "product_ladder", "lead_magnets", "audience",
    "avatars", "psychotypes", "pains", "triggers", "offers",
    "funnels", "advertising", "content_plan", "reels",
    "blog_articles", "posts", "visual_briefs", "sales_scripts",
    "kpi", "first_7_days", "launch_plan", "quality_control",
]

try:
    import importlib

    for i, slug in enumerate(EXPECTED_SLUGS, start=1):
        block_id = f"{i:02d}_{slug}"
        module_name = f"ai_engine.prompts.blocks.block_{i:02d}_{slug}_prompt"
        mod = importlib.import_module(module_name)
        # Find the PROMPT constant (e.g., BLOCK_01_MARKET_ANALYSIS_PROMPT)
        prompt_attr = next(
            (name for name in dir(mod) if name.endswith("_PROMPT")), None
        )
        if prompt_attr:
            registry.register(block_id, getattr(mod, prompt_attr))
except ImportError:
    pass  # Will be populated when all files exist


# ============================================================
# Convenience functions (delegate to registry)
# ============================================================

def get_block_prompt(block_id: str) -> Optional[str]:
    """Get a block prompt by block ID."""
    return registry.get(block_id)


def get_all_block_prompts() -> dict[str, str]:
    """Return all 27 block prompts."""
    return registry.get_all()


def get_block_prompt_list() -> list[str]:
    """Return sorted list of all block IDs."""
    return registry.list_ids()


def check_all_block_prompts_exist() -> tuple[bool, list[str]]:
    """Check that all 27 block prompts exist."""
    return registry.check_complete(
        [f"{i:02d}_{slug}" for i, slug in enumerate(EXPECTED_SLUGS, start=1)]
    )


def get_master_system_prompt() -> str:
    """Get the Master System Prompt."""
    from ai_engine.prompts.system.master_system_prompt import MASTER_SYSTEM_PROMPT
    return MASTER_SYSTEM_PROMPT


def get_repair_prompt() -> str:
    """Get the Repair Prompt."""
    from ai_engine.prompts.repair.repair_prompt import REPAIR_PROMPT
    return REPAIR_PROMPT


def get_execution_planner_prompt() -> str:
    """Get the Execution Planner Prompt."""
    from ai_engine.prompts.execution.execution_planner_prompt import EXECUTION_PLANNER_PROMPT
    return EXECUTION_PLANNER_PROMPT
