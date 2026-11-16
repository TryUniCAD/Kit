# Circle/arc discovery field and identity correlation, SOLIDWORKS 2026

Status: **partial construction knowledge; no generated curve output accepted**

This ledger correlates the 24 discovery cases and two controls in the prepared
curve source corpus. It uses complete linked resolved-feature JSON graphs and
recorded source API observations. It reads no native file, raw stream or held-out
payload and implements no writer. The production adapter remains read-only.

A completed source graph and a coherent cold constructor graph can differ. Such
a difference does not itself reject a research writer candidate. A cold policy
still needs native justification for its inputs and derived state, followed by
held-out generated-output acceptance. Source editing history must not become a
fixed writer table or be treated as mandatory neutral design intent.

## Evidence identity and method

The companion [JSON ledger](CurveDiscoveryFieldCorrelation2026.json) contains
30 field classifications, all 26 case ledgers, object/container JSON pointers,
exact integer/float witnesses, original/prepared native and stream hashes,
source-manifest hashes, registration chains and per-case comparison results.
These are research observations, not writer data or a construction program.

| Input | Identity |
| --- | --- |
| CI source | `b291c4da06406d61059b6a0095d3bbb825ef7ef1` |
| Synthetic CI commit | `63e9c44b81ddeb529970fb251a66bd7bece9381b` |
| Run / job / artifact | `43805235770` / `133094377267` / `14198610885` |
| Linked inventory | `SourceParser/Curve/Fields/LinkedConfig0ResolvedFeatures.json`, 337984279 bytes, SHA-256 `1f93991f73bf6c2393432608bf67912cf3ec8b9152a23f205d241416cc5fe3fb` |
| Prepared manifest | `re/solidworks/v2026/corpus/curves-discovery/Manifest.json`, SHA-256 `83fdec0c415f6b2152d8df6bb12deba1b24313e8580597452505b139ec59a42e` |
| Original source lock | SHA-256 `21da3f3e8a6e2a6fe732f69c377a9539bc26a3ee1111795319b4a95d0124ad25`, source `4ed467bc94a9e7da00bc9782a603a525250242cd` |
| Native model image, as bound by the existing ledgers | SOLIDWORKS 2026 SP05.2, `34.5.2.0604`, `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000` |

The artifact receipt records the archive digest; this task did not reopen or
rehash that archive. All input JSON and cited repository-file hashes are retained
in the companion ledger. Its source implementation inventory is the recorded
FieldScan core/definition list, not a transitive provenance claim for production
package or container imports.

Only explicit JSON references are followed. References are identified by their
`target_id`; node IDs are scoped to one file entry, and aliases are not expanded
into new objects. Embedded entity records
retain their dictionary node IDs and point/segment array positions. Native
encodings come from the existing hash-bound construction ledgers and committed
schema declarations, never from the inventory's Python scalar type. Reported
object record positions are stream-local evidence, not field offsets.

All 26 linked reports are complete, proven-admitted, have zero unresolved
references and have no used provisional or missing schemas. Every selected file,
resolved stream and Config-0 seed hash matches the prepared manifest. This is a
bounded read/correlation result. It does not reassert fresh native acceptance of
the prepared redacted files and does not substitute for writer acceptance.

## Concrete graph and separate namespaces

