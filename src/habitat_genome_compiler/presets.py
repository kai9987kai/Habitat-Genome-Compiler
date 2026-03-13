"""Preset mission catalog helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import load_json_file

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def _is_blocked_example(payload: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(payload.get("name", "")),
            str(payload.get("summary", "")),
            str(payload.get("domain", "")),
            " ".join(str(item.get("title", "")) for item in payload.get("objectives", [])),
        ]
    ).lower()
    return any(term in text for term in ("pathogen", "virulence", "immune evasion", "transmissible", "toxin"))


def load_template(name: str) -> dict[str, Any]:
    path = EXAMPLES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Unknown template: {name}")
    return load_json_file(path)


def list_templates() -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    for path in sorted(EXAMPLES_DIR.glob("*.json")):
        payload = load_json_file(path)
        environment = payload.get("environment", {})
        blocked = _is_blocked_example(payload)
        templates.append(
            {
                "id": path.stem,
                "name": payload.get("name", path.stem),
                "summary": payload.get("summary", ""),
                "domain": payload.get("domain", ""),
                "status": "blocked-demo" if blocked else "ready",
                "deployment_context": payload.get("deployment_context", ""),
                "environment_name": environment.get("name", ""),
                "stressors": environment.get("stressors", []),
                "objectives": [objective.get("title", "") for objective in payload.get("objectives", [])],
            }
        )
    return sorted(templates, key=lambda item: (item["status"] == "blocked-demo", item["name"]))


__all__ = ["EXAMPLES_DIR", "list_templates", "load_template"]
