"""KPI Action Builder — converts KPI metrics into KPITask objects."""

from shared.schemas.execution_view_model import KPITask


class KPIActionBuilder:
    """Builds KPITask entries for the Metrics tab."""

    _counter = 0

    def build(self, task_id: str, day: int, action: str, metric: str,
              success_threshold: str, warning_threshold: str,
              fail_threshold: str) -> KPITask:
        self._counter += 1
        return KPITask(
            task_id=task_id or f"kpi{self._counter:04d}",
            day=day, action=action, metric=metric,
            success_threshold=success_threshold,
            warning_threshold=warning_threshold,
            fail_threshold=fail_threshold,
        )