# Shared sketch points can reuse relation bindings

## Expectation

Each successful fixed-relation request produces a separate retained relation, so a count by relation type proves that every requested center is constrained.

## Actual behavior

On SOLIDWORKS 2026 SP05.2, build `34.5.2.0604`, the first full circle/arc source run passed 18 discovery cases and failed in `D19Annulus` authoring.
Two `AddRelation` requests for fixed type `17` returned relation objects and reported the requested type and one entity each.
The subsequent native enumeration retained one fixed relation whose entity `GetID` result was `[0, 2]`, alongside two type-3 relations whose entity IDs were `[0, 1]` and `[1, 2]`.
The type-count check rejected the source.
Both before and after controls were healthy; the run produced no family lock.

The original phase record SHA-256 is `50306a50216a2914aaf5ff18838a5baee0a03e0faba6c1535e028b70a0730b24`.
The [source-attempt record](../../../../../re/solidworks/measurements/2026/CurveSourceAttempt01.json)
retains the complete attempt outcome and selected failed API sequence with original hashes.
It did not record the center-point IDs supplied to the two requests.
The hypothesis that the concentric circles shared a center point remains unverified by that record.
Equal coordinates and two successful requests do not establish native identity.
This is a source-harness observation, not proof of a malformed Kit-written file or an attributed format crash.

The [2026 constraint enumeration](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swConstraintType_e.html) names the relevant API kinds.
It supplies vocabulary only and does not prove that any requests share entities or normalize into one constraint.

## Workaround

Record each requested and returned relation's exact type and native entity bindings at `AddRelation`.
Use point `GetID` with the actual point interface, and segment `GetType` plus `GetID` to distinguish line and arc namespaces.
Retain endpoint and center bindings with their owning segment identities.
Resolve those sources again after rebuild, saved-copy reopening and driving edits.

When duplicate point requests have the same exact type and native bindings, one matching retained relation can satisfy that repeated intent.
Distinct point IDs require matching constraints on the distinct points.
Do not deduplicate from coordinates, labels or relation counts.
Already shared-point coincidence must be rechecked against current source identities.

Keep wrong/missing bindings, suppression, dangling relations, overdefinition and broken relations as failures.
Write partial observations and per-request matches before raising so failures retain their evidence.
Reject verification jobs without the new binding metadata rather than inferring bindings from old traces.

The [binding change](../../../../Changes/Solidworks/Inspection/SolidworksCurveRelationBindings.md) describes the repaired harness.
Its new behavior still requires controlled annulus and capsule measurements.
The failed full run, original traces and frozen tools remain preserved.
