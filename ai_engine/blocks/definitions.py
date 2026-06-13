"""Block definitions for all 27 Intelligence Layer blocks."""

from ai_engine.pipeline.block_registry import BlockRegistry, BlockDefinition
from ai_engine.prompts.registry import registry as prompt_registry
from ai_engine.validators.stop_words import validate_stop_words
from ai_engine.validators.content_quality import validate_content_quality
from ai_engine.validators.kpi_validator import validate_kpis
from ai_engine.validators.actionability import validate_actionability

from shared.schemas.blocks import (
    MarketAnalysis, BusinessDiagnosis, CompetitorAnalysis, MarketingPlatform,
    OwnerPortrait, ProductSystem, FlagshipProduct, ProductLadder, LeadMagnets,
    Audience, AvatarSet, Psychotypes, Pains, Triggers, Offers, Funnels,
    AdvertisingStrategy, ContentPlan, Reels, BlogArticles, Posts, VisualBriefs,
    SalesScripts, KPISet, First7Days, LaunchPlan, QualityControl, Confidence,
)


def _schema_validator(model_class):
    from ai_engine.validators.schema_validator import SchemaValidator
    sv = SchemaValidator(model_class)
    def validate(data):
        return sv.validate(data if isinstance(data, dict) else {})
    return validate

def _cross_validate_avatar_pain(stop_set):
    from ai_engine.validators.base import ValidationResult, ValidationIssue, ValidationSeverity
    def validate(data):
        issues = []
        avatars = data.get("avatars", {}).get("avatars", [])
        pains = data.get("pains", {}).get("pains", [])
        avatar_ids = {a.get("avatar_id") for a in avatars if a.get("avatar_id")}
        for pain in pains:
            aid = pain.get("avatar_id")
            if aid and aid not in avatar_ids:
                issues.append(ValidationIssue(code="cross_avatar_pain", message=f"Pain avatar_id '{aid}' not in avatars", path=f"pains.{pain.get('pain_id','?')}", severity=ValidationSeverity.ERROR))
        return ValidationResult(validator_name="cross:avatar->pain", passed=len(issues)==0, score=100.0-len(issues)*20, issues=issues)
    return validate

def _cross_validate_pain_offer(stop_set):
    from ai_engine.validators.base import ValidationResult, ValidationIssue, ValidationSeverity
    def validate(data):
        issues = []
        pains = data.get("pains", {}).get("pains", [])
        offers = data.get("offers", {}).get("offers", [])
        pain_ids = {p.get("pain_id") for p in pains if p.get("pain_id")}
        for offer in offers:
            pid = offer.get("pain_id")
            if pid and pid not in pain_ids:
                issues.append(ValidationIssue(code="cross_pain_offer", message=f"Offer pain_id '{pid}' not in pains", path=f"offers.{offer.get('offer_id','?')}", severity=ValidationSeverity.ERROR))
        return ValidationResult(validator_name="cross:pain->offer", passed=len(issues)==0, score=100.0-len(issues)*20, issues=issues)
    return validate


