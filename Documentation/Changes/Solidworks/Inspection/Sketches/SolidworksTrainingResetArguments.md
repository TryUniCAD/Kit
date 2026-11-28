# Explicit training reset arguments

The controlled `d5f9` run activated all 36 observation hooks and measured healthy native controls on both sides.
It reached zero circle cases.
A bare reset received Frida's trailing null payload as its first argument.
The strict Boolean guard rejected that value before case authoring.

[AuthorRadialTraining.py](../../../../../re/tooling/tupni/AuthorRadialTraining.py) now passes True at its two capture-enable/reset calls.
Its four explicit False calls pause capture and clear tracking before controlled closes and control measurements.
JavaScript validation, native hook locations, qualification checks, input locks, and the action lifecycle remain unchanged.

The [specific gotcha](../../../../Gotchas/Conversion/Solidworks/Tracing/RpcDefaultsNeedExplicitArguments.md) traces the installed Frida 17.26.3 Python wrapper and version-pinned runtime dispatcher and sinks.
It explains why a JavaScript default does not replace the first null value.

[The evidence record](../../../../../re/solidworks/records/TrainingRpcBinding2026.json) binds the installed Python source hash and two immutable run reports.
Observation SHA-256 is `1d3c019da038d43e75efcaa9d553c57c9eedf3bffee9a3bf5ed4ceb41657a28a`.
Training-result SHA-256 is `bb0d45dbd3f31254934c90ba76060dc9b6106173feb48d07c0b3353cdaefe95f`.
The [controlled publication](../../../../../re/solidworks/measurements/2026/RadialTrainingAuthor02.json) records both healthy controls, the failure, source bindings, cleanup, and process inventory.
All original records remain unchanged.
Hook activation and control health establish no training coverage or generated-output acceptance.

Source, AST, and documentation checks passed without running the action or a local test.
Use a new committed source and unused output for the next owner-controlled run.
Repair validation, circle observations, field closure, and generated-output acceptance remain pending.
