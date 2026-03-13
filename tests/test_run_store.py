from __future__ import annotations

import tempfile
import unittest

from habitat_genome_compiler.compiler import compile_mission, load_mission_file
from habitat_genome_compiler.run_store import list_runs, load_run_artifact, read_run_manifest, save_run


class RunStoreTests(unittest.TestCase):
    def test_save_run_persists_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mission = load_mission_file("examples/pfas_brine.json")
            result = compile_mission(mission)

            saved = save_run(result, runs_dir=tmpdir)
            manifest = read_run_manifest(saved.run_id, runs_dir=tmpdir)
            stored_result = load_run_artifact(saved.run_id, "result", runs_dir=tmpdir)
            report = load_run_artifact(saved.run_id, "report", runs_dir=tmpdir)

            self.assertEqual(result.compile_metadata["run_id"], saved.run_id)
            self.assertEqual(manifest["mission_name"], mission.name)
            self.assertEqual(stored_result["compile_metadata"]["run_id"], saved.run_id)
            self.assertIn(mission.name, report)
            self.assertIn("## Candidates", report)

    def test_list_runs_orders_newest_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            older = compile_mission(load_mission_file("examples/pfas_brine.json"))
            older.compile_metadata["timestamp"] = "2026-03-10T09:00:00+00:00"
            older_saved = save_run(older, runs_dir=tmpdir)

            newer = compile_mission(load_mission_file("examples/mars_bioreactor.json"))
            newer.compile_metadata["timestamp"] = "2026-03-11T09:00:00+00:00"
            newer_saved = save_run(newer, runs_dir=tmpdir)

            runs = list_runs(tmpdir)

            self.assertEqual([item["run_id"] for item in runs[:2]], [newer_saved.run_id, older_saved.run_id])


if __name__ == "__main__":
    unittest.main()
