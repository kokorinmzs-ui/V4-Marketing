"""Mission Generator — creates Mission objects from data."""

from shared.schemas.execution_view_model import Mission
from shared.schemas.blocks import MissionType, Difficulty, Platform, ContentFormat, ContentArchetype


class MissionGenerator:
    """Creates Mission objects with all required fields."""

    _counter = 0

    def make_mission(self, day: int, phase: str, mtype: MissionType, title: str, why: str,
                     difficulty: Difficulty, time: str, steps: list[str], ready_text: str,
                     cta: str, metric: str, success: str, warning: str, fail: str,
                     if_success: str, if_warning: str, if_fail: str, xp: int = 15) -> Mission:
        """Create a standard mission."""
        self._counter += 1
        return Mission(
            mission_id=f"m{self._counter:04d}", day=day, phase=phase, mission_type=mtype,
            title=title, objective=why[:100], why=why, difficulty=difficulty,
            estimated_time=time, steps=steps, ready_text=ready_text, cta=cta,
            metric=metric, success_threshold=success, warning_threshold=warning,
            fail_threshold=fail, if_success=if_success, if_warning=if_warning,
            if_fail=if_fail, xp_reward=xp,
        )

    def make_reels_mission(self, day: int, phase: str, reel: dict) -> Mission:
        """Create a Reels mission with 4-frame shot list."""
        self._counter += 1
        hook = reel.get("hook", f"Reels Day {day}")
        return Mission(
            mission_id=f"m{self._counter:04d}", day=day, phase=phase,
            mission_type=MissionType.CONTENT,
            title=f"Снять Reels: {hook[:50]}",
            objective="Reels получают в 3 раза больше охватов",
            why="Reels — самый быстрый способ получить новые контакты",
            difficulty=Difficulty.MEDIUM, estimated_time="20 минут",
            steps=["Возьмите телефон", "Снимите кадр 1", "Снимите кадр 2",
                   "Снимите кадр 3", "Снимите кадр 4", "Наложите текст", "Опубликуйте"],
            ready_text=reel.get("cta", "Напишите ЗАЛ"),
            cta=reel.get("cta", "Напишите ЗАЛ"),
            platform=Platform.INSTAGRAM, content_format=ContentFormat.REEL,
            archetype=ContentArchetype(reel.get("archetype", "case")),
            hook=hook,
            frame_1=reel.get("frame_1", f"Кадр 1 дня {day}"),
            frame_2=reel.get("frame_2", f"Кадр 2 дня {day}"),
            frame_3=reel.get("frame_3", f"Кадр 3 дня {day}"),
            frame_4=reel.get("frame_4", f"Кадр 4 дня {day}"),
            voiceover=reel.get("voiceover", ""),
            metric="5000+ просмотров",
            success_threshold="5000+ просмотров",
            warning_threshold="1500-5000 просмотров",
            fail_threshold="< 1500 просмотров",
            if_success="Повторить формат через 7 дней",
            if_fail="Заменить первый кадр",
            xp_reward=15,
        )

    def make_ads_mission(self, day: int, phase: str, ad: dict) -> Mission:
        """Create an Ads mission with test budget 500-1000."""
        self._counter += 1
        budget = ad.get("budget", "500")
        platform_str = ad.get("platform", "vk")
        return Mission(
            mission_id=f"m{self._counter:04d}", day=day, phase=phase,
            mission_type=MissionType.ADS,
            title=f"Запустить рекламу: {platform_str.upper()} {budget}₽",
            objective=f"Протестировать гипотезу с бюджетом {budget}₽",
            why="Реклама с малым бюджетом позволяет проверить гипотезы без риска",
            difficulty=Difficulty.MEDIUM, estimated_time="30 минут",
            steps=[f"Откройте рекламный кабинет {platform_str.upper()}",
                   "Создайте кампанию", f"Установите бюджет {budget}₽",
                   "Запустите на 3 дня", "Проверьте результат"],
            ready_text=ad.get("offer", ""),
            cta="Запустить тест",
            budget=budget, audience=ad.get("audience", ""),
            metric="CTR > 2%",
            success_threshold="CTR > 2%",
            warning_threshold="CTR 1-2%",
            fail_threshold="CTR < 1%",
            if_success=f"Увеличить бюджет до {int(budget)*2}₽",
            if_warning="Оставить без изменений",
            if_fail="Сменить креатив",
            xp_reward=20,
        )

    def make_sales_mission(self, day: int, phase: str, script: dict) -> Mission:
        """Create a Sales mission with ready text."""
        self._counter += 1
        msg = script.get("message", "Следуйте скрипту продаж")
        return Mission(
            mission_id=f"m{self._counter:04d}", day=day, phase=phase,
            mission_type=MissionType.SALES,
            title="Отработать скрипт продаж",
            objective=script.get("goal", "Закрыть продажу")[:100],
            why="Прямые продажи приносят revenue",
            difficulty=Difficulty.MEDIUM, estimated_time="15 минут",
            steps=["Откройте директ", "Найдите лида",
                   "Используйте готовый скрипт", "Зафиксируйте результат"],
            ready_text=msg, cta="Отправить",
            metric="2+ ответа", success_threshold="2+ ответа",
            warning_threshold="1 ответ", fail_threshold="0 ответов",
            if_success="Повторить завтра", if_fail="Сменить скрипт",
            xp_reward=30,
        )