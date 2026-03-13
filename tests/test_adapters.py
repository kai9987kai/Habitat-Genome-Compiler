"""Tests for dynamic archetype registry in adapters.py."""

from __future__ import annotations

import unittest

from habitat_genome_compiler.adapters import (
    ARCHETYPE_REGISTRY,
    build_habitat_profile,
    propose_candidates,
)
from habitat_genome_compiler.compiler import load_mission_file


class ArchetypeRegistryTests(unittest.TestCase):
    def test_registry_has_five_archetypes(self) -> None:
        self.assertEqual(len(ARCHETYPE_REGISTRY), 5)

    def test_archetype_names_unique(self) -> None:
        names = [t.archetype for t in ARCHETYPE_REGISTRY]
        self.assertEqual(len(names), len(set(names)))

    def test_new_archetypes_present(self) -> None:
        archetypes = {t.archetype for t in ARCHETYPE_REGISTRY}
        self.assertIn("hybrid-consortium", archetypes)
        self.assertIn("phage-assisted", archetypes)


class CandidateGenerationTests(unittest.TestCase):
    def test_five_candidates_generated(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        habitat = build_habitat_profile(mission)
        candidates = propose_candidates(mission, habitat)
        self.assertEqual(len(candidates), 5)

    def test_all_candidates_have_safety_modules(self) -> None:
        mission = load_mission_file("examples/mars_bioreactor.json")
        habitat = build_habitat_profile(mission)
        candidates = propose_candidates(mission, habitat)
        for c in candidates:
            self.assertIn("containment logic", c.modules)
            self.assertIn("shutdown sentinel", c.modules)
            self.assertIn("traceability telemetry", c.modules)

    def test_tag_specific_modules_applied(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        habitat = build_habitat_profile(mission)
        candidates = propose_candidates(mission, habitat)
        consortium = next(c for c in candidates if c.archetype == "consortium")
        self.assertIn("pollutant capture and conversion layer", consortium.modules)

    def test_severity_module_applied_for_harsh_env(self) -> None:
        mission = load_mission_file("examples/mars_bioreactor.json")
        habitat = build_habitat_profile(mission)
        if habitat.severity >= 6:
            candidates = propose_candidates(mission, habitat)
            chassis = next(c for c in candidates if c.archetype == "single-chassis")
            self.assertIn("extreme-environment hardening", chassis.modules)

    def test_unique_candidate_ids(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        habitat = build_habitat_profile(mission)
        candidates = propose_candidates(mission, habitat)
        ids = [c.id for c in candidates]
        self.assertEqual(len(ids), len(set(ids)))

    def test_rl_combinatorial_exploration(self) -> None:
        from habitat_genome_compiler.adapters import SAFETY_MODULES
        mission = load_mission_file("examples/pfas_brine.json")
        habitat = build_habitat_profile(mission)
        candidates = propose_candidates(mission, habitat)
        
        self.assertEqual(len(candidates), 5)
        for c in candidates:
            self.assertIsInstance(c.modules, list)
            self.assertGreaterEqual(len(c.modules), len(SAFETY_MODULES))
            self.assertTrue(any("rl agent converged" in r.lower() for r in c.rationale))


if __name__ == "__main__":
    unittest.main()
