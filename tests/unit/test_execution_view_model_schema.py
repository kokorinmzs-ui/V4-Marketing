"""Unit tests for ExecutionViewModel schema."""

import pytest
from pydantic import ValidationError

from shared.schemas.execution_view_model import (
    ExecutionViewModel,
    ProjectInfo,
    DaySummary,
    Mission,
    ContentTask,
    AdsTask,
    SalesTask,
    KPITask,
    Gamification,
    LevelInfo,
    Achievement,
)
from shared.schemas.blocks import (
    Platform,
    ContentFormat,
    ContentArchetype,
    Difficulty,
    MissionType,
    TaskStatus,
)


class TestExecutionViewModelValid:
    """Valid ExecutionViewModel scenarios."""

    def test_minimal_execution_view_model(self):
        """Minimal valid ExecutionViewModel."""
        evm = ExecutionViewModel(
            project=ProjectInfo(
                name="Фотостудия Воздух",
                industry="photography_studio",
                goal="Получить 20 заявок за 30 дней",
                current_day=1,
                current_phase="setup",
            ),
            today=DaySummary(
                day=1,
                phase="setup",
                mission_count=3,
                goal="Подготовить систему",
            ),
            total_missions=3,
        )
        assert evm.project.name == "Фотостудия Воздух"
        assert evm.today.day == 1
        assert evm.missions == []
        assert evm.schema_version == "4.0"

    def test_execution_view_model_with_missions(self):
        """ExecutionViewModel with missions."""
        missions = [
            Mission(
                mission_id="m1",
                day=1,
                phase="setup",
                mission_type=MissionType.SETUP,
                title="Утвердить позиционирование",
                objective="Чтобы весь контент был направлен на одну цель",
                why="Позиционирование — основа маркетинга. Без него контент не будет работать.",
                difficulty=Difficulty.EASY,
                estimated_time="15 минут",
                steps=[
                    "Откройте файл с позиционированием",
                    "Прочитайте и согласуйте с командой",
                    "Внесите правки если нужно",
                ],
                ready_text="Доступная фотостудия для контент-мейкеров",
                cta="Утвердить",
                metric="Позиционирование утверждено",
                success_threshold="Утверждено",
                warning_threshold="",
                fail_threshold="",
                if_success="Перейти к Дню 2",
                if_fail="Вернуться к обсуждению",
                xp_reward=10,
            ),
            Mission(
                mission_id="m2",
                day=2,
                phase="setup",
                mission_type=MissionType.CONTENT,
                title="Опубликовать пост-знакомство",
                objective="Получить первые реакции аудитории",
                why="Первый пост должен показать экспертность и вызвать доверие.",
                difficulty=Difficulty.EASY,
                estimated_time="20 минут",
                steps=[
                    "Откройте Instagram",
                    "Создайте пост",
                    "Вставьте готовый текст ниже",
                    "Добавьте фото студии",
                    "Опубликуйте",
                ],
                ready_text="Привет! Мы — фотостудия Воздух. 7 залов, оборудование Profoto, 100+ довольных клиентов. Запишитесь на первую съёмку.",
                cta="Напишите СТАРТ в директ",
                platform=Platform.INSTAGRAM,
                content_format=ContentFormat.POST,
                metric="Лайки и комментарии",
                success_threshold="20+ лайков",
                warning_threshold="10-20 лайков",
                fail_threshold="Менее 10 лайков",
                if_success="Повторить формат через 3 дня",
                if_fail="Заменить фото на результат съёмки",
                xp_reward=15,
            ),
        ]
        evm = ExecutionViewModel(
            project=ProjectInfo(
                name="Фотостудия Воздух",
                industry="photography_studio",
                goal="Получить 20 заявок",
                current_day=2,
                current_phase="setup",
            ),
            today=DaySummary(day=2, phase="setup", mission_count=1, goal="Первый пост"),
            days=[
                DaySummary(day=1, phase="setup", mission_count=3, goal="Подготовка"),
                DaySummary(day=2, phase="setup", mission_count=1, goal="Первый пост"),
            ],
            missions=missions,
            total_missions=2,
        )
        assert len(evm.missions) == 2
        assert evm.missions[0].title == "Утвердить позиционирование"
        assert evm.missions[1].platform == Platform.INSTAGRAM

    def test_mission_with_all_fields(self):
        """Mission with all optional fields filled."""
        mission = Mission(
            mission_id="m3",
            day=12,
            phase="content",
            mission_type=MissionType.CONTENT,
            title="Снять Reels 'Как выбрать зал'",
            objective="Получить первые сообщения от новичков",
            why="Новички боятся ошибиться с выбором зала. Этот Reels снимает страх.",
            difficulty=Difficulty.MEDIUM,
            estimated_time="20 минут",
            steps=[
                "Возьмите телефон",
                "Снимите кадр 1: вход в студию",
                "Снимите кадр 2: зал с циклорамой",
                "Снимите кадр 3: гримёрка",
                "Снимите кадр 4: администратор показывает даты",
                "Наложите текст из ready_text",
                "Опубликуйте",
            ],
            ready_text="Не знаете, какой зал выбрать для первой съёмки? Напишите слово ЗАЛ — подскажем.",
            cta="Напишите ЗАЛ",
            platform=Platform.INSTAGRAM,
            content_format=ContentFormat.REEL,
            archetype=ContentArchetype.TOUR,
            hook="Как выбрать зал для первой съёмки?",
            frame_1="Вход в студию",
            frame_2="Зал с циклорамой",
            frame_3="Гримёрка",
            frame_4="Администратор показывает свободные даты",
            voiceover="Первый раз бронируете фотостудию? Покажем какой зал выбрать под вашу задачу.",
            metric="Сообщения в директ",
            success_threshold="3+ сообщения за 48 часов",
            warning_threshold="1-2 сообщения",
            fail_threshold="0 сообщений",
            if_success="Повторить формат через 7 дней с другим залом",
            if_warning="Поменять CTA",
            if_fail="Заменить первый кадр на результат съёмки",
            xp_reward=15,
        )
        assert mission.hook is not None
        assert mission.frame_1 is not None
        assert mission.frame_4 is not None
        assert mission.xp_reward == 15

    def test_ads_task_valid(self):
        """AdsTask should validate correctly."""
        task = AdsTask(
            task_id="ad1",
            day=15,
            platform=Platform.VK,
            audience="Женщины 25-40, интересуются фотосъёмкой",
            creative="Карусель с примерами залов",
            offer="Подберём зал под вашу задачу",
            budget="500",
            kpi="CTR > 2%",
            success_threshold="CTR > 2%",
            stop_threshold="CTR < 1%",
            scale_threshold="CTR > 3%",
        )
        assert task.budget == "500"
        assert task.platform == Platform.VK

    def test_gamification_valid(self):
        """Gamification should validate."""
        gamification = Gamification(
            xp=120,
            level="Новичок",
            progress_percent=43.0,
            completed_tasks=13,
            total_tasks=30,
            streak=3,
            levels=[
                LevelInfo(name="Новичок", min_xp=0, max_xp=200),
                LevelInfo(name="Контент-Машина", min_xp=200, max_xp=500),
            ],
            achievements=[
                Achievement(
                    id="first_post",
                    title="Первый пост",
                    description="Опубликуйте первый пост",
                    unlocked=True,
                    unlocked_at="2026-01-15",
                ),
            ],
        )
        assert gamification.xp == 120
        assert len(gamification.levels) == 2
        assert gamification.achievements[0].unlocked is True


