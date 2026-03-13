# Build Plan

This is the implementation roadmap from the current prototype to a real multiscale mission compiler.

## Phase 0: current state

Implemented in this repo:

- typed mission schema
- biosafety gate
- expert routing
- workflow compiler
- deterministic candidate generation
- candidate scoring
- CLI and HTTP API
- cited research notes

## Phase 1: adapter interfaces

Goal: replace deterministic mock stages with real adapters.

Work:

- add adapter contracts for `didactic-lamp`, `evo2`, `nexusflow`, and `OmniForge`
- persist workflow runs and artifacts
- add structured stage outputs instead of plain strings
- add provenance records for every stage decision

Research basis:

- [Evo 2](https://www.nature.com/articles/s41586-026-10176-5)
- [Agent Laboratory](https://aclanthology.org/2025.findings-emnlp.320/)

## Phase 2: phenotype and regulation stack

Goal: make the middle of the pipeline more than a placeholder.

Work:

- add phenotype critic interfaces backed by CellFM and EpiAgent style models
- add regulatory-program abstractions for enhancer and stress-response control
- make candidate scoring consume explicit uncertainty values

Research basis:

- [EpiAgent](https://www.nature.com/articles/s41592-025-02822-z)
- [CellFM](https://www.nature.com/articles/s41467-025-59926-5)
- [DNA-Diffusion](https://www.nature.com/articles/s41588-025-02441-6)

## Phase 3: molecular interface stack

Goal: connect program concepts to interface-level evidence.

Work:

- attach interface design requests to AlphaFold 3 or RoseTTAFold-style backends
- add peptide/binder proposal tasks
- split feasibility into structural confidence and manufacturing confidence

Research basis:

- [AlphaFold 3](https://www.nature.com/articles/s41586-024-07487-w)
- [RoseTTAFold All-Atom](https://pubmed.ncbi.nlm.nih.gov/38452047/)
- [Peptide binder design with masked language modeling](https://www.nature.com/articles/s41587-025-02761-2)

## Phase 4: closed-loop operations

Goal: turn the compiler into a governed design-test-learn system.

Work:

- store runs in a real database
- expose review gates in a web UI
- add intervention policies and human approvals
- attach external simulators and scoring jobs through OmniForge-style orchestration

Research basis:

- [SAMPLE self-driving protein lab](https://www.nature.com/articles/s44286-023-00002-4)
- [OpenCRISPR / editor design](https://www.nature.com/articles/s41586-025-09298-z)
- [Protein2PAM](https://www.nature.com/articles/s41587-025-02995-0)

## Phase 5: hardening

Work:

- add configuration files and environment-variable support
- add typed persistence and migration strategy
- add integration tests with stubbed adapters
- add benchmark missions and regression scoring
- define refusal policy tests for high-risk biology requests

## Non-goals for this repo

- sequence generation
- pathogen workflows
- wet-lab execution planning
- uncontrolled deployment recommendations
