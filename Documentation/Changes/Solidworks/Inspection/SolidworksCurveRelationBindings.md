# Verify curve-source relations by native entity bindings

The [curve-source authoring harness](../../../../re/tooling/sw2026/AuthorCurves.py) now records and verifies each requested relation's actual native entities.
It replaces relation-type counts with exact type-and-entity matching.
This changes only research source authoring and verification.
It does not implement a curve writer, establish a family lock or promote the read-only SOLIDWORKS adapter.

## Behavior

Each requested relation records a binding schema, its neutral entity labels, native `GetID` values and the actual segment sources for any endpoint or center.
Point bindings require the registered point interface.
Segment bindings include native `GetType` and the corresponding line/arc interface, so identical numeric IDs in different geometry namespaces cannot match.
Requests and partial bindings are written before `AddRelation`.
Returned relation type, entity count, bindings and suppression state are recorded and checked immediately.

The helper supports only the four relation kinds currently authored by the harness: coincident `9`, fixed `17`, tangent `6` and same-length `14`.
The [2026 constraint enumeration](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swConstraintType_e.html) supplies API vocabulary.
It does not prove relation normalization or shared native point identity.

Every rebuild snapshot retains observed relations and per-request verification evidence before a failure can discard the snapshot.
Requests resolve their segment and endpoint/center sources against the current native geometry IDs.
Already shared-point coincidences must still refer to the same native point after reopening and editing.
Equal coordinates never establish identity.

Duplicate point-relation requests with the same exact type and native point bindings may match one retained constraint.
Requests on distinct points still need the matching constraints on those points.
Tangent and same-length segment requests require separate retained matches per request.
Wrong types, wrong entities, missing sources, suppression, dangling relations, overdefinition and broken relations still fail.

Verification jobs require complete native binding metadata and the neutral specification's full relation intent.
Old jobs that contain only labels or relation counts fail closed.
There is no reuse or resume path.
The neutral specifications, geometry tolerances, control sequence, fresh-process ownership and all-30-case lock rule are unchanged.

## Evidence and limits

The first full source run passed 18 discovery cases, then failed during `D19Annulus` authoring because two successful fixed-relation requests were compared with one retained fixed relation.
Both control pairs were healthy and no `Lock.json` was produced.
The [source-attempt publication](../../../../re/solidworks/measurements/2026/CurveSourceAttempt01.json)
retains 43 process lifetimes, all 490 recorded numeric checks and 64 completed one-body snapshots.
Eighteen discovery cases passed, one failed and eleven subsequent cases remained pending.
No held-out native source was generated in this attempt.
The original phase record SHA-256 is `50306a50216a2914aaf5ff18838a5baee0a03e0faba6c1535e028b70a0730b24`.

That record contains a retained fixed relation with `GetID` result `[0, 2]` and two type-3 relations with results `[0, 1]` and `[1, 2]`.
It does not log the requested center-point IDs.
Shared center identity is therefore an inference, not an established explanation of the original failure.
The [installed type-library capture](../../../../re/solidworks/v2026/evidence/RevolveAndConstraintTypeLibrary.json)
independently confirms the four relation codes and the dangling, overdefining and broken filter codes.
The [specific gotcha](../../../Gotchas/Conversion/Solidworks/Tracing/SharedSketchPointsCanReuseRelations.md) preserves this distinction.
The failed source run remains failed and is not an attributed format crash.

The repair has only source inspection, AST and formatting validation before oracle use.
No local product tests, CAD execution or held-out native stream inspection occurred during its implementation.
The oracle owner must commit the tool, stage a new immutable toolset and measure annulus and capsule preflights with controls before starting another full source run.
The older frozen toolset and failed traces remain unchanged.
Only a newly completed, healthy full-family run can create the source lock.
