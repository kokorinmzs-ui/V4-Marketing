"""ExecutionViewModel schema — the contract for HTML Dashboard rendering."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field

from shared.schemas.base import MarketingOSBaseModel
from shared.schemas.blocks import (
    ContentArchetype,
    ContentFormat,
    Difficulty,
    MissionType,
    Platform,
    TaskStatus,
)


# ============================================================
# Gamification
# ============================================================

class LevelInfo(MarketingOSBaseModel):
    """Level definition for the gamification system."""

    name: str = Field(..., description="Level name (Новичок, Контент-Машина, ...)")
    min_xp: int = Field(..., ge=0, description="Minimum XP for this level")
    max_xp: int = Field(..., ge=0, description="Maximum XP for this level")


class Achievement(MarketingOSBaseModel):
    """An achievement the client can unlock."""

    id: str = Field(..., min_length=1, description="Achievement ID")
    title: str = Field(..., min_length=1, description="Achievement title")
    description: str = Field(default="", description="How to unlock")
    unlocked: bool = Field(default=False, description="Whether unlocked")
    unlocked_at: Optional[str] = Field(default=None, description="ISO timestamp of unlock")


class Gamification(MarketingOSBaseModel):
    """Gamification state embedded in the Dashboard."""

    xp: int = Field(default=0, ge=0, description="Experience points")
    level: str = Field(default="Новичок", description="Current level name")
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall progress %")
    completed_tasks: int = Field(default=0, ge=0, description="Tasks done")
    total_tasks: int = Field(default=0, ge=0, description="Total tasks")
    streak: int = Field(default=0, ge=0, description="Daily streak")
    levels: list[LevelInfo] = Field(default_factory=list, description="Level definitions")
    achievements: list[Achievement] = Field(default_factory=list, description="Achievements")


# ============================================================
# Mission (Daily Task)
# ============================================================

class Mission(MarketingOSBaseModel):
    """A single mission — the core unit of the Execution Dashboard.

    Each mission MUST answer:
    - What to do?
    - Where to do it?
    - How to do it? (steps)
    - What to say? (ready_text)
    - What to show?
    - What to measure?
    - What to do next?
    """

    mission_id: str = Field(default="", description="Unique mission ID")
    source_id: str = Field(default="", description="Source record ID from final_data")
    day: int = Field(..., ge=1, le=30, description="Day number 1-30")
    phase: str = Field(default="setup", description="Phase: setup / content / traffic / scale")
    mission_type: MissionType = Field(default=MissionType.CONTENT, description="Type of mission")
    
    # What & Why
    title: str = Field(..., min_length=1, description="Mission title")
    objective: str = Field(default="", description="Why this mission matters")
    why: str = Field(default="", description="Deeper explanation for the client")
    
    # How
    difficulty: Difficulty = Field(default=Difficulty.EASY, description="Difficulty level")
    estimated_time: str = Field(default="10 минут", description="Estimated time")
    steps: list[str] = Field(default_factory=list, description="Step-by-step instructions (min 2)")
    
    # Ready content
    ready_text: str = Field(default="", description="Ready-to-copy text")
    cta: str = Field(default="", description="Call to action")
    avatar_id: Optional[str] = Field(default=None, description="Linked avatar ID")
    pain_id: Optional[str] = Field(default=None, description="Linked pain ID")
    offer_id: Optional[str] = Field(default=None, description="Linked offer ID")
    content_id: Optional[str] = Field(default=None, description="Linked content/post/reel ID")
    kpi_id: Optional[str] = Field(default=None, description="Linked KPI ID")
    
    # Content-specific (if mission_type=content)
    platform: Optional[Platform] = Field(default=None, description="Target platform")
    content_format: Optional[ContentFormat] = Field(default=None, description="Content format")
    archetype: Optional[ContentArchetype] = Field(default=None, description="Content archetype")
    
    # Reels-specific
    hook: Optional[str] = Field(default=None, description="Reels hook")
    frame_1: Optional[str] = Field(default=None, description="Shot 1")
    frame_2: Optional[str] = Field(default=None, description="Shot 2")
    frame_3: Optional[str] = Field(default=None, description="Shot 3")
    frame_4: Optional[str] = Field(default=None, description="Shot 4")
    voiceover: Optional[str] = Field(default=None, description="Voiceover text")
    
    # Ads-specific
    budget: Optional[str] = Field(default=None, description="Ad budget (test only, max 1000)")
    audience: Optional[str] = Field(default=None, description="Ad target audience")
    
    # KPI
    metric: str = Field(default="", description="KPI to measure")
    success_threshold: str = Field(default="", description="Numeric success threshold")
    warning_threshold: str = Field(default="", description="Numeric warning threshold")
    fail_threshold: str = Field(default="", description="Numeric fail threshold")
    
    # Decision tree
    if_success: str = Field(default="", description="What to do if success")
    if_warning: str = Field(default="", description="What to do if warning")
    if_fail: str = Field(default="", description="What to do if fail")
    
    # Gamification
    xp_reward: int = Field(default=10, ge=0, description="XP earned on completion")
    
    # State
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task status")


# ============================================================
# Day Summary
# ============================================================

class DaySummary(MarketingOSBaseModel):
    """Summary for one day in the 30-day plan."""

    day: int = Field(..., ge=1, le=30)
    phase: str = Field(default="setup")
    mission_count: int = Field(default=0, ge=0)
    estimated_time: str = Field(default="30 минут")
    goal: str = Field(default="", description="Day goal")
    completed: bool = Field(default=False)


# ============================================================
# Project Info
# ============================================================

class ProjectInfo(MarketingOSBaseModel):
    """Project metadata for the Dashboard header."""

    name: str = Field(..., min_length=1, description="Project / company name")
    industry: str = Field(default="", description="Industry")
    goal: str = Field(default="", description="30-day goal")
    current_day: int = Field(default=1, ge=1, le=30)
    current_phase: str = Field(default="setup")


# ============================================================
# Content Task (for Content Library tab)
# ============================================================

class ContentTask(MarketingOSBaseModel):
    """A content piece in the Content Library."""

    task_id: str = Field(default="", description="Unique ID")
    source_id: str = Field(default="", description="Source content identifier")
    day: int = Field(..., ge=1, le=30)
    title: str = Field(..., min_length=1)
    content_format: ContentFormat = Field(default=ContentFormat.POST)
    archetype: Optional[ContentArchetype] = Field(default=None)
    ready_text: str = Field(default="", description="Full text to copy")
    cta: str = Field(default="")
    platform: Optional[Platform] = Field(default=None)
    avatar_id: Optional[str] = Field(default=None)
    pain_id: Optional[str] = Field(default=None)
    offer_id: Optional[str] = Field(default=None)
    hashtags: list[str] = Field(default_factory=list)
    metric: str = Field(default="")


# ============================================================
# Ads Task (for Advertising tab)
# ============================================================

class AdsTask(MarketingOSBaseModel):
    """An advertising task."""

    task_id: str = Field(default="")
    source_id: str = Field(default="", description="Source ad identifier")
    day: int = Field(..., ge=1, le=30)
    platform: Platform = Field(default=Platform.VK)
    audience: str = Field(default="")
    creative: str = Field(default="")
    offer: str = Field(default="")
    avatar_id: Optional[str] = Field(default=None)
    offer_id: Optional[str] = Field(default=None)
    budget: str = Field(default="500")
    kpi: str = Field(default="")
    success_threshold: str = Field(default="")
    stop_threshold: str = Field(default="")
    scale_threshold: str = Field(default="")


# ============================================================
# Sales Task (for Sales tab)
# ============================================================

class SalesTask(MarketingOSBaseModel):
    """A sales script task."""

    task_id: str = Field(default="")
    source_id: str = Field(default="", description="Source script identifier")
    day: int = Field(..., ge=1, le=30)
    scenario: str = Field(..., min_length=1)
    goal: str = Field(default="")
    message: str = Field(..., min_length=1, description="Ready-to-copy message")
    next_step: str = Field(default="")
    avatar_id: Optional[str] = Field(default=None)
    pain_id: Optional[str] = Field(default=None)
    offer_id: Optional[str] = Field(default=None)


# ============================================================
# KPI Task
# ============================================================

class KPITask(MarketingOSBaseModel):
    """A KPI measurement task."""

    task_id: str = Field(default="")
    source_id: str = Field(default="", description="Source KPI identifier")
    day: int = Field(..., ge=1, le=30)
    action: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    success_threshold: str = Field(...)
    warning_threshold: str = Field(...)
    fail_threshold: str = Field(...)


# ============================================================
# ExecutionViewModel — THE MAIN CLIENT CONTRACT
# ============================================================

class ExecutionViewModel(MarketingOSBaseModel):
    """The Execution View Model — the single source for HTML Dashboard rendering.

    Generated from final_data.json by Execution Planner.
    The HTML Renderer reads ONLY this model — NEVER brief.json or final_data.json.
    """

    project: ProjectInfo = Field(..., description="Project metadata")

    # Today missions (for the "Сегодня" tab)
    today: DaySummary = Field(..., description="Today's summary")

    # Full 30-day plan
    days: list[DaySummary] = Field(default_factory=list, description="30 days summary")

    # All missions (137+)
    missions: list[Mission] = Field(
        default_factory=list, description="All missions (min 60, target 137)"
    )

    # Content library
    content_tasks: list[ContentTask] = Field(
        default_factory=list, description="Content for 'Контент' tab"
    )

    # Advertising tasks
    ads_tasks: list[AdsTask] = Field(
        default_factory=list, description="Ads for 'Реклама' tab"
    )

    # Sales scripts
    sales_tasks: list[SalesTask] = Field(
        default_factory=list, description="Scripts for 'Продажи' tab"
    )

    # KPI tasks
    kpi_tasks: list[KPITask] = Field(
        default_factory=list, description="KPIs for 'Метрики' tab"
    )

    # Gamification layer
    gamification: Gamification = Field(
        default_factory=Gamification, description="Gamification state"
    )

    # Why it works (explanation for the "Почему это работает" tab)
    why_it_works: list[str] = Field(
        default_factory=list, description="List of explanations for each action"
    )

    # Generated metadata
    generated_at: str = Field(default="", description="ISO timestamp")
    total_missions: int = Field(default=0, ge=0)
    total_days: int = Field(default=30, ge=30)
