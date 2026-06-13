"""Pydantic schemas for all 27 Intelligence Layer blocks."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import Field

from shared.schemas.base import MarketingOSBaseModel


# ============================================================
# Enums
# ============================================================

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Psychotype(str, Enum):
    RATIONAL = "rational"
    EMOTIONAL = "emotional"
    STATUS = "status"
    SAFETY = "safety"
    EXPERTISE = "expertise"
    URGENCY = "urgency"


class TriggerType(str, Enum):
    FEAR = "fear"
    BENEFIT = "benefit"
    SIMPLICITY = "simplicity"
    STATUS = "status"
    SPEED = "speed"
    SAFETY = "safety"
    PROOF = "proof"
    NOVELTY = "novelty"


class FunnelStage(str, Enum):
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    PURCHASE = "purchase"
    REPEAT = "repeat"
    REFERRAL = "referral"


class ContentFormat(str, Enum):
    POST = "post"
    STORY = "story"
    REEL = "reel"
    ARTICLE = "article"
    LEAD_MAGNET = "lead_magnet"


class ContentArchetype(str, Enum):
    TOUR = "tour"
    BEFORE_AFTER = "before_after"
    CHECKLIST = "checklist"
    CASE = "case"
    FAQ = "faq"
    OBJECTION = "objection"
    MISTAKE = "mistake"
    BEHIND_THE_SCENES = "behind_the_scenes"
    COMPARISON = "comparison"
    REVIEW = "review"
    TRANSFORMATION = "transformation"


class Platform(str, Enum):
    VK = "vk"
    TELEGRAM = "telegram"
    YANDEX = "yandex"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    SEO = "seo"
    PARTNERS = "partners"


class MissionType(str, Enum):
    SETUP = "setup"
    CONTENT = "content"
    ADS = "ads"
    SALES = "sales"
    REVIEW = "review"


class TaskStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    REWORK = "rework"
    FAILED = "failed"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================
# BLOCK 01 — Market Analysis
# ============================================================

class MarketAnalysis(MarketingOSBaseModel):
    """BLOCK 01 — Market Analysis. Understand the market, not the company."""

    market_overview: str = Field(default="", description="Summary of the market")
    market_size: str = Field(default="", description="Estimated market size (qualitative)")
    seasonality: list[str] = Field(default_factory=list, description="Seasonal patterns")
    buying_triggers: list[str] = Field(default_factory=list, description="What triggers purchases")
    buying_barriers: list[str] = Field(default_factory=list, description="What prevents purchases")
    growth_opportunities: list[str] = Field(default_factory=list, description="Growth vectors")
    channels: list[str] = Field(default_factory=list, description="Active market channels")
    risks: list[str] = Field(default_factory=list, description="Market risks")
    confidence: Confidence = Field(default=Confidence.MEDIUM, description="Confidence level")


# ============================================================
# BLOCK 02 — Business Diagnosis
# ============================================================

class BusinessDiagnosis(MarketingOSBaseModel):
    """BLOCK 02 — Business Diagnosis. Find what prevents growth."""

    constraints: list[str] = Field(default_factory=list, description="Growth constraints")
    quick_wins: list[str] = Field(default_factory=list, description="Quick improvements (min 5)")
    growth_barriers: list[str] = Field(default_factory=list, description="Critical bottlenecks")
    focus_areas: list[str] = Field(default_factory=list, description="Recommended focus areas")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 03 — Competitor Analysis
# ============================================================

class Competitor(MarketingOSBaseModel):
    """Single competitor profile."""

    name: str = Field(..., min_length=1, description="Competitor name")
    offer: str = Field(default="", description="Main offer")
    pricing: str = Field(default="", description="Pricing model")
    channels: list[str] = Field(default_factory=list, description="Active channels")
    strengths: list[str] = Field(default_factory=list, description="Competitive advantages")
    weaknesses: list[str] = Field(default_factory=list, description="Vulnerabilities")
    lead_magnets: list[str] = Field(default_factory=list, description="Lead magnets used")
    status: str = Field(default="analyzed", description="Data status (analyzed / insufficient_data)")
    assumption: str = Field(default="", description="Assumption if data is insufficient")


class CompetitorAnalysis(MarketingOSBaseModel):
    """BLOCK 03 — Competitor Analysis. Minimum 10 competitors."""

    competitors: list[Competitor] = Field(default_factory=list, description="Min 10 competitors")
    advantages: list[str] = Field(default_factory=list, description="Our advantages over competitors")
    gaps: list[str] = Field(default_factory=list, description="Market gaps to exploit")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 04 — Marketing Platform
# ============================================================

class MarketingPlatform(MarketingOSBaseModel):
    """BLOCK 04 — Marketing Platform. Brand foundation."""

    positioning: str = Field(default="", description="Positioning statement")
    usp: str = Field(default="", description="Unique Selling Proposition")
    big_idea: str = Field(default="", description="The big idea / core message")
    tone_of_voice: str = Field(default="", description="Brand tone of voice")
    proof_points: list[str] = Field(default_factory=list, description="Reasons to believe (RTB)")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 05 — Owner Portrait
# ============================================================

class OwnerPortrait(MarketingOSBaseModel):
    """BLOCK 05 — Owner Portrait. How the owner amplifies sales."""

    owner_story: str = Field(default="", description="Founder story")
    expertise: str = Field(default="", description="Area of expertise")
    trust_points: list[str] = Field(default_factory=list, description="Min 3 reasons to trust")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 06 — Product System
# ============================================================

class ProductSystem(MarketingOSBaseModel):
    """BLOCK 06 — Product System. Full product ladder."""

    lead_magnets: list[str] = Field(default_factory=list, description="Lead magnets")
    content_magnets: list[str] = Field(default_factory=list, description="Content lead magnets")
    tripwires: list[str] = Field(default_factory=list, description="Tripwire products")
    core_products: list[str] = Field(default_factory=list, description="Core products")
    flagship_products: list[str] = Field(default_factory=list, description="Flagship products")
    upsells: list[str] = Field(default_factory=list, description="Upsell products")
    cross_sells: list[str] = Field(default_factory=list, description="Cross-sell products")
    retention: list[str] = Field(default_factory=list, description="Retention tools")
    referrals: list[str] = Field(default_factory=list, description="Referral programs")


# ============================================================
# BLOCK 07 — Flagship Product
# ============================================================

class FlagshipProduct(MarketingOSBaseModel):
    """BLOCK 07 — Flagship Product. The main product."""

    product: str = Field(default="", description="Product name")
    audience: list[str] = Field(default_factory=list, description="Target audience for this product")
    core_pains: list[str] = Field(default_factory=list, description="Core pains it solves")
    core_benefits: list[str] = Field(default_factory=list, description="Core benefits")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 08 — Product Ladder
# ============================================================

class ProductLadderStep(MarketingOSBaseModel):
    """A step in the product ladder."""

    product_name: str = Field(..., min_length=1)
    price: str = Field(default="")
    next_step: str = Field(default="", description="Where this leads")


class ProductLadder(MarketingOSBaseModel):
    """BLOCK 08 — Product Ladder. Linked product chain."""

    steps: list[ProductLadderStep] = Field(default_factory=list, description="Ordered product steps")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 09 — Lead Magnets
# ============================================================

class LeadMagnet(MarketingOSBaseModel):
    """A single lead magnet."""

    title: str = Field(..., min_length=1, description="Lead magnet title")
    pain: str = Field(default="", description="Pain it addresses")
    cta: str = Field(default="", description="Call to action")
    magnet_type: str = Field(default="checklist", description="Type (checklist, calculator, test, ...)")


class LeadMagnets(MarketingOSBaseModel):
    """BLOCK 09 — Lead Magnets. Min 10."""

    magnets: list[LeadMagnet] = Field(default_factory=list, description="Min 10 lead magnets")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 10 — Audience
# ============================================================

class AudienceSegment(MarketingOSBaseModel):
    """A market segment."""

    segment_name: str = Field(..., min_length=1, description="Segment name")
    description: str = Field(default="", description="Segment description")
    problem: str = Field(default="", description="Core problem")
    motivation: str = Field(default="", description="Purchase motivation")


class Audience(MarketingOSBaseModel):
    """BLOCK 10 — Target Audience. Segmentation by solutions."""

    segments: list[AudienceSegment] = Field(default_factory=list, description="Min 5 segments")
    max_segments: int = Field(default=15, description="Maximum segments")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 11 — Avatars
# ============================================================

class Avatar(MarketingOSBaseModel):
    """A detailed customer avatar."""

    avatar_id: str = Field(default="", description="Unique avatar ID")
    name: str = Field(..., min_length=1, description="Persona name")
    age: int = Field(..., ge=14, le=120, description="Age (must be int, not string)")
    occupation: str = Field(default="", description="Occupation")
    income: str = Field(default="", description="Income level (required)")
    interests: list[str] = Field(default_factory=list, description="Interests")
    goals: list[str] = Field(default_factory=list, description="Goals (required)")
    fears: list[str] = Field(default_factory=list, description="Fears (required)")
    buying_motivation: list[str] = Field(default_factory=list, description="Why they buy")
    trust_triggers: list[str] = Field(default_factory=list, description="What builds trust")
    channels: list[str] = Field(default_factory=list, description="Preferred platforms")


class AvatarSet(MarketingOSBaseModel):
    """BLOCK 11 — Avatars. Min 5, all distinct (similarity < 70%)."""

    avatars: list[Avatar] = Field(default_factory=list, description="Min 5 distinct avatars")
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Max similarity across avatars")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 12 — Psychotypes
# ============================================================

class PsychotypeMapping(MarketingOSBaseModel):
    """Psychotype mapping for one avatar."""

    avatar_id: str = Field(..., min_length=1)
    primary_type: Psychotype = Field(..., description="Primary decision psychotype")
    secondary_type: Psychotype = Field(..., description="Secondary psychotype")


class Psychotypes(MarketingOSBaseModel):
    """BLOCK 12 — Psychotypes. Decision-making styles."""

    mappings: list[PsychotypeMapping] = Field(default_factory=list)
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 13 — Pains
# ============================================================

class Pain(MarketingOSBaseModel):
    """A specific customer pain point."""

    pain_id: str = Field(default="", description="Unique pain ID")
    avatar_id: str = Field(..., min_length=1, description="Linked avatar ID")
    pain: str = Field(..., min_length=1, description="Pain description")
    severity: Severity = Field(default=Severity.MEDIUM, description="Pain severity")
    emotion: str = Field(default="", description="Associated emotion")
    consequence: str = Field(default="", description="Price of inaction")
    solution: str = Field(default="", description="How to solve (required)")
    offer: str = Field(default="", description="Linked offer hint")
    cta: str = Field(default="", description="Call to action")
    metric: str = Field(default="", description="How to measure relief")


class Pains(MarketingOSBaseModel):
    """BLOCK 13 — Pains. Min 10 per avatar (50 total)."""

    pains: list[Pain] = Field(default_factory=list, description="Min 50 pains")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 14 — Triggers
# ============================================================

class Trigger(MarketingOSBaseModel):
    """A marketing trigger."""

    trigger_id: str = Field(default="", description="Unique trigger ID")
    pain_id: str = Field(..., min_length=1, description="Linked pain ID")
    avatar_id: str = Field(default="", description="Linked avatar ID")
    trigger_text: str = Field(..., min_length=1, description="Trigger text")
    trigger_type: TriggerType = Field(default=TriggerType.FEAR, description="Trigger category")


class Triggers(MarketingOSBaseModel):
    """BLOCK 14 — Triggers. Min 10 per avatar."""

    triggers: list[Trigger] = Field(default_factory=list)
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 15 — Offers
# ============================================================

class Offer(MarketingOSBaseModel):
    """A marketing offer (not a product description — a reason to buy)."""

    offer_id: str = Field(default="", description="Unique offer ID")
    avatar_id: str = Field(..., min_length=1, description="Linked avatar ID")
    pain_id: str = Field(..., min_length=1, description="Linked pain ID (required)")
    headline: str = Field(..., min_length=1, description="Offer headline")
    value: str = Field(default="", description="Value proposition")
    result: str = Field(default="", description="Expected result")
    timeframe: str = Field(default="", description="Time to result")
    cta: str = Field(default="", description="Call to action")


class Offers(MarketingOSBaseModel):
    """BLOCK 15 — Offers. Min 10 per avatar (50 total)."""

    offers: list[Offer] = Field(default_factory=list)
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 16 — Funnels
# ============================================================

class FunnelStep(MarketingOSBaseModel):
    """One step in the auto-funnel."""

    stage: FunnelStage = Field(..., description="Funnel stage")
    client_state: str = Field(default="", description="Client's state of mind")
    content: str = Field(default="", description="Content at this stage")
    cta: str = Field(default="", description="Call to action")
    kpi: str = Field(default="", description="KPI for this stage")
    next_step: str = Field(default="", description="Next step description")


class Funnels(MarketingOSBaseModel):
    """BLOCK 16 — Auto Funnel. Min 5 stages."""

    steps: list[FunnelStep] = Field(default_factory=list, description="Min 5 funnel steps")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 17 — Advertising Strategy
# ============================================================

class AdCampaign(MarketingOSBaseModel):
    """A single advertising campaign."""

    platform: Platform = Field(default=Platform.VK, description="Ad platform")
    audience: str = Field(default="", description="Target audience description")
    creative: str = Field(default="", description="Creative idea")
    offer: str = Field(default="", description="Offer to promote")
    budget: str = Field(default="500", description="Test budget (max 1000 first run)")
    test_duration: str = Field(default="3", description="Test duration in days")
    kpi: str = Field(default="", description="Success KPI")
    success_threshold: str = Field(default="CTR > 2%", description="When to scale")
    stop_threshold: str = Field(default="CTR < 1%", description="When to stop")
    scale_threshold: str = Field(default="", description="When to increase budget")


class AdvertisingStrategy(MarketingOSBaseModel):
    """BLOCK 17 — Advertising Strategy. Test → Analyze → Scale."""

    campaigns: list[AdCampaign] = Field(default_factory=list)
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 18 — Content Plan
# ============================================================

class ContentDay(MarketingOSBaseModel):
    """Content plan for a single day."""

    day: int = Field(..., ge=1, le=30, description="Day number 1-30")
    avatar_id: str = Field(default="", description="Target avatar")
    pain_id: str = Field(default="", description="Target pain")
    offer_id: str = Field(default="", description="Linked offer")
    platform: Platform = Field(default=Platform.INSTAGRAM)
    content_format: ContentFormat = Field(default=ContentFormat.POST)
    archetype: ContentArchetype = Field(default=ContentArchetype.CASE, description="Content archetype")
    cta: str = Field(default="", description="Call to action")
    kpi: str = Field(default="", description="KPI to measure")


class ContentPlan(MarketingOSBaseModel):
    """BLOCK 18 — Content Plan. 30 unique days."""

    days: list[ContentDay] = Field(default_factory=list, description="30 days of content")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 19 — Reels
# ============================================================

class Reel(MarketingOSBaseModel):
    """A Reels specification."""

    archetype: ContentArchetype = Field(default=ContentArchetype.CASE)
    hook: str = Field(..., min_length=1, description="Opening hook")
    problem: str = Field(default="", description="Problem statement")
    insight: str = Field(default="", description="Key insight")
    proof: str = Field(default="", description="Proof / evidence")
    frame_1: str = Field(default="", description="Shot 1 description")
    frame_2: str = Field(default="", description="Shot 2 description")
    frame_3: str = Field(default="", description="Shot 3 description")
    frame_4: str = Field(default="", description="Shot 4 description")
    voiceover: str = Field(default="", description="Voiceover script")
    on_screen_text: str = Field(default="", description="Text overlay")
    cta: str = Field(default="", description="Call to action")


class Reels(MarketingOSBaseModel):
    """BLOCK 19 — Reels. Min 30."""

    reels: list[Reel] = Field(default_factory=list, description="Min 30 Reels")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 20 — Blog Articles
# ============================================================

class BlogArticle(MarketingOSBaseModel):
    """A blog article / SEO piece."""

    title: str = Field(..., min_length=1, description="Article title")
    search_query: str = Field(default="", description="SEO search query")
    structure: list[str] = Field(default_factory=list, description="Article structure")
    key_points: list[str] = Field(default_factory=list, description="Key takeaways")
    cta: str = Field(default="", description="Call to action")
    linked_product: str = Field(default="", description="Related product")
    linked_lead_magnet: str = Field(default="", description="Related lead magnet")


class BlogArticles(MarketingOSBaseModel):
    """BLOCK 20 — Blog Articles. Min 30."""

    articles: list[BlogArticle] = Field(default_factory=list, description="Min 30 articles")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 21 — Posts
# ============================================================

class Post(MarketingOSBaseModel):
    """A ready-to-publish social media post."""

    platform: Platform = Field(default=Platform.INSTAGRAM)
    offer_id: str = Field(default="", description="Linked offer ID")
    avatar_id: str = Field(default="", description="Target avatar")
    pain_id: str = Field(default="", description="Target pain")
    headline: str = Field(..., min_length=1, description="Post headline")
    post_text: str = Field(..., min_length=1, description="Full post text")
    cta: str = Field(default="", description="Call to action")
    hashtags: list[str] = Field(default_factory=list, description="Hashtags")
    target_action: str = Field(default="", description="Where it leads")
    metric: str = Field(default="", description="Success metric")


class Posts(MarketingOSBaseModel):
    """BLOCK 21 — Posts. Min 30 ready posts."""

    posts: list[Post] = Field(default_factory=list, description="Min 30 posts")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 22 — Visual Briefs
# ============================================================

class VisualFrame(MarketingOSBaseModel):
    """A single visual shot description."""

    frame_number: int = Field(..., ge=1, le=10)
    description: str = Field(..., min_length=1, description="What to show")
    angle: str = Field(default="", description="Camera angle")
    lighting: str = Field(default="", description="Lighting notes")
    text_overlay: str = Field(default="", description="On-screen text")


class VisualBrief(MarketingOSBaseModel):
    """Visual brief for a content piece."""

    material_id: str = Field(default="", description="Linked material ID")
    visual_type: str = Field(default="photo", description="Type: photo / video / carousel")
    frames: list[VisualFrame] = Field(default_factory=list, description="Shot list")
    goal: str = Field(default="", description="Visual goal")


class VisualBriefs(MarketingOSBaseModel):
    """BLOCK 22 — Visual Briefs."""

    briefs: list[VisualBrief] = Field(default_factory=list)
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 23 — Sales Scripts
# ============================================================

class SalesScript(MarketingOSBaseModel):
    """A ready-to-use sales script."""

    scenario: str = Field(..., min_length=1, description="Scenario name (first_response, price, ...)")
    goal: str = Field(default="", description="Script goal")
    message: str = Field(..., min_length=1, description="Ready-to-copy message")
    next_step: str = Field(default="", description="Where this leads")
    notes: str = Field(default="", description="Usage notes")


class SalesScripts(MarketingOSBaseModel):
    """BLOCK 23 — Sales Scripts."""

    scripts: list[SalesScript] = Field(default_factory=list)
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 24 — KPI
# ============================================================

class KPI(MarketingOSBaseModel):
    """A numeric KPI definition."""

    action: str = Field(..., min_length=1, description="Action being measured")
    metric: str = Field(..., min_length=1, description="Metric name")
    success_threshold: str = Field(..., description="Numeric success threshold")
    warning_threshold: str = Field(..., description="Numeric warning threshold")
    fail_threshold: str = Field(..., description="Numeric fail threshold")
    if_success: str = Field(default="", description="Action if success")
    if_warning: str = Field(default="", description="Action if warning")
    if_fail: str = Field(default="", description="Action if fail")


class KPISet(MarketingOSBaseModel):
    """BLOCK 24 — KPI Metrics."""

    kpis: list[KPI] = Field(default_factory=list)
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 25 — First 7 Days Plan
# ============================================================

class FirstDayPlan(MarketingOSBaseModel):
    """Plan for a single day in the first week."""

    day: int = Field(..., ge=1, le=7)
    preparation: list[str] = Field(default_factory=list)
    content: list[str] = Field(default_factory=list)
    ads: list[str] = Field(default_factory=list)
    kpi_check: list[str] = Field(default_factory=list)


class First7Days(MarketingOSBaseModel):
    """BLOCK 25 — First 7 Days Plan."""

    days: list[FirstDayPlan] = Field(default_factory=list, description="7 days with at least 1 action each")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 26 — Launch Plan
# ============================================================

class LaunchPlanStep(MarketingOSBaseModel):
    """A step in the unified launch plan."""

    step_number: int = Field(..., ge=1)
    action: str = Field(..., min_length=1, description="What to do")
    next_step: str = Field(default="", description="What follows")


class LaunchPlan(MarketingOSBaseModel):
    """BLOCK 26 — Unified Launch Plan."""

    steps: list[LaunchPlanStep] = Field(default_factory=list, description="All launch steps chained")
    outcome: str = Field(default="", description="What happens if client executes everything")
    confidence: Confidence = Field(default=Confidence.MEDIUM)


# ============================================================
# BLOCK 27 — Quality Control
# ============================================================

class CrossValidationResult(MarketingOSBaseModel):
    """Result of one cross-validator."""

    validator: str = Field(..., description="Validator name (avatar→pain, pain→offer, ...)")
    passed: bool = Field(..., description="Whether the check passed")
    issues: list[str] = Field(default_factory=list, description="Issues found")


class QualityControl(MarketingOSBaseModel):
    """BLOCK 27 — Quality Control. Final validation of the entire project."""

    overall_pass: bool = Field(default=False, description="Overall quality gate")
    cross_validations: list[CrossValidationResult] = Field(default_factory=list, description="6 cross-validator results")
    stop_words_found: list[str] = Field(default_factory=list, description="Stop words detected")
    hallucinations: list[str] = Field(default_factory=list, description="Potential hallucinations")
    empties: list[str] = Field(default_factory=list, description="Empty blocks / fields")
    repeats: list[str] = Field(default_factory=list, description="Repeated content")
    disconnected_ctas: list[str] = Field(default_factory=list, description="CTAs that lead nowhere")
    disconnected_offers: list[str] = Field(default_factory=list, description="Offers not linked to pains")
    disconnected_content: list[str] = Field(default_factory=list, description="Content without purpose")
    can_deliver_to_client: bool = Field(default=False, description="Can this be given to the client?")
    quality_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Final quality score 0-100")
