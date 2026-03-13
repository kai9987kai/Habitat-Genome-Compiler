from __future__ import annotations

from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
import os
import tempfile
import threading
import unittest

from habitat_genome_compiler.api import CompilerHandler
from habitat_genome_compiler.models import load_json_file


class ApiArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.previous_runs_dir = os.environ.get("HABITAT_COMPILER_RUNS_DIR")
        os.environ["HABITAT_COMPILER_RUNS_DIR"] = self.tempdir.name

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), CompilerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        if self.previous_runs_dir is None:
            os.environ.pop("HABITAT_COMPILER_RUNS_DIR", None)
        else:
            os.environ["HABITAT_COMPILER_RUNS_DIR"] = self.previous_runs_dir
        self.tempdir.cleanup()

    def _request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        connection = HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = None
        headers: dict[str, str] = {}
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"

        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        connection.close()
        decoded = json.loads(raw.decode("utf-8")) if raw else {}
        return response.status, decoded

    def test_compile_save_and_list_runs(self) -> None:
        mission = load_json_file("examples/pfas_brine.json")

        status, compile_payload = self._request("POST", "/compile?save=1", mission)
        self.assertEqual(status, 200)
        self.assertIn("saved_run", compile_payload)
        run_id = compile_payload["saved_run"]["run_id"]

        status, runs_payload = self._request("GET", "/runs?limit=5")
        self.assertEqual(status, 200)
        self.assertEqual(runs_payload["runs"][0]["run_id"], run_id)

        status, result_payload = self._request("GET", f"/runs/{run_id}?artifact=result")
        self.assertEqual(status, 200)
        self.assertEqual(result_payload["compile_metadata"]["run_id"], run_id)


if __name__ == "__main__":
    unittest.main()
