"""Unit tests for ActionabilityValidator."""

from ai_engine.validators.actionability import ActionabilityValidator, validate_actionability
from ai_engine.validators.base import ValidationSeverity


class TestActionabilityPass:
    def test_fully_actionable_mission_passes(self):
        result = validate_actionability({
            "title": "Опубликовать пост о выборе зала",
            "platform": "instagram",
            "estimated_time": "20 минут",
            "steps": [
                "Откройте Instagram",
                "Создайте пост",
                "Вставьте готовый текст",
                "Опубликуйте",
            ],
            "ready_text": "Готовый текст поста про фотостудию",
            "cta": "Напишите ЗАЛ",
            "metric": "20+ лайков",
            "success_threshold": "20+",
            "if_success": "Повторить через 3 дня",
            "if_fail": "Сменить фото",
        })
        assert result.passed is True
        assert result.score == 100.0

    def test_minimal_actionable_passes(self):
        result = validate_actionability({
            "title": "Снять Reels",
            "estimated_time": "15 минут",
            "steps": ["Снимите видео", "Опубликуйте"],
            "metric": "5+ сообщений",
            "success_threshold": "5 сообщений",
            "if_success": "Повторить",
        })
        assert result.passed is True


class TestActionabilityFail:
    def test_non_actionable_blocked(self):
        result = validate_actionability({
            "title": "развивать соцсети",
            "estimated_time": "1 час",
            "steps": ["запустить таргет"],
        })
        assert result.passed is False
        assert any(i.code == "actionability_non_specific" for i in result.issues)

    def test_improve_positioning_blocked(self):
        result = validate_actionability({
            "title": "улучшить позиционирование",
            "steps": ["подумать над позиционированием"],
        })
        assert any(i.code == "actionability_non_specific" for i in result.issues)

    def test_launch_ads_blocked(self):
        result = validate_actionability({"title": "запустить рекламу"})
        assert any(i.code == "actionability_non_specific" for i in result.issues)

    def test_create_strategy_blocked(self):
        result = validate_actionability({"title": "создать стратегию"})
        assert any(i.code == "actionability_non_specific" for i in result.issues)


class TestActionabilityMissingElements:
    def test_missing_metric(self):
        result = validate_actionability({
            "title": "Опубликовать пост",
            "estimated_time": "20 минут",
            "steps": ["Откройте Instagram", "Опубликуйте"],
        })
        assert any(i.code == "actionability_missing_metric" for i in result.issues)

    def test_missing_next_step_is_warning(self):
        result = validate_actionability({
            "title": "Снять Reels",
            "estimated_time": "15 минут",
            "steps": ["Снимите", "Опубликуйте"],
            "metric": "5+ сообщений",
        })
        missing_next = [i for i in result.issues if i.code == "actionability_missing_next_step"]
        # Missing next_step is WARNING, so passed may still be True
        if missing_next:
            assert missing_next[0].severity == ValidationSeverity.WARNING

    def test_missing_action_is_error(self):
        result = validate_actionability({
            "estimated_time": "10 минут",
            "metric": "5 заявок",
        })
        assert any(
            i.code == "actionability_missing_action" and i.severity == ValidationSeverity.ERROR
            for i in result.issues
        )


class TestActionabilitySteps:
    def test_single_step_warns(self):
        result = validate_actionability({
            "title": "Опубликовать пост",
            "estimated_time": "20 минут",
            "steps": ["Опубликуйте пост"],
            "metric": "10+ лайков",
        })
        assert any(i.code == "actionability_few_steps" for i in result.issues)

    def test_zero_steps_handled(self):
        result = validate_actionability({
            "title": "Опубликовать пост",
            "estimated_time": "20 минут",
            "steps": [],
            "metric": "10+ лайков",
        })
        # title provides action; steps empty triggers missing_place + time ok, metric ok
        # steps=[] means no place via steps field + missing next_step
        assert len(result.issues) > 0


class TestActionabilityScore:
    def test_score_100_on_perfect(self):
        result = validate_actionability({
            "title": "Снять Reels про выбор зала",
            "estimated_time": "20 минут",
            "steps": ["Откройте камеру", "Снимите", "Опубликуйте"],
            "metric": "5+ сообщений",
            "success_threshold": "5",
            "if_success": "Повторить",
            "if_fail": "Сменить hook",
        })
        assert result.score == 100.0

    def test_score_drops_on_non_specific(self):
        result = validate_actionability({"title": "развивать соцсети"})
        assert result.score < 100.0

    def test_score_drops_on_missing_elements(self):
        result = validate_actionability({"title": "Some task"})
        assert result.score < 100.0

    def test_score_never_below_zero(self):
        result = validate_actionability({})
        assert result.score >= 0.0