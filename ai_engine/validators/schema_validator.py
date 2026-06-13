"""Schema Validator — validates data against Pydantic models without throwing raw exceptions."""

from __future__ import annotations

from typing import Type

from pydantic import BaseModel, ValidationError as PydanticValidationError

from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity


class SchemaValidator:
    """Validates arbitrary data against a Pydantic model class.

    Does NOT raise raw exceptions — always returns a ValidationResult.
    """

    def __init__(self, model_class: Type[BaseModel]):
        self.model_class = model_class

    def validate(self, data: dict) -> ValidationResult:
        """Validate data against the model class."""
        issues: list[ValidationIssue] = []
        try:
            instance = self.model_class(**data)
            # Also validate by serializing back (catches nested issues)
            instance.model_dump()
        except PydanticValidationError as e:
            for error in e.errors():
                loc = ".".join(str(p) for p in error["loc"]) if error["loc"] else ""
                issues.append(
                    ValidationIssue(
                        code=f"schema_{error['type']}",
                        message=str(error["msg"]),
                        path=loc,
                        severity=self._map_severity(error["type"]),
                        suggestion=f"Provide a valid value for field '{loc}'",
                    )
                )
        except Exception as e:
            issues.append(
                ValidationIssue(
                    code="schema_unexpected_error",
                    message=f"Unexpected schema error: {str(e)}",
                    severity=ValidationSeverity.ERROR,
                )
            )

        score = self._calculate_score(issues)
        return ValidationResult(
            validator_name=f"schema:{self.model_class.__name__}",
            passed=len([i for i in issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]) == 0,
            score=score,
            issues=issues,
        )

    @staticmethod
    def _map_severity(error_type: str) -> ValidationSeverity:
        critical_types = {"missing", "value_error"}
        error_types = {"string_type", "int_type", "float_type", "bool_type", "list_type", "dict_type"}
        if error_type in critical_types:
            return ValidationSeverity.CRITICAL
        if error_type in error_types:
            return ValidationSeverity.ERROR
        return ValidationSeverity.WARNING

    @staticmethod
    def _calculate_score(issues: list[ValidationIssue]) -> float:
        if not issues:
            return 100.0
        criticals = sum(1 for i in issues if i.severity == ValidationSeverity.CRITICAL)
        errors = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        score = 100.0 - (criticals * 30) - (errors * 15) - (warnings * 5)
        return max(0.0, score)


def validate_schema(model_class: Type[BaseModel], data: dict) -> ValidationResult:
    """Convenience function to validate data against a Pydantic model."""
    validator = SchemaValidator(model_class)
    return validator.validate(data)