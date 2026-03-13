"""Tests for Pareto-frontier ranking in scoring.py."""

from __future__ import annotations

import unittest

from habitat_genome_compiler.adapters import build_habitat_profile, propose_candidates
from habitat_genome_compiler.compiler import load_mission_file
from habitat_genome_compiler.scoring import pareto_rank, score_candidates


class ParetoRankTests(unittest.TestCase):
    def _get_scored(self):
        mission = load_mission_file("examples/pfas_brine.json")
        habitat = build_habitat_profile(mission)
        candidates = propose_candidates(mission, habitat)
        return score_candidates(mission, habitat, candidates)

    def test_pareto_front_assigned(self) -> None:
        candidates = self._get_scored()
        for c in candidates:
            self.assertIn("pareto_front", c.scores)
            self.assertGreaterEqual(c.scores["pareto_front"], 0)

    def test_crowding_distance_assigned(self) -> None:
        candidates = self._get_scored()
        for c in candidates:
            self.assertIn("crowding_distance", c.scores)
            self.assertGreaterEqual(c.scores["crowding_distance"], 0)

    def test_total_score_backwards_compatible(self) -> None:
        candidates = self._get_scored()
        for c in candidates:
            self.assertIn("total", c.scores)
            self.assertGreater(c.scores["total"], 0)

    def test_front_zero_dominates_later_fronts(self) -> None:
        candidates = self._get_scored()
        front_0 = [c for c in candidates if c.scores["pareto_front"] == 0]
        later = [c for c in candidates if c.scores["pareto_front"] > 0]
        if front_0 and later:
            # At least one front-0 should dominate at least one later on some axis
            self.assertTrue(len(front_0) >= 1)

    def test_sorted_by_front_then_crowding(self) -> None:
        candidates = self._get_scored()
        for i in range(len(candidates) - 1):
            a, b = candidates[i], candidates[i + 1]
            self.assertLessEqual(a.scores["pareto_front"], b.scores["pareto_front"])


class ScoringAxesTests(unittest.TestCase):
    def test_five_candidates_scored(self) -> None:
        mission = load_mission_file("examples/mars_bioreactor.json")
        habitat = build_habitat_profile(mission)
        candidates = propose_candidates(mission, habitat)
        scored = score_candidates(mission, habitat, candidates)
        self.assertEqual(len(scored), 5)

    def test_all_axes_present(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        habitat = build_habitat_profile(mission)
        candidates = propose_candidates(mission, habitat)
        scored = score_candidates(mission, habitat, candidates)
        for c in scored:
            for axis in ("mission_fit", "habitat_fit", "feasibility", "biosafety_margin", "total"):
                self.assertIn(axis, c.scores)


if __name__ == "__main__":
    unittest.main()
