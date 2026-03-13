"""DNA Language Model Proxy for synthetic sequence generation."""

import hashlib
import random
from habitat_genome_compiler.models import CandidateProgram

def generate_sequences(candidate: CandidateProgram) -> str:
    """
    Acts as a proxy for a 2025-era GenAI DNA model (e.g., Evo).
    Generates a representative nucleotide sequence based on the selected modules.
    Returns a string of base pairs (A, T, C, G).
    """
    sequence_parts = []
    
    # Generate an origin of replication based on archetype
    if "consortium" in candidate.archetype:
        sequence_parts.append("GATCCTAG" * 5) # Generic placeholder
    elif "phage" in candidate.archetype:
        sequence_parts.append("ATTAAAGTTTG") 
    else:
        sequence_parts.append("GATCGATC")
        
    # Generate synthetic segments for each module deterministically by hashing the module name
    for module in candidate.modules:
        h = int(hashlib.md5(module.encode()).hexdigest()[:8], 16)
        random.seed(h) # Deterministic for consistent UI
        
        # typical module size 100-300 bp in this proxy
        length = random.randint(100, 300)
        bases = ["A", "T", "C", "G"]
        
        # GC bias dependent on module type or arbitrary
        weights = [10, 10, 10, 10]
        if "extreme" in module.lower():
            weights = [5, 5, 20, 20] # high GC for thermal stability
            
        segment = "".join(random.choices(bases, weights=weights, k=length))
        sequence_parts.append(segment)
        
        # Add a synthetic spacer
        sequence_parts.append("NNNN")
        
    full_seq = "".join(sequence_parts)
    return full_seq
