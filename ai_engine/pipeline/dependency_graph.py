"""DependencyGraph — directed acyclic graph for block execution order."""

from __future__ import annotations

from typing import Optional


class DependencyGraph:
    """Directed graph for block dependencies."""

    def __init__(self):
        self._forward: dict[str, set[str]] = {}
        self._reverse: dict[str, set[str]] = {}

    def add_node(self, block_id: str) -> None:
        if block_id not in self._forward:
            self._forward[block_id] = set()
        if block_id not in self._reverse:
            self._reverse[block_id] = set()

    def add_edge(self, from_block: str, to_block: str) -> None:
        self.add_node(from_block)
        self.add_node(to_block)
        self._forward[from_block].add(to_block)
        self._reverse[to_block].add(from_block)

    def get_dependencies(self, block_id: str) -> set[str]:
        return self._reverse.get(block_id, set())

    def get_dependents(self, block_id: str) -> set[str]:
        return self._forward.get(block_id, set())

    def get_roots(self) -> set[str]:
        return {b for b, deps in self._reverse.items() if not deps}

    def is_ready(self, block_id: str, completed: set[str]) -> bool:
        return self.get_dependencies(block_id).issubset(completed)

    def topological_order(self) -> list[str]:
        in_degree: dict[str, int] = {b: len(deps) for b, deps in self._reverse.items()}
        for b in self._forward:
            if b not in in_degree:
                in_degree[b] = 0
        queue = [b for b, deg in in_degree.items() if deg == 0]
        result = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            for dependent in self._forward.get(node, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        if len(result) != len(in_degree):
            remaining = set(in_degree.keys()) - set(result)
            cycle_nodes = [b for b in result if any(d in remaining for d in self._forward.get(b, set()))]
            raise ValueError(f"Cycle detected in dependency graph. Remaining nodes: {sorted(remaining)}. Possible entry points: {sorted(cycle_nodes)}")
        return result

    def validate_no_cycles(self) -> bool:
        try:
            self.topological_order()
            return True
        except ValueError as e:
            raise ValueError(f"Cycle detected: {e}") from e

    def find_path(self, from_block: str, to_block: str) -> Optional[list[str]]:
        if from_block not in self._forward:
            return None
        visited = {from_block}
        queue = [(from_block, [from_block])]
        while queue:
            current, path = queue.pop(0)
            if current == to_block:
                return path
            for neighbor in self._forward.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None

    def __len__(self) -> int:
        return len(self._forward)

    def __contains__(self, block_id: str) -> bool:
        return block_id in self._forward


def build_marketing_os_dependency_graph() -> DependencyGraph:
    g = DependencyGraph()
    g.add_node("01_market_analysis")
    g.add_node("02_business_diagnosis")
    g.add_node("03_competitors")
    for root in ("01_market_analysis", "02_business_diagnosis", "03_competitors"):
        g.add_edge(root, "04_platform")
    g.add_edge("04_platform", "05_owner_portrait")
    g.add_edge("04_platform", "06_product_system")
    g.add_edge("06_product_system", "07_flagship")
    g.add_edge("07_flagship", "08_product_ladder")
    g.add_edge("08_product_ladder", "09_lead_magnets")
    g.add_edge("04_platform", "10_audience")
    g.add_edge("05_owner_portrait", "10_audience")
    g.add_edge("09_lead_magnets", "10_audience")
    g.add_edge("10_audience", "11_avatars")
    g.add_edge("11_avatars", "12_psychotypes")
    g.add_edge("12_psychotypes", "13_pains")
    g.add_edge("13_pains", "14_triggers")
    g.add_edge("14_triggers", "15_offers")
    g.add_edge("15_offers", "16_funnels")
    g.add_edge("16_funnels", "17_advertising")
    g.add_edge("16_funnels", "18_content_plan")
    g.add_edge("17_advertising", "18_content_plan")
    for cb in ("19_reels", "20_blog_articles", "21_posts", "22_visual_briefs"):
        g.add_edge("18_content_plan", cb)
    g.add_edge("16_funnels", "23_sales_scripts")
    for src in ("17_advertising", "18_content_plan", "19_reels", "21_posts", "23_sales_scripts"):
        g.add_edge(src, "24_kpi")
    g.add_edge("24_kpi", "25_first_7_days")
    g.add_edge("25_first_7_days", "26_launch_plan")
    g.add_edge("26_launch_plan", "27_quality_control")
    return g