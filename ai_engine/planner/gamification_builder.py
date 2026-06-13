"""Gamification Builder — creates gamification layer for Execution Dashboard."""

from shared.schemas.execution_view_model import Gamification, LevelInfo, Achievement


class GamificationBuilder:
    """Builds Gamification state with levels and achievements."""

    def build(self, total_tasks: int = 90) -> Gamification:
        levels = [
            LevelInfo(name="Новичок", min_xp=0, max_xp=200),
            LevelInfo(name="Контент-Машина", min_xp=200, max_xp=500),
            LevelInfo(name="Генератор Лидов", min_xp=500, max_xp=1000),
            LevelInfo(name="Мастер Продаж", min_xp=1000, max_xp=2000),
            LevelInfo(name="Маркетинг Командир", min_xp=2000, max_xp=5000),
        ]
        achievements = [
            Achievement(id="first_post", title="Первый пост", description="Опубликуйте первый пост", unlocked=False),
            Achievement(id="first_reel", title="Первый Reels", description="Снимите первый Reels", unlocked=False),
            Achievement(id="first_lead", title="Первый лид", description="Получите первую заявку", unlocked=False),
            Achievement(id="first_sale", title="Первая продажа", description="Закройте первую продажу", unlocked=False),
            Achievement(id="streak_7", title="7 дней подряд", description="Выполняйте задания 7 дней подряд", unlocked=False),
            Achievement(id="streak_30", title="30 дней подряд", description="Выполните все 30 дней", unlocked=False),
        ]
        return Gamification(xp=0, level="Новичок", progress_percent=0.0,
                           completed_tasks=0, total_tasks=total_tasks, streak=0,
                           levels=levels, achievements=achievements)