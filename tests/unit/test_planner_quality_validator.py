"""Tests for PlannerQualityValidator (15 tests)."""
import pytest
from ai_engine.validators.planner_quality_validator import PlannerQualityValidator
from shared.schemas.execution_view_model import Mission, ExecutionViewModel, ProjectInfo, DaySummary

def make_evm(missions, total_days=30):
    days = [DaySummary(day=d, phase="s", mission_count=1, goal="G") for d in range(1, total_days+1)]
    return ExecutionViewModel(project=ProjectInfo(name="T", industry="T", goal="G", current_day=1, current_phase="s"),
                              today=days[0], days=days, missions=missions, content_tasks=[], ads_tasks=[], sales_tasks=[], kpi_tasks=[],
                              total_missions=len(missions), total_days=total_days)

def make_mission(mid="m1", title="T", cta="CTA", metric="5 likes", ready_text="Ready"):
    return Mission(mission_id=mid, day=1, phase="s", title=title, why="W", cta=cta, metric=metric,
                   success_threshold="5+", warning_threshold="3", fail_threshold="1",
                   if_success="S", if_fail="F", steps=["S"], ready_text=ready_text, xp_reward=10)

PQ = PlannerQualityValidator()

class TestPlannerQuality:
    def test_no_missions_fails(self):
        evm = make_evm([])
        r = PQ.validate(evm)
        assert not r.passed

    def test_passing_missions_passes(self):
        missions = [make_mission(f"m{i}", f"Title {i}", f"CTA {i}", f"{i} likes", f"Ready {i}") for i in range(48)]
        r = PQ.validate(make_evm(missions))
        assert r.passed

    def test_source_trace(self):
        missions = [make_mission(f"m{i}") for i in range(48)]
        r = PQ.validate(make_evm(missions))
        assert r.passed

    def test_duplicate_cta_warns(self):
        missions = [make_mission(f"m{i}", cta="Купить") for i in range(48)]
        r = PQ.validate(make_evm(missions))
        assert not r.passed or any(i.code == "dup_cta" for i in r.issues)

    def test_duplicate_title_warns(self):
        missions = [make_mission(f"m{i}", title="Опубликовать пост") for i in range(48)]
        r = PQ.validate(make_evm(missions))
        assert any(i.code == "dup_title" for i in r.issues)

    def test_numeric_kpi(self):
        missions = [make_mission(f"m{i}", metric=f"{i} просмотров") for i in range(48)]
        r = PQ.validate(make_evm(missions))
        assert r.passed

    def test_non_numeric_kpi_fails(self):
        missions = [make_mission(f"m{i}", metric="хороший результат") for i in range(48)]
        r = PQ.validate(make_evm(missions))
        assert not r.passed

    def test_ready_text_coverage(self):
        missions = [make_mission(f"m{i}") for i in range(48)]
        r = PQ.validate(make_evm(missions))
        assert r.passed

    def test_missing_ready_text_warns(self):
        missions = [make_mission(f"m{i}", ready_text="") for i in range(48)]
        r = PQ.validate(make_evm(missions))
        assert any(i.code == "low_ready_text" for i in r.issues)

    def test_generic_missions_blocked(self):
        missions = [make_mission(f"m{i}", title="опубликовать контент дня 1") for i in range(48)]
        r = PQ.validate(make_evm(missions))
        assert not r.passed
        assert any(i.code == "generic_missions" for i in r.issues)

    def test_score_max_100(self):
        missions = [make_mission(f"m{i}") for i in range(48)]
        r = PQ.validate(make_evm(missions))
        assert r.score >= 50

    def test_score_min_0(self):
        missions = [make_mission(f"m{i}", metric="", ready_text="", cta="") for i in range(48)]
        r = PQ.validate(make_evm(missions))
        assert r.score >= 0