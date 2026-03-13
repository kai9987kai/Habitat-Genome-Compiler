# Habitat-Genome Compiler

Habitat-Genome Compiler is a safe, local-first mission compiler for speculative habitat and environmental bio-design programs. It turns a mission JSON spec into a ranked candidate set, a markdown dossier, and an auditable local run archive. The project now also includes a browser-based mission studio that can generate valid mission specs through a guided builder instead of requiring hand-authored JSON.

## What is included

- A mission JSON compiler with biosafety-aware validation and refusal handling.
- A GUI mission builder that generates safe mission specs and keeps the JSON view in sync.
- A preset library for industrial, water, climate, and offworld mission scenarios.
- Local run persistence with `manifest.json`, `mission.json`, `result.json`, and `report.md` for every saved compile.
- A lightweight HTTP API plus CLI commands for compile, serve, list runs, and inspect archived artifacts.

## Quick start

Clone the repository, then install the package in editable mode:

```bash
pip install -e .
```

For the GUI builder, make sure `fastapi` and `uvicorn` are available in your environment, then start the app:

```bash
python gui_app.py
```

Open `http://127.0.0.1:8000` to use the mission studio.

## CLI usage

Compile a bundled example and save the full run archive:

```bash
habitat-compiler compile examples/pfas_brine.json --save-run
```

List recent saved runs:

```bash
habitat-compiler runs
```

Inspect a saved markdown dossier:

```bash
habitat-compiler show-run <run_id> --artifact report
```

Run the lightweight API server:

```bash
habitat-compiler serve --host 127.0.0.1 --port 8080
```

## Mission studio

The browser UI now includes:

- Preset cards with safe-first ordering and blocked-demo missions pushed to the end.
- A guided builder for name, domain, environment, stressors, objectives, and safety profile.
- Research-note cards that explain why extra control, containment, consortium, or offworld objectives were added.
- A live JSON panel so generated missions can still be reviewed and edited directly.
- Compile results that surface verdicts and the saved run ID for traceability.

## Bundled presets

Current example missions include:

- `examples/pfas_brine.json`
- `examples/desalination_brine_polishing.json`
- `examples/methane_biofilter.json`
- `examples/mine_tailings_recovery.json`
- `examples/mars_bioreactor.json`
- `examples/mars_regolith_biofertility.json`
- `examples/blocked_mission.json`

## Research-backed generator

The mission builder adds extra objectives and constraints using rules derived from published work on:

- Digital twins for bioprocess control
- Long-term microbial consortium homeostasis
- Layered biological containment
- Offworld resource loops and regolith-linked nutrient recycling

The applied source mapping is documented in `docs/research-upgrades.md`.

## Saved runs

When a compile is saved, the run archive stores:

- `manifest.json` with metadata, timestamps, compiler version, and artifact references
- `mission.json` with the validated mission input
- `result.json` with the compiler output
- `report.md` with the rendered dossier

Runs are stored in `./runs` by default, or in the directory pointed to by `HABITAT_COMPILER_RUNS_DIR`.

## Safety model

This project is intentionally simulation-first. Unsafe mission requests are blocked, and the builder refuses pathogen, toxin, immune-evasion, transmissibility, and similar harmful capability framing. Generated missions bias toward containment, telemetry, shutdown logic, and review gates instead of actionable wet-lab instructions.

## Verification

The current automated test suite passes with:

```bash
python -m pytest -q
```

Latest verified result: `75 passed`.
