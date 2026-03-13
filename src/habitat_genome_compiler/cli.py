"""Command-line interface for the compiler."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .api import run_server
from .compiler import compile_mission, load_mission_file, render_markdown


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

    subparsers.add_parser("examples", help="List bundled example missions.")

    serve_parser = subparsers.add_parser("serve", help="Run the lightweight HTTP API.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8080)

    return parser


def _handle_compile(args: argparse.Namespace) -> int:
    mission = load_mission_file(args.mission_file)
    result = compile_mission(mission)
    rendered = result.to_json() if args.format == "json" else render_markdown(result)

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
        if not rendered.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def _handle_examples() -> int:
    examples = sorted(Path("examples").glob("*.json"))
    for path in examples:
        print(path.as_posix())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compile":
        return _handle_compile(args)
    if args.command == "examples":
        return _handle_examples()
    if args.command == "serve":
        run_server(host=args.host, port=args.port)
        return 0
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
