# Controlled annulus and capsule source preflight

The [binding-aware source preflight](../../../../../re/solidworks/measurements/2026/CurveSourceBindingPreflight09.json)
passed ten fresh SOLIDWORKS 2026 SP05.2 phases and all 121 numeric checks.
Both independent controls passed before and after the annulus and tangent capsule.
All sixteen completed snapshots contain one solid body and the same 25-node
feature tree, without feature errors, warnings, suppression, invalid relations,
dialogs or cleanup errors.

The annulus's two fixed-relation requests refer to the same native point
`[0, 2]`, through distinct arc identities `[0, 1]` and `[1, 2]`.
One retained fixed relation satisfies both exact bindings after authoring,
fresh reopening and a driving inner-radius edit.
This confirms shared identity in this run; it does not supply the missing request
IDs from the original failed attempt.
The capsule retains its shared endpoints, tangent relations and distinct line/arc
namespaces through its driving radius edit.
The [relation gotcha](../../../../Gotchas/Conversion/Solidworks/Tracing/SharedSketchPointsCanReuseRelations.md)
preserves these evidence boundaries.

The annulus edit changed volume from `1.6162633878677136e-5` to
`1.6948407098658675e-5` cubic metres.
The capsule edit changed it from `4.795442392117491e-6` to
`5.44168725039073e-6` cubic metres.
Independent neutral formulas pass all eighty mass-property comparisons at the
unchanged tolerances. Original source hashes remain unchanged.
Edited dimensions were rebuilt and measured, then discarded without saving.
No edited-file save or subsequent fresh reopening was measured here.

The committed author source is `4ed467bc94a9e7da00bc9782a603a525250242cd`.
The host supervisor observed natural transport exit `2` in `269.309277084`
seconds. That exit correctly refuses a full lock for this two-of-thirty subset;
it is not a failed numeric check or a deadline exercise.
The publication retains all numeric checks and complete snapshots with documented
exact-equality references, original hashes and process birth identities.

Verification independently rechecked all 36 original hashes, reconstructed every
snapshot exactly, and compared all 121 numeric checks with their original records.
No local product tests or native file parsing ran during publication.
These are API-authored source documents. They establish neither held-out
generalization nor a Kit-written curve, full source-family lock or production
write capability. The [adapter](../../../../Reference/Adapters/Solidworks.md)
remains read-only.
