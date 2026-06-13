"""Base models for all validators in Marketing OS v4."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity level of a validation issue."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationIssue(BaseModel):
    """A single issue found during validation."""

    code: str = Field(..., description="Machine-readable error code (e.g., missing_cta, stop_word_detected)")
    message: str = Field(..., description="Human-readable description of the issue")
    path: str = Field(default="", description="JSON path or field name where the issue was found")
    severity: ValidationSeverity = Field(default=ValidationSeverity.ERROR, description="Severity level")
    suggestion: str = Field(default="", description="Suggested fix or replacement")
    category: str = Field(default="", description="Category of the issue (e.g., marketing_fluff, empty_advice)")


class ValidationResult(BaseModel):
    """Result of running a validator."""

    validator_name: str = Field(..., description="Name of the validator")
    passed: bool = Field(..., description="Whether validation passed")
    score: float = Field(default=100.0, ge=0.0, le=100.0, description="Quality score 0-100")
    issues: list[ValidationIssue] = Field(default_factory=list, description="List of issues found")
    metadata: dict = Field(default_factory=dict, description="Arbitrary metadata about the validation run")

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.CRITICAL)