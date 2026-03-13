from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import tempfile
import unittest

from habitat_genome_compiler.cli import main
from habitat_genome_compiler.run_store import list_runs


class CliArchiveTests(unittest.TestCase):
    def test_compile_with_save_run_creates_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        "compile",
                        "examples/pfas_brine.json",
                        "--format",
                        "json",
                        "--save-run",
                        "--runs-dir",
                        tmpdir,
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn('"mission"', stdout.getvalue())
            self.assertEqual(len(list_runs(tmpdir)), 1)
            self.assertIn("Saved run", stderr.getvalue())

    def test_runs_and_show_run_render_saved_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                main(["compile", "examples/mars_bioreactor.json", "--save-run", "--runs-dir", tmpdir])
            run_id = list_runs(tmpdir)[0]["run_id"]

            runs_output = io.StringIO()
            with redirect_stdout(runs_output):
                exit_code = main(["runs", "--runs-dir", tmpdir, "--limit", "5"])
            self.assertEqual(exit_code, 0)
            self.assertIn(run_id, runs_output.getvalue())

            report_output = io.StringIO()
            with redirect_stdout(report_output):
                exit_code = main(["show-run", run_id, "--artifact", "report", "--runs-dir", tmpdir])
            self.assertEqual(exit_code, 0)
            self.assertIn("## Candidates", report_output.getvalue())


if __name__ == "__main__":
    unittest.main()
