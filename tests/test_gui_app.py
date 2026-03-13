from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from gui_app import app


class GuiAppApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_templates_endpoint_lists_presets(self) -> None:
        response = self.client.get("/api/templates")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        template_ids = {template["id"] for template in payload["templates"]}
        self.assertIn("desalination_brine_polishing", template_ids)

    def test_generate_mission_endpoint_returns_notes(self) -> None:
        response = self.client.post(
            "/api/generate-mission",
            json={
                "name": "Telemetry Mission",
                "domain": "industrial-emissions-control",
                "deployment_context": "closed skid-mounted biofilter pilot",
                "problem_focus": "methane polishing with telemetry",
                "primary_objective_title": "Reduce methane slip",
                "primary_objective_metric": "relative methane concentration",
                "primary_objective_target": ">=70% reduction in simulation",
                "stressors": "flow surges, methane fluctuations",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("mission", payload)
        self.assertIn("research_notes", payload)
        titles = {objective["title"] for objective in payload["mission"]["objectives"]}
        self.assertIn("Maintain observability and control", titles)


if __name__ == "__main__":
    unittest.main()
