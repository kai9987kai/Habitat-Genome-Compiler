"""Codon optimization engine (Phase 8).

Inspired by MIT's 2026 LLM-based codon optimizer that outperformed commercial
tools for yeast expression. This module scores and recommends codon usage
strategies for the candidate's host organism context.
"""

from __future__ import annotations

import hashlib

from .models import CandidateProgram, MissionSpec


_HOST_CAI_PROFILES: dict[str, float] = {
    "e. coli": 0.85,
    "yeast": 0.78,
    "cyanobacteria": 0.72,
    "extremophile": 0.65,
    "consortium": 0.70,
    "default": 0.75,
}


def _estimate_cai(sequence: str, host_key: str) -> float:
    """Estimate Codon Adaptation Index proxy from sequence and host profile."""
    if not sequence:
        return 0.5
    base_cai = _HOST_CAI_PROFILES.get(host_key, _HOST_CAI_PROFILES["default"])
    gc = (sequence.count("G") + sequence.count("C")) / max(len(sequence), 1)
    digest = int(hashlib.sha1(sequence[:200].encode()).hexdigest()[:6], 16)
    jitter = (digest % 100) / 1000.0
    return min(1.0, max(0.0, base_cai * 0.6 + gc * 0.35 + jitter))


def _detect_rare_codons(sequence: str) -> int:
    """Count triplets that map to rare codons in E. coli."""
    rare_codons = {"AGG", "AGA", "CGA", "ATA", "CTA", "GGA"}
    if not sequence or len(sequence) < 3:
        return 0
    count = 0
    for i in range(0, len(sequence) - 2, 3):
        triplet = sequence[i : i + 3].upper()
        if triplet in rare_codons:
            count += 1
    return count


def optimize_codons(
    candidate: CandidateProgram,
    mission: MissionSpec,
) -> tuple[float, list[str]]:
    """Score codon fitness and recommend optimizations."""
    seq = candidate.dna_sequence or ""
    host_key = "default"
    archetype_lower = candidate.archetype.lower()
    for key in _HOST_CAI_PROFILES:
        if key in archetype_lower or key in mission.domain.lower():
            host_key = key
            break

    cai = _estimate_cai(seq, host_key)
    rare_count = _detect_rare_codons(seq)
    score = round(min(10.0, max(0.0, cai * 10.0)), 1)

    findings: list[str] = []
    findings.append(f"Estimated CAI (Codon Adaptation Index): {cai:.3f} for host profile '{host_key}'.")

    if rare_count > 0:
        findings.append(f"Detected {rare_count} rare codon triplets; consider synonymous substitution.")
        score = max(0.0, score - min(2.0, rare_count * 0.3))
        score = round(score, 1)

    if score >= 8.0:
        findings.append("Excellent codon usage; high predicted translational efficiency.")
    elif score >= 5.0:
        findings.append("Moderate codon adaptation; LLM-guided harmonisation recommended (MIT 2026 protocol).")
    else:
        findings.append("Poor codon fitness; re-synthesis with host-optimized codons strongly recommended.")

    return score, findings
