"""BlockResult — standard result type for all block executions."""

from __future__ import annotations

from dataclasses import dataclass, field

from ai_engine.validators.base import ValidationIssue, ValidationResult
from ai_engine.providers.base import LLMUsage


@dataclass
class BlockResult:
    """Result of executing a single block."""

    block_id: str = ""
    block_name: str = ""

    # Status
    status: str = "pending"  # pending → running → passed | failed
    passed: bool = False

    # Output
    data: dict = field(default_factory=dict)
    raw_response: str = ""

    # Validation
    validation_results: list[ValidationResult] = field(default_factory=list)
    all_validators_passed: bool = False

    # Repair
    repair_attempts: int = 0
    repair_results: list[BlockResult] = field(default_factory=list)
    repaired: bool = False

    # Timing & Usage
    elapsed_seconds: float = 0.0
    usage: LLMUsage = field(default_factory=LLMUsage)
    total_usage: LLMUsage = field(default_factory=LLMUsage)

    # Errors
    error: str = ""