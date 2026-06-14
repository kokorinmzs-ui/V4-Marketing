"""Drift Tracker — records schema mismatch events between AI output and Pydantic schemas."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DriftEvent:
    block_id: str
    raw_keys: list[str]
    expected_keys: list[str]
    aliased_count: int
    defaults_filled: int
    normalization_required: bool


class DriftTracker:
    """Collects drift events during pipeline execution."""

    def __init__(self):
        self._events: list[DriftEvent] = []

    def record(self, block_id: str, raw_data: dict[str, Any], normalized: dict[str, Any],
               aliases_applied: int = 0, defaults_filled: int = 0):
        from ai_engine.pipeline.schema_normalizer import SCHEMA_ALIASES
        expected_keys = list(SCHEMA_ALIASES.get(block_id, {}).values()) + list(SCHEMA_ALIASES.get(block_id, {}).keys())
        event = DriftEvent(
            block_id=block_id,
            raw_keys=list(raw_data.keys()),
            expected_keys=list(set(expected_keys)),
            aliased_count=aliases_applied,
            defaults_filled=defaults_filled,
            normalization_required=aliases_applied > 0 or defaults_filled > 0,
        )
        self._events.append(event)

    def events(self) -> list[DriftEvent]:
        return list(self._events)

    def total_drift_count(self) -> int:
        return sum(1 for e in self._events if e.normalization_required)

    def raw_pass_rate(self) -> float:
        if not self._events:
            return 1.0
        passed = sum(1 for e in self._events if not e.normalization_required)
        return passed / len(self._events)

    def drift_summary(self) -> dict[str, Any]:
        return {
            "total_blocks": len(self._events),
            "drift_blocks": self.total_drift_count(),
            "raw_pass_rate": round(self.raw_pass_rate(), 2),
            "events": [
                {
                    "block_id": e.block_id,
                    "raw_keys": e.raw_keys[:5],
                    "aliased": e.aliased_count,
                    "defaults": e.defaults_filled,
                    "normalized": e.normalization_required,
                }
                for e in self._events
            ],
        }