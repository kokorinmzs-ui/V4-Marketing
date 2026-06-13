"""Unit tests for FinalData schema."""

import pytest
from pydantic import ValidationError

from shared.schemas.final_data import FinalData
from shared.schemas.blocks import (
    MarketAnalysis, BusinessDiagnosis, Competitor, CompetitorAnalysis,
    MarketingPlatform, OwnerPortrait, Avatar, AvatarSet, Pain, Pains,
    Offer, Offers, KPISet, KPI, QualityControl, CrossValidationResult,
    Confidence,
)


class TestFinalDataValid:
    """Valid FinalData scenarios."""

    def test_empty_final_data(self):
        """Minimal valid FinalData (all blocks optional)."""
        fd = FinalData(
            project_id="proj-001",
            project_name="Фотостудия Воздух",
        )
        assert fd.project_id == "proj-001"
        assert fd.market_analysis is None
        assert fd.business_diagnosis is None
        assert fd.schema_version == "4.0"

    def test_final_data_with_market_analysis(self):
        """FinalData with BLOCK 01 populated."""
        fd = FinalData(
            project_id="proj-001",
            project_name="Фотостудия Воздух",
            market_analysis=MarketAnalysis(
                market_overview="Рынок фотостудий в Москве растёт",
                market_size="Средний",
                seasonality=["Осень — пик"],
                channels=["Instagram", "VK"],
                confidence=Confidence.MEDIUM,
            ),
        )
        assert fd.market_analysis is not None
        assert fd.market_analysis.market_overview != ""

    def test_final_data_with_multiple_blocks(self):
        """FinalData with several blocks populated."""
        fd = FinalData(
            project_id="proj-001",
            project_name="Фотостудия Воздух",
            market_analysis=MarketAnalysis(
                market_overview="Growing market",
                confidence=Confidence.HIGH,
            ),
            business_diagnosis=BusinessDiagnosis(
                constraints=["Нет контента"],
                quick_wins=["Запустить Instagram", "Создать лид-магнит", "Настроить VK Ads", "Сделать сайт", "Внедрить CRM"],
                confidence=Confidence.MEDIUM,
            ),
            platform=MarketingPlatform(
                positioning="Доступная фотостудия для контент-мейкеров",
                usp="Снимите месяц контента за один день",
                proof_points=["7 залов", "100+ отзывов", "Оборудование Profoto"],
            ),
            total_blocks_passed=3,
        )
        assert fd.market_analysis is not None
        assert fd.business_diagnosis is not None
        assert fd.platform is not None
        assert fd.total_blocks_passed == 3

    def test_final_data_with_competitors(self):
        """FinalData with competitor analysis (min 10)."""
        competitors = [
            Competitor(name=f"Competitor {i}", offer=f"Offer {i}")
            for i in range(1, 11)
        ]
        fd = FinalData(
            project_id="proj-001",
            project_name="Test",
            competitors=CompetitorAnalysis(
                competitors=competitors,
                advantages=["У нас лучше сервис"],
                gaps=["Нет предложений для новичков"],
            ),
        )
        assert len(fd.competitors.competitors) == 10

    def test_final_data_with_avatars_and_pains(self):
        """FinalData with avatars linked to pains."""
        avatars = [
            Avatar(
                avatar_id="av1",
                name="Анна",
                age=34,
                occupation="Маркетолог",
                income="150 000 ₽",
                goals=["Снимать 20 видео в месяц"],
                fears=["Выглядеть непрофессионально"],
            ),
            Avatar(
                avatar_id="av2",
                name="Дмитрий",
                age=28,
                occupation="Контент-мейкер",
                income="80 000 ₽",
                goals=["Снимать контент для клиентов"],
                fears=["Переплатить за аренду"],
            ),
        ]
        pains = [
            Pain(pain_id="p1", avatar_id="av1", pain="Нет времени на контент", solution="Контент за один съёмочный день"),
            Pain(pain_id="p2", avatar_id="av2", pain="Дорогая аренда", solution="Гибкие тарифы"),
        ]
        fd = FinalData(
            project_id="proj-001",
            project_name="Test",
            avatars=AvatarSet(avatars=avatars),
            pains=Pains(pains=pains),
        )
        assert len(fd.avatars.avatars) == 2
        assert len(fd.pains.pains) == 2

    def test_final_data_with_quality_control(self):
        """FinalData with Quality Control block."""
        fd = FinalData(
            project_id="proj-001",
            project_name="Test",
            quality_control=QualityControl(
                overall_pass=True,
                cross_validations=[
                    CrossValidationResult(validator="avatar→pain", passed=True),
                    CrossValidationResult(validator="pain→offer", passed=True),
                ],
                can_deliver_to_client=True,
                quality_score=95.0,
            ),
        )
        assert fd.quality_control.overall_pass is True
        assert fd.quality_control.quality_score == 95.0
        assert fd.quality_control.can_deliver_to_client is True


class TestFinalDataInvalid:
    """Invalid FinalData scenarios."""

    def test_missing_project_id(self):
        """Missing project_id should fail."""
        with pytest.raises(ValidationError):
            FinalData(project_name="Test")

    def test_missing_project_name(self):
        """Missing project_name should fail."""
        with pytest.raises(ValidationError):
            FinalData(project_id="proj-001")

    def test_invalid_confidence_score(self):
        """Confidence score out of range should fail."""
        with pytest.raises(ValidationError):
            FinalData(
                project_id="proj-001",
                project_name="Test",
                confidence_score=1.5,  # > 1.0
            )


class TestFinalDataEdgeCases:
    """Edge cases for FinalData."""

    def test_serialization_roundtrip(self):
        """FinalData should serialize and deserialize correctly."""
        fd = FinalData(
            project_id="proj-001",
            project_name="Test",
            total_blocks_passed=5,
            total_blocks_failed=2,
            confidence_score=0.85,
        )
        data = fd.model_dump()
        fd2 = FinalData(**data)
        assert fd2.project_id == fd.project_id
        assert fd2.total_blocks_passed == 5
        assert fd2.confidence_score == 0.85