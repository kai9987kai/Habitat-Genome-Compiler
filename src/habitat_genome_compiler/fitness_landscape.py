"""Protein fitness landscape prediction via language-model proxy.

Inspired by 2026-era PLM-guided directed evolution (MULTI-evolve, AlphaProteo)
this module scores each candidate's predicted protein fitness using zero-shot
sequence-likelihood heuristics and epistatic interaction modeling.
"""

from __future__ import annotations

import hashlib
import math

from .models import CandidateProgram


def _pseudo_plm_likelihood(sequence: str) -> float:
    """Hash-based deterministic proxy for a PLM log-likelihood score.

    In production this would call an ESM-2 or ProtTrans checkpoint.
    Here we derive a stable 0-1 score from sequence composition.
    """
    if not sequence:
        return 0.5

    gc = (sequence.count("G") + sequence.count("C")) / max(len(sequence), 1)
    digest = int(hashlib.md5(sequence[:120].encode()).hexdigest()[:8], 16)
    jitter = (digest % 1000) / 10000.0  # 0.0 – 0.1
    return min(1.0, max(0.0, 0.4 + gc * 0.5 + jitter))


def _epistatic_penalty(modules: list[str]) -> float:
    """Penalise module combinations that are likely to have negative epistasis."""
    penalty = 0.0
    lowers = [m.lower() for m in modules]

    conflict_pairs = [
        ("consortium", "single chassis"),
        ("phage", "cell-free"),
        ("living-material", "adaptive gene shuttle"),
    ]
    for a, b in conflict_pairs:
        if any(a in m for m in lowers) and any(b in m for m in lowers):
            penalty += 0.15
    return min(0.4, penalty)


def predict_fitness_landscape(candidate: CandidateProgram) -> tuple[float, list[str]]:
    """Return a 0-10 PLM fitness score and explanatory findings."""
    seq = candidate.dna_sequence or ""
    likelihood = _pseudo_plm_likelihood(seq)
    epistasis = _epistatic_penalty(candidate.modules)
    raw = likelihood - epistasis

    score = round(min(10.0, max(0.0, raw * 10.0)), 1)
    findings: list[str] = []

    if score >= 7.0:
        findings.append("PLM zero-shot likelihood indicates a high-fitness region of sequence space.")
    elif score >= 4.0:
        findings.append("Moderate fitness predicted; directed-evolution cycles recommended.")
    else:
        findings.append("Low predicted fitness; consider sequence redesign or codon harmonisation.")

    if epistasis > 0.0:
        findings.append(
            f"Negative epistatic interaction detected across module boundaries (penalty {epistasis:.2f})."
        )

    findings.append(f"Pseudo-PLM log-likelihood proxy: {likelihood:.3f}.")
    return score, findings