def register_blocks_01_10(block_registry: BlockRegistry) -> BlockRegistry:
    blocks = [
        BlockDefinition(block_id="01_market_analysis", block_name="Анализ ниши", prompt=prompt_registry.get("01_market_analysis") or "", validators=[_schema_validator(MarketAnalysis), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="02_business_diagnosis", block_name="Диагностика бизнеса", prompt=prompt_registry.get("02_business_diagnosis") or "", validators=[_schema_validator(BusinessDiagnosis), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="03_competitors", block_name="Анализ конкурентов", prompt=prompt_registry.get("03_competitors") or "", validators=[_schema_validator(CompetitorAnalysis), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="04_platform", block_name="Маркетинговая платформа", prompt=prompt_registry.get("04_platform") or "", validators=[_schema_validator(MarketingPlatform), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="05_owner_portrait", block_name="Портрет собственника", prompt=prompt_registry.get("05_owner_portrait") or "", validators=[_schema_validator(OwnerPortrait), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="06_product_system", block_name="Продуктовая линейка", prompt=prompt_registry.get("06_product_system") or "", validators=[_schema_validator(ProductSystem), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="07_flagship", block_name="Флагманский продукт", prompt=prompt_registry.get("07_flagship") or "", validators=[_schema_validator(FlagshipProduct), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="08_product_ladder", block_name="Раскладка продуктовой линейки", prompt=prompt_registry.get("08_product_ladder") or "", validators=[_schema_validator(ProductLadder), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="09_lead_magnets", block_name="Стартовые лид-магниты", prompt=prompt_registry.get("09_lead_magnets") or "", validators=[_schema_validator(LeadMagnets), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="10_audience", block_name="Анализ целевой аудитории", prompt=prompt_registry.get("10_audience") or "", validators=[_schema_validator(Audience), validate_stop_words, validate_content_quality]),
    ]
    for block in blocks:
        block_registry.register(block)
    return block_registry


def register_blocks_11_20(block_registry: BlockRegistry) -> BlockRegistry:
    blocks = [
        BlockDefinition(block_id="11_avatars", block_name="Аватары клиентов", prompt=prompt_registry.get("11_avatars") or "", validators=[_schema_validator(AvatarSet), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="12_psychotypes", block_name="Психотипы", prompt=prompt_registry.get("12_psychotypes") or "", validators=[_schema_validator(Psychotypes), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="13_pains", block_name="Боли аватаров", prompt=prompt_registry.get("13_pains") or "", validators=[_schema_validator(Pains), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="14_triggers", block_name="Маркетинговые триггеры", prompt=prompt_registry.get("14_triggers") or "", validators=[_schema_validator(Triggers), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="15_offers", block_name="Офферы", prompt=prompt_registry.get("15_offers") or "", validators=[_schema_validator(Offers), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="16_funnels", block_name="Автоворонка", prompt=prompt_registry.get("16_funnels") or "", validators=[_schema_validator(Funnels), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="17_advertising", block_name="Рекламная стратегия", prompt=prompt_registry.get("17_advertising") or "", validators=[_schema_validator(AdvertisingStrategy), validate_stop_words, validate_content_quality, validate_kpis]),
        BlockDefinition(block_id="18_content_plan", block_name="Контент-план", prompt=prompt_registry.get("18_content_plan") or "", validators=[_schema_validator(ContentPlan), validate_stop_words, validate_content_quality, validate_kpis]),
        BlockDefinition(block_id="19_reels", block_name="Reels", prompt=prompt_registry.get("19_reels") or "", validators=[_schema_validator(Reels), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="20_blog_articles", block_name="Блог-статьи", prompt=prompt_registry.get("20_blog_articles") or "", validators=[_schema_validator(BlogArticles), validate_stop_words, validate_content_quality]),
    ]
    for block in blocks:
        block_registry.register(block)
    return block_registry


def register_blocks_21_27(block_registry: BlockRegistry) -> BlockRegistry:
    """Register blocks 21-27.

    21 - Posts (min 30)
    22 - Visual Briefs
    23 - Sales Scripts (min 7 scenarios)
    24 - KPI Metrics
    25 - First 7 Days Plan
    26 - Unified Launch Plan
    27 - Quality Control
    """
    blocks = [
        BlockDefinition(block_id="21_posts", block_name="Посты для всех площадок",
                        prompt=prompt_registry.get("21_posts") or "",
                        validators=[_schema_validator(Posts), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="22_visual_briefs", block_name="Визуальные ТЗ",
                        prompt=prompt_registry.get("22_visual_briefs") or "",
                        validators=[_schema_validator(VisualBriefs), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="23_sales_scripts", block_name="Скрипты продаж",
                        prompt=prompt_registry.get("23_sales_scripts") or "",
                        validators=[_schema_validator(SalesScripts), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="24_kpi", block_name="KPI Метрики",
                        prompt=prompt_registry.get("24_kpi") or "",
                        validators=[_schema_validator(KPISet), validate_stop_words, validate_content_quality, validate_kpis]),
        BlockDefinition(block_id="25_first_7_days", block_name="План первых 7 дней",
                        prompt=prompt_registry.get("25_first_7_days") or "",
                        validators=[_schema_validator(First7Days), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="26_launch_plan", block_name="Единый план запуска",
                        prompt=prompt_registry.get("26_launch_plan") or "",
                        validators=[_schema_validator(LaunchPlan), validate_stop_words, validate_content_quality]),
        BlockDefinition(block_id="27_quality_control", block_name="Контроль качества",
                        prompt=prompt_registry.get("27_quality_control") or "",
                        validators=[_schema_validator(QualityControl), validate_stop_words, validate_content_quality]),
    ]
    for block in blocks:
        block_registry.register(block)
    return block_registry