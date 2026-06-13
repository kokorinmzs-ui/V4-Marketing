"""Block Registry — register/get pattern for blocks (executor + prompt + validators)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ai_engine.validators.base import ValidationResult


@dataclass
class BlockDefinition:
    """Definition of a single block: its ID, prompt, and validators."""

    block_id: str
    block_name: str = ""
    prompt: str = ""
    # Validator functions: callable(data) → ValidationResult
    validators: list[Callable[[Any], ValidationResult]] = field(default_factory=list)
    # JSON schema for structured output (optional)
    json_schema: Optional[dict[str, Any]] = None


class BlockRegistry:
    """Registry for block definitions.

    Usage:
        reg = BlockRegistry()
        reg.register(BlockDefinition(
            block_id="01_market_analysis",
            block_name="Market Analysis",
            prompt="...",
            validators=[validate_schema, validate_stop_words],
        ))
        block_def = reg.get("01_market_analysis")
    """

    def __init__(self):
        self._blocks: dict[str, BlockDefinition] = {}

    def register(self, definition: BlockDefinition) -> None:
        """Register a block definition."""
        self._blocks[definition.block_id] = definition

    def get(self, block_id: str) -> Optional[BlockDefinition]:
        """Get a block definition by ID."""
        return self._blocks.get(block_id)

    def get_all_ids(self) -> list[str]:
        """Return sorted list of all registered block IDs."""
        return sorted(self._blocks.keys())

    def check_complete(self, expected_ids: list[str]) -> tuple[bool, list[str]]:
        """Check that all expected blocks are registered."""
        missing = [bid for bid in expected_ids if bid not in self._blocks]
        return len(missing) == 0, missing

    def __len__(self) -> int:
        return len(self._blocks)

    def __contains__(self, block_id: str) -> bool:
        return block_id in self._blocks