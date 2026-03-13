"""Workflow compilation for habitat-to-genome missions.

Includes DAG topological validation and critical-path analysis inspired by
iBioSim and Galaxy-SynBioCAD workflow compilers.
"""

from __future__ import annotations

from collections import defaultdict, deque

from .models import MissionSpec, WorkflowStage


# ---------------------------------------------------------------------------
# DAG analysis utilities
# ---------------------------------------------------------------------------


def validate_dag(stages: list[WorkflowStage]) -> list[str]:
    """Run Kahn's topological sort.  Return error strings if cycles exist."""
    id_set = {s.id for s in stages}
    in_degree: dict[str, int] = {s.id: 0 for s in stages}
    children: dict[str, list[str]] = defaultdict(list)

    errors: list[str] = []
    for stage in stages:
        for dep in stage.dependencies:
            if dep not in id_set:
                errors.append(f"Stage '{stage.id}' depends on unknown stage '{dep}'.")
                continue
            children[dep].append(stage.id)
            in_degree[stage.id] += 1

    queue: deque[str] = deque(sid for sid, deg in in_degree.items() if deg == 0)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for child in children[node]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if visited < len(stages):
        cycle_members = [sid for sid, deg in in_degree.items() if deg > 0]
        errors.append(f"Cycle detected among stages: {', '.join(cycle_members)}.")

    return errors


def critical_path(stages: list[WorkflowStage]) -> list[str]:
    """Return the longest dependency chain (list of stage IDs).

    Uses a simple DAG longest-path algorithm via topological ordering.
    """
    id_to_stage = {s.id: s for s in stages}
    in_degree: dict[str, int] = {s.id: 0 for s in stages}
    children: dict[str, list[str]] = defaultdict(list)

    for stage in stages:
        for dep in stage.dependencies:
            if dep in id_to_stage:
                children[dep].append(stage.id)
                in_degree[stage.id] += 1

    # Topological order via Kahn's
    queue: deque[str] = deque(sid for sid, deg in in_degree.items() if deg == 0)
    topo_order: list[str] = []
    while queue:
        node = queue.popleft()
        topo_order.append(node)
        for child in children[node]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # Longest path
    dist: dict[str, int] = {sid: 0 for sid in topo_order}
    parent: dict[str, str | None] = {sid: None for sid in topo_order}

    for node in topo_order:
        for child in children[node]:
            if dist[node] + 1 > dist[child]:
                dist[child] = dist[node] + 1
                parent[child] = node

    # Trace back from the farthest node
    end = max(topo_order, key=lambda sid: dist[sid])
    path: list[str] = []
    current: str | None = end
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    return path


def parallel_groups(stages: list[WorkflowStage]) -> list[list[str]]:
    """Return stages grouped by DAG level (stages within a group can run concurrently)."""
    id_to_stage = {s.id: s for s in stages}
    in_degree: dict[str, int] = {s.id: 0 for s in stages}
    children: dict[str, list[str]] = defaultdict(list)

    for stage in stages:
        for dep in stage.dependencies:
            if dep in id_to_stage:
                children[dep].append(stage.id)
                in_degree[stage.id] += 1

    groups: list[list[str]] = []
    queue = [sid for sid, deg in in_degree.items() if deg == 0]

    while queue:
        groups.append(sorted(queue))
        next_queue: list[str] = []
        for node in queue:
            for child in children[node]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    next_queue.append(child)
        queue = next_queue

    return groups


# ---------------------------------------------------------------------------
# Workflow builder (extended with validation)
# ---------------------------------------------------------------------------


