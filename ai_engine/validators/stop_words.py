"""Stop Words Validator — detects prohibited words/phrases in any text content."""

from __future__ import annotations

from typing import Any

from shared.constants import load_stop_words

from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity


class StopWordsValidator:
    """Validates text content against the global Stop Words Registry.

    Recursively checks all string fields in any dict/list/str structure.
    Returns path to the problematic field.
    Distinguishes between 7 categories of stop words.
    """

    def __init__(self):
        self.stop_words: dict = load_stop_words()
        self.categories: dict = self.stop_words.get("categories", {})

    def validate(self, data: Any, root_path: str = "") -> ValidationResult:
        """Validate arbitrary data structure for stop words."""
        issues: list[ValidationIssue] = []
        self._check(data, "", issues)

        score = self._calculate_score(issues)
        return ValidationResult(
            validator_name="stop_words",
            passed=len([i for i in issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]) == 0,
            score=score,
            issues=issues,
        )

    def _check(self, data: Any, path: str, issues: list[ValidationIssue]) -> None:
        """Recursively check data for stop words."""
        if isinstance(data, str):
            self._check_string(data, path, issues)
        elif isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                self._check(value, new_path, issues)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                self._check(item, new_path, issues)

    def _check_string(self, text: str, path: str, issues: list[ValidationIssue]) -> None:
        """Check a single string against all stop word categories."""
        text_lower = text.lower()
        for cat_name, cat_info in self.categories.items():
            words = cat_info.get("words", [])
            rule = cat_info.get("rule", "")
            for word in words:
                if word in text_lower:
                    severity = self._severity_for_category(cat_name)
                    issues.append(
                        ValidationIssue(
                            code=f"stop_word_{cat_name}",
                            message=f"Stop word detected: '{word}' ({cat_info.get('description', cat_name)})",
                            path=path,
                            severity=severity,
                            suggestion=self._suggestion_for_category(cat_name),
                            category=cat_name,
                        )
                    )
                    # One issue per string per category is enough
                    break

    @staticmethod
    def _severity_for_category(cat_name: str) -> ValidationSeverity:
        critical_cats = {"medical_risk", "dangerous_promises", "ads_risk"}
        error_cats = {"placeholders", "hallucination_risk"}
        warning_cats = {"empty_advice", "marketing_fluff"}
        if cat_name in critical_cats:
            return ValidationSeverity.CRITICAL
        if cat_name in error_cats:
            return ValidationSeverity.ERROR
        return ValidationSeverity.WARNING

    @staticmethod
    def _suggestion_for_category(cat_name: str) -> str:
        suggestions = {
            "marketing_fluff": "Replace with a specific, verifiable claim with numbers or facts",
            "empty_advice": "Replace with a specific actionable instruction (where, what, when, how)",
            "placeholders": "Provide actual data, or use assumption with confidence=low",
            "hallucination_risk": "Add verifiable source, or state this is a hypothesis",
            "dangerous_promises": "Remove absolute guarantees; use 'может помочь', 'в среднем'",
            "ads_risk": "Remove financial claims; comply with platform ad policies",
            "medical_risk": "Remove medical claims; refer to medical professionals",
        }
        return suggestions.get(cat_name, "Replace the prohibited phrase")

    @staticmethod
    def _calculate_score(issues: list[ValidationIssue]) -> float:
        if not issues:
            return 100.0
        criticals = sum(1 for i in issues if i.severity == ValidationSeverity.CRITICAL)
        errors = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        score = 100.0 - (criticals * 50) - (errors * 20) - (warnings * 10)
        return max(0.0, score)


def validate_stop_words(data: Any) -> ValidationResult:
    """Convenience function to validate data for stop words."""
    validator = StopWordsValidator()
    return validator.validate(data)