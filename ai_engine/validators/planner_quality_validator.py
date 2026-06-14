"""PlannerQualityValidator — проверяет качество ExecutionViewModel."""
from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity


class PlannerQualityValidator:
    MIN_SOURCE_TRACE = 0.90
    MAX_DUP_CTA = 0.30
    MIN_KPI_NUMERIC = 0.95
    MIN_READY_TEXT = 0.90

    def validate(self, evm) -> ValidationResult:
        missions = evm.missions if hasattr(evm, "missions") else getattr(evm, "missions", [])
        if not missions:
            return ValidationResult(validator_name="planner_quality", passed=False, score=0, issues=[ValidationIssue(code="no_missions", message="No missions", severity=ValidationSeverity.ERROR)])

        issues = []
        total = len(missions)

        # Source trace coverage
        with_source_id = sum(1 for m in missions if getattr(m, "source_id", ""))
        with_trace_id = sum(1 for m in missions if getattr(m, "source_id", "") or getattr(m, "mission_id", ""))
        source_id_ratio = with_source_id / total
        source_ratio = with_trace_id / total
        if source_ratio < self.MIN_SOURCE_TRACE:
            issues.append(ValidationIssue(code="low_trace", message=f"Source trace: {source_ratio:.0%} < {self.MIN_SOURCE_TRACE:.0%}", severity=ValidationSeverity.ERROR))
        elif source_id_ratio < self.MIN_SOURCE_TRACE:
            issues.append(ValidationIssue(code="low_source_id", message=f"Source IDs: {source_id_ratio:.0%} < {self.MIN_SOURCE_TRACE:.0%}", severity=ValidationSeverity.WARNING))

        # Duplicate CTA ratio
        ctas = [m.cta for m in missions if getattr(m, "cta", "")]
        unique_ctas = len(set(ctas))
        cta_dup = 1 - unique_ctas / max(total, 1)
        if cta_dup > self.MAX_DUP_CTA:
            issues.append(ValidationIssue(code="dup_cta", message=f"CTA duplicates: {cta_dup:.0%} > {self.MAX_DUP_CTA:.0%}", severity=ValidationSeverity.WARNING))

        # Duplicate title ratio
        titles = [m.title for m in missions if getattr(m, "title", "")]
        unique_titles = len(set(titles))
        title_dup = 1 - unique_titles / max(total, 1)
        if title_dup > self.MAX_DUP_CTA:
            issues.append(ValidationIssue(code="dup_title", message=f"Title duplicates: {title_dup:.0%}", severity=ValidationSeverity.WARNING))

        # KPI numeric coverage
        def _has_numeric_value(value: str) -> bool:
            return any(character.isdigit() for character in (value or ""))

        with_numeric_kpi = sum(1 for m in missions if _has_numeric_value(getattr(m, "metric", "")))
        kpi_ratio = with_numeric_kpi / total
        if kpi_ratio < self.MIN_KPI_NUMERIC:
            issues.append(ValidationIssue(code="low_kpi_numeric", message=f"Numeric KPI: {kpi_ratio:.0%} < {self.MIN_KPI_NUMERIC:.0%}", severity=ValidationSeverity.ERROR))

        # Ready text coverage
        with_ready = sum(1 for m in missions if getattr(m, "ready_text", ""))
        ready_ratio = with_ready / total
        if ready_ratio < self.MIN_READY_TEXT:
            issues.append(ValidationIssue(code="low_ready_text", message=f"Ready text: {ready_ratio:.0%} < {self.MIN_READY_TEXT:.0%}", severity=ValidationSeverity.WARNING))

        # Generic mission detection
        generic_words = ["опубликовать контент", "запустить рекламу", "развивать соцсети", "улучшить маркетинг"]
        generic_count = sum(1 for m in missions for gw in generic_words if gw in (getattr(m, "title", "") or "").lower())
        if generic_count > 0:
            issues.append(ValidationIssue(code="generic_missions", message=f"Generic missions: {generic_count}", severity=ValidationSeverity.ERROR))

        passed = len([i for i in issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]) == 0
        score = max(0, 100 - len(issues) * 10)
        return ValidationResult(
            validator_name="planner_quality",
            passed=passed,
            score=score,
            issues=issues,
            metadata={
                "source_trace_coverage": source_ratio,
                "source_id_coverage": source_id_ratio,
                "kpi_numeric_coverage": kpi_ratio,
                "ready_text_coverage": ready_ratio,
            },
        )
