# Shared owners for seven geometry archive helpers

The research serializer now has one authoritative owner for seven embedded geometry grammars.
The new `defs/Geometry.py` translates their actual SOLIDWORKS 2026 native readers and matching ordinary save paths.
It preserves existing field names and keeps strict schema admission unchanged.

The owned helpers are matrix restore, three-dimensional point/vector restore, two-dimensional point restore, point archive input, and both transform input forms.
Point/vector coordinates remain doubles.
The two-dimensional point grammar contains two doubles; runtime z clearing adds no stored field.
The compact transform and 30-word transform operator remain distinct grammars.
Projection payloads continue through their existing independently scoped schemas.

The [native format record](../../../../re/solidworks/records/GeometryArchive2026.md) records binary identities, complete function hashes, field order and dispatch.
It also records matrix reconstruction, transform scale repair and native save fixups.
Those runtime operations do not replace preserved wire values or supply fresh-writer defaults.

## Registration and use

The registry loads `Geometry` after `Definition` and before the later resolved modules.
Its definitions replace only the seven provisional declarations with matching identifiers.
Later provisional declarations cannot change the active fields.
The compact transform keeps `f08/f58/f60/f68/f70/f78/f80` rather than later alias names.
The separate operator keeps `words[].w` and optional `persp`.

Run existing source round-trip process checks remotely with `--require-proven`.
Keep every other used provisional or missing schema blocking admission.
This change modifies neither the admission rules nor the round-trip and field-inventory tools.
See the [field-name gotcha](../../../Gotchas/Conversion/Solidworks/ProvisionalTransformFieldNames.md)
and [schema usage limits](../../../Gotchas/Conversion/Solidworks/Archive/ProvisionalSchemasDoNotProveClosure.md).

## Actual verification and limits

The worker inspected pinned 2026 DLLs, exports, imports and complete function bodies without executing vendor code.
The geometry module hash matches the committed 2026 binary manifest.
Source/AST inspection established registration order and field-name compatibility.
No local product, codec, schema, registry or test execution occurred.
Held-out native payloads, the VM, CAD processes and licensing remained untouched.

The pre-change remote reports covered 208 ordinary and 26 linked stream comparisons across 26 prepared source fixtures.
Every comparison was byte-identical with zero unread tail.
Strict admission still failed because those reports used 77 and 75 provisional schema names respectively.
The seven helpers owned here are a subset, leaving 70 and 68 other pre-change names for independent verification.
The [post-change source-parser receipt](../../../../re/solidworks/measurements/2026/CurveDiscoveryAdmission42525.json)
binds source `42525e342ee326eebb2b2be87aeb87cfaff2a71b` to its actual synthetic
candidate, retained reports and prepared manifest. All 234 comparisons remain
byte-identical with zero tails. After all 76 shared owners in that revision,
only `su_CMapStringToInt` remains actually used and provisional, with no missing
schemas. Strict admission passes 156 primary streams and zero linked streams;
both strict process cases still fail. This is source-parser evidence, not new
field classifications, generated curves or native rebuild/edit acceptance.

These are source-grammar instruments, not generated curve parts or production writer acceptance.
Fresh construction rules, complete field classification and controlled held-out native measurements remain unfinished.
The [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md) state:
“The first is success under every criterion on this page.”
They also state: “The second is the end of the available context.”
This bounded schema addition does not close that goal.
