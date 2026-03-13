"""Command-line interface for the compiler."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from .api import run_server
from .compiler import compile_mission, load_mission_file, render_markdown
from .run_store import list_runs, load_run_artifact, read_run_manifest, save_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="habitat-compiler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="Compile a mission JSON file.")
    compile_parser.add_argument("mission_file", help="Path to a mission JSON file.")
    compile_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Output format.",
    )
    compile_parser.add_argument("--output", help="Optional output file.")
    compile_parser.add_argument(
        "--save-run",
        action="store_true",
        help="Persist the mission, result JSON, and Markdown dossier to the local run archive.",
    )
    compile_parser.add_argument(
        "--runs-dir",
        help="Override the run archive directory (defaults to ./runs or HABITAT_COMPILER_RUNS_DIR).",
    )

    subparsers.add_parser("examples", help="List bundled example missions.")

    runs_parser = subparsers.add_parser("runs", help="List persisted compile runs.")
    runs_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for run history.",
    )
    runs_parser.add_argument("--limit", type=int, default=20, help="Maximum number of runs to display.")
    runs_parser.add_argument("--runs-dir", help="Override the run archive directory.")

    show_run_parser = subparsers.add_parser("show-run", help="Display a persisted run artifact.")
    show_run_parser.add_argument("run_id", help="Run identifier from `habitat-compiler runs`.")
    show_run_parser.add_argument(
        "--artifact",
        choices=("manifest", "mission", "result", "report"),
        default="manifest",
        help="Artifact to display.",
    )
    show_run_parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="text",
        help="Formatting mode. `text` is only useful with the Markdown report artifact.",
    )
    show_run_parser.add_argument("--runs-dir", help="Override the run archive directory.")

    serve_parser = subparsers.add_parser("serve", help="Run the lightweight HTTP API.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8080)

    return parser


def _handle_compile(args: argparse.Namespace) -> int:
    mission = load_mission_file(args.mission_file)
    result = compile_mission(mission)
    rendered = result.to_json() if args.format == "json" else render_markdown(result)
    saved_run = save_run(result, runs_dir=args.runs_dir) if args.save_run else None

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
        if not rendered.endswith("\n"):
            sys.stdout.write("\n")

    if saved_run:
        sys.stderr.write(
            f"Saved run {saved_run.run_id} to {saved_run.directory}{os.linesep}"
        )
    return 0


def _handle_examples() -> int:
    examples = sorted(Path("examples").glob("*.json"))
    for path in examples:
        print(path.as_posix())
    return 0


def _handle_runs(args: argparse.Namespace) -> int:
    runs = list_runs(args.runs_dir, limit=args.limit)
    if args.format == "json":
        sys.stdout.write(json.dumps({"runs": runs}, indent=2))
        sys.stdout.write("\n")
        return 0

    if not runs:
        sys.stdout.write("No persisted runs found.\n")
        return 0

    headers = ("RUN ID", "MISSION", "CREATED", "ALLOWED", "TIER")
    rows = [
        (
            str(item.get("run_id", "")),
            str(item.get("mission_name", "")),
            str(item.get("created_at", "")),
            "yes" if item.get("allowed") else "no",
            str(item.get("risk_tier", "")),
        )
        for item in runs
    ]
    widths = [
        max([len(header), *(len(row[index]) for row in rows)])
        for index, header in enumerate(headers)
    ]

    def _format_row(values: tuple[str, ...]) -> str:
        return "  ".join(value.ljust(widths[index]) for index, value in enumerate(values))

    sys.stdout.write(_format_row(headers) + "\n")
    sys.stdout.write(_format_row(tuple("-" * width for width in widths)) + "\n")
    for row in rows:
        sys.stdout.write(_format_row(row) + "\n")
    return 0


def _handle_show_run(args: argparse.Namespace) -> int:
    if args.artifact == "manifest":
        artifact = read_run_manifest(args.run_id, args.runs_dir)
    else:
        artifact = load_run_artifact(args.run_id, artifact=args.artifact, runs_dir=args.runs_dir)

    if isinstance(artifact, str):
        if args.format == "json":
            sys.stdout.write(
                json.dumps(
                    {"run_id": args.run_id, "artifact": args.artifact, "content": artifact},
                    indent=2,
                )
            )
            sys.stdout.write("\n")
            return 0
        sys.stdout.write(artifact)
        if not artifact.endswith("\n"):
            sys.stdout.write("\n")
        return 0

    if args.format == "text":
        sys.stdout.write(json.dumps(artifact, indent=2))
        sys.stdout.write("\n")
        return 0

    sys.stdout.write(json.dumps(artifact, indent=2))
    sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compile":
        return _handle_compile(args)
    if args.command == "examples":
        return _handle_examples()
    if args.command == "runs":
        return _handle_runs(args)
    if args.command == "show-run":
        return _handle_show_run(args)
    if args.command == "serve":
        run_server(host=args.host, port=args.port)
        return 0
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
