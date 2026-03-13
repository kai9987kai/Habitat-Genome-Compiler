"""Local persistence for compiler runs and derived artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Literal

from .compiler import render_markdown
from .models import CompileResult

RUN_STORE_ENV_VAR = "HABITAT_COMPILER_RUNS_DIR"
RUN_STORE_SCHEMA_VERSION = 1
DEFAULT_RUNS_DIR = "runs"
ArtifactName = Literal["manifest", "mission", "result", "report"]

ARTIFACT_FILENAMES: dict[ArtifactName, str] = {
    "manifest": "manifest.json",
    "mission": "mission.json",
    "result": "result.json",
    "report": "report.md",
}


class RunStoreError(RuntimeError):
    """Raised when a persisted run cannot be resolved."""


@dataclass(slots=True)
class SavedRun:
    run_id: str
    created_at: str
    mission_name: str
    allowed: bool
    risk_tier: str
    compiler_version: str
    directory: str
    manifest_path: str
    mission_path: str
    result_path: str
    report_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "mission_name": self.mission_name,
            "allowed": self.allowed,
            "risk_tier": self.risk_tier,
            "compiler_version": self.compiler_version,
            "directory": self.directory,
            "artifacts": {
                "manifest": self.manifest_path,
                "mission": self.mission_path,
                "result": self.result_path,
                "report": self.report_path,
            },
        }


def resolve_runs_dir(runs_dir: str | Path | None = None) -> Path:
    configured = runs_dir or os.environ.get(RUN_STORE_ENV_VAR) or DEFAULT_RUNS_DIR
    return Path(configured).resolve()


def _coerce_timestamp(raw_timestamp: str | None) -> datetime:
    if not raw_timestamp:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def _build_run_id(result: CompileResult, base_dir: Path) -> str:
    timestamp = _coerce_timestamp(result.compile_metadata.get("timestamp"))
    timestamp_prefix = timestamp.strftime("%Y%m%dT%H%M%SZ")
    hash_prefix = str(result.compile_metadata.get("input_hash", "adhoc"))[:16] or "adhoc"
    base_run_id = f"{timestamp_prefix}_{hash_prefix}"

    run_id = base_run_id
    index = 2
    while (base_dir / run_id).exists():
        run_id = f"{base_run_id}-{index}"
        index += 1
    return run_id


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - thin guard
        raise RunStoreError(f"Run artifact not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RunStoreError(f"Run artifact is not valid JSON: {path}") from exc


def save_run(result: CompileResult, runs_dir: str | Path | None = None) -> SavedRun:
    """Persist a compile result with its source mission and Markdown dossier."""
    base_dir = resolve_runs_dir(runs_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    run_id = _build_run_id(result, base_dir)
    run_dir = base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    created_at = str(result.compile_metadata.get("timestamp", datetime.now(timezone.utc).isoformat()))
    compiler_version = str(result.compile_metadata.get("compiler_version", "unknown"))
    result.compile_metadata["run_id"] = run_id

    paths = {name: run_dir / filename for name, filename in ARTIFACT_FILENAMES.items()}

    manifest = {
        "schema_version": RUN_STORE_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": created_at,
        "mission_name": result.mission.name,
        "allowed": result.allowed,
        "risk_level": result.risk_level,
        "risk_tier": result.risk_tier,
        "compiler_version": compiler_version,
        "input_hash": result.compile_metadata.get("input_hash"),
        "artifacts": {name: path.name for name, path in paths.items()},
    }

    paths["mission"].write_text(
        json.dumps(result.mission.to_dict(), indent=2),
        encoding="utf-8",
    )
    paths["result"].write_text(result.to_json(), encoding="utf-8")
    paths["report"].write_text(render_markdown(result), encoding="utf-8")
    paths["manifest"].write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return SavedRun(
        run_id=run_id,
        created_at=created_at,
        mission_name=result.mission.name,
        allowed=result.allowed,
        risk_tier=result.risk_tier,
        compiler_version=compiler_version,
        directory=str(run_dir),
        manifest_path=str(paths["manifest"]),
        mission_path=str(paths["mission"]),
        result_path=str(paths["result"]),
        report_path=str(paths["report"]),
    )


def list_runs(runs_dir: str | Path | None = None, *, limit: int | None = None) -> list[dict[str, Any]]:
    """Return saved run manifests ordered from newest to oldest."""
    base_dir = resolve_runs_dir(runs_dir)
    if not base_dir.exists():
        return []

    items: list[dict[str, Any]] = []
    for manifest_path in base_dir.glob("*/manifest.json"):
        try:
            manifest = _read_json(manifest_path)
        except RunStoreError:
            continue

        manifest["directory"] = str(manifest_path.parent.resolve())
        artifacts = manifest.get("artifacts", {})
        manifest["artifact_paths"] = {
            name: str((manifest_path.parent / relative_path).resolve())
            for name, relative_path in artifacts.items()
        }
        items.append(manifest)

    items.sort(
        key=lambda item: _coerce_timestamp(str(item.get("created_at", ""))).timestamp(),
        reverse=True,
    )
    if limit is not None:
        return items[:limit]
    return items


def read_run_manifest(run_id: str, runs_dir: str | Path | None = None) -> dict[str, Any]:
    base_dir = resolve_runs_dir(runs_dir)
    manifest_path = base_dir / run_id / ARTIFACT_FILENAMES["manifest"]
    manifest = _read_json(manifest_path)
    manifest["directory"] = str(manifest_path.parent.resolve())
    manifest["artifact_paths"] = {
        name: str((manifest_path.parent / relative_path).resolve())
        for name, relative_path in manifest.get("artifacts", {}).items()
    }
    return manifest


def load_run_artifact(
    run_id: str,
    artifact: ArtifactName = "result",
    runs_dir: str | Path | None = None,
) -> dict[str, Any] | str:
    if artifact == "manifest":
        return read_run_manifest(run_id, runs_dir)

    manifest = read_run_manifest(run_id, runs_dir)
    artifact_name = manifest.get("artifacts", {}).get(artifact)
    if not artifact_name:
        raise RunStoreError(f"Artifact '{artifact}' is not registered for run '{run_id}'.")

    artifact_path = Path(manifest["directory"]) / artifact_name
    if artifact == "report":
        try:
            return artifact_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:  # pragma: no cover - thin guard
            raise RunStoreError(f"Run artifact not found: {artifact_path}") from exc
    return _read_json(artifact_path)


__all__ = [
    "ArtifactName",
    "RunStoreError",
    "SavedRun",
    "list_runs",
    "load_run_artifact",
    "read_run_manifest",
    "resolve_runs_dir",
    "save_run",
]
