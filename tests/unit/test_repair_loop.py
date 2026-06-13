"""Unit tests for RepairLoop."""

import pytest

from ai_engine.repair.repair_loop import RepairLoop, RepairResult
from ai_engine.validators.base import ValidationIssue, ValidationSeverity
from ai_engine.services.ai_service import AIServiceConfig, AIService
from ai_engine.validators.stop_words import validate_stop_words
from ai_engine.validators.kpi_validator import validate_kpis


def make_mock_generate(return_data=None, return_error=False):
    """Create a mock generate function for testing."""
    calls = []

    def mock_gen(system_prompt="", user_prompt="", json_schema=None):
        calls.append({"system": system_prompt, "user": user_prompt})
        if return_error:
            from ai_engine.services.ai_service import AIServiceResponse
            return AIServiceResponse(status="error", error="Mock error")
        from ai_engine.services.ai_service import AIServiceResponse
        from ai_engine.providers.base import LLMUsage
        data = return_data or {"status": "success", "data": {"title": "Fixed title"}}
        return AIServiceResponse(
            status="success",
            data=data.get("data", data) if isinstance(data, dict) else {"fixed": True},
            usage=LLMUsage(model="mock", input_tokens=10, output_tokens=20, cost=0.001),
        )

    mock_gen.calls = calls
    return mock_gen


class TestRepairLoopUnit:
    def test_no_errors_returns_original(self):
        repair = RepairLoop(
            repair_prompt="Fix only errors",
            generate_func=make_mock_generate(),
        )
        result = repair.repair(
            original_data={"title": "Good title", "cta": "Good CTA"},
            validation_issues=[
                ValidationIssue(
                    code="test_warning",
                    message="Just a warning",
                    path="title",
                    severity=ValidationSeverity.WARNING,
                )
            ],
        )
        assert result.success is True
        assert result.repaired_data["title"] == "Good title"
        assert len(result.fields_fixed) == 0

    def test_error_fixes_field(self):
        mock_gen = make_mock_generate(
            return_data={"data": {"title": "Fixed title"}}
        )
        repair = RepairLoop(
            repair_prompt="Fix only errors",
            generate_func=mock_gen,
        )
        result = repair.repair(
            original_data={"title": "Bad", "cta": "Good CTA"},
            validation_issues=[
                ValidationIssue(
                    code="content_generic",
                    message="Generic statement",
                    path="title",
                    severity=ValidationSeverity.ERROR,
                    suggestion="Be specific",
                )
            ],
        )
        assert result.success is True
        assert "title" in result.fields_fixed
        assert result.repaired_data["cta"] == "Good CTA"  # Unchanged

    def test_repair_keeps_unchanged_fields(self):
        mock_gen = make_mock_generate(
            return_data={"data": {"cta": "Fixed CTA"}}
        )
        repair = RepairLoop(
            repair_prompt="Fix only errors",
            generate_func=mock_gen,
        )
        result = repair.repair(
            original_data={"title": "Good title", "cta": "bad cta"},
            validation_issues=[
                ValidationIssue(
                    code="kpi_vague",
                    message="Vague CTA",
                    path="cta",
                    severity=ValidationSeverity.ERROR,
                )
            ],
        )
        assert result.success is True
        assert "cta" in result.fields_fixed
        assert result.repaired_data["title"] == "Good title"  # Unchanged!

    def test_generate_failure_returns_error(self):
        mock_gen = make_mock_generate(return_error=True)
        repair = RepairLoop(
            repair_prompt="Fix only errors",
            generate_func=mock_gen,
        )
        result = repair.repair(
            original_data={"title": "Bad"},
            validation_issues=[
                ValidationIssue(
                    code="test_error",
                    message="Error",
                    path="title",
                    severity=ValidationSeverity.ERROR,
                )
            ],
        )
        assert result.success is False
        assert "Repair generation failed" in result.error


class TestRepairUntilPass:
    def test_clean_data_returns_immediately(self):
        mock_gen = make_mock_generate()
        repair = RepairLoop(
            repair_prompt="Fix only errors",
            generate_func=mock_gen,
        )

        from ai_engine.validators.stop_words import validate_stop_words
        data, attempts, results = repair.repair_until_pass(
            original_data={"title": "Clean title with specific action"},
            validators=[validate_stop_words],
        )
        assert attempts == 0  # No repair needed
        assert len(results) == 0

    def test_max_attempts_exhausted(self):
        # Repair returns success but with same bad data → loop runs all attempts
        mock_gen = make_mock_generate(
            return_data={"data": {"title": "нет информации о рынке"}}
        )
        repair = RepairLoop(
            repair_prompt="Fix only errors",
            generate_func=mock_gen,
        )
        repair.MAX_REPAIR_ATTEMPTS = 2

        data, attempts, results = repair.repair_until_pass(
            original_data={"title": "нет информации о рынке"},
            validators=[validate_stop_words],
        )
        assert attempts == 2
        assert len(results) == 2


class TestRepairLoopExtract:
    def test_extract_from_data_field(self):
        result = RepairLoop._extract_repaired_data(
            {"status": "success", "data": {"title": "Fixed"}}
        )
        assert result == {"title": "Fixed"}

    def test_extract_flat_dict(self):
        result = RepairLoop._extract_repaired_data({"title": "Fixed"})
        assert result == {"title": "Fixed"}

    def test_extract_none_for_non_dict(self):
        result = RepairLoop._extract_repaired_data("just a string")
        assert result is None


class TestRepairLoopNested:
    def test_get_nested_simple(self):
        data = {"a": {"b": "value"}}
        assert RepairLoop._get_nested(data, "a.b") == "value"

    def test_get_nested_list(self):
        data = {"items": ["first", "second"]}
        assert RepairLoop._get_nested(data, "items[0]") == "first"

    def test_set_nested_simple(self):
        data = {"a": {"b": "old"}}
        result = RepairLoop._set_nested(data, "a.b", "new")
        assert result["a"]["b"] == "new"

    def test_set_nested_preserves_other_fields(self):
        data = {"a": {"b": "old", "c": "keep"}}
        result = RepairLoop._set_nested(data, "a.b", "new")
        assert result["a"]["b"] == "new"
        assert result["a"]["c"] == "keep"