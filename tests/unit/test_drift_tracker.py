"""Sprint 22 — Drift Tracker Tests (14 tests)."""
import pytest
from ai_engine.pipeline.drift_tracker import DriftTracker, DriftEvent

class TestDriftTracker:
    def test_no_drift_zero_rate(self):
        dt = DriftTracker()
        dt.record("01_market_analysis", {"market_overview": "Test"}, {"market_overview": "Test"}, 0, 0)
        assert dt.raw_pass_rate() == 1.0

    def test_alias_drift_detected(self):
        dt = DriftTracker()
        dt.record("01_market_analysis", {"market_trends": "X"}, {"market_overview": "X"}, 1, 0)
        assert dt.total_drift_count() == 1
        assert dt.raw_pass_rate() == 0.0

    def test_defaults_filled_drift(self):
        dt = DriftTracker()
        dt.record("01_market_analysis", {}, {}, 0, 5)
        assert dt.total_drift_count() == 1

    def test_mixed_blocks_rate(self):
        dt = DriftTracker()
        dt.record("01", {"a": 1}, {"a": 1}, 0, 0)
        dt.record("02", {"b": 1}, {"c": 1}, 1, 0)
        dt.record("03", {"d": 1}, {"d": 1}, 0, 0)
        assert dt.raw_pass_rate() > 0.5
        assert dt.total_drift_count() == 1

    def test_empty_tracker(self):
        dt = DriftTracker()
        assert dt.raw_pass_rate() == 1.0
        assert dt.total_drift_count() == 0

    def test_summary_structure(self):
        dt = DriftTracker()
        dt.record("01_market_analysis", {"market_trends": "X"}, {"market_overview": "X"}, 1, 0)
        summary = dt.drift_summary()
        assert "total_blocks" in summary
        assert "drift_blocks" in summary
        assert "raw_pass_rate" in summary
        assert "events" in summary
        assert len(summary["events"]) == 1

    def test_event_has_required_fields(self):
        e = DriftEvent("01", ["a"], ["b"], 1, 0, True)
        assert e.block_id == "01"
        assert e.aliased_count == 1
        assert e.normalization_required is True

    def test_multiple_events_accumulate(self):
        dt = DriftTracker()
        for i in range(5):
            dt.record(f"0{i}", {"k": i}, {"k": i}, int(i % 2), 0)
        assert len(dt.events()) == 5
        assert dt.total_drift_count() == 2  # i=1, i=3 have aliases

    def test_no_events_summary(self):
        dt = DriftTracker()
        s = dt.drift_summary()
        assert s["total_blocks"] == 0
        assert s["raw_pass_rate"] == 1.0

    def test_known_block_drift_patterns(self):
        # Simulate the 5 blocks known to drift from live_chain audit
        dt = DriftTracker()
        dt.record("01_market_analysis", {"market_trends": "X"}, {"market_overview": "X"}, 1, 2)
        dt.record("04_platform", {"usp": "X"}, {"usp": "X"}, 0, 3)
        dt.record("11_avatars", {"avatar_list": []}, {"avatars": []}, 1, 1)
        dt.record("14_triggers", {"trigger_list": []}, {"triggers": []}, 1, 1)
        dt.record("15_offers", {"offer_list": []}, {"offers": []}, 1, 0)
        assert dt.total_drift_count() == 5
        assert dt.raw_pass_rate() == 0.0  # All 5 need normalization

    def test_schema_awareness_flag(self):
        dt = DriftTracker()
        dt.record("block_ok", {"title": "T"}, {"title": "T"}, 0, 0)
        assert dt.drift_summary()["raw_pass_rate"] == 1.0

    def test_drift_rate_between_40_and_60_percent(self):
        dt = DriftTracker()
        for i in range(10):
            has_alias = i < 6  # 6 out of 10 drift
            dt.record(f"b{i}", {"k": i}, {"k": i}, int(has_alias), 0)
        rate = dt.raw_pass_rate()
        assert 0.35 <= rate <= 0.65, f"Expected ~40% rate, got {rate}"

    def test_per_block_drift_summary_keys(self):
        dt = DriftTracker()
        dt.record("01_market_analysis", {"market_trends": "X"}, {"market_overview": "X"}, 1, 2)
        event = dt.drift_summary()["events"][0]
        assert event["block_id"] == "01_market_analysis"
        assert "raw_keys" in event
        assert event["aliased"] == 1
        assert event["defaults"] == 2
        assert event["normalized"] is True