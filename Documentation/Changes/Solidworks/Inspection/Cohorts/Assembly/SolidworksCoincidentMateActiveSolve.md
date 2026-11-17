# Measure coincident mate correction from a displaced start

The SOLIDWORKS 2026 research probe freezes a generated assembly with one aligned Top Plane mate and a floating occurrence initially displaced by `0.00473 m` along the plane normal. It verifies the stored occurrence and endpoint frames through the typed archive reader, then measures the first native pose and the pose after an explicit rebuild. It requires exact ordered plane identities, independent transforms and geometry, and healthy A17 brackets.

Use the probe's `prepare` command with the frozen generator reports and its `run` command in the pinned native oracle. The generated files and both native controls stay read-only.

The first post-open pose had zero plane offset. The explicit rebuild preserved the solved pose, both exact native plane references and two bodies. Three isolated SOLIDWORKS processes passed cleanly, including both A17 controls. Persistence from the displaced start remains unmeasured.

[Off-plane trial protocol](../../../../../../re/solidworks/records/CoincidentMateActiveSolve2026.md) · [Native receipt](../../../../../../re/solidworks/measurements/2026/GeneratedCoincidentMateActiveSolve01.json)
