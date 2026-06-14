"""Project generation service that runs the real pipeline."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_engine.blocks.definitions import register_blocks_01_10, register_blocks_11_20, register_blocks_21_27
from ai_engine.prompts.registry import get_master_system_prompt, get_repair_prompt
from ai_engine.exporters.html_dashboard_renderer import render_dashboard
from ai_engine.exporters.package_builder import PackageBuilder
from ai_engine.exporters.zip_exporter import ZipExporter
from ai_engine.pipeline.block_executor import BlockExecutor
from ai_engine.pipeline.block_registry import BlockRegistry
from ai_engine.pipeline.final_data_assembler import FinalDataAssembler
from ai_engine.planner.execution_planner import ExecutionPlanner
from ai_engine.services.ai_service import AIService, AIServiceConfig, AIServiceResponse
from ai_engine.providers.base import LLMUsage
from backend.models.project import ProjectRecord
from backend.services.project_service import ProjectService


class GenerationService:
    def __init__(self, project_service: ProjectService, ai_service: AIService | None = None):
        self.project_service = project_service
        self.ai_service = ai_service or AIService(AIServiceConfig())
        self._llm_mode = self._resolve_llm_mode()
        self._strict_assembly = self._resolve_strict_assembly()

    def generate(self, project_id: str) -> dict[str, Any]:
        project = self.project_service.get_project(project_id)
        self.project_service.set_status(project_id, "running", 10)

        try:
            block_results = self._run_blocks(project)
            llm_summary = self._summarize_llm_usage(block_results)
            assembler = FinalDataAssembler()
            for block_id, result in block_results.items():
                assembler.add_block(block_id, result.status == "passed", result.data)
            assembly = assembler.assemble(strict=self._strict_assembly)
            if not assembly.success or not assembly.final_data:
                raise RuntimeError("; ".join(assembly.errors) or "FinalData assembly failed")

            final_data = assembly.final_data.model_copy(
                update={
                    "project_id": project.project_id,
                    "project_name": project.name,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            planner = ExecutionPlanner()
            planner_result = planner.plan(final_data.model_dump(mode="json"))
            if not planner_result.success or not planner_result.execution_view_model:
                raise RuntimeError("; ".join(planner_result.errors) or "Execution planning failed")

            evm = planner_result.execution_view_model
            html = render_dashboard(evm)
            files = PackageBuilder().build(evm)
            zip_bytes = ZipExporter().export(files)

            artifacts_dir = self.project_service.artifacts_path(project_id)
            self.project_service.write_bundle(project_id, "brief.json", json.dumps(project.brief.model_dump(mode="json"), ensure_ascii=False, indent=2))
            self.project_service.write_bundle(project_id, "final_data.json", json.dumps(final_data.model_dump(mode="json"), ensure_ascii=False, indent=2))
            self.project_service.write_bundle(project_id, "execution_view_model.json", json.dumps(evm.model_dump(mode="json"), ensure_ascii=False, indent=2))
            self.project_service.write_bundle(project_id, "dashboard.html", html)
            self.project_service.write_bundle(project_id, "client-package.zip", zip_bytes)

            self.project_service.set_status(project_id, "completed", 100)
            return {
                "project_id": project_id,
                "status": "completed",
                "artifacts_dir": str(artifacts_dir),
                "files": list(files.keys()),
                "llm_summary": llm_summary,
            }
        except Exception as exc:
            self.project_service.set_status(project_id, "failed", 100, last_error=str(exc))
            raise

    def _run_blocks(self, project: ProjectRecord):
        reg = BlockRegistry()
        register_blocks_01_10(reg)
        register_blocks_11_20(reg)
        register_blocks_21_27(reg)

        payloads = self._build_block_payloads(project)
        results = {}
        for block_id in reg.get_all_ids():
            results[block_id] = BlockExecutor(
                reg,
                self._make_generate_func(block_id, payloads),
                get_repair_prompt(),
                max_repair_attempts=1,
                system_prompt_prefix=get_master_system_prompt(),
            ).execute(block_id)
        return results

    def _summarize_llm_usage(self, block_results: dict[str, Any]) -> dict[str, Any]:
        providers: list[str] = []
        models: list[str] = []
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0

        for result in block_results.values():
            provider_used = getattr(result, "provider_used", "") or ""
            model_used = getattr(result, "model_used", "") or ""
            if provider_used and provider_used not in providers:
                providers.append(provider_used)
            if model_used and model_used not in models:
                models.append(model_used)

            usage = getattr(result, "usage", None)
            if usage is not None:
                total_input_tokens += getattr(usage, "input_tokens", 0) or 0
                total_output_tokens += getattr(usage, "output_tokens", 0) or 0
                total_cost += getattr(usage, "cost", 0.0) or 0.0

        return {
            "mode": self._llm_mode,
            "live_enabled": self._use_live_llm(),
            "providers": providers,
            "models": models,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "cost": round(total_cost, 6),
        }

    def _make_generate_func(self, block_id: str, payloads: dict[str, dict[str, Any]]):
        def fn(**_kwargs):
            if self._use_live_llm():
                response = self.ai_service.generate(
                    system_prompt=_kwargs.get("system_prompt", ""),
                    user_prompt=_kwargs.get("user_prompt", ""),
                    json_schema=_kwargs.get("json_schema"),
                )
                return response
            data = payloads.get(block_id, {"status": "ok"})
            return AIServiceResponse(
                status="success",
                data=data,
                usage=LLMUsage(model="mock", input_tokens=100, output_tokens=50, cost=0.001),
                provider_used="mock",
                model_used="mock",
            )

        return fn

    def _use_live_llm(self) -> bool:
        if self._llm_mode == "live":
            return True
        if self._llm_mode == "deterministic":
            return False
        config = self.ai_service.config
        return bool(config.deepseek_api_key or config.openai_api_key)

    @staticmethod
    def _resolve_llm_mode() -> str:
        mode = (os.getenv("PIPELINE_LLM_MODE") or "auto").strip().lower()
        if mode in {"live", "deterministic", "auto"}:
            return mode
        return "auto"

    @staticmethod
    def _resolve_strict_assembly() -> bool:
        value = (os.getenv("PIPELINE_STRICT_ASSEMBLY") or "true").strip().lower()
        return value not in {"0", "false", "no", "off", "soft"}

    def _build_block_payloads(self, project: ProjectRecord) -> dict[str, dict[str, Any]]:
        brief = project.brief
        project_name = project.name
        industry = brief.industry
        region = brief.region or "Москва"
        primary_product = brief.products[0] if brief.products else project_name
        goal = brief.goals[0] if brief.goals else "Рост продаж за 30 дней"
        competitors = [
            {
                "name": f"Конкурент {index}",
                "offer": f"Услуга {index}",
                "pricing": "от 1 000 ₽",
                "channels": ["instagram"],
                "strengths": ["Узнаваемость"],
                "weaknesses": ["Слабая упаковка"],
                "lead_magnets": ["чек-лист"],
                "status": "analyzed",
                "assumption": "",
            }
            for index in range(1, 11)
        ]
        avatars = [
            {
                "avatar_id": f"av{index}",
                "name": f"Persona {index}",
                "age": 25 + index,
                "occupation": f"Профессия {index}",
                "income": f"{70 + index * 10}k",
                "interests": [industry],
                "goals": [goal],
                "fears": ["Потеря времени"],
                "buying_motivation": ["Получить готовый результат"],
                "trust_triggers": ["Портфолио", "Отзывы"],
                "channels": ["instagram"],
            }
            for index in range(1, 6)
        ]
        pains = [
            {
                "pain_id": f"p{avatar_index}{pain_index}",
                "avatar_id": f"av{avatar_index}",
                "pain": f"Боль {pain_index} для аватара {avatar_index}",
                "severity": "medium",
                "emotion": "fear",
                "consequence": "loss",
                "solution": f"Решение {pain_index}",
                "offer": f"Оффер {pain_index}",
                "cta": f"CTA {pain_index}",
                "metric": f"Metric {pain_index}",
            }
            for avatar_index in range(1, 6)
            for pain_index in range(1, 11)
        ]
        triggers = [
            {
                "trigger_id": f"t{avatar_index}{pain_index}",
                "pain_id": f"p{avatar_index}{pain_index}",
                "avatar_id": f"av{avatar_index}",
                "trigger_text": f"Trigger {pain_index}",
                "trigger_type": "fear",
            }
            for avatar_index in range(1, 6)
            for pain_index in range(1, 11)
        ]
        offers = [
            {
                "offer_id": f"o{avatar_index}{pain_index}",
                "avatar_id": f"av{avatar_index}",
                "pain_id": f"p{avatar_index}{pain_index}",
                "headline": f"Offer {pain_index}",
                "value": f"Value {pain_index}",
                "result": f"Result {pain_index}",
                "timeframe": "3d",
                "cta": f"CTA {pain_index}",
            }
            for avatar_index in range(1, 6)
            for pain_index in range(1, 11)
        ]
        days = []
        for day in range(1, 31):
            avatar_index = ((day - 1) % 5) + 1
            pain_index = ((day - 1) % 10) + 1
            offer_index = ((day - 1) % 10) + 1
            content_format = "reel" if day % 7 == 0 else "post"
            days.append(
                {
                    "day": day,
                    "avatar_id": f"av{avatar_index}",
                    "pain_id": f"p{avatar_index}{pain_index}",
                    "offer_id": f"o{avatar_index}{offer_index}",
                    "platform": "instagram",
                    "content_format": content_format,
                    "archetype": "case",
                    "cta": f"CTA {day}",
                    "kpi": f"{day} likes",
                }
            )
        reels = [
            {
                "archetype": "case",
                "hook": f"Hook {index}",
                "problem": f"Problem {index}",
                "insight": f"Insight {index}",
                "proof": f"Proof {index}",
                "frame_1": f"Frame 1 {index}",
                "frame_2": f"Frame 2 {index}",
                "frame_3": f"Frame 3 {index}",
                "frame_4": f"Frame 4 {index}",
                "voiceover": f"Voiceover {index}",
                "on_screen_text": f"Text {index}",
                "cta": f"CTA {index}",
            }
            for index in range(1, 31)
        ]
        articles = [
            {
                "title": f"Article {index}",
                "search_query": f"{industry} article {index}",
                "structure": ["Intro", "Body", "Offer"],
                "key_points": [f"Point {index}"],
                "cta": f"C{index}",
                "linked_product": primary_product,
                "linked_lead_magnet": "Checklist",
            }
            for index in range(1, 31)
        ]
        posts = [
            {
                "platform": "instagram",
                "avatar_id": f"av{((index - 1) % 5) + 1}",
                "pain_id": f"p{((index - 1) % 5) + 1}{((index - 1) % 10) + 1}",
                "headline": f"Post {index}",
                "post_text": f"Полезный пост {index} для {project_name}",
                "cta": f"CTA {index}",
                "hashtags": ["marketing", "content"],
                "target_action": f"action {index}",
                "metric": f"{index} likes",
                "offer_id": f"o{((index - 1) % 5) + 1}{((index - 1) % 10) + 1}",
            }
            for index in range(1, 31)
        ]
        briefs = [
            {
                "material_id": f"m{index}",
                "visual_type": "photo",
                "frames": [
                    {
                        "frame_number": 1,
                        "description": f"Frame {index}.1",
                        "angle": "wide",
                        "lighting": "natural",
                        "text_overlay": "Overlay",
                    },
                    {
                        "frame_number": 2,
                        "description": f"Frame {index}.2",
                        "angle": "close-up",
                        "lighting": "studio",
                        "text_overlay": "",
                    },
                ],
                "goal": f"Goal {index}",
            }
            for index in range(1, 31)
        ]
        scripts = [
            {
                "scenario": "first_response",
                "goal": "Start conversation",
                "message": f"Здравствуйте! Спасибо за интерес к {project_name}. Какой запрос у вас сейчас?",
                "next_step": "Уточнить потребности",
            },
            {
                "scenario": "price_question",
                "goal": "Handle price objection",
                "message": f"Понимаю вопрос по бюджету. Давайте посмотрим, как {project_name} решает задачу без лишних расходов.",
                "next_step": "Предложить пробный шаг",
            },
            {
                "scenario": "doubt",
                "goal": "Address doubts",
                "message": "Сомнения — это нормально. Покажу кейсы и конкретные результаты.",
                "next_step": "Показать кейсы",
            },
            {
                "scenario": "follow_up",
                "goal": "Re-engage silent lead",
                "message": "Добрый день! Напоминаю о нашем разговоре и хочу предложить удобный следующий шаг.",
                "next_step": "Забронировать слот",
            },
            {
                "scenario": "repeat",
                "goal": "Bring back past client",
                "message": "Рад снова видеть вас. У нас появились новые решения, которые могут усилить результат.",
                "next_step": "Предложить обновление",
            },
            {
                "scenario": "review",
                "goal": "Get testimonial",
                "message": "Спасибо за сотрудничество! Если всё было полезно, будем благодарны за отзыв.",
                "next_step": "Получить отзыв",
            },
            {
                "scenario": "referral",
                "goal": "Get referral",
                "message": "Если знаете коллег, которым это тоже пригодится, с радостью поможем и им.",
                "next_step": "Отправить рекомендацию",
            },
        ]
        kpis = [
            {
                "action": "Reels",
                "metric": "5000 views",
                "success_threshold": "5000",
                "warning_threshold": "1500",
                "fail_threshold": "500",
                "if_success": "scale",
                "if_warning": "keep",
                "if_fail": "change",
            }
        ]
        first_7_days = [
            {
                "day": day,
                "preparation": [f"Prep {day}"],
                "content": [f"Content {day}"],
                "ads": [],
                "kpi_check": [f"Check {day}"],
            }
            for day in range(1, 8)
        ]
        launch_plan = [
            {"step_number": 1, "action": "A", "next_step": "B"},
            {"step_number": 2, "action": "B", "next_step": "C"},
            {"step_number": 3, "action": "C", "next_step": ""},
        ]

        return {
            "01_market_analysis": {
                "market_overview": f"Рынок {industry} в {region}",
                "market_size": "Средний",
                "seasonality": ["Весна", "Осень"],
                "buying_triggers": [goal],
                "buying_barriers": ["Цена"],
                "growth_opportunities": [f"Рост спроса в {region}"],
                "channels": ["instagram"],
                "risks": ["Насыщение"],
                "confidence": "medium",
            },
            "02_business_diagnosis": {
                "constraints": [f"Constraint {index}" for index in range(1, 6)],
                "quick_wins": [f"Quick win {index}" for index in range(1, 6)],
                "growth_barriers": ["Недостаток системности"],
                "focus_areas": ["Контент", "Продажи"],
                "confidence": "medium",
            },
            "03_competitors": {
                "competitors": competitors,
                "advantages": [f"{project_name} выделяется упаковкой"],
                "gaps": ["Нет связки контента с продажами"],
                "confidence": "medium",
            },
            "04_platform": {
                "positioning": f"{project_name} — понятное решение для {industry}",
                "usp": f"Быстрый результат для бизнеса в {region}",
                "big_idea": f"Маркетинг, который ведёт клиента к действию",
                "tone_of_voice": "Дружелюбный",
                "proof_points": ["Кейсы", "Прозрачный процесс", "Понятные шаги"],
                "confidence": "medium",
            },
            "05_owner_portrait": {
                "owner_story": f"Владелец {project_name} знает рынок изнутри",
                "expertise": "Практический опыт и системный подход",
                "trust_points": ["Сильные кейсы", "Честная коммуникация", "Упакованная экспертиза"],
                "confidence": "medium",
            },
            "06_product_system": {
                "lead_magnets": ["Чек-лист"],
                "tripwires": ["Диагностика"],
                "core_products": [primary_product],
                "flagship_products": [f"{primary_product} Pro"],
                "upsells": ["Сопровождение"],
                "cross_sells": ["Доп. услуги"],
                "retention": ["Подписка"],
                "referrals": ["Реферальная программа"],
                "confidence": "medium",
            },
            "07_flagship": {
                "product": primary_product,
                "audience": [f"Клиенты {industry}"],
                "core_pains": ["Нет понятного результата"],
                "core_benefits": ["Прозрачный процесс"],
                "confidence": "medium",
            },
            "08_product_ladder": {
                "steps": [
                    {"product_name": "Entry", "price": "0", "next_step": "Core"},
                    {"product_name": "Core", "price": "990", "next_step": "Flagship"},
                ],
                "confidence": "medium",
            },
            "09_lead_magnets": {
                "magnets": [
                    {"title": f"Lead Magnet {index}", "pain": f"Pain {index}", "cta": f"CTA {index}", "magnet_type": "checklist"}
                    for index in range(1, 11)
                ],
                "confidence": "medium",
            },
            "10_audience": {
                "segments": [
                    {
                        "segment_name": f"Segment {index}",
                        "description": f"Audience segment {index}",
                        "problem": f"Problem {index}",
                        "motivation": f"Motivation {index}",
                    }
                    for index in range(1, 6)
                ],
                "max_segments": 15,
                "confidence": "medium",
            },
            "11_avatars": {"avatars": avatars, "similarity_score": 0.4, "confidence": "medium"},
            "12_psychotypes": {
                "mappings": [
                    {"avatar_id": f"av{index}", "primary_type": "rational", "secondary_type": "emotional"}
                    for index in range(1, 6)
                ],
                "confidence": "medium",
            },
            "13_pains": {"pains": pains, "confidence": "medium"},
            "14_triggers": {"triggers": triggers, "confidence": "medium"},
            "15_offers": {"offers": offers, "confidence": "medium"},
            "16_funnels": {
                "steps": [
                    {"stage": "awareness", "client_state": "cold", "content": "Intro content", "cta": "CTA", "kpi": "KPI", "next_step": "Interest"},
                    {"stage": "interest", "client_state": "warm", "content": "Nurture content", "cta": "CTA", "kpi": "KPI", "next_step": "Consideration"},
                ],
                "confidence": "medium",
            },
            "17_advertising": {
                "campaigns": [
                    {
                        "platform": "vk",
                        "audience": f"Audience in {region}",
                        "creative": "Creative angle",
                        "offer": primary_product,
                        "budget": "500",
                        "test_duration": "3",
                        "kpi": "CTR > 2%",
                        "success_threshold": "CTR > 2%",
                        "stop_threshold": "CTR < 1%",
                        "scale_threshold": "CTR > 3%",
                    }
                ],
                "confidence": "medium",
            },
            "18_content_plan": {"days": days, "confidence": "medium"},
            "19_reels": {"reels": reels, "confidence": "medium"},
            "20_blog_articles": {"articles": articles, "confidence": "medium"},
            "21_posts": {"posts": posts, "confidence": "medium"},
            "22_visual_briefs": {"briefs": briefs, "confidence": "medium"},
            "23_sales_scripts": {"scripts": scripts, "confidence": "medium"},
            "24_kpi": {"kpis": kpis, "confidence": "medium"},
            "25_first_7_days": {"days": first_7_days, "confidence": "medium"},
            "26_launch_plan": {"steps": launch_plan, "outcome": f"Launch {project_name}", "confidence": "medium"},
            "27_quality_control": {
                "overall_pass": True,
                "cross_validations": [],
                "stop_words_found": [],
                "hallucinations": [],
                "empties": [],
                "repeats": [],
                "disconnected_ctas": [],
                "disconnected_offers": [],
                "disconnected_content": [],
                "can_deliver_to_client": True,
                "quality_score": 95.0,
            },
        }
