"""ExecutionPlanner — orchestrates builders to transform final_data.json into execution_view_model.json."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.schemas.execution_view_model import ExecutionViewModel, ProjectInfo, DaySummary, Mission
from shared.schemas.blocks import MissionType, Difficulty

from ai_engine.planner.mission_generator import MissionGenerator
from ai_engine.planner.content_action_builder import ContentActionBuilder
from ai_engine.planner.ads_action_builder import AdsActionBuilder
from ai_engine.planner.sales_action_builder import SalesActionBuilder
from ai_engine.planner.gamification_builder import GamificationBuilder


@dataclass
class PlannerResult:
    success: bool = False
    execution_view_model: ExecutionViewModel | None = None
    errors: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


class ExecutionPlanner:
    def __init__(self):
        self._mg = MissionGenerator()
        self._cab = ContentActionBuilder()
        self._aab = AdsActionBuilder()
        self._sab = SalesActionBuilder()
        self._gb = GamificationBuilder()

    def plan(self, final_data: dict[str, Any] | Any) -> PlannerResult:
        self._mg.__class__._counter = 0
        data = final_data if isinstance(final_data, dict) else final_data.model_dump() if hasattr(final_data, "model_dump") else {}
        project_name = data.get("project_name", "Project")
        market = data.get("market_analysis", {})
        industry = market.get("market_overview", "") or "unknown"
        avatars = data.get("avatars", {}).get("avatars", [])
        reels = data.get("reels", {}).get("reels", [])
        advertising = data.get("advertising", {}).get("campaigns", [])
        scripts = data.get("sales_scripts", {}).get("scripts", [])

        all_missions: list[Mission] = []
        content_tasks, ads_tasks, sales_tasks = [], [], []
        days: list[DaySummary] = []

        for d in range(1, 6):
            ms = self._build_setup_phase(d)
            all_missions.extend(ms)
            for m in ms:
                content_tasks.append(self._cab.build_from_mission(m.mission_id, d, m.title, "post", m.ready_text, m.cta, m.metric))
            days.append(DaySummary(day=d, phase="setup", mission_count=len(ms), goal="Подготовить маркетинговую систему"))

        for d in range(6, 16):
            ms = self._build_content_phase(d, reels, scripts, (d - 6))
            all_missions.extend(ms)
            for m in ms:
                fmt = "reel" if m.content_format and m.content_format.value == "reel" else "post"
                arch = m.archetype.value if m.archetype else "case"
                plat = m.platform.value if m.platform else "instagram"
                content_tasks.append(self._cab.build_from_mission(m.mission_id, d, m.title, fmt, m.ready_text, m.cta, m.metric, plat, arch))
            if (d - 6) % 5 == 0:
                for m in ms:
                    if m.mission_type == MissionType.SALES:
                        sales_tasks.append(self._sab.build(m.mission_id, d, "follow_up", m.objective, m.ready_text, m.if_success or m.if_fail))
            days.append(DaySummary(day=d, phase="content", mission_count=len(ms), goal="Собрать первые сигналы рынка"))

        for d in range(16, 24):
            ms = self._build_traffic_phase(d, advertising)
            all_missions.extend(ms)
            for m in ms:
                if m.mission_type == MissionType.ADS:
                    ads_tasks.append(self._aab.build(m.mission_id, d, "vk", m.audience or "", budget=m.budget or "500", kpi=m.metric, success_threshold=m.success_threshold or "CTR > 2%"))
                else:
                    content_tasks.append(self._cab.build_from_mission(m.mission_id, d, m.title, "post", m.ready_text, m.cta, m.metric))
            days.append(DaySummary(day=d, phase="traffic", mission_count=len(ms), goal="Протестировать рекламу с малым бюджетом"))

        for d in range(24, 31):
            ms = self._build_scale_phase(d, scripts)
            all_missions.extend(ms)
            for m in ms:
                if m.mission_type == MissionType.SALES:
                    sales_tasks.append(self._sab.build(m.mission_id, d, "sales", m.objective, m.ready_text, m.if_success or m.if_fail))
                else:
                    content_tasks.append(self._cab.build_from_mission(m.mission_id, d, m.title, "post", m.ready_text, m.cta, m.metric))
            days.append(DaySummary(day=d, phase="scale", mission_count=len(ms), goal="Масштабировать рабочие связки"))

        project = ProjectInfo(name=project_name, industry=industry, goal="Получить первых клиентов за 30 дней", current_day=1, current_phase="setup")
        try:
            evm = ExecutionViewModel(
                project=project, today=days[0], days=days, missions=all_missions,
                content_tasks=content_tasks, ads_tasks=ads_tasks, sales_tasks=sales_tasks,
                kpi_tasks=[], gamification=self._gb.build(total_tasks=len(all_missions)),
                why_it_works=[f"Миссии построены на основе {len(avatars)} аватаров"],
                total_missions=len(all_missions), total_days=30,
            )
            return PlannerResult(success=True, execution_view_model=evm, stats={
                "missions": len(all_missions), "days": 30, "content": len(content_tasks),
                "ads": len(ads_tasks), "sales": len(sales_tasks),
            })
        except Exception as e:
            return PlannerResult(success=False, errors=[str(e)])

    def _build_setup_phase(self, day: int) -> list[Mission]:
        ms = []
        if day == 1:
            ms.append(self._mg.make_mission(day, "setup", MissionType.SETUP,
                "Утвердить позиционирование", "Без позиционирования контент не будет работать на нужную аудиторию",
                Difficulty.EASY, "10 минут",
                ["Откройте файл с позиционированием", "Прочитайте и согласуйте", "Внесите правки если нужно"],
                "Доступная студия для контент-мейкеров", "Утвердить",
                "Утверждено за 1 день", "Утверждено за 1 день", "Не утверждено за 1 день", "Отклонено",
                "Перейти к Дню 2", "Ускорить обсуждение", "Вернуться к обсуждению", xp=10))
        if day <= 3:
            ms.append(self._mg.make_mission(day, "setup", MissionType.SETUP,
                "Подготовить Instagram к работе", "Площадка должна быть готова к публикации контента",
                Difficulty.EASY, "15 минут",
                ["Откройте Instagram", "Обновите bio", "Добавьте ссылку на сайт", "Загрузите аватар"],
                "Студия Воздух — 7 залов для вашего контента", "Сохранить",
                "Профиль заполнен за 1 день", "Профиль готов за 1 день", "Профиль готов за 2 дня", "Профиль не готов",
                "Перейти к Дню 3", "Проверить bio заново", "Обратиться за помощью", xp=10))
        if 2 <= day <= 4:
            ms.append(self._mg.make_mission(day, "setup", MissionType.SETUP,
                "Подготовить лид-магнит", "Лид-магнит нужен для сбора контактов",
                Difficulty.EASY, "20 минут",
                ["Выберите формат лид-магнита из списка", "Создайте чек-лист", "Оформите в Canva", "Загрузите в облако"],
                "Чек-лист 'Как выбрать зал для съёмки'", "Скачать чек-лист",
                "Лид-магнит готов за 1 день", "Готов за 1 день", "Готов за 2 дня", "Не готов",
                "Перейти к Дню 5", "Пересоздать лид-магнит", "Пропустить лид-магнит", xp=10))
        if 3 <= day <= 5:
            ms.append(self._mg.make_mission(day, "setup", MissionType.CONTENT,
                "Написать пост-знакомство", "Первый пост должен показать экспертность",
                Difficulty.EASY, "20 минут",
                ["Откройте Instagram", "Создайте пост", "Вставьте готовый текст", "Добавьте фото студии", "Опубликуйте"],
                "Привет! Мы — фотостудия Воздух. 7 залов, оборудование Profoto, 100+ довольных клиентов.",
                "Напишите СТАРТ в директ",
                "20+ лайков", "20+ лайков", "10-20 лайков", "Менее 10 лайков",
                "Повторить формат через 3 дня", "Поменять фото", "Заменить фото на результат съёмки", xp=15))
        return ms

    def _build_content_phase(self, day: int, reels: list[dict], scripts: list[dict], idx: int) -> list[Mission]:
        ms = []
        ms.append(self._mg.make_mission(day, "content", MissionType.CONTENT,
            f"Опубликовать контент дня {day}", "Регулярный контент прогревает аудиторию",
            Difficulty.MEDIUM, "20 минут",
            ["Откройте Instagram", "Создайте пост", "Вставьте готовый текст", "Опубликуйте"],
            f"Контент для дня {day}: как выбрать зал для первой съёмки", f"Напишите ЗАЛ в директ",
            f"{10 + day}+ лайков", f"{10 + day}+ лайков", f"{5 + day}-{10 + day} лайков", f"< {5 + day} лайков",
            "Повторить через 3 дня", "Поменять CTA", "Заменить hook", xp=15))
        if idx % 3 == 0 and reels:
            reel = reels[idx // 3 % len(reels)] if reels else {}
            ms.append(self._mg.make_reels_mission(day, "content", reel))
        if idx % 5 == 0 and scripts:
            script = scripts[idx // 5 % len(scripts)] if scripts else {}
            ms.append(self._mg.make_sales_mission(day, "content", script))
        return ms

    def _build_traffic_phase(self, day: int, advertising: list[dict]) -> list[Mission]:
        ms = []
        ms.append(self._mg.make_mission(day, "traffic", MissionType.CONTENT,
            f"Опубликовать контент дня {day}", "Контент продолжает работать на прогрев",
            Difficulty.MEDIUM, "20 минут",
            ["Откройте Instagram", "Создайте пост", "Опубликуйте"],
            f"Контент дня {day}", f"CTA дня {day}",
            f"{20 + day}+ просмотров", f"{20 + day}+ просмотров", f"{10 + day}-{20 + day} просмотров", f"< {10 + day} просмотров",
            "Повторить", "Поменять формат", "Сменить тему", xp=15))
        if (day - 16) % 2 == 0 and advertising:
            ad = advertising[(day - 16) // 2 % len(advertising)] if advertising else {}
            ms.append(self._mg.make_ads_mission(day, "traffic", ad))
        return ms

    def _build_scale_phase(self, day: int, scripts: list[dict]) -> list[Mission]:
        ms = []
        ms.append(self._mg.make_mission(day, "scale", MissionType.CONTENT,
            "Масштабировать лучший контент", "Повтор лучших форматов удваивает охваты",
            Difficulty.EASY, "15 минут",
            ["Посмотрите статистику за неделю", "Найдите пост с лучшими метриками", "Создайте похожий пост", "Опубликуйте"],
            "Лучший контент недели — повторить формат", f"CTA дня {day}",
            "30+ лайков", "30+ лайков", "15-30 лайков", "< 15 лайков",
            "Повторить через неделю", "Поменять визуал", "Сменить тему", xp=15))
        if day % 3 == 0 and scripts:
            script = scripts[day % len(scripts)] if scripts else {}
            ms.append(self._mg.make_sales_mission(day, "scale", script))
        return ms