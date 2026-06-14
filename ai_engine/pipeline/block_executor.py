"""BlockExecutor — executes a single block: generate → validate → repair → passed/failed."""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

from ai_engine.pipeline.block_result import BlockResult
from ai_engine.pipeline.block_registry import BlockDefinition, BlockRegistry
from ai_engine.pipeline.dependency_graph import DependencyGraph
from ai_engine.repair.repair_loop import RepairLoop, RepairResult
from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity
from ai_engine.providers.base import LLMUsage


class BlockExecutor:
    """Executes a single block through the full pipeline.

    Flow:
    1. GENERATE → AIService.generate(block_prompt)
    2. VALIDATE → schema_validator → stop_words → content_quality → ...
    3. REPAIR (if errors) → fix only erroneous fields, max 3 attempts
    4. PASSED or FAILED
    """

    def __init__(
        self,
        block_registry: BlockRegistry,
        generate_func: Any,
        repair_prompt: str,
        max_repair_attempts: int = 3,
        system_prompt_prefix: str = "",
    ):
        self._block_registry = block_registry
        self._generate = generate_func
        self._system_prompt_prefix = system_prompt_prefix.strip()
        self._repair_loop = RepairLoop(
            repair_prompt=repair_prompt,
            generate_func=generate_func,
        )
        self._repair_loop.MAX_REPAIR_ATTEMPTS = max_repair_attempts

    def execute(self, block_id: str, context: Optional[dict[str, Any]] = None) -> BlockResult:
        """Execute a single block.

        Args:
            block_id: Block ID (e.g., "01_market_analysis")
            context: Optional context from previous blocks

        Returns:
            BlockResult with status, data, validation, repair info
        """
        start = time.time()
        block_def = self._block_registry.get(block_id)
        if not block_def:
            return BlockResult(
                block_id=block_id,
                status="failed",
                error=f"Block {block_id} not found in registry",
                elapsed_seconds=time.time() - start,
            )

        result = BlockResult(
            block_id=block_id,
            block_name=block_def.block_name,
            status="running",
        )

        # === STEP 1: GENERATE ===
        system_prompt = block_def.prompt
        if self._system_prompt_prefix:
            system_prompt = f"{self._system_prompt_prefix}\n\n{block_def.prompt}".strip()
        generate_response = self._generate(
            system_prompt=system_prompt,
            user_prompt=self._build_user_prompt(block_def, context),
            json_schema=block_def.json_schema,
        )

        if generate_response.status != "success":
            result.status = "failed"
            result.error = f"Generation failed: {generate_response.error}"
            result.elapsed_seconds = time.time() - start
            return result

        result.data = generate_response.data if isinstance(generate_response.data, dict) else {}
        result.raw_response = ""
        result.usage = generate_response.usage
        result.provider_used = getattr(generate_response, "provider_used", "")
        result.model_used = getattr(generate_response, "model_used", "")

        # === STEP 2: VALIDATE ===
        validation_results = self._run_validators(
            result.data, block_def.validators
        )
        result.validation_results = validation_results

        # Check if passed
        all_errors = [
            i for vr in validation_results for i in vr.issues
            if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
        ]
        if not all_errors:
            result.status = "passed"
            result.passed = True
            result.all_validators_passed = True
            result.elapsed_seconds = time.time() - start
            result.total_usage = self._sum_usage([result.usage])
            return result

        # === STEP 3: REPAIR (only if errors) ===
        all_issues = [
            i for vr in validation_results for i in vr.issues
        ]
        repaired_data, attempts, repair_results = self._repair_loop.repair_until_pass(
            original_data=result.data,
            validators=block_def.validators,
            block_id=block_id,
        )
        result.repair_attempts = attempts
        result.repair_results = [
            BlockResult(
                block_id=block_id,
                status="repairing",
                data=rr.repaired_data,
                repair_attempts=1,
                usage=rr.usage,
            )
            for rr in repair_results
        ]

        # Re-validate after repair
        result.data = repaired_data
        post_validation = self._run_validators(repaired_data, block_def.validators)
        result.validation_results = post_validation

        post_errors = [
            i for vr in post_validation for i in vr.issues
            if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
        ]

        if not post_errors:
            result.status = "passed"
            result.passed = True
            result.all_validators_passed = True
            result.repaired = attempts > 0
        elif attempts > self._repair_loop.MAX_REPAIR_ATTEMPTS:
            result.status = "failed"
            result.error = f"Repair exhausted after {attempts} attempts"
        else:
            result.status = "failed"
            result.error = "Validation failed and repair did not fix all issues"

        result.elapsed_seconds = time.time() - start
        total_usage = [result.usage] + [
            rr.usage for rr in repair_results
        ]
        result.total_usage = self._sum_usage(total_usage)
        return result

    def _run_validators(
        self,
        data: dict[str, Any],
        validators: list[Callable[[Any], ValidationResult]],
    ) -> list[ValidationResult]:
        """Run all validators on the data."""
        results = []
        for validator in validators:
            try:
                result = validator(data)
                results.append(result)
            except Exception as e:
                results.append(
                    ValidationResult(
                        validator_name="unknown",
                        passed=False,
                        issues=[
                            ValidationIssue(
                                code="validator_exception",
                                message=f"Validator error: {str(e)}",
                                severity=ValidationSeverity.ERROR,
                            )
                        ],
                    )
                )
        return results

    @staticmethod
    def _build_user_prompt(
        block_def: BlockDefinition,
        context: Optional[dict[str, Any]],
    ) -> str:
        """Build user prompt with context from previous blocks."""
        parts = []
        if context:
            parts.append("## PROJECT CONTEXT")
            parts.append(str(context))
        parts.append(f"## BLOCK: {block_def.block_name}")
        parts.append("Generate the JSON output for this block.")
        return "\n".join(parts)

    @staticmethod
    def _sum_usage(usages: list[LLMUsage]) -> LLMUsage:
        """Sum multiple LLMUsage records."""
        total = LLMUsage()
        for u in usages:
            total.input_tokens += u.input_tokens
            total.output_tokens += u.output_tokens
            total.cost += u.cost
        return total
