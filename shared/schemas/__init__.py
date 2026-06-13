"""Shared Pydantic schemas for Marketing OS v4.

All components communicate through these schemas ONLY.
No dict[str, Any], no Markdown, no HTML, no free text.
"""

from shared.schemas.base import MarketingOSBaseModel
from shared.schemas.brief import Brief, BriefPricing, BriefMarketing, BriefSales, BriefBudget, BriefValidationResult
from shared.schemas.blocks import (
    # Enums
    Severity, Difficulty, Psychotype, TriggerType, FunnelStage,
    ContentFormat, ContentArchetype, Platform, MissionType, TaskStatus, Confidence,
    # BLOCK 01-02
    MarketAnalysis, BusinessDiagnosis,
    # BLOCK 03
    Competitor, CompetitorAnalysis,
    # BLOCK 04-05
    MarketingPlatform, OwnerPortrait,
    # BLOCK 06-07-08
    ProductSystem, FlagshipProduct, ProductLadderStep, ProductLadder,
    # BLOCK 09
    LeadMagnet, LeadMagnets,
    # BLOCK 10
    AudienceSegment, Audience,
    # BLOCK 11
    Avatar, AvatarSet,
    # BLOCK 12
    PsychotypeMapping, Psychotypes,
    # BLOCK 13
    Pain, Pains,
    # BLOCK 14
    Trigger, Triggers,
    # BLOCK 15
    Offer, Offers,
    # BLOCK 16
    FunnelStep, Funnels,
    # BLOCK 17
    AdCampaign, AdvertisingStrategy,
    # BLOCK 18
    ContentDay, ContentPlan,
    # BLOCK 19
    Reel, Reels,
    # BLOCK 20
    BlogArticle, BlogArticles,
    # BLOCK 21
    Post, Posts,
    # BLOCK 22
    VisualFrame, VisualBrief, VisualBriefs,
    # BLOCK 23
    SalesScript, SalesScripts,
    # BLOCK 24
    KPI, KPISet,
    # BLOCK 25
    FirstDayPlan, First7Days,
    # BLOCK 26
    LaunchPlanStep, LaunchPlan,
    # BLOCK 27
    CrossValidationResult, QualityControl,
)
from shared.schemas.final_data import FinalData
from shared.schemas.execution_view_model import (
    LevelInfo, Achievement, Gamification,
    Mission, DaySummary, ProjectInfo,
    ContentTask, AdsTask, SalesTask, KPITask,
    ExecutionViewModel,
)
from shared.schemas.export_package import ExportPackage

__all__ = [
    # Base
    "MarketingOSBaseModel",
    # Brief
    "Brief", "BriefPricing", "BriefMarketing", "BriefSales", "BriefBudget",
    "BriefValidationResult",
    # Enums
    "Severity", "Difficulty", "Psychotype", "TriggerType", "FunnelStage",
    "ContentFormat", "ContentArchetype", "Platform", "MissionType", "TaskStatus",
    "Confidence",
    # Blocks
    "MarketAnalysis", "BusinessDiagnosis",
    "Competitor", "CompetitorAnalysis",
    "MarketingPlatform", "OwnerPortrait",
    "ProductSystem", "FlagshipProduct", "ProductLadderStep", "ProductLadder",
    "LeadMagnet", "LeadMagnets",
    "AudienceSegment", "Audience",
    "Avatar", "AvatarSet",
    "PsychotypeMapping", "Psychotypes",
    "Pain", "Pains",
    "Trigger", "Triggers",
    "Offer", "Offers",
    "FunnelStep", "Funnels",
    "AdCampaign", "AdvertisingStrategy",
    "ContentDay", "ContentPlan",
    "Reel", "Reels",
    "BlogArticle", "BlogArticles",
    "Post", "Posts",
    "VisualFrame", "VisualBrief", "VisualBriefs",
    "SalesScript", "SalesScripts",
    "KPI", "KPISet",
    "FirstDayPlan", "First7Days",
    "LaunchPlanStep", "LaunchPlan",
    "CrossValidationResult", "QualityControl",
    # FinalData
    "FinalData",
    # ExecutionViewModel
    "LevelInfo", "Achievement", "Gamification",
    "Mission", "DaySummary", "ProjectInfo",
    "ContentTask", "AdsTask", "SalesTask", "KPITask",
    "ExecutionViewModel",
    # Export
    "ExportPackage",
]