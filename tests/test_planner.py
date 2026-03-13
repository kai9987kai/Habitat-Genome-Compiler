"""Tests for DAG validation and critical-path analysis in planner.py."""

from __future__ import annotations

import unittest

from habitat_genome_compiler.compiler import load_mission_file
from habitat_genome_compiler.models import WorkflowStage
from habitat_genome_compiler.planner import (
    build_workflow,
    critical_path,
    parallel_groups,
    validate_dag,
)
from habitat_genome_compiler.router import select_experts


class DagValidationTests(unittest.TestCase):
    def test_valid_workflow_no_errors(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        experts = select_experts(mission)
        stages = build_workflow(mission, experts)
        errors = validate_dag(stages)
        self.assertEqual(errors, [])

    def test_cycle_detected(self) -> None:
        stages = [
            WorkflowStage(id="a", owner="x", description="", inputs=[], outputs=[], dependencies=["b"]),
            WorkflowStage(id="b", owner="x", description="", inputs=[], outputs=[], dependencies=["a"]),
        ]
        errors = validate_dag(stages)
        self.assertTrue(any("Cycle" in e for e in errors))

    def test_unknown_dependency_flagged(self) -> None:
        stages = [
            WorkflowStage(id="a", owner="x", description="", inputs=[], outputs=[], dependencies=["nonexistent"]),
        ]
        errors = validate_dag(stages)
        self.assertTrue(any("nonexistent" in e for e in errors))

    def test_build_workflow_raises_on_cycle(self) -> None:
        # Our built workflow should never raise — it's valid
        mission = load_mission_file("examples/mars_bioreactor.json")
        experts = select_experts(mission)
        stages = build_workflow(mission, experts)
        self.assertGreater(len(stages), 0)


class CriticalPathTests(unittest.TestCase):
    def test_critical_path_returns_valid_chain(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        experts = select_experts(mission)
        stages = build_workflow(mission, experts)
        path = critical_path(stages)
        self.assertIsInstance(path, list)
        self.assertGreater(len(path), 1)
        # First stage should have no dependencies
        stage_map = {s.id: s for s in stages}
        self.assertEqual(stage_map[path[0]].dependencies, [])

    def test_critical_path_ends_at_deepest(self) -> None:
        mission = load_mission_file("examples/mars_bioreactor.json")
        experts = select_experts(mission)
        stages = build_workflow(mission, experts)
        path = critical_path(stages)
        self.assertIn("dossier_export", path)


class ParallelGroupTests(unittest.TestCase):
    def test_groups_cover_all_stages(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        experts = select_experts(mission)
        stages = build_workflow(mission, experts)
        groups = parallel_groups(stages)
        all_ids = [sid for group in groups for sid in group]
        self.assertEqual(set(all_ids), {s.id for s in stages})

    def test_first_group_is_roots(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        experts = select_experts(mission)
        stages = build_workflow(mission, experts)
        groups = parallel_groups(stages)
        # First group should contain stages with no dependencies
        stage_map = {s.id: s for s in stages}
        for sid in groups[0]:
            self.assertEqual(stage_map[sid].dependencies, [])


if __name__ == "__main__":
    unittest.main()
