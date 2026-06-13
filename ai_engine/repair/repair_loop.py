"""RepairLoop — fixes ONLY erroneous fields, never rewrites the entire block."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Optional

from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity
from ai_engine.providers.base import LLMUsage


@dataclass
class RepairResult:
    """Result of a repair attempt."""

    success: bool = False
    repaired_data: dict[str, Any] = field(default_factory=dict)
    fields_fixed: list[str] = field(default_factory=list)
    fields_not_fixed: list[str] = field(default_factory=list)
    error: str = ""
    usage: LLMUsage = field(default_factory=LLMUsage)
    raw_response: str = ""


class RepairLoop:
    """Repairs only erroneous fields using the Repair Prompt.

    Does NOT regenerate the entire block.
    Fixes only fields listed in ValidationIssue.path.
    Maximum 3 repair attempts.
    """

    MAX_REPAIR_ATTEMPTS: int = 3

    def __init__(
        self,
        repair_prompt: str,
        generate_func: Any,
    ):
        """Initialize RepairLoop.

        Args:
            repair_prompt: The Repair Prompt from prompt library
            generate_func: A function like ai_service.generate() for LLM calls
        """
        self._repair_prompt = repair_prompt
        self._generate = generate_func

    def repair(
        self,
        original_data: dict[str, Any],
        validation_issues: list[ValidationIssue],
        block_id: str = "",
    ) -> RepairResult:
        """Attempt to repair erroneous fields.

        Args:
            original_data: The full original block data
            validation_issues: List of issues from validators
            block_id: Block identifier for context

        Returns:
            RepairResult with repaired data or error
        """
        # Extract only error/critical issues — warnings don't need repair
        errors = [
            i for i in validation_issues
            if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
        ]
        if not errors:
            return RepairResult(
                success=True,
                repaired_data=deepcopy(original_data),
                fields_fixed=[],
            )

        # Build repair input: only the problematic fields
        error_fields = []
        error_descriptions = []
        for issue in errors:
            path = issue.path
            error_fields.append(path)
            error_descriptions.append({
                "code": issue.code,
                "path": path,
                "message": issue.message,
                "suggestion": issue.suggestion,
            })

        # Build user prompt with original data and errors
        user_prompt = f"""
## ORIGINAL DATA
{original_data}

## ERRORS TO FIX
{error_descriptions}

## INSTRUCTION
Fix ONLY the fields listed in ERRORS TO FIX.
Do NOT change any other fields.
Return the corrected JSON.
"""

        # Call AI service
        response = self._generate(
            system_prompt=self._repair_prompt,
            user_prompt=user_prompt,
        )

        if response.status != "success" or not response.data:
            return RepairResult(
                success=False,
                error=f"Repair generation failed: {response.error}",
                usage=response.usage,
            )

        # Extract repaired data
        repaired = self._extract_repaired_data(response.data)
        if not repaired:
            return RepairResult(
                success=False,
                error="Could not extract repaired data from response",
                raw_response="",
                usage=response.usage,
            )

        # Merge: apply only the repaired fields to original data
        merged = deepcopy(original_data)
        fields_fixed = []
        for path in error_fields:
            value = self._get_nested(repaired, path)
            if value is not None:
                merged = self._set_nested(merged, path, value)
                fields_fixed.append(path)

        fields_not_fixed = [f for f in error_fields if f not in fields_fixed]

        return RepairResult(
            success=len(fields_fixed) > 0,
            repaired_data=merged,
            fields_fixed=fields_fixed,
            fields_not_fixed=fields_not_fixed,
            usage=response.usage,
            raw_response="",
        )

    def repair_until_pass(
        self,
        original_data: dict[str, Any],
        validators: list[Any],
        block_id: str = "",
    ) -> tuple[dict[str, Any], int, list[RepairResult]]:
        """Try to repair data until all validators pass, or max attempts exhausted.

        Args:
            original_data: The full original block data
            validators: List of validator functions (data → ValidationResult)
            block_id: Block identifier

        Returns:
            (repaired_data, attempts_used, repair_results)
        """
        current_data = deepcopy(original_data)
        repair_results = []

        for attempt in range(self.MAX_REPAIR_ATTEMPTS):
            # Validate current data
            all_issues = []
            for validator in validators:
                result = validator(current_data)
                all_issues.extend(result.issues)

            # Check if passed
            errors = [
                i for i in all_issues
                if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
            ]
            if not errors:
                # Already passed — no repair needed
                return current_data, attempt, repair_results

            # Attempt repair
            repair_result = self.repair(current_data, all_issues, block_id)
            repair_results.append(repair_result)

            if repair_result.success:
                current_data = repair_result.repaired_data
                # Re-validate immediately after repair
                new_issues = []
                for validator in validators:
                    vr = validator(current_data)
                    new_issues.extend(vr.issues)
                new_errors = [
                    i for i in new_issues
                    if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
                ]
                if not new_errors:
                    return current_data, attempt + 1, repair_results
            else:
                # Repair failed — return current state
                return current_data, attempt + 1, repair_results

        return current_data, self.MAX_REPAIR_ATTEMPTS, repair_results

    @staticmethod
    def _extract_repaired_data(data: Any) -> dict[str, Any] | None:
        """Extract repaired data from AI response."""
        if isinstance(data, dict):
            # Check for common wrapper: {"status": "success", "data": {...}}
            if "data" in data and isinstance(data["data"], dict):
                return data["data"]
            if "status" in data:
                return data
            return data
        return None

    @staticmethod
    def _get_nested(data: dict, path: str) -> Any:
        """Get a value from nested dict by dot-separated path or index."""
        keys = path.replace("[", ".").replace("]", "").split(".")
        current = data
        try:
            for key in keys:
                if not key:
                    continue
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list):
                    idx = int(key)
                    current = current[idx] if idx < len(current) else None
                else:
                    return None
            return current
        except (KeyError, IndexError, ValueError, TypeError):
            return None

    @staticmethod
    def _set_nested(data: dict, path: str, value: Any) -> dict:
        """Set a value in nested dict by path. Returns modified copy."""
        result = deepcopy(data)
        keys = path.replace("[", ".").replace("]", "").split(".")
        keys = [k for k in keys if k]
        if not keys:
            return result

        current = result
        for key in keys[:-1]:
            if isinstance(current, dict):
                if key not in current:
                    current[key] = {}
                current = current[key]
        if isinstance(current, dict):
            current[keys[-1]] = value
        return result