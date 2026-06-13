"""FinalData schema — the main output of Intelligence Layer (27 blocks)."""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from shared.schemas.base import MarketingOSBaseModel
from shared.schemas.blocks import (
    AdvertisingStrategy,
    Audience,
    AvatarSet,
    BlogArticles,
    BusinessDiagnosis,
    CompetitorAnalysis,
    ContentPlan,
    First7Days,
    Funnels,
    KPISet,
    LaunchPlan,
    LeadMagnets,
    MarketAnalysis,
    MarketingPlatform,
    Offers,
    OwnerPortrait,
    Pains,
    Posts,
    ProductLadder,
    ProductSystem,
    Psychotypes,
    QualityControl,
    Reels,
    SalesScripts,
    Triggers,
    VisualBriefs,
)


class FinalData(MarketingOSBaseModel):
    """Main output of the Intelligence Layer — complete marketing system.

    Contains results from all 27 blocks.
    Empty blocks {} are FORBIDDEN — they must be omitted.
    """

    project_id: str = Field(..., description="Project identifier")
    project_name: str = Field(..., description="Project name from brief")

    # BLOCK 01
    market_analysis: Optional[MarketAnalysis] = Field(
        default=None, description="BLOCK 01 — Market Analysis"
    )
    # BLOCK 02
    business_diagnosis: Optional[BusinessDiagnosis] = Field(
        default=None, description="BLOCK 02 — Business Diagnosis"
    )
    # BLOCK 03
    competitors: Optional[CompetitorAnalysis] = Field(
        default=None, description="BLOCK 03 — Competitor Analysis"
    )
    # BLOCK 04
    platform: Optional[MarketingPlatform] = Field(
        default=None, description="BLOCK 04 — Marketing Platform"
    )
    # BLOCK 05
    owner_portrait: Optional[OwnerPortrait] = Field(
        default=None, description="BLOCK 05 — Owner Portrait"
    )
    # BLOCK 06
    product_system: Optional[ProductSystem] = Field(
        default=None, description="BLOCK 06 — Product System"
    )
    # BLOCK 07
    flagship_product: Optional[ProductSystem] = Field(
        default=None, description="BLOCK 07 — Flagship Product"
    )
    # BLOCK 08
    product_ladder: Optional[ProductLadder] = Field(
        default=None, description="BLOCK 08 — Product Ladder"
    )
    # BLOCK 09
    lead_magnets: Optional[LeadMagnets] = Field(
        default=None, description="BLOCK 09 — Lead Magnets"
    )
    # BLOCK 10
    audience: Optional[Audience] = Field(
        default=None, description="BLOCK 10 — Target Audience"
    )
    # BLOCK 11
    avatars: Optional[AvatarSet] = Field(
        default=None, description="BLOCK 11 — Avatars"
    )
    # BLOCK 12
    psychotypes: Optional[Psychotypes] = Field(
        default=None, description="BLOCK 12 — Psychotypes"
    )
    # BLOCK 13
    pains: Optional[Pains] = Field(
        default=None, description="BLOCK 13 — Pains"
    )
    # BLOCK 14
    triggers: Optional[Triggers] = Field(
        default=None, description="BLOCK 14 — Triggers"
    )
    # BLOCK 15
    offers: Optional[Offers] = Field(
        default=None, description="BLOCK 15 — Offers"
    )
    # BLOCK 16
    funnels: Optional[Funnels] = Field(
        default=None, description="BLOCK 16 — Auto Funnels"
    )
    # BLOCK 17
    advertising: Optional[AdvertisingStrategy] = Field(
        default=None, description="BLOCK 17 — Advertising Strategy"
    )
    # BLOCK 18
    content_plan: Optional[ContentPlan] = Field(
        default=None, description="BLOCK 18 — Content Plan"
    )
    # BLOCK 19
    reels: Optional[Reels] = Field(
        default=None, description="BLOCK 19 — Reels"
    )
    # BLOCK 20
    blog_articles: Optional[BlogArticles] = Field(
        default=None, description="BLOCK 20 — Blog Articles"
    )
    # BLOCK 21
    posts: Optional[Posts] = Field(
        default=None, description="BLOCK 21 — Posts"
    )
    # BLOCK 22
    visual_briefs: Optional[VisualBriefs] = Field(
        default=None, description="BLOCK 22 — Visual Briefs"
    )
    # BLOCK 23
    sales_scripts: Optional[SalesScripts] = Field(
        default=None, description="BLOCK 23 — Sales Scripts"
    )
    # BLOCK 24
    kpi: Optional[KPISet] = Field(
        default=None, description="BLOCK 24 — KPI Metrics"
    )
    # BLOCK 25
    first_7_days: Optional[First7Days] = Field(
        default=None, description="BLOCK 25 — First 7 Days Plan"
    )
    # BLOCK 26
    launch_plan: Optional[LaunchPlan] = Field(
        default=None, description="BLOCK 26 — Unified Launch Plan"
    )
    # BLOCK 27
    quality_control: Optional[QualityControl] = Field(
        default=None, description="BLOCK 27 — Quality Control"
    )

    # Metadata
    generated_at: str = Field(default="", description="Generation timestamp ISO")
    total_blocks_passed: int = Field(default=0, description="Count of blocks with status=passed")
    total_blocks_failed: int = Field(default=0, description="Count of blocks with status=failed")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence 0.0-1.0")