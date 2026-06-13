"""Unit tests for Brief schema."""

import pytest
from pydantic import ValidationError

from shared.schemas.brief import Brief, BriefValidationResult


class TestBriefValid:
    """Valid brief scenarios."""

    def test_minimal_brief(self):
        """Minimal valid brief with only required fields."""
        brief = Brief(
            project_name="Фотостудия Воздух",
            industry="photography_studio",
            business_description="Аренда фотостудий в Москве",
            project_id="custom-id-001",
        )
        assert brief.project_name == "Фотостудия Воздух"
        assert brief.industry == "photography_studio"
        assert brief.schema_version == "4.0"
        assert brief.project_id == "custom-id-001"

    def test_full_brief(self):
        """Full brief with all optional fields."""
        brief = Brief(
            project_name="Автосервис Быстрый",
            industry="auto_repair",
            business_description="Ремонт и обслуживание автомобилей в СПб",
            region="Санкт-Петербург",
            target_markets=["владельцы авто", "корпоративные парки"],
            products=["ТО", "Кузовной ремонт"],
            services=["Диагностика", "Эвакуация"],
            website="https://example.com",
            social_links=["https://vk.com/example"],
            goals=["Увеличить поток клиентов на 30%"],
            constraints=["Небольшой бюджет на рекламу"],
        )
        assert brief.project_name == "Автосервис Быстрый"
        assert brief.region == "Санкт-Петербург"
        assert len(brief.target_markets) == 2
        assert len(brief.goals) == 1

    def test_industry_normalization(self):
        """Industry should be normalized: strip, lower, spaces to underscores."""
        brief = Brief(
            project_name="Test",
            industry="Фото студия",
            business_description="Some business",
        )
        assert brief.industry == "фото_студия"

    def test_brief_validation_result(self):
        """BriefValidationResult should work."""
        result = BriefValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Минимальный бриф, данных может не хватить"],
        )
        assert result.is_valid is True
        assert len(result.warnings) == 1


class TestBriefInvalid:
    """Invalid brief scenarios."""

    def test_missing_project_name(self):
        """Missing project_name should raise ValidationError."""
        with pytest.raises(ValidationError):
            Brief(
                industry="photography",
                business_description="Some business",
            )

    def test_missing_industry(self):
        """Missing industry should raise ValidationError."""
        with pytest.raises(ValidationError):
            Brief(
                project_name="Test",
                business_description="Some business",
            )

    def test_missing_business_description(self):
        """Missing business_description should raise ValidationError."""
        with pytest.raises(ValidationError):
            Brief(
                project_name="Test",
                industry="photography",
            )

    def test_empty_project_name(self):
        """Empty project_name should raise ValidationError."""
        with pytest.raises(ValidationError):
            Brief(
                project_name="",
                industry="photography",
                business_description="Some business",
            )

    def test_empty_industry(self):
        """Empty industry should raise ValidationError from validator."""
        with pytest.raises(ValidationError):
            Brief(
                project_name="Test",
                industry="",
                business_description="Some business",
            )


class TestBriefEdgeCases:
    """Edge cases for brief validation."""

    def test_very_long_project_name(self):
        """Project name at max length should work."""
        long_name = "A" * 500
        brief = Brief(
            project_name=long_name,
            industry="test",
            business_description="Test",
        )
        assert len(brief.project_name) == 500

    def test_too_long_project_name(self):
        """Project name exceeding max length should fail."""
        too_long = "A" * 501
        with pytest.raises(ValidationError):
            Brief(
                project_name=too_long,
                industry="test",
                business_description="Test",
            )

    def test_default_values(self):
        """All default values should be set correctly."""
        brief = Brief(
            project_name="Test",
            industry="photography",
            business_description="Some business",
        )
        assert brief.region == ""
        assert brief.products == []
        assert brief.goals == []
        assert brief.constraints == []
        assert brief.schema_version == "4.0"