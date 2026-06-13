"""Sales Action Builder — converts sales scripts into SalesTask objects."""

from shared.schemas.execution_view_model import SalesTask


class SalesActionBuilder:
    """Builds SalesTask entries for the Sales tab."""

    _counter = 0

    def build(self, task_id: str, day: int, scenario: str, goal: str,
              message: str, next_step: str) -> SalesTask:
        self._counter += 1
        return SalesTask(
            task_id=task_id or f"sl{self._counter:04d}",
            day=day, scenario=scenario, goal=goal,
            message=message, next_step=next_step,
        )