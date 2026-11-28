# SOLIDWORKS revolved-radius dimension schema

The [shared research dimension codec](../../../../re/tooling/sw2026/serial/defs/ResolvedDims.py) now describes `moRevolvedRadiusDim_c` at effective archive version `19000`.
It reuses `ThreeDRadiusDim_c`, then reads or writes a `moSkDimHandleValG2_c` reference at `f130` and an i32 at `f128`.
The class uses its actual native parent in the shared hierarchy.

A zero-byte callback rejects other effective versions on load and store.
The native reader's older `f128` gate differs from native store behavior.
This narrow guard prevents an unsupported old-format encoding claim.
The [format record](../../../../re/solidworks/records/RevolvedRadiusDimensionArchive2026.md) gives module and function hashes, field order, gates, and the declared-reference closure.

Use the existing [research archive workflow](../../../../re/tooling/sw2026/serial/README.md).
Its ordinary non-DB scope remains in effect.
Existing dimension, handle, and wire-preservation definitions are unchanged.
No field default, constructor, fresh builder, or production writer is added.

Verification is limited to Python AST parsing and static source comparison.
No local tests, schema execution, native files, or held-out streams were used.
Remote CI, class-specific round trips, actual case reachability, field domains, nullability, and construction rules remain pending.
The future revolve family must be locked before fresh writer construction.
The [SOLIDWORKS adapter](../../../Reference/Adapters/Solidworks.md) remains read-only.
