"""FinalDataAssembler — assembles final_data.json from passed blocks with cross-validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.schemas.final_data import FinalData
from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity


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
    """Assembles final_data.json ONLY from PASSED blocks.

    Cross-validates all block relationships before assembly.
    If any required block failed or cross-validation fails, assembly is DENIED.
    """

    REQUIRED_BLOCKS = [
        "01_market_analysis", "02_business_diagnosis", "03_competitors",
        "04_platform", "10_audience", "11_avatars", "13_pains",
        "14_triggers", "15_offers", "16_funnels", "17_advertising",
        "18_content_plan", "19_reels", "21_posts", "23_sales_scripts",
        "24_kpi", "25_first_7_days", "26_launch_plan", "27_quality_control",
    ]

    def __init__(self):
        self._block_data: dict[str, dict[str, Any]] = {}

    def add_block(self, block_id: str, passed: bool, data: dict[str, Any]) -> None:
        """Add a block's result."""
        if passed:
            self._block_data[block_id] = data

    def assemble(self) -> AssemblyResult:
        """Assemble final_data.json with cross-validation.

        Returns:
            AssemblyResult with success/failure and final_data if successful
        """
        result = AssemblyResult()

        # Check required blocks
        for required in self.REQUIRED_BLOCKS:
            if required not in self._block_data:
                result.blocks_failed.append(required)
                result.errors.append(f"Required block {required} missing or failed")

        if result.blocks_failed:
            return result

        result.blocks_passed = list(self._block_data.keys())

        # Run cross-validators
        cross_validators = [
            self._cv_avatar_pain,
            self._cv_pain_trigger,
            self._cv_pain_offer,
            self._cv_offer_cta,
            self._cv_offer_funnel,
            self._cv_content_avatar,
            self._cv_content_pain,
            self._cv_reels_content,
            self._cv_posts_offer,
            self._cv_ads_audience,
            self._cv_kpi_action,
            self._cv_launch_chain,
        ]

        for cv in cross_validators:
            vr = cv()
            result.cross_validation_results.append(vr)
            if not vr.passed:
                # Only ERROR/CRITICAL block assembly; WARNING passes through
                blocking = [i for i in vr.issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]
                result.errors.extend(i.message for i in blocking)

        if result.errors:
            return result

        # Build FinalData
        try:
            fd = FinalData(
                project_id="assembed-001",
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
            result.success = True
            result.final_data = fd
        except Exception as e:
            result.errors.append(f"FinalData construction failed: {e}")

        return result

    # ---- Cross-validators ----

    def _get_avatar_ids(self) -> set:
        av = self._block_data.get("11_avatars", {})
        return {a.get("avatar_id") for a in av.get("avatars", []) if a.get("avatar_id")}

    def _get_pain_ids(self) -> set:
        pa = self._block_data.get("13_pains", {})
        return {p.get("pain_id") for p in pa.get("pains", []) if p.get("pain_id")}

    def _get_offer_ids(self) -> set:
        of = self._block_data.get("15_offers", {})
        return {o.get("offer_id") for o in of.get("offers", []) if o.get("offer_id")}

    def _get_content_ids(self) -> set:
        cp = self._block_data.get("18_content_plan", {})
        return {f"day{d.get('day','')}" for d in cp.get("days", [])}

    def _get_reel_ids(self) -> set:
        re = self._block_data.get("19_reels", {})
        return {f"reel{i}" for i, _ in enumerate(re.get("reels", []))}

    def _get_post_offer_ids(self) -> set:
        po = self._block_data.get("21_posts", {})
        return {p.get("pain_id") for p in po.get("posts", []) if p.get("pain_id")}

    def _cv_avatar_pain(self) -> ValidationResult:
        issues = []
        avatar_ids = self._get_avatar_ids()
        pains = self._block_data.get("13_pains", {}).get("pains", [])
        for pain in pains:
            aid = pain.get("avatar_id")
            if aid and aid not in avatar_ids:
                issues.append(ValidationIssue(code="cv_avatar_pain", message=f"Pain avatar_id '{aid}' not in avatars", path="pains", severity=ValidationSeverity.ERROR))
        return ValidationResult(validator_name="avatar→pain", passed=len(issues)==0, score=100-len(issues)*20, issues=issues)

    def _cv_pain_trigger(self) -> ValidationResult:
        issues = []
        pain_ids = self._get_pain_ids()
        triggers = self._block_data.get("14_triggers", {}).get("triggers", [])
        for t in triggers:
            pid = t.get("pain_id")
            if pid and pid not in pain_ids:
                issues.append(ValidationIssue(code="cv_pain_trigger", message=f"Trigger pain_id '{pid}' not in pains", path="triggers", severity=ValidationSeverity.ERROR))
        return ValidationResult(validator_name="pain→trigger", passed=len(issues)==0, score=100-len(issues)*20, issues=issues)

    def _cv_pain_offer(self) -> ValidationResult:
        issues = []
        pain_ids = self._get_pain_ids()
        offers = self._block_data.get("15_offers", {}).get("offers", [])
        for o in offers:
            pid = o.get("pain_id")
            if pid and pid not in pain_ids:
                issues.append(ValidationIssue(code="cv_pain_offer", message=f"Offer pain_id '{pid}' not in pains", path="offers", severity=ValidationSeverity.ERROR))
        return ValidationResult(validator_name="pain→offer", passed=len(issues)==0, score=100-len(issues)*20, issues=issues)

    def _cv_offer_cta(self) -> ValidationResult:
        issues = []
        offers = self._block_data.get("15_offers", {}).get("offers", [])
        for o in offers:
            if not o.get("cta"):
                issues.append(ValidationIssue(code="cv_offer_cta", message=f"Offer '{o.get('offer_id','?')}' missing CTA", path="offers", severity=ValidationSeverity.ERROR))
        return ValidationResult(validator_name="offer→CTA", passed=len(issues)==0, score=100-len(issues)*20, issues=issues)

    def _cv_offer_funnel(self) -> ValidationResult:
        issues = []
        offer_ids = self._get_offer_ids()
        funnels = self._block_data.get("16_funnels", {}).get("steps", [])
        if not funnels:
            issues.append(ValidationIssue(code="cv_offer_funnel_empty", message="Funnels has no steps", path="funnels", severity=ValidationSeverity.ERROR))
        return ValidationResult(validator_name="offer→funnel", passed=len(issues)==0, score=100-len(issues)*20, issues=issues)

    def _cv_content_avatar(self) -> ValidationResult:
        issues = []
        avatar_ids = self._get_avatar_ids()
        days = self._block_data.get("18_content_plan", {}).get("days", [])
        for d in days:
            aid = d.get("avatar_id")
            if aid and aid not in avatar_ids:
                issues.append(ValidationIssue(code="cv_content_avatar", message=f"Content day {d.get('day','?')} avatar_id '{aid}' not in avatars", path="content_plan", severity=ValidationSeverity.WARNING))
        return ValidationResult(validator_name="content→avatar", passed=len(issues)==0, score=100-len(issues)*10, issues=issues)

    def _cv_content_pain(self) -> ValidationResult:
        issues = []
        pain_ids = self._get_pain_ids()
        days = self._block_data.get("18_content_plan", {}).get("days", [])
        for d in days:
            pid = d.get("pain_id")
            if pid and pid not in pain_ids:
                issues.append(ValidationIssue(code="cv_content_pain", message=f"Content day {d.get('day','?')} pain_id '{pid}' not in pains", path="content_plan", severity=ValidationSeverity.WARNING))
        return ValidationResult(validator_name="content→pain", passed=len(issues)==0, score=100-len(issues)*10, issues=issues)

    def _cv_reels_content(self) -> ValidationResult:
        issues = []
        reels = self._block_data.get("19_reels", {}).get("reels", [])
        if not reels:
            issues.append(ValidationIssue(code="cv_reels_empty", message="Reels block has no reels", path="reels", severity=ValidationSeverity.ERROR))
        return ValidationResult(validator_name="reels→content", passed=len(issues)==0, score=100-len(issues)*20, issues=issues)

    def _cv_posts_offer(self) -> ValidationResult:
        issues = []
        posts = self._block_data.get("21_posts", {}).get("posts", [])
        for p in posts:
            if not p.get("cta"):
                issues.append(ValidationIssue(code="cv_posts_cta", message=f"Post '{p.get('headline','?')}' missing CTA", path="posts", severity=ValidationSeverity.WARNING))
        return ValidationResult(validator_name="posts→offer", passed=len(issues)==0, score=100-len(issues)*10, issues=issues)

    def _cv_ads_audience(self) -> ValidationResult:
        issues = []
        campaigns = self._block_data.get("17_advertising", {}).get("campaigns", [])
        for c in campaigns:
            if not c.get("audience"):
                issues.append(ValidationIssue(code="cv_ads_audience", message="Ad campaign missing audience", path="advertising", severity=ValidationSeverity.ERROR))
        return ValidationResult(validator_name="ads→audience", passed=len(issues)==0, score=100-len(issues)*20, issues=issues)

    def _cv_kpi_action(self) -> ValidationResult:
        issues = []
        kpis = self._block_data.get("24_kpi", {}).get("kpis", [])
        for k in kpis:
            if not k.get("action"):
                issues.append(ValidationIssue(code="cv_kpi_action", message="KPI missing action", path="kpi", severity=ValidationSeverity.ERROR))
            if not k.get("success_threshold"):
                issues.append(ValidationIssue(code="cv_kpi_threshold", message="KPI missing success_threshold", path="kpi", severity=ValidationSeverity.ERROR))
        return ValidationResult(validator_name="KPI→action", passed=len(issues)==0, score=100-len(issues)*20, issues=issues)

    def _cv_launch_chain(self) -> ValidationResult:
        issues = []
        steps = self._block_data.get("26_launch_plan", {}).get("steps", [])
        for i, s in enumerate(steps):
            if not s.get("next_step") and i < len(steps) - 1:
                issues.append(ValidationIssue(code="cv_launch_chain", message=f"Launch step {i+1} missing next_step", path="launch_plan", severity=ValidationSeverity.ERROR))
        if len(steps) < 2:
            issues.append(ValidationIssue(code="cv_launch_chain_short", message=f"Launch plan has only {len(steps)} steps, min 2 required", path="launch_plan", severity=ValidationSeverity.ERROR))
        return ValidationResult(validator_name="launch→next_step", passed=len(issues)==0, score=100-len(issues)*20, issues=issues)
