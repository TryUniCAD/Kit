# Typed ordinary SOLIDWORKS polygon reading

The public reader now projects an ordinary unconstrained SOLIDWORKS 2026 polygon from its actual typed sketch point, line and handle owners.
It preserves each line's permanent native marker, exact endpoints, one connected closed loop and source metadata, and computes prism bounds from those vertices.
Owned vertices no longer become duplicate primitives or malformed curves through the legacy marker scanner.

The change is automatic for the qualified version-19000 schema-one branch.
Dimensions, mixed curves, construction or external entities, additional reference points, multiple loops and unproven owner states retain the previous reader path.
No public schema, writer registration or broad writer qualification changes.

The [reader guide](../../../../Reference/Research/Solidworks/Sketches/TypedLineLoops.md) describes identities, metadata and scope.
The [format record](../../../../../re/solidworks/records/TypedLineLoops2026.md) binds native field rules and the [sanitized receipt](../../../../../re/solidworks/measurements/2026/TypedLineLoopsSdk01.json).
The final copied-source replay passed 40 fresh processes, three new independent neutral designs, five rejection controls, namespace/order/extension checks, four exact disclosed native-file reads and the existing geometry/presentation regressions.
Static format, naming/steering, Ruff, strict Mypy, Pyright and donor checks passed within the recorded scope.
This task performed no new native or held-out execution.
