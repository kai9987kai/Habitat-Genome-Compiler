from __future__ import annotations

import unittest

from habitat_genome_compiler.presets import list_templates, load_template


class PresetCatalogTests(unittest.TestCase):
    def test_catalog_includes_expanded_presets(self) -> None:
        template_ids = {template["id"] for template in list_templates()}
        self.assertIn("mars_regolith_biofertility", template_ids)
        self.assertIn("methane_biofilter", template_ids)
        self.assertGreaterEqual(len(template_ids), 7)

    def test_load_template_returns_expected_payload(self) -> None:
        payload = load_template("mine_tailings_recovery")
        self.assertEqual(payload["domain"], "industrial-remediation")
        self.assertEqual(payload["environment"]["name"], "acidic tailings slurry")


if __name__ == "__main__":
    unittest.main()
