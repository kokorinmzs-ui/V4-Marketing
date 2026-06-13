"""KPI Validator — blocks vague metrics and requires numeric thresholds."""

from __future__ import annotations

import re
from typing import Any

from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity

VAGUE_KPI_PATTERNS: list[str] = [
    "хороший результат", "много заявок", "много просмотров", "много клиентов",
    "много продаж", "много сообщений", "высокий ctr", "высокий охват",
    "нормальная конверсия", "хорошая конверсия", "хороший ctr", "хороший охват",
    "мало заявок", "мало клиентов", "низкий ctr", "хорошо", "плохо", "много",
    "мало", "нормально", "отлично", "средне", "высокий", "низкий",
]
_NUMERIC_RE = re.compile(r"\d+", re.IGNORECASE)


class KPIValidator:
    KPI_FIELDS: set[str] = {
        "metric", "kpi", "success_threshold", "warning_threshold",
        "fail_threshold",
    }

    def validate(self, data: Any) -> ValidationResult:
        issues: list[ValidationIssue] = []
        self._check(data, "", issues)
        score = self._calculate_score(issues)
        return ValidationResult(
            validator_name="kpi_validator",
            passed=len([i for i in issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]) == 0,
            score=score, issues=issues,
        )

    def _check(self, data: Any, path: str, issues: list[ValidationIssue]) -> None:
        if isinstance(data, str):
            fn = path.split(".")[-1] if "." in path else path
            if fn in self.KPI_FIELDS and data.strip():
                self._check_kpi_string(data, path, issues)
        elif isinstance(data, dict):
            for k, v in data.items():
                self._check(v, f"{path}.{k}" if path else k, issues)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._check(item, f"{path}[{i}]", issues)

    def _check_kpi_string(self, text: str, path: str, issues: list[ValidationIssue]) -> None:
        t = text.lower().strip()
        for vague in VAGUE_KPI_PATTERNS:
            if vague in t:
                issues.append(ValidationIssue(code="kpi_vague", message=f"Vague KPI: '{vague}'", path=path, severity=ValidationSeverity.ERROR, suggestion="Use numeric KPIs: 'CTR > 2%', '3+ заявки'"))
                return
        if not _NUMERIC_RE.search(text):
            issues.append(ValidationIssue(code="kpi_not_numeric", message=f"KPI '{text}' has no numbers", path=path, severity=ValidationSeverity.ERROR, suggestion="Include numeric threshold"))

    @staticmethod
    def _calculate_score(issues: list[ValidationIssue]) -> float:
        return max(0.0, 100.0 - sum(1 for i in issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)) * 25)


def validate_kpis(data: Any) -> ValidationResult:
    return KPIValidator().validate(data)