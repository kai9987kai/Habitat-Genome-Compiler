# Research Foundations

This document ties the repo architecture to the primary papers that motivated it.

## Core thesis

The strongest version of the project is not a single model. It is a mission compiler that joins environment simulation, genome-scale reasoning, regulatory control, phenotype forecasting, molecular interface design, and workflow orchestration.

## Paper-to-stage mapping

### 1. Genome architecture

- [Evo 2, Nature, March 4 2026](https://www.nature.com/articles/s41586-026-10176-5)
- Role in repo: `planner.py` stage `genome_architecture`, surfaced through `evo2`.
- Why it matters: long-range genomic context makes whole-program architecture plausible instead of treating design as isolated motifs.

### 2. Regulatory DNA design

- [Designing synthetic regulatory elements using DNA-Diffusion, Nature Genetics, December 23 2025](https://www.nature.com/articles/s41588-025-02441-6)
- [Machine-guided design of cell-type-targeting cis-regulatory elements, Nature, October 23 2024](https://www.nature.com/articles/s41586-024-08070-z)
- [Cell-type-directed design of synthetic enhancers, Nature, January 17 2024](https://www.nature.com/articles/s41586-023-06936-2)
- Role in repo: `planner.py` stage `regulatory_programming`.
- Why it matters: the system can reason about control logic, not only payload genes.

### 3. Cell-state and phenotype projection

- [EpiAgent, Nature Methods, September 25 2025](https://www.nature.com/articles/s41592-025-02822-z)
- [CellFM, Nature Communications, May 20 2025](https://www.nature.com/articles/s41467-025-59926-5)
- Role in repo: `planner.py` stage `phenotype_projection`.
- Why it matters: phenotype becomes a scoring layer rather than a post hoc guess.

### 4. Protein, peptide, and interface reasoning

- [AlphaFold 3, Nature, May 8 2024](https://www.nature.com/articles/s41586-024-07487-w)
- [RoseTTAFold All-Atom, Science, April 19 2024](https://pubmed.ncbi.nlm.nih.gov/38452047/)
- [Target sequence-conditioned design of peptide binders using masked language modeling, Nature Biotechnology, August 13 2025](https://www.nature.com/articles/s41587-025-02761-2)
- Role in repo: `planner.py` stage `molecular_interface_design`.
- Why it matters: design spans beyond enzymes into complexes and binding interfaces.

### 5. Editor selection and safety envelopes

- [Customizing CRISPR-Cas PAM specificity with protein language models, Nature Biotechnology, February 2 2026](https://www.nature.com/articles/s41587-025-02995-0)
- [Design of highly functional genome editors by modelling CRISPR-Cas sequences, Nature, July 30 2025](https://www.nature.com/articles/s41586-025-09298-z)
- Role in repo: `planner.py` stage `editor_strategy`.
- Why it matters: future versions should co-design the editor class with the program, not assume a fixed editor.

### 6. Autonomous research loop

- [SAMPLE self-driving protein lab, Nature Chemical Engineering, January 11 2024](https://www.nature.com/articles/s44286-023-00002-4)
- [Agent Laboratory, Findings of EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.320/)
- Role in repo: `cli.py`, `api.py`, and the workflow materialization step.
- Why it matters: the frontier is an iterative design-test-learn loop, not a one-shot model invocation.

### 7. Biosafety and containment engineering

- Biocontainment of genetically modified organisms by synthetic protein design, Nature, 2015
- A robust yeast biocontainment system with two-layered regulation switch dependent on unnatural amino acid, Nature Communications, 2023
- Engineering stringent genetic biocontainment of yeast with a protein stability switch, Nature Communications, 2024
- Synthetic biological containment by programmed cleavage of horizontal gene transfer, Nature Communications, 2024
- Ser/Leu-swapped cell-free translation system generates a genetic firewall for biocontained engineered bacteria, Nature Communications, 2024
- NIH Guidelines for Research Involving Recombinant or Synthetic Nucleic Acid Molecules, revised April 4 2024
- Role in repo: `biosafety.py` and `xenobiology.py`.
- Why it matters: the stronger pattern is layered containment, not a single kill switch. The repo should score explicit safeguard layers, require stronger barriers for open deployment, and recommend HGT-resistant or orthogonal execution paths when escape pressure is high.

## Repo mapping assumptions

- `Supermix_29`: expert routing and orchestration logic.
- `OmniForge`: operational shell, API surface, observability, and dossier export.
- `nexusflow`: workflow graph materialization.
- `didactic-lamp`: simulation or world-model substrate.
- `evo2`: long-context genome reasoning.

The current code treats `nexusflow` and `didactic-lamp` as architectural roles because this repo is a fresh scaffold, not a checked-out integration workspace.
