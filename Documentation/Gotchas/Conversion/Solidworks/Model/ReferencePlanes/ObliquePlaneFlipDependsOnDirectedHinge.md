# An oblique plane's flip depends on its actual directed hinge

Expectation: selecting the Front/Right or Front/Top planes as an undirected hinge would make a positive angular scalar produce the desired signed source tilt. The original disclosed oblique-cylinder prediction used that assumption.

Actual behavior on the pinned SOLIDWORKS 2026 build: the native axis constructor retains two ordered plane references, and the plane-intersection helper uses the first normal crossed with the second. The disclosed original attempt exposed directed hinges `-Y` and `+X`; positive unflipped angles then produced positive-Z plane normals, opposite the original prediction. Its dynamic output call failed before mass/save/edit/reopen, so this remains controlled partial source evidence.

The exact native angle branch reads the positive angle geometry and negates it when reverse is set. Use the real hinge, base normal and desired normal to calculate `atan2(u·(n×m), n·m)`. Pass its magnitude and set reverse only for a negative rotation. Check the real directed hinge before angular construction and the signed plane normal afterward; undirected line checks alone lose the distinction. Do not silently rewrite the earlier prediction or infer serialized reference-role order from `GetParents` alone.

The [source/evidence record](../../../../../../re/solidworks/records/FreecadObliqueCylinderSign2026.md) pins the code, preserves the failure and defines a separate disclosed positive/negative flip pair. Its [receipt](../../../../../../re/solidworks/measurements/2026/FreecadObliqueCylinderSign01.json) reports static/host verification only. Skew/projected/degenerate hinges and native acceptance remain separate gates.
