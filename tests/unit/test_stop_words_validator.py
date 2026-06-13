"""Unit tests for StopWordsValidator."""

from ai_engine.validators.stop_words import StopWordsValidator, validate_stop_words
from ai_engine.validators.base import ValidationSeverity


class TestStopWordsPass:
    def test_clean_content_passes(self):
        result = validate_stop_words({
            "title": "Опубликуйте пост о выборе фотостудии",
            "cta": "Напишите ЗАЛ",
        })
        assert result.passed is True
        assert result.score == 100.0

    def test_specific_instructions_pass(self):
        result = validate_stop_words({
            "steps": [
                "Откройте Instagram",
                "Создайте пост",
                "Вставьте готовый текст",
                "Опубликуйте",
            ],
        })
        assert result.passed is True


class TestStopWordsFail:
    def test_marketing_fluff_detected(self):
        result = validate_stop_words({"positioning": "Наш уникальный подход"})
        # marketing_fluff is WARNING — passed remains True, but score drops
        assert result.score < 100.0
        assert any("уникальный" in i.message for i in result.issues)
        assert any(i.category == "marketing_fluff" for i in result.issues)

    def test_empty_advice_detected(self):
        result = validate_stop_words({"advice": "Нужно развивать соцсети"})
        assert any(i.category == "empty_advice" for i in result.issues)

    def test_placeholder_detected(self):
        result = validate_stop_words({"data": "нет информации о конкурентах"})
        issues = [i for i in result.issues if i.severity == ValidationSeverity.ERROR]
        assert len(issues) > 0
        assert any("нет информации" in i.message for i in result.issues)

    def test_hallucination_risk_detected(self):
        result = validate_stop_words({"claim": "Гарантированно получите 100% рост"})
        assert any(i.severity == ValidationSeverity.ERROR for i in result.issues)

    def test_medical_risk_critical(self):
        result = validate_stop_words({"text": "Наш препарат лечит"})
        assert any(i.severity == ValidationSeverity.CRITICAL for i in result.issues)


class TestStopWordsPath:
    def test_path_is_set(self):
        result = validate_stop_words({"title": "уникальный сервис"})
        for issue in result.issues:
            assert issue.path != ""
            assert "title" in issue.path

    def test_nested_path(self):
        result = validate_stop_words({"block": {"text": "развивать соцсети"}})
        assert any("block.text" in i.path for i in result.issues)

    def test_list_path(self):
        result = validate_stop_words({"items": ["нет информации"]})
        assert any("[0]" in i.path for i in result.issues)


class TestStopWordsScore:
    def test_score_drops_on_warnings(self):
        result = validate_stop_words({"title": "уникальный инновационный подход"})
        assert result.score < 100.0  # marketing_fluff = WARNING = -10 each

    def test_score_drops_on_errors(self):
        result = validate_stop_words({"title": "нет информации"})
        assert result.score < 100.0  # placeholder = ERROR = -20

    def test_score_never_below_zero(self):
        result = validate_stop_words({
            "a": "лечит",
            "b": "лечит",
            "c": "лечит",
            "d": "лечит",
            "e": "лечит",
        })
        assert result.score >= 0.0