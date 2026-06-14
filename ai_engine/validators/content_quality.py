"""Content Quality Validator — catches empty content, placeholders, fluff, and generic statements."""

from __future__ import annotations

from typing import Any

from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity


# Generic marketing statements that indicate lack of specificity
GENERIC_STATEMENTS = [
    "расскажем о нашей компании",
    "расскажем о компании",
    "наша компания",
    "мы на рынке",
    "мы работаем с",
    "добро пожаловать",
    "рады представить",
    "следите за новостями",
    "подписывайтесь на обновления",
    "будьте в курсе",
    "самые низкие цены",
    "лучшее качество",
    "индивидуальный подход",
    "команда профессионалов",
]

# Minimum length for meaningful content
MIN_CONTENT_LENGTH = 15
# Fields that should have substantial content
IMPORTANT_FIELDS = {"title", "ready_text", "cta", "message", "pain", "offer", "headline", "why", "objective"}


class ContentQualityValidator:
    """Validates content quality: empty/short fields, placeholders, generic fluff.

    Score drops with each violation.
    """

    def validate(self, data: Any) -> ValidationResult:
        """Validate content quality of arbitrary data structure."""
        issues: list[ValidationIssue] = []
        self._check(data, "", issues)

        score = self._calculate_score(issues)
        passed = len([i for i in issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]) == 0
        if score < 50:
            passed = False
        return ValidationResult(
            validator_name="content_quality",
            passed=passed,
            score=score,
            issues=issues,
        )

    def _check(self, data: Any, path: str, issues: list[ValidationIssue]) -> None:
        """Recursively check data for quality issues."""
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
        """Check a single string for quality issues."""
        field_name = path.split(".")[-1] if "." in path else path

        # Empty or whitespace-only
        if not text or not text.strip():
            return  # Empty is checked by schema validator; here we only flag if in important fields

        # Too short for important fields
        if field_name in IMPORTANT_FIELDS and len(text.strip()) < MIN_CONTENT_LENGTH:
            issues.append(
                ValidationIssue(
                    code="content_too_short",
                    message=f"Content too short ({len(text.strip())} chars) for important field '{field_name}'",
                    path=path,
                    severity=ValidationSeverity.WARNING,
                    suggestion=f"Provide at least {MIN_CONTENT_LENGTH} characters of specific content",
                )
            )

        # Placeholder / stub detection
        placeholder_patterns = [
            "lorem ipsum", "todo", "fixme", "tbd", "text here",
            "здесь будет текст", "текст здесь", "заглушка", "рыба",
        ]
        text_lower = text.lower().strip()
        for pattern in placeholder_patterns:
            if pattern in text_lower:
                issues.append(
                    ValidationIssue(
                        code="content_placeholder",
                        message=f"Placeholder/stub detected: '{pattern}'",
                        path=path,
                        severity=ValidationSeverity.ERROR,
                        suggestion="Replace with actual content",
                    )
                )

        # Generic statements
        for generic in GENERIC_STATEMENTS:
            if generic in text_lower:
                issues.append(
                    ValidationIssue(
                        code="content_generic",
                        message=f"Generic statement detected: '{generic}'",
                        path=path,
                        severity=ValidationSeverity.WARNING,
                        suggestion="Replace with a specific, unique statement about the business",
                    )
                )
                break  # One generic warning per string

        # Marketing fluff detection (inline — check common patterns)
        fluff_patterns = [
            "уникальный", "инновационный", "революционный", "синергия",
            "экосистема", "лидер рынка", "экспертный подход", "комплексное решение",
            "качественный", "современный", "лучший", "надёжный",
            "профессиональный", "эффективный",
        ]
        for fluff in fluff_patterns:
            if fluff in text_lower:
                issues.append(
                    ValidationIssue(
                        code="content_marketing_fluff",
                        message=f"Marketing fluff detected: '{fluff}'",
                        path=path,
                        severity=ValidationSeverity.WARNING,
                        suggestion="Replace with a specific claim backed by evidence or numbers",
                    )
                )
                break

    @staticmethod
    def _calculate_score(issues: list[ValidationIssue]) -> float:
        if not issues:
            return 100.0
        errors = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        score = 100.0 - (errors * 20) - (warnings * 10)
        score = max(0.0, score)
        return score


def validate_content_quality(data: Any) -> ValidationResult:
    """Convenience function to validate content quality."""
    validator = ContentQualityValidator()
    return validator.validate(data)
