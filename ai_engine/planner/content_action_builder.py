"""Content Action Builder — converts content data into ContentTask objects."""

from shared.schemas.execution_view_model import ContentTask
from shared.schemas.blocks import Platform, ContentFormat, ContentArchetype


class ContentActionBuilder:
    """Builds ContentTask entries for the Content Library tab."""

    def __init__(self):
        self._counter = 0

    def build_from_mission(self, mission_id: str, day: int, title: str,
                           content_format: str, ready_text: str, cta: str,
                           metric: str, platform: str = "instagram",
                           archetype: str = "case") -> ContentTask:
        self._counter += 1
        return ContentTask(
            task_id=mission_id or f"ct{self._counter:04d}",
            day=day, title=title,
            content_format=ContentFormat(content_format),
            archetype=ContentArchetype(archetype) if archetype else None,
            ready_text=ready_text, cta=cta,
            platform=Platform(platform) if platform else None,
            metric=metric,
        )