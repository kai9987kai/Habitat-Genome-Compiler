"""Tests for Monte Carlo robustness analysis."""

from __future__ import annotations

import unittest

from habitat_genome_compiler.adapters import build_habitat_profile, propose_candidates
from habitat_genome_compiler.compiler import load_mission_file
from habitat_genome_compiler.robustness import robustness_sweep
from habitat_genome_compiler.scoring import score_candidates


class RobustnessSweepTests(unittest.TestCase):
    def _run_sweep(self, example: str = "examples/pfas_brine.json", n: int = 50):
        mission = load_mission_file(example)
        habitat = build_habitat_profile(mission)
        candidates = propose_candidates(mission, habitat)
        scored = score_candidates(mission, habitat, candidates)
        return robustness_sweep(mission, scored, n_samples=n, seed=42)

    def test_reports_match_candidates(self) -> None:
        reports = self._run_sweep()
        self.assertEqual(len(reports), 5)

    def test_failure_rate_in_range(self) -> None:
        reports = self._run_sweep()
        for r in reports:
            self.assertGreaterEqual(r.failure_rate, 0.0)
            self.assertLessEqual(r.failure_rate, 1.0)

    def test_sensitivity_keys(self) -> None:
        reports = self._run_sweep()
        expected_keys = {"radiation_level", "salinity_ppt", "gravity_g"}
        for r in reports:
            self.assertEqual(set(r.sensitivity.keys()), expected_keys)

    def test_deterministic_with_seed(self) -> None:
        r1 = self._run_sweep(n=30)
        r2 = self._run_sweep(n=30)
        for a, b in zip(r1, r2):
            self.assertEqual(a.mean_total, b.mean_total)
            self.assertEqual(a.std_total, b.std_total)
            self.assertEqual(a.failure_rate, b.failure_rate)

    def test_mean_total_positive(self) -> None:
        reports = self._run_sweep()
        for r in reports:
            self.assertGreater(r.mean_total, 0)

    def test_std_total_nonnegative(self) -> None:
        reports = self._run_sweep()
        for r in reports:
            self.assertGreaterEqual(r.std_total, 0)


if __name__ == "__main__":
    unittest.main()