def build_workflow(mission: MissionSpec, experts: list[str]) -> list[WorkflowStage]:
    """Build and validate the mission workflow DAG."""
    del experts
    stages = [
        WorkflowStage(
            id="mission_intake",
            owner="Supermix_29",
            description=(
                "Decompose mission objectives into environment, biology, safety, and automation tracks."
            ),
            inputs=["mission spec"],
            outputs=["mission graph", "expert allocation"],
        ),
        WorkflowStage(
            id="habitat_simulation",
            owner="didactic-lamp",
            description=(
                f"Construct a digital twin for {mission.environment.name} with stressors, resource gradients, and failure envelopes."
            ),
            inputs=["mission graph", "environment spec"],
            outputs=["habitat profile", "stress map"],
            dependencies=["mission_intake"],
        ),
        WorkflowStage(
            id="consortium_synthesis",
            owner="Supermix_29",
            description=(
                "Select safe organism or living-material archetypes and assign division-of-labor strategies."
            ),
            inputs=["mission graph", "stress map"],
            outputs=["candidate archetypes", "role allocation"],
            dependencies=["habitat_simulation"],
        ),
        WorkflowStage(
            id="genome_architecture",
            owner="evo2",
            description=(
                "Score long-range genome architecture concepts and non-actionable edit classes against environmental demands."
            ),
            inputs=["candidate archetypes", "stress map"],
            outputs=["genome concepts", "robustness envelope"],
            dependencies=["consortium_synthesis"],
        ),
        WorkflowStage(
            id="regulatory_programming",
            owner="DNA-Diffusion / enhancer stack",
            description=(
                "Plan promoter-enhancer-response programs for stress adaptation without emitting sequence-level artifacts."
            ),
            inputs=["genome concepts", "objective targets"],
            outputs=["regulatory motifs", "control logic"],
            dependencies=["genome_architecture"],
        ),
        WorkflowStage(
            id="molecular_interface_design",
            owner="AlphaFold3 / RoseTTAFold / peptide models",
            description=(
                "Evaluate high-level protein, peptide, and binder interface concepts for mission utility and manufacturability."
            ),
            inputs=["regulatory motifs", "candidate archetypes"],
            outputs=["interface concepts", "interaction hypotheses"],
            dependencies=["regulatory_programming"],
        ),
        WorkflowStage(
            id="phenotype_projection",
            owner="CellFM / EpiAgent",
            description=(
                "Project likely cell-state behavior and failure modes under the simulated habitat."
            ),
            inputs=["control logic", "interaction hypotheses", "stress map"],
            outputs=["phenotype forecast", "instability flags"],
            dependencies=["molecular_interface_design"],
        ),
        WorkflowStage(
            id="robustness_sweep",
            owner="Monte Carlo Engine",
            description=(
                "Run perturbation-based sensitivity analysis across environmental uncertainty axes."
            ),
            inputs=["phenotype forecast", "habitat profile"],
            outputs=["robustness envelope", "sensitivity vectors"],
            dependencies=["phenotype_projection", "habitat_simulation"],
        ),
        WorkflowStage(
            id="editor_strategy",
            owner="OpenCRISPR / Protein2PAM",
            description=(
                "Attach only abstract editor classes and safety envelopes needed for future implementation work."
            ),
            inputs=["genome concepts", "instability flags"],
            outputs=["editor classes", "editor safety notes"],
            dependencies=["robustness_sweep"],
        ),
        WorkflowStage(
            id="workflow_materialization",
            owner="nexusflow",
            description=(
                "Compile the full search, simulation, scoring, and review plan into a reproducible execution graph."
            ),
            inputs=["all upstream outputs"],
            outputs=["workflow graph", "review gates"],
            dependencies=["editor_strategy"],
        ),
        WorkflowStage(
            id="dossier_export",
            owner="OmniForge",
            description=(
                "Rank candidates, attach evidence channels, and export a machine-readable design dossier."
            ),
            inputs=["workflow graph", "review gates"],
            outputs=["candidate dossier", "topline report"],
            dependencies=["workflow_materialization"],
        ),
    ]

    errors = validate_dag(stages)
    if errors:
        raise ValueError("Workflow DAG validation failed: " + "; ".join(errors))

    return stages
