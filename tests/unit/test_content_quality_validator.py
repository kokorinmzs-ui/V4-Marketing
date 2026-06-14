"""Unit tests for ContentQualityValidator."""

from ai_engine.validators.content_quality import ContentQualityValidator, validate_content_quality
from ai_engine.validators.base import ValidationSeverity


class TestContentQualityPass:
    def test_good_content_passes(self):
        result = validate_content_quality({
            "title": "Как выбрать зал для первой съёмки",
            "ready_text": "Если вы впервые бронируете фотостудию, напишите нам слово ЗАЛ",
            "cta": "Напишите слово ЗАЛ в директ",
        })
        assert result.passed is True
        assert result.score == 100.0

    def test_specific_content_passes(self):
        result = validate_content_quality({
            "steps": [
                "Откройте Instagram",
                "Снимите видео 15 секунд",
                "Опубликуйте",
            ],
        })
        assert result.passed is True


class TestContentQualityFail:
    def test_placeholder_detected(self):
        result = validate_content_quality({"title": "TODO: написать заголовок"})
        assert any(i.severity == ValidationSeverity.ERROR for i in result.issues)
        assert any(i.code == "content_placeholder" for i in result.issues)

    def test_generic_statement_detected(self):
        result = validate_content_quality({"title": "расскажем о нашей компании"})
        assert any(i.code == "content_generic" for i in result.issues)

    def test_marketing_fluff_detected(self):
        result = validate_content_quality({"offer": "наш уникальный инновационный подход"})
        assert any(i.code == "content_marketing_fluff" for i in result.issues)

    def test_too_short_important_field(self):
        result = validate_content_quality({"title": "Hi"})  # 2 chars < 15 min
        title_issues = [i for i in result.issues if i.path.endswith("title")]
        # title is in IMPORTANT_FIELDS, so < MIN_CONTENT_LENGTH triggers warning
        assert any(i.code == "content_too_short" for i in title_issues)


class TestContentQualityScore:
    def test_score_100_on_clean(self):
        result = validate_content_quality({"title": "Снять Reels про выбор фотостудии"})
        assert result.score == 100.0

    def test_score_drops_on_error(self):
        result = validate_content_quality({"title": "TODO: fix this"})
        assert result.score < 100.0
        assert result.score > 0.0

    def test_score_drops_on_warning(self):
        result = validate_content_quality({"title": "расскажем о нашей компании"})
        assert result.score < 100.0


class TestContentQualityContract:
    def test_low_score_for_multiple_warnings_forces_fail(self):
        result = validate_content_quality(
            {
                "title": "расскажем о нашей компании",
                "ready_text": "будьте в курсе",
                "cta": "лучшее качество",
                "message": "мы на рынке",
                "offer": "наш профессиональный подход",
            }
        )
        assert result.score < 50
        assert result.passed is False
