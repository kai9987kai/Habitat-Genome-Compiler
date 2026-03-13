# Research-grounded mission builder upgrades

This document records the external papers used to shape the mission-spec generator and GUI builder added in March 2026.

## Applied sources

- `Digital Twins for Bioprocess Control Strategy Development and Realisation`
  - Link: https://pubmed.ncbi.nlm.nih.gov/33215237/
  - Applied in code: builder-generated missions now add observability and control-loop objectives for closed-loop process missions.

- `Long-term homeostasis of synthetic microbial consortia through auxotrophic division of labor`
  - Link: https://www.nature.com/articles/s41467-025-57022-3
  - Applied in code: multi-stressor and consortium-biased missions now add community-balance objectives and stability constraints.

- `Cas9-assisted biological containment for safe deployment of engineered microbes in environments`
  - Link: https://www.nature.com/articles/s41587-024-02277-7
  - Applied in code: non-trivial safety profiles now default to layered containment language, telemetry, and genetic-firewall style guardrails.

- `Cyanobacteria as candidates to support Mars colonization: growth, biofertilization and biomining capacity using Mars regolith as a resource`
  - Link: https://pubmed.ncbi.nlm.nih.gov/35710677/
  - Applied in code: offworld and regolith-linked missions now add nutrient-recycle and resource-loop objectives.

## Product impact

- Added a mission JSON generator so users can create valid safe mission specs through the GUI.
- Expanded the preset library with more industrial, water, climate, and offworld examples.
- Fed builder outputs back into routing and tagging so the compiler responds to telemetry, regolith, and community-stability intent.
