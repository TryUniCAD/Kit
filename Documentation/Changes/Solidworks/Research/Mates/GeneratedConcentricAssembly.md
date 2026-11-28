# Generated concentric assembly research

The neutral research constructor writes a cylinder part and its parent assembly with one concentric mate. It binds the two selections to the actual generated lateral face, support snapshots, occurrence transforms, fixed anchor and rotation lock. It serializes the three linked assembly streams through the shared SDK archive maps.

Run the guarded replay with `python -B -m para.concentric.CheckConcentricAssembly INPUT.json --case 1` after adding `src`, `re/tooling/sw2026`, `re/tooling/sw2026/serial` and the repository root to `PYTHONPATH`. Use the [feature-only document](../../../../../re/solidworks/inputs/ConcentricFeatureNeutral01.json) with case 1 or the [authored B-rep document](../../../../../re/solidworks/inputs/ConcentricBrepNeutral01.json) with case 2. Each portable document contains the actual owned child. Use `--native-destination` and an unused `--output` directory to retain the two candidates at their intended sibling identities.

Four guarded processes round-trip Config-0, ResolvedFeatures and MatesList with zero runtime inputs, verify occurrence and anchor order, and reject foreign face selections. The separate admission proof covers 45 processes including 31 refusals. The generated state remains pre-solve. SOLIDWORKS validation and public writer qualification remain pending.

[Construction rules](../../../../../re/solidworks/records/GeneratedConcentricAssembly2026.md) · [Process receipt](../../../../../re/solidworks/measurements/2026/GeneratedConcentricAssembly01.json)
