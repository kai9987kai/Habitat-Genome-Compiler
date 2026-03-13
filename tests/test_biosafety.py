"""Tests for tiered biosafety assessment."""

from __future__ import annotations

import unittest

from habitat_genome_compiler.biosafety import assess_mission, quantitative_risk_score
from habitat_genome_compiler.compiler import load_mission_file
from habitat_genome_compiler.models import MissionEnvironment, MissionSpec, ObjectiveSpec


class QuantitativeRiskTests(unittest.TestCase):
    def test_blocked_mission_high_score(self) -> None:
        mission = load_mission_file("examples/blocked_mission.json")
        score, _findings, hits, blocked = quantitative_risk_score(mission)
        self.assertTrue(blocked)
        self.assertGreater(score, 5.0)
        self.assertGreater(len(hits), 0)

    def test_safe_mission_low_score(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        score, _findings, _hits, blocked = quantitative_risk_score(mission)
        self.assertFalse(blocked)
        self.assertLess(score, 5.0)

    def test_score_in_range(self) -> None:
        for example in ("examples/pfas_brine.json", "examples/mars_bioreactor.json"):
            mission = load_mission_file(example)
            score, _, _, _ = quantitative_risk_score(mission)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 10.0)

    def test_open_context_safeguards_reduce_risk(self) -> None:
        mission = MissionSpec(
            name="Contained runoff remediation scout",
            summary="Simulation-first design for an open-field remediation concept with layered containment.",
            domain="environmental remediation",
            deployment_context="open field pilot",
            biosafety_constraints=[
                "simulation only",
                "synthetic auxotrophy",
                "orthogonal translation genetic firewall",
                "kill switch",
            ],
            allowed_modalities=["simulation"],
            environment=MissionEnvironment(
                name="Canal edge",
                radiation_level=0.5,
                salinity_ppt=1.0,
                gravity_g=1.0,
                temperature_range_c=(12, 28),
                ph_range=(6.8, 7.4),
                nutrients=["nitrate"],
                stressors=["runoff"],
            ),
            objectives=[
                ObjectiveSpec(
                    id="o1",
                    title="Reduce nitrate burden",
                    target="Lower simulated nitrate accumulation in runoff",
                    metric="relative concentration",
                    priority=1,
                )
            ],
        )

        score, findings, _hits, blocked = quantitative_risk_score(mission)

        self.assertFalse(blocked)
        self.assertLess(score, 2.0)
        self.assertTrue(any("Detected safeguard layers" in finding for finding in findings))


class BiosafetyAssessmentTests(unittest.TestCase):
    def test_safe_mission_allowed(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        assessment = assess_mission(mission)
        self.assertTrue(assessment.allowed)
        self.assertIn(assessment.risk_tier, {"negligible", "low", "moderate", "elevated"})

    def test_blocked_mission_refused(self) -> None:
        mission = load_mission_file("examples/blocked_mission.json")
        assessment = assess_mission(mission)
        self.assertFalse(assessment.allowed)
        self.assertEqual(assessment.risk_tier, "blocked")

    def test_containment_recommendation(self) -> None:
        mission = load_mission_file("examples/pfas_brine.json")
        assessment = assess_mission(mission)
        self.assertIn(assessment.recommended_containment, {"simulation-only", "BSL-1", "BSL-2", "BSL-3"})

    def test_keyword_hits_tracked(self) -> None:
        mission = load_mission_file("examples/blocked_mission.json")
        assessment = assess_mission(mission)
        self.assertGreater(len(assessment.keyword_hits), 0)

    def test_risk_score_present(self) -> None:
        mission = load_mission_file("examples/mars_bioreactor.json")
        assessment = assess_mission(mission)
        self.assertGreaterEqual(assessment.risk_score, 0.0)
        self.assertLessEqual(assessment.risk_score, 10.0)

    def test_active_biocontainment_plan(self) -> None:
        mission = MissionSpec(
            name="High Risk Payload",
            summary="",
            domain="",
            objectives=[
                ObjectiveSpec(
                    id="o1",
                    title="toxin synthesis",
                    target="synthesize restricted pathogen toxin for vaccine",
                    metric="",
                    priority=1,
                )
            ],
            deployment_context="open field",
            environment=MissionEnvironment(
                name="Test",
                radiation_level=1.0,
                salinity_ppt=0.0,
                gravity_g=1.0,
                temperature_range_c=(20, 25),
                ph_range=(7.0, 7.5),
                nutrients=[],
                stressors=[],
            ),
        )
        assessment = assess_mission(mission)

        self.assertGreaterEqual(assessment.risk_score, 5.5)
        self.assertIsNotNone(assessment.containment_plan)
        plan = assessment.containment_plan
        self.assertIn("Simulation-only execution", plan.active_strategies)
        self.assertIn("Synthetic auxotrophy", plan.active_strategies)
        self.assertIn("Multi-input CRISPR kill-switch", plan.active_strategies)
        self.assertIn("Semantic containment (genetic firewall)", plan.active_strategies)
        self.assertTrue(any("absence" in trigger.lower() for trigger in plan.kill_switch_triggers))

    def test_gene_drive_minimum_containment(self) -> None:
        mission = MissionSpec(
            name="Contained drive benchmark",
            summary="Simulation-only evaluation of gene drive shutdown logic in a contained insectary.",
            domain="insect-control research",
            deployment_context="contained insectary",
            biosafety_constraints=["simulation only", "closed containment"],
            allowed_modalities=["simulation"],
            environment=MissionEnvironment(
                name="Insectary",
                radiation_level=0.2,
                salinity_ppt=0.0,
                gravity_g=1.0,
                temperature_range_c=(20, 26),
                ph_range=(6.8, 7.2),
                nutrients=["standard feed"],
                stressors=[],
            ),
            objectives=[
                ObjectiveSpec(
                    id="o1",
                    title="Benchmark gene drive shutdown",
                    target="Measure simulated shutdown fidelity of a gene drive control circuit",
                    metric="shutdown fidelity",
                    priority=1,
                )
            ],
        )

        assessment = assess_mission(mission)

        self.assertEqual(assessment.recommended_containment, "BSL-2")
        self.assertTrue(any("April 4, 2024" in finding for finding in assessment.findings))


if __name__ == "__main__":
    unittest.main()
