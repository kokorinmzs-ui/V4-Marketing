"""Actionability Validator — ensures tasks contain specific, executable instructions."""

from __future__ import annotations

from typing import Any

from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity


# Phrases that indicate non-actionable content — these must FAIL
NON_ACTIONABLE_PATTERNS: list[str] = [
    "развивать соцсети",
    "развивать социальные сети",
    "повышать узнаваемость",
    "работать над брендом",
    "увеличивать вовлечённость",
    "улучшать маркетинг",
    "повысить вовлеченность",
    "повысить узнаваемость",
    "увеличить вовлеченность",
    "развивать бренд",
    "улучшить маркетинг",
    "публикуйте контент",
    "сделайте продающий контент",
    "повышайте вовлечённость",
    "работайте над брендом",
    "развивайте соцсети",
    "улучшить позиционирование",
    "сделать ребрендинг",
    "запустить рекламу",
    "настроить таргет",
    "проработать аудиторию",
    "создать стратегию",
    "написать контент-план",
    "продумать воронку",
    "протестировать гипотезу",
    "сделать сайт",
]


class ActionabilityValidator:
    """Validates that tasks contain specific, executable actions.

    A task MUST have:
    - A specific action (what to do)
    - A place/platform (where to do it)
    - A timeframe (how long)
    - A metric (how to measure)
    - A next step (what after)

    Phrases like "развивать соцсети" must FAIL.
    """

    # Fields to check
    ELEMENTS_TO_CHECK: dict[str, list[str]] = {
        "action": ["title", "objective", "steps", "action"],
        "place": ["platform", "steps", "ready_text"],
        "time": ["estimated_time"],
        "metric": ["metric", "success_threshold", "kpi"],
        "next_step": ["if_success", "if_fail", "next_step"],
    }

    def validate(self, data: Any) -> ValidationResult:
        """Validate actionability of a task/mission."""
        issues: list[ValidationIssue] = []
        
        if isinstance(data, dict):
            self._check_dict(data, "", issues)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    self._check_dict(item, f"[{i}]", issues)

        score = self._calculate_score(issues)
        return ValidationResult(
            validator_name="actionability",
            passed=len([i for i in issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]) == 0,
            score=score,
            issues=issues,
        )

    def _check_dict(self, data: dict, path: str, issues: list[ValidationIssue]) -> None:
        """Check a single dict (task/mission) for actionability."""
        # Combine all text fields for non-actionable pattern checking
        all_text = " ".join(
            str(v) for v in data.values()
            if isinstance(v, str)
        ).lower()

        for pattern in NON_ACTIONABLE_PATTERNS:
            if pattern in all_text:
                issues.append(
                    ValidationIssue(
                        code="actionability_non_specific",
                        message=f"Non-actionable instruction detected: '{pattern}'. Must be a specific, executable action.",
                        path=f"{path}.title" if path else "title",
                        severity=ValidationSeverity.ERROR,
                        suggestion="Provide specific action: where, what exactly, how long, what to measure",
                    )
                )
                break  # One issue per task

        # Check for presence of key elements
        self._check_element(data, path, "action", issues)
        self._check_place(data, path, issues)
        self._check_time(data, path, issues)
        self._check_metric(data, path, issues)
        self._check_next_step(data, path, issues)
        self._check_steps_quality(data, path, issues)

    def _check_element(
        self, data: dict, path: str, element: str, issues: list[ValidationIssue]
    ) -> None:
        """Check if a required element is present in the task."""
        fields_to_check = self.ELEMENTS_TO_CHECK.get(element, [element])
        found = False
        for field in fields_to_check:
            value = data.get(field, "")
            if isinstance(value, list):
                value = " ".join(str(v) for v in value)
            if value and str(value).strip():
                found = True
                break
        
        if not found:
            # Action and metric are critical; time and next_step are warnings
            severity = ValidationSeverity.ERROR if element in ("action", "metric") else ValidationSeverity.WARNING
            messages = {
                "action": "Task missing specific action (what to do)",
                "place": "Task missing place/platform (where to do it)",
                "time": "Task missing estimated time",
                "metric": "Task missing metric (how to measure success)",
                "next_step": "Task missing next step (what to do after)",
            }
            suggestions = {
                "action": "Add a specific action: 'Откройте Instagram, создайте пост'",
                "place": "Specify where: platform, app, website",
                "time": "Add estimated time: '15 минут', '30 минут'",
                "metric": "Add a measurable metric: '20+ лайков', '3+ заявки'",
                "next_step": "Add next step: 'Если успех — повторить', 'Если провал — изменить CTA'",
            }
            issues.append(
                ValidationIssue(
                    code=f"actionability_missing_{element}",
                    message=messages.get(element, f"Missing {element}"),
                    path=path,
                    severity=severity,
                    suggestion=suggestions.get(element, ""),
                )
            )

    def _check_place(self, data: dict, path: str, issues: list[ValidationIssue]) -> None:
        self._check_element(data, path, "place", issues)

    def _check_time(self, data: dict, path: str, issues: list[ValidationIssue]) -> None:
        self._check_element(data, path, "time", issues)

    def _check_metric(self, data: dict, path: str, issues: list[ValidationIssue]) -> None:
        self._check_element(data, path, "metric", issues)

    def _check_next_step(self, data: dict, path: str, issues: list[ValidationIssue]) -> None:
        self._check_element(data, path, "next_step", issues)

    def _check_steps_quality(self, data: dict, path: str, issues: list[ValidationIssue]) -> None:
        """Check the quality of the steps array."""
        steps = data.get("steps", [])
        if isinstance(steps, list) and len(steps) >= 2:
            # Good — at least 2 steps
            return
        elif isinstance(steps, list) and len(steps) == 1:
            issues.append(
                ValidationIssue(
                    code="actionability_few_steps",
                    message="Task has only 1 step — provide at least 2 for clarity",
                    path=f"{path}.steps" if path else "steps",
                    severity=ValidationSeverity.WARNING,
                    suggestion="Break down the action into at least 2 concrete steps",
                )
            )
        # If steps is missing or not a list, the "missing action" element check will catch it

    @staticmethod
    def _calculate_score(issues: list[ValidationIssue]) -> float:
        if not issues:
            return 100.0
        errors = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        score = 100.0 - (errors * 25) - (warnings * 10)
        return max(0.0, score)


def validate_actionability(data: Any) -> ValidationResult:
    """Convenience function to validate actionability."""
    validator = ActionabilityValidator()
    return validator.validate(data)