class TestExecutionViewModelInvalid:
    """Invalid ExecutionViewModel scenarios."""

    def test_mission_missing_title(self):
        """Mission without title should fail."""
        with pytest.raises(ValidationError):
            Mission(day=1, phase="setup")

    def test_mission_invalid_day(self):
        """Mission with day > 30 should fail."""
        with pytest.raises(ValidationError):
            Mission(day=31, title="Test", phase="setup")

    def test_mission_invalid_day_zero(self):
        """Mission with day < 1 should fail."""
        with pytest.raises(ValidationError):
            Mission(day=0, title="Test", phase="setup")

    def test_evm_missing_project(self):
        """ExecutionViewModel without project should fail."""
        with pytest.raises(ValidationError):
            ExecutionViewModel(
                today=DaySummary(day=1, phase="setup", mission_count=0, goal="Test"),
            )

    def test_avatar_age_string(self):
        """Avatar age as string is coerced to int by Pydantic v2."""
        from shared.schemas.blocks import Avatar
        avatar = Avatar(
            name="Test",
            age="34",  # string is coerced to int by Pydantic v2
            income="100k",
            goals=["Goal"],
            fears=["Fear"],
        )
        assert avatar.age == 34
        assert isinstance(avatar.age, int)

    def test_avatar_age_too_low(self):
        """Avatar age < 14 should fail."""
        from shared.schemas.blocks import Avatar
        with pytest.raises(ValidationError):
            Avatar(
                name="Test",
                age=10,
                income="100k",
                goals=["Goal"],
                fears=["Fear"],
            )


class TestExecutionViewModelEdgeCases:
    """Edge cases for ExecutionViewModel."""

    def test_serialization_roundtrip(self):
        """ExecutionViewModel should serialize and deserialize."""
        evm = ExecutionViewModel(
            project=ProjectInfo(name="Test", industry="photography"),
            today=DaySummary(day=1, phase="setup", mission_count=2, goal="Test"),
            days=[DaySummary(day=1, phase="setup", mission_count=2, goal="Test")],
            total_missions=2,
        )
        data = evm.model_dump()
        evm2 = ExecutionViewModel(**data)
        assert evm2.project.name == "Test"
        assert evm2.total_missions == 2

    def test_mission_status_transitions(self):
        """Mission status should support all states."""
        for status in TaskStatus:
            mission = Mission(
                mission_id=f"m-{status.value}",
                day=1,
                phase="setup",
                title=f"Test {status.value}",
                status=status,
            )
            assert mission.status == status