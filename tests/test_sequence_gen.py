"""Tests for the DNA Language Model proxy sequence generation."""

import pytest
from habitat_genome_compiler.models import CandidateProgram
from habitat_genome_compiler.sequence_gen import generate_sequences

@pytest.fixture
def base_candidate() -> CandidateProgram:
    return CandidateProgram(
        id="c1",
        title="DNA Tester",
        summary="",
        archetype="single-chassis microbial factory",
        modules=["extreme-environment hardening", "payload synthesis"],
        rationale=[],
        risks=[],
        scores={},
        evidence_channels=[]
    )

def test_generate_sequences_format(base_candidate):
    seq = generate_sequences(base_candidate)
    assert len(seq) > 50
    # Must only contain A, T, C, G, N
    valid_chars = set("ATGCN")
    assert all(base in valid_chars for base in seq)

def test_gc_bias(base_candidate):
    seq = generate_sequences(base_candidate)
    gc_count = seq.count("G") + seq.count("C")
    gc_ratio = gc_count / len(seq)
    
    # Extreme environment hardening module should trigger high GC ~80%
    assert gc_ratio > 0.50

def test_determinism(base_candidate):
    seq1 = generate_sequences(base_candidate)
    seq2 = generate_sequences(base_candidate)
    assert seq1 == seq2
