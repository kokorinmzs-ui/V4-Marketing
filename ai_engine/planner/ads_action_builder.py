"""Ads Action Builder — converts advertising data into AdsTask objects."""

from shared.schemas.execution_view_model import AdsTask
from shared.schemas.blocks import Platform


class AdsActionBuilder:
    """Builds AdsTask entries for the Advertising tab."""

    _counter = 0

    def build(self, task_id: str, day: int, platform: str, audience: str,
              creative: str = "", offer: str = "", budget: str = "500",
              kpi: str = "CTR > 2%", success_threshold: str = "CTR > 2%",
              stop_threshold: str = "CTR < 1%", scale_threshold: str = "CTR > 3%") -> AdsTask:
        self._counter += 1
        return AdsTask(
            task_id=task_id or f"ad{self._counter:04d}",
            day=day, platform=Platform(platform) if platform else Platform.VK,
            audience=audience, creative=creative, offer=offer,
            budget=budget, kpi=kpi,
            success_threshold=success_threshold, stop_threshold=stop_threshold,
            scale_threshold=scale_threshold,
        )