The owning path is `moProfileFeature_c.pd_f80 -> sgSketch`. The sketch's
`points[i].point` and `arcs[i].arc` are embedded records selected by the verified
ordinary discriminators, not separately class-tagged `sgPoint` or `sgArc` archive
objects. Their dictionary node IDs are JSON graph identities only. Native class
ownership and order follow
[CurvedSketchConstruction2026.md](CurvedSketchConstruction2026.md#active-2026-archive-order).

| Quantity | Owner / path | Meaning |
| --- | --- | --- |
| Point/line/arc array index | `sgSketch.points`, `lines`, `arcs` | Typed topology namespace, used by endpoints, centres and concrete handles |
| Entity creation ID | Embedded `sg2DEnt.f0c` | Independent point/line/arc allocation sequence; not the array position |
| Next creation IDs | `sgSketch.f140.f08/f0c/f10` | Point/line/arc allocator state |
| Permanent segment marker | `sg2DEnt.f08`, next counter `sgSketch.f130` | Shared marker namespace across eligible segment types |
| Value dimension index | `sgSketch.dims.val_g1[j]` and display handle `ff8` | Zero-based registration namespace |
| Dimension persistent ID | `sgCircleDim.f50` | Allocation from the model header |
| Parameter node ID | `moLengthParameter_c.f08` | Separate integer node identity; all observed values here are `-1` |
| Parameter text | `moLengthParameter_c.f18 -> moNodeName_c.f08` | The name object's `f08` is a string, not either ID above |
| Archive reference | Object `archive_origin` and `archive_index` | Archive-map identity with explicit stream provenance |

There are 51 observed active segment bindings and 90 exposed point-role bindings.
Every segment `GetID` pair matches `[typed array position, entity f0c]`; every
recorded point role matches `[point-array position, point f0c]`. This is a
correlation of this source corpus, not an independent native proof of every
public API ID route. All 78 author/reopen/edit binding sets remain identical;
that statement concerns identities, not unchanged edited geometry.

Arc and line IDs overlap. In `D09Arc17Ccw`, both native bindings are `[0,1]`,
but one is an arc (`segment_type=1`) and the other a line (`segment_type=0`).
The capsule repeats that overlap with `[0,1]` and `[1,2]`. Removing concrete
geometry kind would merge distinct objects. Point equality is established by
actual indices/bindings, never equal coordinates.

The source graph contains 90 stored point records, of which 86 pass the native
low-bit live/permanent screen; 36 arcs (24 full circles and 12 distinct-endpoint
arcs); and 16 stored lines, of which 15 pass that screen. The four excluded points
and one line are retained rectangle tombstones, not silently discarded data.
The screen is a bounded flag predicate, not a complete geometry validator.

## Point roles, identities and counters

[Arc permanence](CurvedSketchConstruction2026.md#common-fields-and-point-roles)
uses points in start, end, centre order. Each use increments `point.fe8`; centre
role additionally increments `point.fec`. A circle uses the same endpoint twice.
All 90 stored `fe8` values equal the explicit role sum over the currently
permanent segments, and all 90 `fec` values equal the centre-use sum. This
corroborates the bounded native operations; arbitrary deletion or edit histories
still need their matching removal/update rules.

| Case | Stored point order and creation IDs | Roles / retained state |
| --- | --- | --- |
| Isolated circle (`D01`–`D08`, `D17`, `D18`, control) | Centre index 0 / ID 2; marker index 1 / ID 1; arc index 0 / ID 1 | Centre `fe8=fec=1`, marker `fe4=2, fe8=2, fec=0` |
| Chord-closed arc (`D09`–`D16`, `D24`) | Centre/start/end indices 0/1/2 with IDs 3/1/2 | Arc uses start 1, end 2, centre 0; closing line uses 2 -> 1; endpoint use counts are 2 |
| `D19Annulus` | One centre index 0 / ID 2; markers 1 / ID 1 and 2 / ID 3 | Both arcs use the same centre; centre `fe8=fec=2`, one retained fixed point constraint, two radial dimensions |
| `D22ConstructionArc` | Centre 0 / ID 2, marker 1 / ID 1, construction endpoints 2/3 with IDs 3/4 | Centre `fe8=fec=2`; construction endpoints each have `fe8=1`, no retained adjacency handles; construction arc `f38=2, f54=12, f08=0, fd0=0` |
| `D23TangentCapsule` | Point IDs in array order `[3,1,2,4,6,5]` | Arc 0 uses 1 -> 2 about 0; arc 1 uses 3 -> 5 about 4; lines use 2 -> 3 and 5 -> 1; both arc centres are fixed |
| `ControlRectangle` | Eight stored points, live indices `[0,1,6,7]` with IDs `[1,2,3,4]` | Point indices 2–5 and line index 0 have `f54=5`; the four live lines use indices 1–4 and carry IDs 1–4 |

All 24 full-circle markers lie on local +X in the completed source graphs and
retain one `h1` arc-handle object with `h2=null`. Each radial dimension owns a
*different* arc-handle object targeting that same arc. Equal targets do not imply
identical handle allocations.

The previous construction-ledger assertion of two fresh adjacency clones was
incorrect. The root's independent pinned-2026 static review shows that endpoint
registration deduplicates equivalent handles. Registrar `0x4c5f8460` calls the
existing-equivalent check `0x4c5f8060` at `0x4c5f84d3` and `0x4c5f8556`. Equality
`0x4c5bce10` compares the entity index at `+0x18`, owning sketch at `+0x10`, block
at `+0x1c` and runtime class. Clone `0x4c55eb40` preserves the concrete arc-handle
class and target; other-end lookup `0x4c5c7020` returns the same marker point for
a full circle. The first registration installs `h1`; opposite-point and second
role registration then find the equivalent handle. The bounded ordinary fresh
circle therefore has **one `h1` and null `h2`**, without requiring later cleanup.
Both endpoint roles still independently increment `fe8` through `0x4c602c10`, so
`fe8=2` remains correct. All 24 source observations agree with that static rule.
The [native adjacency record](CircleAdjacencyRegistration2026.md) and its
[hash record](CircleAdjacencyRegistration2026.json) bind 13 function extents and
seven concrete vtable slots to the pinned model image.
Its prerequisites remain mandatory: exact full-circle endpoint identity, a valid
coherent local arc handle and successful registrar admission, nonzero
`sketch+0x128`, fresh empty marker adjacency slots, successful concrete cloning,
and excluded external/construction branches. The companion JSON preserves the
original input-document hash and identifies this superseding correction. This
task reads that native proof as JSON metadata, without rereading native bytes.
Generated-output runtime acceptance remains pending.

Marker placement is a separate question. The native ledger derives a 17-degree
first-free marker for one specific search route.
[CircleMarkerPlacement2026.md](CircleMarkerPlacement2026.md) distinguishes initial
construction, conditional solver replacement and their different failure paths.
The observed +X position does not reveal which public API path or later mutation
produced it. It is not a new default. A coherent cold construction using native
rules remains a candidate for later proof.

All 78 observed next point/line/arc creation counters equal one plus the maximum
observed nonnegative ID in their own namespace. That is a dataset observation;
it must not replace allocation history. The native rule assigns IDs at actual
first permanence. Permanent markers likewise follow allocation events, not a
cross-type array-index formula: the capsule's lines have markers `[3,1]` and its
arcs `[4,2]`.

The insertion-only stamp candidate `1 + live line count + live arc count` matches
24 of 26 saved source states. It predicts 3 for `D22ConstructionArc`, whose
`f56c=4`, and 5 for the rectangle control, whose `f56c=10`. These reject a universal
reconstruction of completed source history. They do not show that neutral input
must retain an omitted authoring history, nor disprove a justified cold stamp.
[ProfileConstruction2026.md](ProfileConstruction2026.md#sketch-update-dataflow)
records separate insertion, solver-coordinate and update increments. Final
stamp/neutral-regeneration policy is still unresolved for a generated family.

## Radial dimensions and reference lifecycle

The 34 registered values comprise 31 radius and three diameter dimensions.
All concrete value objects are `sgCircleDim`, all parameters are independent
`moLengthParameter_c`, and all saved display handles are `moSkDimHandleRadial_c`.
The latter derives from the ValG1 handle in the committed hierarchy; its saved
concrete class should not be conflated with a fresh base-class constructor.

The actual chain for every retained radial annotation is:

```text
sgSketch.dims.val_g1[j].d -> sgCircleDim
  f28 -> moLengthParameter_c
    f18 -> moNodeName_c (f08 = D1, D2, ...)
  h1 -> distinct sgArcHandle (typed arc-array index)
  h2 -> nonnull sgEntHandle (extended index -2)
sgSketch.dims.f118 -> suObList.items[k].o -> moDisplayRadialDim_c
  f850[0].o -> moSkDimHandleRadial_c
    ff0 -> the very same owning sgSketch
    ff8 = j
```

The last reference closes a cycle. It must remain an archive alias, not be expanded
as another sketch. The Config-0 seed and resolved graph retain distinct origins
and one linked map namespace. Per-case seed hashes, map bases/counters and object
origins are recorded. Embedded point/arc dictionary nodes have no archive object
index. Neither array indices nor JSON node IDs substitute for archive indices.
For example, the annulus seed name object `node-4` has Config-0 origin at archive
index 5, while its profile `node-955`, sketch `node-963` and first dimension
`node-1021` have resolved-stream origins at archive indices 183, 185 and 190.
The resolved map base 110 is the recorded seed counter in this case, not a
universal constant. Each case retains its own seed-origin witness.

The native [radial construction rule](CurvedSketchConstruction2026.md#radius-and-diameter-dimension-construction-partial-graph)
computes `r = length(secondPoint - centre)` and selects type 3/value `r` for
radius or type 15/value `2*r` for diameter. Explicit options 9/8 control that
choice; the fallback uses endpoint identity. This is native-backed representation
knowledge, not a value fitted to the radius ladder.

All 34 second geometry handles are real generic objects with wire `idx=0x777f`
and extended `f18=-2`, followed by local block sentinel `f1c=-1`. They are not null,
and are independent of the circle marker's *point-adjacency* `h2=null` field.
The native constraint-count/accessor virtuals visit only the first geometry handle
for this actual dimension class. The optional runtime map uses the `sgValG1Dim`
array namespace and a u16-widened index, not the persistent ID or an archive ID.
This task has no runtime map observation and makes no absence claim from the
serialized graph. See [ArcDimensionReferences2026.md](ArcDimensionReferences2026.md).

Every geometry `f20` equals the incidence of explicit retained logical/value
constraint handles here: 90 point records and 52 segment records, including the
inactive records with zero count. The capsule illustrates why a universal one
would be wrong: its arcs have `f20=4/3`, lines `2/2`, and fixed centres `1/1`.
This agreement is a correlation, not a general replacement for the native
add/remove-reference lifecycle.

All value dimensions have stored `refcount=0`, independently of that geometry
count. Their concrete reference virtuals are no-ops in the bounded native
sequence; private parameter runtime connections have another owner and are not
node IDs. Dimension `f50` values 27–34 and names D1–D8 are observed history, not
ID formulas. The model allocator and collision-aware name registration determine
those values. See [RadialParameterLifecycle2026.md](RadialParameterLifecycle2026.md).

## Authored data, derived state and unresolved policy

The JSON field ledger classifies exact paths with their native evidence and
limits. Its essential separation is:

- **Persistent design intent:** local geometry, topology identities, orientation,
  driving radius/diameter values, relation bindings, parameter names and retained
  annotation presence. Existing native rules explain the specific owners and
  registration operations. They must remain coherent under editing.
- **Derived identity/bookkeeping:** array references, per-type creation IDs,
  permanent markers, geometry-use/reference counts, model dimension IDs and
  archive maps. These require operations on the chosen generated model; they are
  not copied from a source row or conflated with one another.
- **Derived solve, display and history state:** current constraint status/colour,
  contour-admission and adjacency state, update stamps and optional geometry
  caches. Native bounds are known for parts of these lifecycles. No blanket claim
  that they are optional, safely zero, or ordinary selection caches is made.
- **Unclassified or incomplete:** full construction-mode flag domain, arbitrary
  final status/stamp policy, later adjacency mutation, unresolved auxiliary
  fields, radial presentation/selection lifecycle and cache-neutrality rules.
  A constant observation does not close any of these questions.

Current `sgSketch.f12c` is 2 in 15 graphs and 1 in 11; separately saved `f128` is 1
in all 26. Native getters/serializer distinguish them. Neither field is the
neighbouring entity `f38` LineType. Presentation is also not uniformly cache state:
`ff80/SelLeader` is stored although the inspected constructors do not initialize
it. An explicit supported presentation choice or native-proven neutral value is
still required; a saved zero is insufficient evidence.

Neutral-to-API geometry was recomputed independently from millimetre specs,
signed start/sweep angles and the explicit zero-rotation capsule geometry.
Maximum local coordinate residual is `3.469446951953614e-18 m`; maximum radius
residual is `2.6020852139652106e-18 m`. Selected decoded centre/endpoint coordinates
agree exactly with the recorded author snapshot (120 scalar comparisons).
The maximum graph-endpoint radius versus API radius residual and the maximum
parameter versus geometry-derived value residual are each
`6.938893903907228e-18 m`. Host `math.hypot` and trig do not prove bit-identical
vendor math. No new acceptance tolerance or bit-identity claim follows from
these numerical correlations.

## Next evidence and acceptance boundary

The separately assigned native training observer should identify the actual
public authoring route, first permanence/creation allocation, circle marker
writes, adjacency mutations, retained constraint references and update/solve
boundaries. The JSON lists the exact missing questions. This task adds no
observer code and makes no native calls.

Before a writer can be admitted, each chosen cold neutral policy needs explicit
native evidence and generated held-out measurements between healthy controls.
The six held-out native inputs remain unread. Completed source read closure is
not a fresh writer generalization result. Body topology, visual usability,
parameter edits, rebuild diagnostics and all other CAD criteria still apply.

The mandatory stopping conditions remain “success under every criterion on this
page” and “the end of the available context”. This bounded ledger does not
satisfy the full CAD goal.
