"""Lightweight HTTP API with no third-party dependencies."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .compiler import compile_mission
from .models import MissionSpec
from .run_store import RunStoreError, list_runs, load_run_artifact, read_run_manifest, save_run


def _json_response(handler: BaseHTTPRequestHandler, status: HTTPStatus, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _parse_request_target(target: str) -> tuple[str, dict[str, list[str]]]:
    parsed = urlparse(target)
    return parsed.path, parse_qs(parsed.query)


class CompilerHandler(BaseHTTPRequestHandler):
    server_version = "HabitatCompiler/0.1"
    _valid_artifacts = {"manifest", "mission", "result", "report"}

    def do_GET(self) -> None:  # noqa: N802
        path, query = _parse_request_target(self.path)

        if path == "/health":
            _json_response(self, HTTPStatus.OK, {"status": "ok"})
            return
        if path == "/examples":
            examples = [path.as_posix() for path in sorted(Path("examples").glob("*.json"))]
            _json_response(self, HTTPStatus.OK, {"examples": examples})
            return
        if path == "/runs":
            limit_param = query.get("limit", ["20"])[0]
            runs_dir = query.get("runs_dir", [None])[0]
            try:
                limit = int(limit_param)
            except ValueError:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "limit must be an integer"})
                return
            _json_response(self, HTTPStatus.OK, {"runs": list_runs(runs_dir, limit=limit)})
            return
        if path.startswith("/runs/"):
            run_id = path.removeprefix("/runs/")
            artifact = query.get("artifact", ["manifest"])[0]
            runs_dir = query.get("runs_dir", [None])[0]
            if artifact not in self._valid_artifacts:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "unknown artifact"})
                return
            try:
                if artifact == "manifest":
                    payload = read_run_manifest(run_id, runs_dir)
                else:
                    payload = load_run_artifact(run_id, artifact=artifact, runs_dir=runs_dir)
            except RunStoreError as exc:
                _json_response(self, HTTPStatus.NOT_FOUND, {"error": str(exc)})
                return

            if isinstance(payload, str):
                _json_response(
                    self,
                    HTTPStatus.OK,
                    {"run_id": run_id, "artifact": artifact, "content": payload},
                )
            else:
                _json_response(self, HTTPStatus.OK, payload)
            return
        _json_response(self, HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path, query = _parse_request_target(self.path)
        if path != "/compile":
            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            result = compile_mission(MissionSpec.from_dict(payload))
        except Exception as exc:  # pragma: no cover
            _json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        response = result.to_dict()
        save_requested = query.get("save", ["0"])[0].lower() in {"1", "true", "yes"}
        if save_requested:
            saved_run = save_run(result, runs_dir=query.get("runs_dir", [None])[0])
            response["saved_run"] = saved_run.to_dict()

        _json_response(self, HTTPStatus.OK, response)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        del format, args


def run_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), CompilerHandler)
    print(f"Serving Habitat Compiler API on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8080, type=int)
    args = parser.parse_args(argv)
    run_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
