from __future__ import annotations

import unittest

from habitat_genome_compiler.compiler import compile_mission, load_mission_file, render_markdown


class CompilerTests(unittest.TestCase):
    def test_safe_mission_compiles(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        result = compile_mission(mission)
        self.assertTrue(result.allowed)
        self.assertGreaterEqual(len(result.candidates), 5)
        self.assertEqual(result.workflow[0].id, "mission_intake")

    def test_blocked_mission_is_refused(self) -> None:
        mission = load_mission_file("examples/blocked_mission.json")
        result = compile_mission(mission)
        self.assertFalse(result.allowed)
        self.assertEqual(result.candidates, [])
        self.assertIn("blocked", result.risk_level)

    def test_markdown_contains_candidate_section(self) -> None:
        mission = load_mission_file("examples/mars_bioreactor.json")
        result = compile_mission(mission)
        rendered = render_markdown(result)
        self.assertIn("## Candidates", rendered)
        self.assertIn("Closed-loop specialist consortium", rendered)

    def test_compile_metadata_present(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        result = compile_mission(mission)
        self.assertIn("compiler_version", result.compile_metadata)
        self.assertIn("timestamp", result.compile_metadata)
        self.assertIn("input_hash", result.compile_metadata)

    def test_dag_analysis_present(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        result = compile_mission(mission)
        self.assertIn("critical_path", result.dag_analysis)
        self.assertGreater(result.dag_analysis["critical_path_length"], 0)
        self.assertGreater(result.dag_analysis["max_parallelism"], 0)

    def test_risk_tier_and_containment(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        result = compile_mission(mission)
        self.assertIn(result.risk_tier, {"negligible", "low", "moderate", "elevated", "blocked"})
        self.assertIn(result.recommended_containment, {"simulation-only", "BSL-1", "BSL-2", "BSL-3"})

    def test_allowed_mission_has_containment_plan(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        result = compile_mission(mission)
        self.assertIsNotNone(result.containment_plan)
        self.assertGreater(len(result.containment_plan.active_strategies), 0)

    def test_robustness_attached_to_candidates(self) -> None:
        mission = load_mission_file("examples/mars_bioreactor.json")
        result = compile_mission(mission)
        for candidate in result.candidates:
            self.assertIsNotNone(candidate.robustness)
            self.assertGreaterEqual(candidate.robustness.mean_total, 0)
            self.assertGreaterEqual(candidate.robustness.failure_rate, 0)
            self.assertLessEqual(candidate.robustness.failure_rate, 1)

    def test_markdown_contains_new_sections(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        result = compile_mission(mission)
        rendered = render_markdown(result)
        self.assertIn("## DAG Analysis", rendered)
        self.assertIn("## Compile Metadata", rendered)
        self.assertIn("Robustness", rendered)
        self.assertIn("Pareto front", rendered)


if __name__ == "__main__":
    unittest.main()
