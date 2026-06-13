"""Brief schema — the main entry point of the Marketing OS v4 system."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator

from shared.schemas.base import MarketingOSBaseModel


class BriefPricing(MarketingOSBaseModel):
    """Pricing information for products/services."""

    model_config = {"extra": "allow"}


class BriefMarketing(MarketingOSBaseModel):
    """Current marketing state."""

    model_config = {"extra": "allow"}


class BriefSales(MarketingOSBaseModel):
    """Current sales state."""

    model_config = {"extra": "allow"}


class BriefBudget(MarketingOSBaseModel):
    """Budget information."""

    model_config = {"extra": "allow"}


class Brief(MarketingOSBaseModel):
    """Main brief submitted by the user (marketer/agency owner).

    The brief is the entry point of the system.
    Required fields: project_name, industry, business_description.
    """

    project_id: str = Field(
        default="",
        description="Unique project identifier (auto-generated if empty)",
    )
    project_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Name of the project / client company",
    )
    industry: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Industry / niche (e.g., photography_studio, dentistry)",
    )
    business_description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Detailed description of the business",
    )
    region: str = Field(
        default="",
        max_length=300,
        description="Target region / city",
    )
    target_markets: list[str] = Field(
        default_factory=list,
        description="List of target markets",
    )
    products: list[str] = Field(
        default_factory=list,
        description="List of products",
    )
    services: list[str] = Field(
        default_factory=list,
        description="List of services",
    )
    pricing: BriefPricing = Field(
        default_factory=BriefPricing,
        description="Pricing information",
    )
    website: str = Field(
        default="",
        max_length=1000,
        description="Company website URL",
    )
    social_links: list[str] = Field(
        default_factory=list,
        description="Social media links",
    )
    current_marketing: BriefMarketing = Field(
        default_factory=BriefMarketing,
        description="Current marketing activities",
    )
    current_sales: BriefSales = Field(
        default_factory=BriefSales,
        description="Current sales process",
    )
    goals: list[str] = Field(
        default_factory=list,
        description="Business goals",
    )
    budget: BriefBudget = Field(
        default_factory=BriefBudget,
        description="Budget constraints",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Known constraints / limitations",
    )
    additional_notes: str = Field(
        default="",
        max_length=10000,
        description="Any additional information",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Brief creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        """Auto-generate project_id if empty."""
        if not v:
            import uuid

            return str(uuid.uuid4())
        return v

    @field_validator("industry")
    @classmethod
    def validate_industry(cls, v: str) -> str:
        """Normalize industry to snake_case."""
        if not v:
            raise ValueError("industry is required")
        return v.strip().lower().replace(" ", "_")


class BriefValidationResult(MarketingOSBaseModel):
    """Result of brief validation."""

    is_valid: bool = Field(..., description="Whether the brief is valid")
    errors: list[str] = Field(
        default_factory=list,
        description="List of validation errors",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="List of warnings (non-blocking)",
    )