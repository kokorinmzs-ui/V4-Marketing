"""ExecutionPlanner — transforms final_data.json into execution_view_model.json."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai_engine.planner.ads_action_builder import AdsActionBuilder
from ai_engine.planner.content_action_builder import ContentActionBuilder
from ai_engine.planner.gamification_builder import GamificationBuilder
from ai_engine.planner.mission_generator import MissionGenerator
from ai_engine.planner.sales_action_builder import SalesActionBuilder
from shared.schemas.blocks import ContentArchetype, ContentFormat, Difficulty, MissionType, Platform
from shared.schemas.execution_view_model import (
    AdsTask,
    ContentTask,
    DaySummary,
    ExecutionViewModel,
    KPITask,
    Mission,
    ProjectInfo,
    SalesTask,
)


@dataclass
class PlannerResult:
    success: bool = False
    execution_view_model: ExecutionViewModel | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


class ExecutionPlanner:
    """Builds the execution dashboard from real FinalData sections."""

    def __init__(self):
        self._mg = MissionGenerator()
        self._cab = ContentActionBuilder()
        self._aab = AdsActionBuilder()
        self._sab = SalesActionBuilder()
        self._gb = GamificationBuilder()

    def plan(self, final_data: dict[str, Any] | Any) -> PlannerResult:
        self._mg._counter = 0
        data = self._normalize(final_data)

        result = PlannerResult()
        content_plan = self._section(data, "content_plan", "days")
        if not content_plan:
            result.errors.append("content_plan is missing or empty; planner refuses to synthesize content")
            return result

        market = self._mapping(data, "market_analysis")
        project_name = data.get("project_name") or "Project"
        industry = self._string(market.get("market_overview")) or "unknown"

        avatars = self._section(data, "avatars", "avatars")
        pains = self._section(data, "pains", "pains")
        offers = self._section(data, "offers", "offers")
        reels = self._section(data, "reels", "reels")
        posts = self._section(data, "posts", "posts")
        advertising = self._section(data, "advertising", "campaigns")
        scripts = self._section(data, "sales_scripts", "scripts")
        kpis = self._section(data, "kpi", "kpis")
        launch_steps = self._section(data, "launch_plan", "steps")

        if not avatars:
            result.warnings.append("avatars section is empty; setup missions will be less specific")
        if not pains:
            result.warnings.append("pains section is empty; setup missions will be less specific")
        if not offers:
            result.warnings.append("offers section is empty; setup missions will be less specific")
        if not posts:
            result.warnings.append("posts section is empty; content tasks will reuse content plan copy")
        if not reels:
            result.warnings.append("reels section is empty; reel missions will be skipped")
        if not advertising:
            result.warnings.append("advertising section is empty; ad missions will be skipped")
        if not scripts:
            result.warnings.append("sales_scripts section is empty; sales missions will be skipped")
        if not kpis:
            result.warnings.append("kpi section is empty; KPI tasks will be skipped")
        if not launch_steps:
            result.warnings.append("launch_plan section is empty; launch-review mission will be skipped")

        missions: list[Mission] = []
        content_tasks: list[ContentTask] = []
        ads_tasks: list[AdsTask] = []
        sales_tasks: list[SalesTask] = []
        kpi_tasks: list[KPITask] = []
        days: list[DaySummary] = []

        for day in range(1, 31):
            phase = self._phase_for_day(day)
            day_content = self._cycle(content_plan, day - 1)
            content_task, content_mission = self._build_content_artifact(day, phase, day_content, posts, reels)
            content_tasks.append(content_task)
            missions.append(content_mission)

            if day <= 5:
                missions.extend(self._build_setup_missions(day, phase, market, avatars, pains, offers, content_plan, kpis, launch_steps))
            elif 6 <= day <= 15:
                if day % 2 == 0 and reels:
                    reel = self._cycle(reels, day - 6)
                    missions.append(self._build_reel_mission(day, phase, reel))
                if day % 3 == 1 and scripts:
                    script = self._cycle(scripts, day - 6)
                    sales_task, sales_mission = self._build_sales_artifact(day, phase, script)
                    sales_tasks.append(sales_task)
                    missions.append(sales_mission)
            elif 16 <= day <= 23:
                if day % 2 == 0 and advertising:
                    ad = self._cycle(advertising, day - 16)
                    ads_task, ads_mission = self._build_ads_artifact(day, phase, ad)
                    ads_tasks.append(ads_task)
                    missions.append(ads_mission)
            else:
                if day % 3 == 0 and scripts:
                    script = self._cycle(scripts, day - 24)
                    sales_task, sales_mission = self._build_sales_artifact(day, phase, script)
                    sales_tasks.append(sales_task)
                    missions.append(sales_mission)
                if day % 2 == 0 and kpis:
                    kpi = self._cycle(kpis, day - 24)
                    kpi_task, kpi_mission = self._build_kpi_artifact(day, phase, kpi)
                    kpi_tasks.append(kpi_task)
                    missions.append(kpi_mission)
                if day % 5 == 0 and launch_steps:
                    missions.append(self._build_launch_review_mission(day, phase, launch_steps))

            days.append(
                DaySummary(
                    day=day,
                    phase=phase,
                    mission_count=len([m for m in missions if m.day == day]),
                    estimated_time="30 минут" if phase == "setup" else "45 минут",
                    goal=self._day_goal(phase, day_content),
                    completed=False,
                )
            )

        if not missions:
            result.errors.append("planner produced no missions")
            return result

        # If we have KPI rows but no dedicated KPI missions yet, create one per KPI.
        if kpis and not kpi_tasks:
            for idx, kpi in enumerate(kpis, start=1):
                kpi_task, kpi_mission = self._build_kpi_artifact(24 + (idx - 1) % 7, "scale", kpi)
                kpi_tasks.append(kpi_task)
                missions.append(kpi_mission)

        today = days[0]
        project = ProjectInfo(
            name=project_name,
            industry=industry,
            goal="Получить первых клиентов за 30 дней",
            current_day=1,
            current_phase="setup",
        )

        why_it_works = [
            f"План опирается на {len(content_plan)} записей контент-плана.",
            f"Использует {len(posts)} постов, {len(reels)} Reels и {len(advertising)} рекламных кампаний.",
            f"Связывает {len(avatars)} аватаров, {len(pains)} болей и {len(offers)} офферов.",
        ]
        if scripts:
            why_it_works.append(f"Включает {len(scripts)} реальных сценариев продаж.")
        if kpis:
            why_it_works.append(f"Привязывает действия к {len(kpis)} KPI-карточкам.")

        try:
            evm = ExecutionViewModel(
                project=project,
                today=today,
                days=days,
                missions=missions,
                content_tasks=content_tasks,
                ads_tasks=ads_tasks,
                sales_tasks=sales_tasks,
                kpi_tasks=kpi_tasks,
                gamification=self._gb.build(total_tasks=len(missions)),
                why_it_works=why_it_works,
                total_missions=len(missions),
                total_days=30,
            )
        except Exception as exc:
            result.errors.append(f"ExecutionViewModel construction failed: {exc}")
            return result

        result.success = True
        result.execution_view_model = evm
        result.stats = {
            "missions": len(missions),
            "days": len(days),
            "content": len(content_tasks),
            "ads": len(ads_tasks),
            "sales": len(sales_tasks),
            "kpi": len(kpi_tasks),
        }
        return result

    def _build_setup_missions(
        self,
        day: int,
        phase: str,
        market: dict[str, Any],
        avatars: list[dict[str, Any]],
        pains: list[dict[str, Any]],
        offers: list[dict[str, Any]],
        content_plan: list[dict[str, Any]],
        kpis: list[dict[str, Any]],
        launch_steps: list[dict[str, Any]],
    ) -> list[Mission]:
        missions: list[Mission] = []
        if day == 1:
            missions.append(
                self._mg.make_mission(
                    day,
                    phase,
                    MissionType.SETUP,
                    title=f"Проверить рынок: {self._string(market.get('market_overview')) or 'рынок'}",
                    why="Нужна конкретная опора на рынок и реальную формулировку оффера.",
                    difficulty=Difficulty.EASY,
                    time="15 минут",
                    steps=["Откройте market_analysis", "Сверьте выводы с позиционированием", "Зафиксируйте итог"],
                    ready_text=self._string(market.get("market_overview")) or "Рынок определён",
                    cta="Зафиксировать позиционирование",
                    metric="1 утверждённая формулировка",
                    success="1 утверждённая формулировка",
                    warning="1 формулировка требует правки",
                    fail="0 согласованных формулировок",
                    if_success="Перейти к аватарам",
                    if_warning="Уточнить формулировку",
                    if_fail="Вернуться к market_analysis",
                    xp=10,
                    source_id="market_analysis",
                )
            )
        if day == 2 and avatars:
            avatar_names = ", ".join(self._string(a.get("name")) for a in avatars[:3] if self._string(a.get("name")))
            missions.append(
                self._mg.make_mission(
                    day,
                    phase,
                    MissionType.SETUP,
                    title="Сверить аватары и боли",
                    why="Аватары и боли должны быть связаны между собой без подмены смысла.",
                    difficulty=Difficulty.EASY,
                    time="20 минут",
                    steps=["Откройте avatars", "Сверьте pains", "Отметьте расхождения"],
                    ready_text=avatar_names or "Аватары готовы",
                    cta="Проверить соответствие",
                    metric=f"{len(avatars)} аватаров",
                    success=f"{len(avatars)} аватаров",
                    warning="1 пробел в связке",
                    fail="0 собранных связок",
                    if_success="Перейти к offers",
                    if_warning="Дочистить связи",
                    if_fail="Вернуться к аватарам",
                    xp=10,
                    source_id="avatars",
                )
            )
        if day == 3 and offers:
            offer_headlines = ", ".join(self._string(o.get("headline")) for o in offers[:3] if self._string(o.get("headline")))
            missions.append(
                self._mg.make_mission(
                    day,
                    phase,
                    MissionType.SETUP,
                    title="Собрать офферы по болям",
                    why="Офферы должны быть привязаны к pain_id и к конкретному результату.",
                    difficulty=Difficulty.MEDIUM,
                    time="20 минут",
                    steps=["Откройте offers", "Сверьте pain_id", "Проверьте cta"],
                    ready_text=offer_headlines or "Офферы готовы",
                    cta="Сверить офферы",
                    metric=f"{len(offers)} офферов",
                    success=f"{len(offers)} офферов",
                    warning="1 расхождение в связках",
                    fail="0 офферов без связки",
                    if_success="Перейти к контенту",
                    if_warning="Пересобрать офферы",
                    if_fail="Вернуться к pain map",
                    xp=10,
                    source_id="offers",
                )
            )
        if day == 4 and content_plan:
            day_count = len(content_plan)
            missions.append(
                self._mg.make_mission(
                    day,
                    phase,
                    MissionType.SETUP,
                    title=f"Собрать контент-план на {day_count} дней",
                    why="Контент должен идти из реального плана, а не из шаблона.",
                    difficulty=Difficulty.MEDIUM,
                    time="25 минут",
                    steps=["Откройте content_plan", "Проверьте связки с offer_id", "Проверьте CTA"],
                    ready_text=f"Контент-план: {day_count} дней",
                    cta="Утвердить контент-план",
                    metric=f"{day_count} дней",
                    success=f"{day_count} дней",
                    warning="1 день без CTA",
                    fail="0 дней без плана",
                    if_success="Перейти к KPI",
                    if_warning="Уточнить дни",
                    if_fail="Вернуться к контент-плану",
                    xp=10,
                    source_id="content_plan",
                )
            )
        if day == 5:
            kpi_count = len(kpis)
            launch_count = len(launch_steps)
            missions.append(
                self._mg.make_mission(
                    day,
                    phase,
                    MissionType.REVIEW,
                    title="Подготовить запуск и KPI-контроль",
                    why="Запуск должен опираться на понятные пороги, а не на общие пожелания.",
                    difficulty=Difficulty.MEDIUM,
                    time="25 минут",
                    steps=["Откройте KPI", "Сверьте launch_plan", "Зафиксируйте следующий шаг"],
                    ready_text=f"KPI: {kpi_count}, launch steps: {launch_count}",
                    cta="Зафиксировать запуск",
                    metric=f"{kpi_count} KPI",
                    success=f"{kpi_count} KPI",
                    warning="1 порог не согласован",
                    fail="0 готовности к запуску",
                    if_success="Переход к контенту",
                    if_warning="Доделать пороги",
                    if_fail="Вернуться к KPI",
                    xp=10,
                    source_id="launch_plan",
                )
            )
        return missions

    def _build_content_artifact(
        self,
        day: int,
        phase: str,
        content_day: dict[str, Any],
        posts: list[dict[str, Any]],
        reels: list[dict[str, Any]],
    ) -> tuple[ContentTask, Mission]:
        content_format = self._enum_value(content_day.get("content_format"), ContentFormat)
        platform = self._enum_value(content_day.get("platform"), Platform)
        content_id = f"day-{day}"

        if content_format == ContentFormat.REEL.value and reels:
            reel = self._cycle(reels, day - 1)
            return self._content_from_reel(day, phase, content_day, reel, content_id, platform)

        post = self._cycle(posts, day - 1) if posts else {}
        return self._content_from_post(day, phase, content_day, post, content_id, platform, content_format)

    def _content_from_post(
        self,
        day: int,
        phase: str,
        content_day: dict[str, Any],
        post: dict[str, Any],
        content_id: str,
        platform: str,
        content_format: str,
    ) -> tuple[ContentTask, Mission]:
        headline = self._string(post.get("headline")) or f"Пост дня {day}"
        post_text = self._string(post.get("post_text")) or self._string(content_day.get("cta")) or headline
        cta = self._string(post.get("cta")) or self._string(content_day.get("cta")) or "Открыть пост"
        metric = self._string(post.get("metric")) or self._string(content_day.get("kpi")) or f"{day} реакций"
        avatar_id = self._string(content_day.get("avatar_id")) or self._string(post.get("avatar_id")) or None
        pain_id = self._string(content_day.get("pain_id")) or self._string(post.get("pain_id")) or None
        offer_id = self._string(content_day.get("offer_id")) or self._string(post.get("offer_id")) or None
        source_id = f"post-{day}"

        content_task = ContentTask(
            task_id=content_id,
            source_id=source_id,
            day=day,
            title=headline,
            content_format=ContentFormat(content_format) if content_format in ContentFormat._value2member_map_ else ContentFormat.POST,
            archetype=None,
            ready_text=post_text,
            cta=cta,
            platform=Platform(platform) if platform in Platform._value2member_map_ else Platform.INSTAGRAM,
            avatar_id=avatar_id,
            pain_id=pain_id,
            offer_id=offer_id,
            hashtags=list(post.get("hashtags", [])),
            metric=metric,
        )

        mission = self._mg.make_mission(
            day,
            phase,
            MissionType.CONTENT,
            title=f"Опубликовать пост: {headline[:60]}",
            why="Пост должен быть основан на реальном тексте и вести к измеримому действию.",
            difficulty=Difficulty.MEDIUM,
            time="20 минут",
            steps=["Откройте платформу", "Вставьте готовый текст", "Опубликуйте и зафиксируйте метрику"],
            ready_text=post_text,
            cta=cta,
            metric=metric,
            success=metric,
            warning=self._warn_metric(metric),
            fail=f"Меньше {self._fail_metric(metric)}",
            if_success="Повторить сильную связку",
            if_warning="Уточнить заголовок",
            if_fail="Заменить первый абзац",
            xp=15,
            source_id=source_id,
            avatar_id=avatar_id,
            pain_id=pain_id,
            offer_id=offer_id,
            content_id=content_id,
        )
        return content_task, mission

    def _content_from_reel(
        self,
        day: int,
        phase: str,
        content_day: dict[str, Any],
        reel: dict[str, Any],
        content_id: str,
        platform: str,
    ) -> tuple[ContentTask, Mission]:
        hook = self._string(reel.get("hook")) or f"Reels day {day}"
        ready_text = " | ".join(
            text for text in [
                self._string(reel.get("frame_1")),
                self._string(reel.get("frame_2")),
                self._string(reel.get("frame_3")),
                self._string(reel.get("frame_4")),
            ]
            if text
        ) or hook
        cta = self._string(reel.get("cta")) or self._string(content_day.get("cta")) or "Снять Reels"
        metric = "5000+ просмотров"
        source_id = f"reel-{day}"

        content_task = ContentTask(
            task_id=content_id,
            source_id=source_id,
            day=day,
            title=hook,
            content_format=ContentFormat.REEL,
            archetype=self._content_archetype(self._string(reel.get("archetype")) or ContentArchetype.CASE.value),
            ready_text=ready_text,
            cta=cta,
            platform=Platform(platform) if platform in Platform._value2member_map_ else Platform.INSTAGRAM,
            avatar_id=self._string(content_day.get("avatar_id")) or None,
            pain_id=self._string(content_day.get("pain_id")) or None,
            offer_id=self._string(content_day.get("offer_id")) or None,
            hashtags=[],
            metric=metric,
        )

        mission = self._mg.make_reels_mission(
            day,
            phase,
            reel=reel,
            source_id=source_id,
            avatar_id=self._string(content_day.get("avatar_id")) or None,
            pain_id=self._string(content_day.get("pain_id")) or None,
            offer_id=self._string(content_day.get("offer_id")) or None,
            content_id=content_id,
        )
        return content_task, mission

    def _build_reel_mission(self, day: int, phase: str, reel: dict[str, Any]) -> Mission:
        return self._mg.make_reels_mission(
            day,
            phase,
            reel=reel,
            source_id=f"reel-{day}",
            content_id=f"day-{day}",
        )

    def _build_ads_artifact(self, day: int, phase: str, ad: dict[str, Any]) -> tuple[AdsTask, Mission]:
        budget = self._string(ad.get("budget")) or "500"
        audience = self._string(ad.get("audience")) or "Тёплая аудитория"
        platform = self._enum_value(ad.get("platform"), Platform)
        creative = self._string(ad.get("creative")) or self._string(ad.get("offer")) or "Тестовый креатив"
        offer = self._string(ad.get("offer")) or creative
        source_id = f"ad-{day}"

        ads_task = self._aab.build(
            task_id=source_id,
            day=day,
            platform=platform,
            audience=audience,
            creative=creative,
            offer=offer,
            budget=budget,
            kpi=self._string(ad.get("kpi")) or "CTR > 2%",
            success_threshold=self._string(ad.get("success_threshold")) or "CTR > 2%",
            stop_threshold=self._string(ad.get("stop_threshold")) or "CTR < 1%",
            scale_threshold=self._string(ad.get("scale_threshold")) or "CTR > 3%",
        )

        mission = self._mg.make_ads_mission(
            day,
            phase,
            ad=ad,
            source_id=source_id,
            avatar_id=None,
            offer_id=None,
        )
        return ads_task, mission

    def _build_sales_artifact(self, day: int, phase: str, script: dict[str, Any]) -> tuple[SalesTask, Mission]:
        source_id = f"script-{day}"
        sales_task = self._sab.build(
            task_id=source_id,
            day=day,
            scenario=self._string(script.get("scenario")) or "first",
            goal=self._string(script.get("goal")) or "Закрыть диалог",
            message=self._string(script.get("message")) or "Здравствуйте!",
            next_step=self._string(script.get("next_step")) or "Уточнить запрос",
        )
        mission = self._mg.make_sales_mission(
            day,
            phase,
            script=script,
            source_id=source_id,
        )
        return sales_task, mission

    def _build_kpi_artifact(self, day: int, phase: str, kpi: dict[str, Any]) -> tuple[KPITask, Mission]:
        source_id = f"kpi-{day}-{self._string(kpi.get('action')) or 'metric'}"
        task = KPITask(
            task_id=source_id,
            source_id=source_id,
            day=day,
            action=self._string(kpi.get("action")) or "Action",
            metric=self._string(kpi.get("metric")) or self._string(kpi.get("success_threshold")) or "5000",
            success_threshold=self._string(kpi.get("success_threshold")) or "5000",
            warning_threshold=self._string(kpi.get("warning_threshold")) or "1500",
            fail_threshold=self._string(kpi.get("fail_threshold")) or "500",
        )
        mission = self._mg.make_mission(
            day,
            phase,
            MissionType.REVIEW,
            title=f"Проверить KPI: {self._string(kpi.get('action')) or 'Action'}",
            why="Каждое действие должно быть связано с конкретным числовым порогом.",
            difficulty=Difficulty.EASY,
            time="10 минут",
            steps=["Откройте KPI", "Сверьте пороги", "Зафиксируйте вывод"],
            ready_text=self._string(kpi.get("metric")) or self._string(kpi.get("success_threshold")) or "KPI",
            cta="Проверить метрику",
            metric=self._string(kpi.get("metric")) or self._string(kpi.get("success_threshold")) or "5000",
            success=self._string(kpi.get("success_threshold")) or "5000",
            warning=self._string(kpi.get("warning_threshold")) or "1500",
            fail=self._string(kpi.get("fail_threshold")) or "500",
            if_success=self._string(kpi.get("if_success")) or "Масштабировать",
            if_warning=self._string(kpi.get("if_warning")) or "Оставить без изменений",
            if_fail=self._string(kpi.get("if_fail")) or "Изменить связку",
            xp=10,
            source_id=source_id,
            kpi_id=source_id,
        )
        return task, mission

    def _build_launch_review_mission(self, day: int, phase: str, launch_steps: list[dict[str, Any]]) -> Mission:
        summary = f"{len(launch_steps)} шагов запуска"
        return self._mg.make_mission(
            day,
            phase,
            MissionType.REVIEW,
            title="Проверить launch-план",
            why="План запуска должен быть последовательным и опираться на реальные шаги.",
            difficulty=Difficulty.EASY,
            time="10 минут",
            steps=["Откройте launch_plan", "Проверьте порядок шагов", "Зафиксируйте следующий шаг"],
            ready_text=summary,
            cta="Проверить запуск",
            metric=summary,
            success=summary,
            warning="1 шаг требует уточнения",
            fail="0 готовности запуска",
            if_success="Двигаться дальше",
            if_warning="Уточнить шаги",
            if_fail="Вернуться к launch_plan",
            xp=10,
            source_id="launch_plan",
        )

    @staticmethod
    def _normalize(final_data: dict[str, Any] | Any) -> dict[str, Any]:
        if isinstance(final_data, dict):
            return final_data
        if hasattr(final_data, "model_dump"):
            return final_data.model_dump()
        return {}

    @staticmethod
    def _section(data: dict[str, Any], key: str, child_key: str | None = None) -> list[dict[str, Any]]:
        section = data.get(key) or {}
        if not isinstance(section, dict):
            return []
        if child_key is None:
            return [section]
        items = section.get(child_key, [])
        result: list[dict[str, Any]] = []
        for item in items if isinstance(items, list) else []:
            if isinstance(item, dict):
                result.append(item)
            elif hasattr(item, "model_dump"):
                result.append(item.model_dump())
        return result

    @staticmethod
    def _mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
        section = data.get(key) or {}
        if isinstance(section, dict):
            return section
        if hasattr(section, "model_dump"):
            return section.model_dump()
        return {}

    @staticmethod
    def _cycle(items: list[dict[str, Any]], index: int) -> dict[str, Any]:
        if not items:
            return {}
        return items[index % len(items)]

    @staticmethod
    def _phase_for_day(day: int) -> str:
        if day <= 5:
            return "setup"
        if day <= 15:
            return "content"
        if day <= 23:
            return "traffic"
        return "scale"

    @staticmethod
    def _day_goal(phase: str, day_content: dict[str, Any]) -> str:
        cta = ExecutionPlanner._string(day_content.get("cta"))
        kpi = ExecutionPlanner._string(day_content.get("kpi"))
        if phase == "setup":
            return "Собрать рабочую систему на основе реальных блоков"
        if phase == "content":
            return cta or "Опубликовать контент и зафиксировать отклик"
        if phase == "traffic":
            return kpi or "Проверить рекламную связку"
        return "Масштабировать связки, которые уже дают отклик"

    @staticmethod
    def _warn_metric(metric: str) -> str:
        if not metric:
            return "Уточнить метрику"
        if any(ch.isdigit() for ch in metric):
            return metric
        return f"Проверить {metric}"

    @staticmethod
    def _fail_metric(metric: str) -> str:
        digits = "".join(ch for ch in metric if ch.isdigit())
        if digits:
            try:
                return str(max(1, int(digits) // 2))
            except ValueError:
                return "1"
        return "1"

    @staticmethod
    def _string(value: Any) -> str:
        if value is None:
            return ""
        if hasattr(value, "value"):
            value = value.value
        return str(value).strip()

    @staticmethod
    def _enum_value(value: Any, enum_cls: Any) -> str:
        text = ExecutionPlanner._string(value).lower()
        if hasattr(enum_cls, "value") and not hasattr(enum_cls, "_value2member_map_"):
            return ExecutionPlanner._string(enum_cls.value).lower()
        if not text:
            return next(iter(enum_cls)).value
        if text in enum_cls._value2member_map_:
            return text
        for member in enum_cls:
            if member.name.lower() == text:
                return member.value
        return next(iter(enum_cls)).value

    @staticmethod
    def _content_archetype(value: str) -> ContentArchetype | None:
        try:
            return ContentArchetype(value)
        except Exception:
            return None


def plan_execution(final_data: dict[str, Any] | Any) -> PlannerResult:
    return ExecutionPlanner().plan(final_data)
