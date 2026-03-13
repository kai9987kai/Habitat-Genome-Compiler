from __future__ import annotations

import unittest

from habitat_genome_compiler.mission_generator import generate_mission_spec
from habitat_genome_compiler.models import MissionSpec
from habitat_genome_compiler.router import select_experts


class MissionGeneratorTests(unittest.TestCase):
    def test_generator_adds_research_backed_objectives(self) -> None:
        payload = {
            "name": "Custom Brine Mission",
            "domain": "industrial-remediation",
            "deployment_context": "closed bioreactor pilot",
            "problem_focus": "brine polishing with telemetry and adaptive control",
            "architecture_preference": "consortium",
            "safety_profile": "closed-loop-pilot",
            "environment_name": "harsh saline loop",
            "temperature_min_c": 8,
            "temperature_max_c": 36,
            "ph_min": 6.1,
            "ph_max": 8.4,
            "radiation_level": 1.0,
            "salinity_ppt": 48,
            "gravity_g": 1.0,
            "atmosphere": "air",
            "nutrients": "trace nitrogen, waste carbon feed",
            "stressors": "salinity, shear stress, temperature cycling",
            "primary_objective_title": "Reduce brine burden",
            "primary_objective_metric": "relative solute burden",
            "primary_objective_target": ">=60% reduction in simulation",
        }

        generated = generate_mission_spec(payload)
        mission = MissionSpec.from_dict(generated["mission"])
        objective_titles = {objective.title for objective in mission.objectives}

        self.assertIn("Maintain observability and control", objective_titles)
        self.assertIn("Maintain community balance", objective_titles)
        self.assertIn("must include online telemetry in the digital twin", mission.biosafety_constraints)
        self.assertIn("must model community balance control", mission.biosafety_constraints)
        self.assertGreaterEqual(len(generated["research_notes"]), 2)

        experts = select_experts(mission)
        self.assertIn("digital-twin-controls-specialist", experts)

    def test_offworld_generation_adds_resource_loop_objective(self) -> None:
        payload = {
            "name": "Regolith Greenhouse Mission",
            "domain": "offworld-biomanufacturing",
            "deployment_context": "closed habitat greenhouse pilot",
            "problem_focus": "regolith conditioning",
            "environment_name": "Mars regolith greenhouse loop",
            "stressors": "radiation, dust, regolith variability",
            "primary_objective_title": "Improve nutrient availability",
            "primary_objective_metric": "relative nutrient release",
            "primary_objective_target": ">=40% increase in simulation",
        }

        generated = generate_mission_spec(payload)
        titles = {objective["title"] for objective in generated["mission"]["objectives"]}

        self.assertIn("Close the resource recycle loop", titles)
        self.assertIn("must quantify nutrient recycle efficiency", generated["mission"]["biosafety_constraints"])

    def test_unsafe_terms_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            generate_mission_spec(
                {
                    "name": "Pathogen Mission",
                    "problem_focus": "transmissible pathogen design",
                    "primary_objective_title": "Increase virulence",
                }
            )


if __name__ == "__main__":
    unittest.main()
