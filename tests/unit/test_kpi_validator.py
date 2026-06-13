"""Unit tests for KPIValidator."""

from ai_engine.validators.kpi_validator import KPIValidator, validate_kpis
from ai_engine.validators.base import ValidationSeverity


class TestKPIValidatorPass:
    def test_numeric_ctr_passes(self):
        result = validate_kpis({"metric": "CTR > 2%"})
        assert result.passed is True
        assert result.score == 100.0

    def test_numeric_requests_passes(self):
        result = validate_kpis({"success_threshold": "3+ заявки"})
        assert result.passed is True

    def test_numeric_cpl_passes(self):
        result = validate_kpis({"kpi": "CPL < 700 руб"})
        assert result.passed is True

    def test_mixed_content_with_number(self):
        result = validate_kpis({"metric": "10 сохранений за 48 часов"})
        assert result.passed is True


class TestKPIValidatorFail:
    def test_vague_good_result_blocks(self):
        result = validate_kpis({"metric": "хороший результат"})
        assert result.passed is False
        assert any(i.code == "kpi_vague" for i in result.issues)

    def test_vague_many_requests_blocks(self):
        result = validate_kpis({"success_threshold": "много заявок"})
        assert any(i.code == "kpi_vague" for i in result.issues)

    def test_vague_high_ctr_blocks(self):
        result = validate_kpis({"kpi": "высокий CTR"})
        assert any(i.code == "kpi_vague" for i in result.issues)

    def test_vague_normal_conversion_blocks(self):
        result = validate_kpis({"metric": "нормальная конверсия"})
        assert any(i.code == "kpi_vague" for i in result.issues)

    def test_no_number_at_all(self):
        result = validate_kpis({"metric": "увеличить охват"})
        # No number at all — must fail with kpi_not_numeric
        assert result.passed is False
        assert any(i.code == "kpi_not_numeric" for i in result.issues)

    def test_single_word_vague(self):
        result = validate_kpis({"metric": "много"})
        assert any(i.code == "kpi_vague" for i in result.issues)

    def test_vague_high_alone(self):
        result = validate_kpis({"success_threshold": "высокий"})
        assert any(i.code == "kpi_vague" for i in result.issues)


class TestKPIValidatorSeverity:
    def test_vague_kpi_is_error(self):
        result = validate_kpis({"metric": "хороший результат"})
        vague_issues = [i for i in result.issues if i.code == "kpi_vague"]
        assert all(i.severity == ValidationSeverity.ERROR for i in vague_issues)

    def test_not_numeric_is_error(self):
        result = validate_kpis({"metric": "увеличить охват"})
        nn_issues = [i for i in result.issues if i.code == "kpi_not_numeric"]
        assert all(i.severity == ValidationSeverity.ERROR for i in nn_issues)


class TestKPIValidatorPath:
    def test_path_is_set(self):
        result = validate_kpis({"metric": "хороший результат"})
        assert any("metric" in i.path for i in result.issues)


class TestKPIValidatorScore:
    def test_score_100_on_good_kpi(self):
        result = validate_kpis({"metric": "CTR > 1.5%"})
        assert result.score == 100.0

    def test_score_drops_on_vague(self):
        result = validate_kpis({"metric": "хороший результат"})
        assert result.score < 100.0

    def test_score_drops_on_non_numeric(self):
        result = validate_kpis({"metric": "увеличить вовлечённость"})
        assert result.score < 100.0

    def test_non_kpi_field_ignored(self):
        """Fields not in KPI_FIELDS should be ignored."""
        result = validate_kpis({"title": "хороший результат", "description": "много заявок"})
        assert result.score == 100.0  # title/description are not KPI fields