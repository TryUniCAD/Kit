# Generate an ordinary aligned planar distance mate in research

The SOLIDWORKS 2026 research composer generates one driving distance mate between two aligned principal planes on ordinary occurrences of a generated child. Supply `distance_m` on the mate and explicit `design_intent` and `selected_leader` in the assembly presentation. The ordered plane selections must have positive signed separation. The driving value can differ from that starting separation.

The shared dimension constructor binds a length parameter named `D1` and reserves its dimension ID before registering the mate. The composer allocates the resolved wrapper IDs, records the mate once in each header, and publishes the active configuration's allocator state. Run `DistanceMateBundleProcess.py` with an authored bundle on stdin to generate and inspect the assembly and its child.

The guarded discovery build round-tripped six logical streams with zero runtime access attempts. Changing the driving length changed only the assembly's MatesList stream. Four pre-change coincident and parallel reports, including both XML metadata modes, reproduced the same assembly and child bytes after integration. The constructor presentation and the native distance edit, rebuild, save and reopen still require measurement.

[Native field and allocation rules](../../../../../../re/solidworks/records/PlanarDistanceMateConstruction2026.md) · [Guarded generator](../../../../../../re/tooling/sw2026/DistanceMateBundleProcess.py) · [Discovery receipt](../../../../../../re/solidworks/measurements/2026/GeneratedDistanceMateBundle01.json)
