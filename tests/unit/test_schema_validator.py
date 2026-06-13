"""Unit tests for SchemaValidator."""

import pytest

from shared.schemas.brief import Brief
from ai_engine.validators.schema_validator import SchemaValidator, validate_schema


class TestSchemaValidatorPass:
    def test_valid_brief_passes(self):
        v = SchemaValidator(Brief)
        result = v.validate({
            "project_name": "Test",
            "industry": "photography",
            "business_description": "A photo studio",
        })
        assert result.passed is True
        assert result.score == 100.0
        assert len(result.issues) == 0

    def test_valid_brief_full(self):
        v = SchemaValidator(Brief)
        result = v.validate({
            "project_name": "Auto Service",
            "industry": "auto_repair",
            "business_description": "Car repair in Moscow",
            "region": "Moscow",
            "products": ["Repair"],
            "website": "https://example.com",
        })
        assert result.passed is True


class TestSchemaValidatorFail:
    def test_missing_required_field(self):
        v = SchemaValidator(Brief)
        result = v.validate({
            "project_name": "Test",
            "industry": "photography",
            # business_description missing
        })
        assert result.passed is False
        assert result.score < 100.0
        assert any(i.severity.value == "critical" for i in result.issues)
        assert any("business_description" in i.path for i in result.issues)

    def test_empty_project_name(self):
        v = SchemaValidator(Brief)
        result = v.validate({
            "project_name": "",
            "industry": "photography",
            "business_description": "Some business",
        })
        # Pydantic v2 treats min_length violations as WARNING
        # The validator catches it as an issue even though passed=True
        assert len(result.issues) > 0
        assert result.score < 100.0


class TestSchemaValidatorPath:
    def test_issue_path_is_set(self):
        v = SchemaValidator(Brief)
        result = v.validate({
            "project_name": "Test",
            "industry": "photography",
        })
        assert not result.passed
        for issue in result.issues:
            assert issue.path != ""

    def test_convenience_function(self):
        result = validate_schema(Brief, {
            "project_name": "Test",
            "industry": "photography",
            "business_description": "A business",
        })
        assert result.passed is True
        assert result.validator_name == "schema:Brief"