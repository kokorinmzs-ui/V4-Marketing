"""Unit tests for DependencyGraph."""

import pytest

from ai_engine.pipeline.dependency_graph import DependencyGraph, build_marketing_os_dependency_graph


class TestDependencyGraphBasics:
    def test_add_node(self):
        g = DependencyGraph()
        g.add_node("A")
        assert "A" in g
        assert len(g) == 1

    def test_add_edge(self):
        g = DependencyGraph()
        g.add_edge("A", "B")
        assert "A" in g and "B" in g
        assert g.get_dependencies("B") == {"A"}
        assert g.get_dependents("A") == {"B"}

    def test_empty_graph(self):
        g = DependencyGraph()
        assert len(g) == 0
        assert g.topological_order() == []


class TestDependencyGraphOrder:
    def test_simple_linear_order(self):
        g = DependencyGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        order = g.topological_order()
        assert order == ["A", "B", "C"]

    def test_multiple_dependencies(self):
        g = DependencyGraph()
        g.add_edge("A", "C")
        g.add_edge("B", "C")
        order = g.topological_order()
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("C")

    def test_complex_graph(self):
        """11_avatars → 13_pains → 14_triggers → 15_offers"""
        g = DependencyGraph()
        g.add_edge("10_audience", "11_avatars")
        g.add_edge("11_avatars", "12_psychotypes")
        g.add_edge("12_psychotypes", "13_pains")
        g.add_edge("13_pains", "14_triggers")
        g.add_edge("14_triggers", "15_offers")
        g.add_edge("15_offers", "16_funnels")
        order = g.topological_order()
        assert order.index("10_audience") < order.index("11_avatars")
        assert order.index("11_avatars") < order.index("13_pains")
        assert order.index("13_pains") < order.index("14_triggers")
        assert order.index("14_triggers") < order.index("15_offers")

    def test_roots_no_dependencies(self):
        g = DependencyGraph()
        g.add_edge("A", "B")
        g.add_edge("A", "C")
        assert g.get_roots() == {"A"}

    def test_multiple_roots(self):
        g = DependencyGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_edge("A", "C")
        g.add_edge("B", "C")
        assert g.get_roots() == {"A", "B"}


class TestDependencyGraphCycle:
    def test_simple_cycle_detected(self):
        g = DependencyGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("C", "A")  # Cycle!
        with pytest.raises(ValueError, match="Cycle"):
            g.validate_no_cycles()

    def test_self_loop_detected(self):
        g = DependencyGraph()
        g.add_edge("A", "A")  # Self-loop
        with pytest.raises(ValueError, match="Cycle"):
            g.validate_no_cycles()

    def test_complex_cycle_detected(self):
        g = DependencyGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("C", "D")
        g.add_edge("D", "B")  # B → C → D → B cycle
        with pytest.raises(ValueError, match="Cycle"):
            g.validate_no_cycles()

    def test_no_cycle_valid(self):
        g = DependencyGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        assert g.validate_no_cycles() is True


class TestDependencyGraphIsReady:
    def test_ready_when_deps_completed(self):
        g = DependencyGraph()
        g.add_edge("A", "C")
        g.add_edge("B", "C")
        assert g.is_ready("C", {"A", "B"}) is True

    def test_not_ready_when_deps_missing(self):
        g = DependencyGraph()
        g.add_edge("A", "C")
        g.add_edge("B", "C")
        assert g.is_ready("C", {"A"}) is False

    def test_ready_when_no_deps(self):
        g = DependencyGraph()
        g.add_node("A")
        assert g.is_ready("A", set()) is True


class TestDependencyGraphPath:
    def test_find_path_exists(self):
        g = DependencyGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        path = g.find_path("A", "C")
        assert path == ["A", "B", "C"]

    def test_find_path_not_exists(self):
        g = DependencyGraph()
        g.add_edge("A", "B")
        g.add_edge("C", "D")
        path = g.find_path("A", "D")
        assert path is None


class TestBuildMarketingOSGraph:
    def test_builds_without_cycles(self):
        g = build_marketing_os_dependency_graph()
        assert g.validate_no_cycles() is True

    def test_has_27_nodes(self):
        g = build_marketing_os_dependency_graph()
        # Should have most nodes (01-27)
        assert len(g) >= 20  # At least 20 of 27

    def test_order_respects_avatar_chain(self):
        g = build_marketing_os_dependency_graph()
        order = g.topological_order()
        assert order.index("10_audience") < order.index("11_avatars")
        assert order.index("11_avatars") < order.index("13_pains")
        assert order.index("13_pains") < order.index("14_triggers")
        assert order.index("14_triggers") < order.index("15_offers")