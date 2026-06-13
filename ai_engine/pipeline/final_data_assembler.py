"""FinalDataAssembler — assembles final_data.json from passed blocks with cross-validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity
from shared.schemas.final_data import FinalData


@dataclass
class AssemblyResult:
    """Result of assembling final_data.json."""

    success: bool = False
    final_data: FinalData | None = None
    blocks_passed: list[str] = field(default_factory=list)
    blocks_failed: list[str] = field(default_factory=list)
    cross_validation_results: list[ValidationResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class FinalDataAssembler:
    """Assembles final_data.json ONLY from passed blocks."""

    BASE_REQUIRED_BLOCKS = [
        "01_market_analysis",
        "02_business_diagnosis",
        "03_competitors",
        "04_platform",
        "10_audience",
        "11_avatars",
        "13_pains",
        "14_triggers",
        "15_offers",
        "16_funnels",
        "17_advertising",
        "18_content_plan",
        "19_reels",
        "21_posts",
        "23_sales_scripts",
        "24_kpi",
        "25_first_7_days",
        "26_launch_plan",
        "27_quality_control",
    ]

    OPTIONAL_BLOCKS = [
        "05_owner_portrait",
        "06_product_system",
        "07_flagship",
        "08_product_ladder",
        "09_lead_magnets",
        "12_psychotypes",
        "20_blog_articles",
        "22_visual_briefs",
    ]

    WARNING_ONLY_BLOCKS = [
        "12_psychotypes",
        "20_blog_articles",
        "22_visual_briefs",
    ]

    REQUIRED_BLOCKS = BASE_REQUIRED_BLOCKS

    STRICT_REQUIRED_BLOCKS = [
        "01_market_analysis",
        "02_business_diagnosis",
        "03_competitors",
        "04_platform",
        "05_owner_portrait",
        "06_product_system",
        "07_flagship",
        "08_product_ladder",
        "09_lead_magnets",
        "10_audience",
        "11_avatars",
        "12_psychotypes",
        "13_pains",
        "14_triggers",
        "15_offers",
        "16_funnels",
        "17_advertising",
        "18_content_plan",
        "19_reels",
        "20_blog_articles",
        "21_posts",
        "22_visual_briefs",
        "23_sales_scripts",
        "24_kpi",
        "25_first_7_days",
        "26_launch_plan",
        "27_quality_control",
    ]

    def __init__(self):
        self._block_data: dict[str, dict[str, Any]] = {}

    def add_block(self, block_id: str, passed: bool, data: dict[str, Any]) -> None:
        if passed:
            self._block_data[block_id] = data

    def assemble(self, strict: bool = False) -> AssemblyResult:
        result = AssemblyResult()

        required_blocks = self.STRICT_REQUIRED_BLOCKS if strict else self.BASE_REQUIRED_BLOCKS
        for required in required_blocks:
            if required not in self._block_data:
                result.blocks_failed.append(required)
                result.errors.append(f"Required block {required} missing or failed")

        if result.blocks_failed:
            return result

        result.blocks_passed = list(self._block_data.keys())

        cross_validators = [
            self._cv_avatar_pain,
            self._cv_pain_trigger,
            self._cv_pain_offer,
            self._cv_offer_cta,
            self._cv_offer_funnel,
            self._cv_content_avatar,
            self._cv_content_pain,
            self._cv_content_offer,
            self._cv_content_cta,
            self._cv_reels_content,
            self._cv_posts_offer,
            self._cv_posts_linkage,
            self._cv_reels_content_plan,
            self._cv_ads_audience,
            self._cv_kpi_action,
            self._cv_launch_chain,
        ]

        for cv in cross_validators:
            vr = cv()
            result.cross_validation_results.append(vr)
            if not vr.passed:
                blocking = [
                    issue
                    for issue in vr.issues
                    if issue.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)
                    or (strict and issue.severity == ValidationSeverity.WARNING)
                ]
                result.errors.extend(issue.message for issue in blocking)

        if result.errors:
            return result

        try:
            fd = FinalData(
                project_id="assembled-001",
                project_name="Assembled Project",
                market_analysis=self._block_data.get("01_market_analysis"),
                business_diagnosis=self._block_data.get("02_business_diagnosis"),
                competitors=self._block_data.get("03_competitors"),
                platform=self._block_data.get("04_platform"),
                owner_portrait=self._block_data.get("05_owner_portrait"),
                product_system=self._block_data.get("06_product_system"),
                flagship_product=self._block_data.get("07_flagship"),
                product_ladder=self._block_data.get("08_product_ladder"),
                lead_magnets=self._block_data.get("09_lead_magnets"),
                audience=self._block_data.get("10_audience"),
                avatars=self._block_data.get("11_avatars"),
                psychotypes=self._block_data.get("12_psychotypes"),
                pains=self._block_data.get("13_pains"),
                triggers=self._block_data.get("14_triggers"),
                offers=self._block_data.get("15_offers"),
                funnels=self._block_data.get("16_funnels"),
                advertising=self._block_data.get("17_advertising"),
                content_plan=self._block_data.get("18_content_plan"),
                reels=self._block_data.get("19_reels"),
                blog_articles=self._block_data.get("20_blog_articles"),
                posts=self._block_data.get("21_posts"),
                visual_briefs=self._block_data.get("22_visual_briefs"),
                sales_scripts=self._block_data.get("23_sales_scripts"),
                kpi=self._block_data.get("24_kpi"),
                first_7_days=self._block_data.get("25_first_7_days"),
                launch_plan=self._block_data.get("26_launch_plan"),
                quality_control=self._block_data.get("27_quality_control"),
                total_blocks_passed=len(result.blocks_passed),
                total_blocks_failed=0,
            )
        except Exception as exc:
            result.errors.append(f"FinalData construction failed: {exc}")
            return result

        result.success = True
        result.final_data = fd
        return result

    # ------------------------------------------------------------------
    # Cross validators
    # ------------------------------------------------------------------

    def _get_avatar_ids(self) -> set[str]:
        avatars = self._block_data.get("11_avatars", {}).get("avatars", [])
        return {self._string(item.get("avatar_id")) for item in avatars if self._string(item.get("avatar_id"))}

    def _get_pain_ids(self) -> set[str]:
        pains = self._block_data.get("13_pains", {}).get("pains", [])
        return {self._string(item.get("pain_id")) for item in pains if self._string(item.get("pain_id"))}

    def _get_offer_ids(self) -> set[str]:
        offers = self._block_data.get("15_offers", {}).get("offers", [])
        return {self._string(item.get("offer_id")) for item in offers if self._string(item.get("offer_id"))}

    def _get_content_offer_ids(self) -> set[str]:
        days = self._block_data.get("18_content_plan", {}).get("days", [])
        return {self._string(item.get("offer_id")) for item in days if self._string(item.get("offer_id"))}

    def _get_reel_count(self) -> int:
        return len(self._block_data.get("19_reels", {}).get("reels", []))

    def _cv_avatar_pain(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        avatar_ids = self._get_avatar_ids()
        pains = self._block_data.get("13_pains", {}).get("pains", [])
        for pain in pains:
            avatar_id = self._string(pain.get("avatar_id"))
            if avatar_id and avatar_id not in avatar_ids:
                issues.append(
                    ValidationIssue(
                        code="cv_avatar_pain",
                        message=f"Pain avatar_id '{avatar_id}' not in avatars",
                        path="pains",
                        severity=ValidationSeverity.ERROR,
                    )
                )
        return ValidationResult(validator_name="avatar→pain", passed=not issues, score=100 - len(issues) * 20, issues=issues)

    def _cv_pain_trigger(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        pain_ids = self._get_pain_ids()
        triggers = self._block_data.get("14_triggers", {}).get("triggers", [])
        for trigger in triggers:
            pain_id = self._string(trigger.get("pain_id"))
            if pain_id and pain_id not in pain_ids:
                issues.append(
                    ValidationIssue(
                        code="cv_pain_trigger",
                        message=f"Trigger pain_id '{pain_id}' not in pains",
                        path="triggers",
                        severity=ValidationSeverity.ERROR,
                    )
                )
        return ValidationResult(validator_name="pain→trigger", passed=not issues, score=100 - len(issues) * 20, issues=issues)

    def _cv_pain_offer(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        pain_ids = self._get_pain_ids()
        offers = self._block_data.get("15_offers", {}).get("offers", [])
        for offer in offers:
            pain_id = self._string(offer.get("pain_id"))
            if pain_id and pain_id not in pain_ids:
                issues.append(
                    ValidationIssue(
                        code="cv_pain_offer",
                        message=f"Offer pain_id '{pain_id}' not in pains",
                        path="offers",
                        severity=ValidationSeverity.ERROR,
                    )
                )
        return ValidationResult(validator_name="pain→offer", passed=not issues, score=100 - len(issues) * 20, issues=issues)

    def _cv_offer_cta(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        offers = self._block_data.get("15_offers", {}).get("offers", [])
        for offer in offers:
            if not self._string(offer.get("cta")):
                issues.append(
                    ValidationIssue(
                        code="cv_offer_cta",
                        message=f"Offer '{offer.get('offer_id', '?')}' missing CTA",
                        path="offers",
                        severity=ValidationSeverity.ERROR,
                    )
                )
        return ValidationResult(validator_name="offer→CTA", passed=not issues, score=100 - len(issues) * 20, issues=issues)

    def _cv_offer_funnel(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        offers = self._block_data.get("15_offers", {}).get("offers", [])
        funnels = self._block_data.get("16_funnels", {}).get("steps", [])
        if not funnels:
            issues.append(
                ValidationIssue(
                    code="cv_offer_funnel_empty",
                    message="Funnels has no steps",
                    path="funnels",
                    severity=ValidationSeverity.ERROR,
                )
            )
        for index, step in enumerate(funnels):
            if not self._string(step.get("content")):
                issues.append(
                    ValidationIssue(
                        code="cv_offer_funnel_content",
                        message=f"Funnel step {index + 1} missing content",
                        path=f"funnels[{index}]",
                        severity=ValidationSeverity.ERROR,
                    )
                )
            if not self._string(step.get("cta")):
                issues.append(
                    ValidationIssue(
                        code="cv_offer_funnel_cta",
                        message=f"Funnel step {index + 1} missing CTA",
                        path=f"funnels[{index}]",
                        severity=ValidationSeverity.ERROR,
                    )
                )
            if not self._string(step.get("kpi")):
                issues.append(
                    ValidationIssue(
                        code="cv_offer_funnel_kpi",
                        message=f"Funnel step {index + 1} missing KPI",
                        path=f"funnels[{index}]",
                        severity=ValidationSeverity.ERROR,
                    )
                )
        if offers and funnels and not any(self._string(step.get("content")) for step in funnels):
            issues.append(
                ValidationIssue(
                    code="cv_offer_funnel_link",
                    message="Funnels are not linked to offer content",
                    path="funnels",
                    severity=ValidationSeverity.ERROR,
                )
            )
        return ValidationResult(validator_name="offer→funnel", passed=not issues, score=100 - len(issues) * 20, issues=issues)

    def _cv_content_avatar(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        avatar_ids = self._get_avatar_ids()
        days = self._block_data.get("18_content_plan", {}).get("days", [])
        for day in days:
            avatar_id = self._string(day.get("avatar_id"))
            if avatar_id and avatar_id not in avatar_ids:
                issues.append(
                    ValidationIssue(
                        code="cv_content_avatar",
                        message=f"Content day {day.get('day', '?')} avatar_id '{avatar_id}' not in avatars",
                        path="content_plan",
                        severity=ValidationSeverity.WARNING,
                    )
                )
        return ValidationResult(validator_name="content→avatar", passed=not issues, score=100 - len(issues) * 10, issues=issues)

    def _cv_content_pain(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        pain_ids = self._get_pain_ids()
        days = self._block_data.get("18_content_plan", {}).get("days", [])
        for day in days:
            pain_id = self._string(day.get("pain_id"))
            if pain_id and pain_id not in pain_ids:
                issues.append(
                    ValidationIssue(
                        code="cv_content_pain",
                        message=f"Content day {day.get('day', '?')} pain_id '{pain_id}' not in pains",
                        path="content_plan",
                        severity=ValidationSeverity.WARNING,
                    )
                )
        return ValidationResult(validator_name="content→pain", passed=not issues, score=100 - len(issues) * 10, issues=issues)

    def _cv_content_offer(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        offer_ids = self._get_offer_ids()
        days = self._block_data.get("18_content_plan", {}).get("days", [])
        for day in days:
            offer_id = self._string(day.get("offer_id"))
            if offer_id and offer_id not in offer_ids:
                issues.append(
                    ValidationIssue(
                        code="cv_content_offer",
                        message=f"Content day {day.get('day', '?')} offer_id '{offer_id}' not in offers",
                        path="content_plan",
                        severity=ValidationSeverity.WARNING,
                    )
                )
        return ValidationResult(validator_name="content→offer", passed=not issues, score=100 - len(issues) * 10, issues=issues)

    def _cv_content_cta(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        days = self._block_data.get("18_content_plan", {}).get("days", [])
        for day in days:
            if not self._string(day.get("cta")):
                issues.append(
                    ValidationIssue(
                        code="cv_content_cta",
                        message=f"Content day {day.get('day', '?')} missing CTA",
                        path="content_plan",
                        severity=ValidationSeverity.ERROR,
                    )
                )
        return ValidationResult(validator_name="content→CTA", passed=not issues, score=100 - len(issues) * 20, issues=issues)

    def _cv_reels_content(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        reels = self._block_data.get("19_reels", {}).get("reels", [])
        if not reels:
            issues.append(
                ValidationIssue(
                    code="cv_reels_empty",
                    message="Reels block has no reels",
                    path="reels",
                    severity=ValidationSeverity.ERROR,
                )
            )
        return ValidationResult(validator_name="reels→content", passed=not issues, score=100 - len(issues) * 20, issues=issues)

    def _cv_posts_offer(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        posts = self._block_data.get("21_posts", {}).get("posts", [])
        offer_ids = self._get_offer_ids()
        avatar_ids = self._get_avatar_ids()
        pain_ids = self._get_pain_ids()
        for post in posts:
            if not self._string(post.get("cta")):
                issues.append(
                    ValidationIssue(
                        code="cv_posts_cta",
                        message=f"Post '{post.get('headline', '?')}' missing CTA",
                        path="posts",
                        severity=ValidationSeverity.WARNING,
                    )
                )
            offer_id = self._string(post.get("offer_id"))
            if offer_id and offer_id not in offer_ids:
                issues.append(
                    ValidationIssue(
                        code="cv_posts_offer",
                        message=f"Post '{post.get('headline', '?')}' offer_id '{offer_id}' not in offers",
                        path="posts",
                        severity=ValidationSeverity.ERROR,
                    )
                )
            avatar_id = self._string(post.get("avatar_id"))
            if avatar_id and avatar_id not in avatar_ids:
                issues.append(
                    ValidationIssue(
                        code="cv_posts_avatar",
                        message=f"Post '{post.get('headline', '?')}' avatar_id '{avatar_id}' not in avatars",
                        path="posts",
                        severity=ValidationSeverity.ERROR,
                    )
                )
            pain_id = self._string(post.get("pain_id"))
            if pain_id and pain_id not in pain_ids:
                issues.append(
                    ValidationIssue(
                        code="cv_posts_pain",
                        message=f"Post '{post.get('headline', '?')}' pain_id '{pain_id}' not in pains",
                        path="posts",
                        severity=ValidationSeverity.ERROR,
                    )
                )
        return ValidationResult(validator_name="posts→offer", passed=not issues, score=100 - len(issues) * 10, issues=issues)

    def _cv_posts_linkage(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        posts = self._block_data.get("21_posts", {}).get("posts", [])
        if posts and not self._get_content_offer_ids():
            issues.append(
                ValidationIssue(
                    code="cv_posts_linkage",
                    message="Posts should carry offer_id links",
                    path="posts",
                    severity=ValidationSeverity.WARNING,
                )
            )
        return ValidationResult(validator_name="posts→linkage", passed=not issues, score=100 - len(issues) * 10, issues=issues)

    def _cv_reels_content_plan(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        reels = self._block_data.get("19_reels", {}).get("reels", [])
        days = self._block_data.get("18_content_plan", {}).get("days", [])
        if reels and not days:
            issues.append(
                ValidationIssue(
                    code="cv_reels_content_plan_empty",
                    message="Reels exist but content plan is empty",
                    path="reels",
                    severity=ValidationSeverity.ERROR,
                )
            )
        if reels and days and not any(self._string(day.get("content_format")).lower() == "reel" for day in days):
            issues.append(
                ValidationIssue(
                    code="cv_reels_content_plan_link",
                    message="Reels are not referenced by content_plan days",
                    path="reels",
                    severity=ValidationSeverity.WARNING,
                )
            )
        return ValidationResult(validator_name="reels→content_plan", passed=not issues, score=100 - len(issues) * 10, issues=issues)

    def _cv_ads_audience(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        campaigns = self._block_data.get("17_advertising", {}).get("campaigns", [])
        for campaign in campaigns:
            if not self._string(campaign.get("audience")):
                issues.append(
                    ValidationIssue(
                        code="cv_ads_audience",
                        message="Ad campaign missing audience",
                        path="advertising",
                        severity=ValidationSeverity.ERROR,
                    )
                )
            budget = self._string(campaign.get("budget"))
            if budget.isdigit() and int(budget) > 1000:
                issues.append(
                    ValidationIssue(
                        code="cv_ads_budget",
                        message=f"Ad campaign budget '{budget}' exceeds test limit",
                        path="advertising",
                        severity=ValidationSeverity.ERROR,
                    )
                )
        return ValidationResult(validator_name="ads→audience", passed=not issues, score=100 - len(issues) * 20, issues=issues)

    def _cv_kpi_action(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        kpis = self._block_data.get("24_kpi", {}).get("kpis", [])
        for kpi in kpis:
            if not self._string(kpi.get("action")):
                issues.append(
                    ValidationIssue(
                        code="cv_kpi_action",
                        message="KPI missing action",
                        path="kpi",
                        severity=ValidationSeverity.ERROR,
                    )
                )
            if not self._string(kpi.get("success_threshold")):
                issues.append(
                    ValidationIssue(
                        code="cv_kpi_threshold",
                        message="KPI missing success_threshold",
                        path="kpi",
                        severity=ValidationSeverity.ERROR,
                    )
                )
            if not self._string(kpi.get("metric")):
                issues.append(
                    ValidationIssue(
                        code="cv_kpi_metric",
                        message="KPI missing metric",
                        path="kpi",
                        severity=ValidationSeverity.ERROR,
                    )
                )
        return ValidationResult(validator_name="KPI→action", passed=not issues, score=100 - len(issues) * 20, issues=issues)

    def _cv_launch_chain(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        steps = self._block_data.get("26_launch_plan", {}).get("steps", [])
        for index, step in enumerate(steps):
            if not self._string(step.get("action")):
                issues.append(
                    ValidationIssue(
                        code="cv_launch_chain_action",
                        message=f"Launch step {index + 1} missing action",
                        path="launch_plan",
                        severity=ValidationSeverity.ERROR,
                    )
                )
            if index < len(steps) - 1 and not self._string(step.get("next_step")):
                issues.append(
                    ValidationIssue(
                        code="cv_launch_chain",
                        message=f"Launch step {index + 1} missing next_step",
                        path="launch_plan",
                        severity=ValidationSeverity.ERROR,
                    )
                )
        if len(steps) < 2:
            issues.append(
                ValidationIssue(
                    code="cv_launch_chain_short",
                    message=f"Launch plan has only {len(steps)} steps, min 2 required",
                    path="launch_plan",
                    severity=ValidationSeverity.ERROR,
                )
            )
        return ValidationResult(validator_name="launch→next_step", passed=not issues, score=100 - len(issues) * 20, issues=issues)

    @staticmethod
    def _string(value: Any) -> str:
        if value is None:
            return ""
        if hasattr(value, "value"):
            value = value.value
        return str(value).strip()
