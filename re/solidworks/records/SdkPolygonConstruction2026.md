# SDK ordinary polygon geometry construction

Task `B04-SW2026-CONSTRUCTION`, owner `/root/flag_ownership`, delivery PR #121.
This tranche owns new `Archive/Construction/Sketch` modules and their separate
generated-build and SDK-prepare process checks. It changes no shared research
builder, prior frozen construction module, archive layout or public adapter.

Status: the bounded source/process construction proof passes on frozen
`Overlay03`. This is not native acceptance or public writer qualification.

The bounded exit condition is a complete ordinary local `sgSketch` ring graph,
with actual point/line owners, adjacency, indices and constructor managers,
serialized and independently prepared through the linked SDK codecs.
Full part synthesis, public writer registration, new native acceptance and
held-out qualification remain outside this component's evidence.

## Evidence and construction boundary

The rules reuse [polygon construction](PolygonConstruction2026.md),
[profile construction](ProfileConstruction2026.md), the
[model-to-sketch transform](ProfileTransformDirection2026.md) and the
[current resolved field grammar](ResolvedBodyGrammar2026.md).
Model addresses refer to `sldmodu.dll` SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`,
preferred base `0x4b140000`. The line-width constructor is bound separately to
the exact 2026 framework image in
[LineWidthConstructor2026.json](../v2026/evidence/LineWidthConstructor2026.json).
This tranche adds no binary extraction, native observation or sealed input.

The production constructors use only standard-library values, `ArchiveNode`
and `RuntimeClass`. They read no files and import no research module, CAD
runtime or oracle. No captured field program, byte array or default row is
present. The existing SDK field grammar owns wire order, conditional widths,
object tags, array lengths and archive maps.

`PolygonInput` accepts ordered local XY coordinates in metres and version 19000. Its exact rational validation operates on the binary64 coordinates that
will be emitted. It preserves coordinate and vertex order. Duplicate closure
vertices, nonfinite or Boolean coordinates, zero area, adjacent backtracking,
nonadjacent contact and self-intersection reject before construction.
The bound of ten million vertices is the existing SDK repeat-safety policy,
within the native signed array-index domain. It is not a discovered vendor
geometry limit. The AVL sweep preserves the existing published research
algorithm and avoids an all-pairs intersection scan.

`MakePolygon` takes that input and an actual allocated, concrete schema-one
`moProfileFeature_c`. The caller supplies the `moCompRefPlane_c`, complete
profile fields and model-to-sketch frame. The selected path requires ordinary
unshared profile state `f3dc=0` and null `pd_f110`. Origin and derived profiles
are rejected. An external-class placeholder cannot substitute for a concrete
runtime class.

The returned `PolygonGraph` retains the new sketch and immutable point/line
orders. The caller attaches `SketchValue` to its profile's `pd_f80`. The
sketch's `f138` is the same actual profile object. This API neither constructs
nor changes the profile, plane wrapper or frame. It synthesizes local geometry,
so validating world placement remains the profile/frame owner's responsibility.
See the [transform-direction gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ProfileTransformStoresModelToSketch.md).

`f138` is a constructor/runtime backlink in the selected ordinary linked mode.
The sketch grammar serializes that reference only with nonzero `ctx874`.
The current linked SDK context defaults that flag to zero, so readback must
follow the serialized profile `pd_f80` reference instead. Feature `owner` is also
constructor metadata; the actual serialized model reference is reached through
profile `pd_f78`, its component reference `f58`, and component `owner`.
The [context gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Construction/SketchBacklinksDependOnArchiveContext.md)
records the checker failure that exposed this distinction.

## Geometry, ownership and namespaces

For `n` vertices, point `i` is the authored position and line `i` joins point
`i` to point `(i+1) mod n`. No origin, construction line, dimension or relation
is invented. The selected input describes an unconstrained polygon only.
Future source dimensions or relations require their own complete construction.

| Field or relationship                    | Classification and rule                                                                                    | Native provenance                                                           |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Point `pos.x/pos.y`                      | Input: finite local binary64 coordinates in caller order                                                   | Point setter `0x4c601d10`, point serializer `0x4c58f910`                    |
| Point record `kind`, line record `flags` | Native selected vocabulary: both zero for ordinary points and plain lines                                  | Point creation `0x4c68ffb0`, sketch serializer `0x4c5916f0`                 |
| Line `fc8/fcc`                           | Derived: actual ordered start/end point-array indices                                                      | Add line `0x4c49cc30`, setters `0x4c44f1b0/0x4c44f010`, lookup `0x4c5fba60` |
| Line `fc8_s/fcc_s`                       | Derived: `min(index,0xffff)`; the shared serializer emits an i32 extension at the marker                   | Segment serializer `0x4c590920`                                             |
| Point/line `f0c`                         | Derived: independent creation sequences `i+1`, each starting at one                                        | Assignment `0x4c3e2450`, allocator `0x4c3e3030`                             |
| Point `f08`                              | Constructor state: zero permanent marker on this path                                                      | Entity constructor `0x4c3e1030`                                             |
| Line `f08`                               | Derived: separately assigned permanent marker `i+1`                                                        | Allocator `0x4c4bb590`, permanence walk `0x4c0cd540`                        |
| Point `h1/h2`                            | Derived actual incident-line handles: point zero uses lines zero and `n-1`; point `i>0` uses `i-1` and `i` | Insertion `0x4c5f7e40/0x4c5f8460`                                           |
| Point `fe8`                              | Derived degree two from its two actual incident lines                                                      | Use registration `0x4c602c10/0x4c490b80`                                    |
| Handle `idx/f18`                         | Derived: `min(line index,0x777f)` and full ordered line index                                              | Line lookup `0x4c5dc250`, handle serializer `0x4c587800`                    |
| Handle `f1c/f08`                         | Native constructor state: local RefId minus one and DimOnCM zero                                           | Constructors `0x4c5bcd50/0x4c5f7da0`                                        |
| Handle identity                          | Two distinct handle nodes per point; adjacent points can target the same actual line                       | Clone/insertion `0x4c5f7e40/0x4c5f8460`                                     |
| Line `fd0`                               | Insertion state one after ordinary nonconstruction adjacency registration                                  | `0x4c5dde50/0x4c5f8460/0x4c4922d0`                                          |
| Line `fd4/fe8`                           | Native constructor state: zero; no direction pointer                                                       | `0x4b92dfc0`, direction clear `0x4c44d700`                                  |
| Line `seg_tol`                           | Native absent NormalScale value minus one; this schema key does not denote a geometric tolerance           | Segment serializer `0x4c590920`                                             |

Array indices, creation IDs, permanent markers and archive-map indices are
distinct namespaces. Points and lines are embedded records in the sketch;
they do not acquire object tags merely because the constructor retains typed
`ArchiveNode` owners. Adjacency handles are tagged runtime objects. Semantic
metadata `_sketch/_start/_end/_line` retains actual ownership during construction
and is not emitted. The native schema-one identities are bound by the runtime
schema audit in the profile ledger.

The ordered ring is one construction plan. Changing its topology requires a
new graph. The API does not offer incremental append or reordering of existing
vertices while retaining obsolete endpoint indices.

## Complete common and point fields

The common entity constructor is `0x4c3e1030`, with companion `0x4c3e1220`
and serializer `0x4c583460`. The table lists every emitted common owner field.
Its constructor states are scoped to the selected fresh local operation sequence.
They are not universal saved-document constants.

| Fields                | Classification and rule                                                                  |
| --------------------- | ---------------------------------------------------------------------------------------- |
| `f08`, `f0c`          | Derived or constructor state as separated above                                          |
| `vis.f00/f02/f04`     | Native visibility construction: layer marker `0xffff`, by-layer mask `0x1f`, flags three |
| `vis.f08.f00/f04`     | Native visibility construction: colour `0xffffffff`, line-type marker `0xffff`           |
| `vis.f08.f08.f06/f00` | Native inherited width: enum minus one and value minus one                               |
| `f20`                 | Constructor zero: no dimension uses are authored                                         |
| `dflt`                | Derived zero because the actual ordinary profile's virtual `+0x1ed8` returns zero        |
| `f30/f34`             | Constructor colour/status five/one; final solver lifecycle is separate                   |
| `f38`                 | Constructor line type one; not another solver-status field                               |
| `lw.f06/f00`          | Native width construction: enum zero and value minus one                                 |
| `ext/group`           | Constructor null pointers: no external entity or group                                   |
| `f54/f56/f50`         | Constructor state four/zero/zero                                                         |
| `has_name`            | Constructor zero: no authored entity name                                                |
| `f68`                 | Constructor binary64 one                                                                 |
| `f74/f78`             | Constructor zero/zero                                                                    |

Visibility arguments are bound at `0x4c151050`, called from the entity
constructor. Width arguments are bound at `0x4c3e1085/0x4c3e10f2` and framework
constructor `0x3c84a8f0`. Ordinary profile `dflt=0` follows constructor
`0x4c0ca780`, vtable `0x4d0e8e80`, target `0x4b27cbe0` and entity predicate
`0x4c3e22e0`. This avoids applying the origin-profile predicate to a normal ring.

Point constructors `0x4c490970/0x4c57ab00` and serializer `0x4c58f910` supply
the remaining fields. `pflags=0x1e` follows ordinary 2D ownership plus the
position setter. `fe4=0` retains an ordinary point. `fec=ff0=0`, `f108=-2`,
`has_jet=0` and auxiliary `p1/p2=(0,0)` retain their fresh constructor state.
The actual `pos`, creation ID, degree and adjacency use the rules above.

## Sketch and manager fields

| Fields                           | Classification and rule                                                                                                                                                               | Native provenance                                                                   |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `points/lines`, `npoints/nlines` | Derived ordered embedded rows and their actual lengths                                                                                                                                | Sketch serializer `0x4c5916f0`                                                      |
| Other entity arrays and counts   | Fresh empty collections: text, hatch, arc, ellipse, parabola, spline, plane, cylinder, sphere, cone, parametric, offset, sketch-offset, styled, intersection, tool, block, silhouette | Sketch constructor `0x4c495450`                                                     |
| `dims`                           | All fifteen dimension/relation/pattern arrays empty with derived zero lengths; distinct fresh `f118` auxiliary `suObList`                                                             | Sketch constructor and dimension-manager serializer `0x4c5a0f00`                    |
| `f140.f08/f0c`                   | Derived independent next point/line creation IDs `n+1`                                                                                                                                | Creation allocator `0x4c3e3030`                                                     |
| Other `f140` words               | Constructor counters one from `f10` through `f3c`; final `f40=0`                                                                                                                      | Sketch constructor `0x4c495450`, creation-ID serializer `0x4c5864f0`                |
| `f130`                           | Derived next permanent marker `n+1`                                                                                                                                                   | Permanent allocator `0x4c4bb590`                                                    |
| `f56c`                           | Derived insertion stamp `1+n`, one permanence operation per line                                                                                                                      | `0x4c5d1740`; point logging `0x4c5d0b90` adds no increment                          |
| `f188`                           | Derived local-reference zero for this local unshared ring, null derived profile, no external geometry or relations                                                                    | Local predicate `0x4c6fcfc0`, dependencies in the profile ledger                    |
| `f12c/f128`                      | Distinct constructor words one/one, not aliases of a known final solved state                                                                                                         | Constructor `0x4c495450`, serializer `0x4c5916f0`                                   |
| `f37c/f18c/f190/f578/f134`       | Fresh constructor zero words                                                                                                                                                          | Sketch constructor `0x4c495450`                                                     |
| `f568`                           | Ordinary 2D constructor minus one                                                                                                                                                     | Sketch constructor `0x4c495450`                                                     |
| `f570`                           | Constructor zero XYZ vector                                                                                                                                                           | Sketch constructor `0x4c495450`                                                     |
| `f448`                           | Null line-display constructor projection: empty string, width enum/value minus one, line type minus one, final integer one                                                            | Sketch serializer null branch `0x4c5916f0`, framework constructor `0x3c802910`      |
| `f590`                           | Fresh empty relation list and equation-variable map                                                                                                                                   | Relation manager `0x4c603200`                                                       |
| `coinc`                          | Four fresh empty coincidence-index maps with lengths derived from their rows                                                                                                          | Sketch constructor and admitted sketch grammar                                      |
| `f5d8`                           | Independently allocated empty `suObList`                                                                                                                                              | Sketch constructor and admitted sketch grammar                                      |
| `f580`                           | Fresh empty block and secondary maps plus empty handle-data list                                                                                                                      | Block constructors `0x4c8f5ac0/0x4c8f9680`                                          |
| `f598`                           | Fresh empty loop collection                                                                                                                                                           | Loop constructor `0x4c452ac0`                                                       |
| `f588`                           | Fresh empty slot collection and zero slot counter                                                                                                                                     | Slot constructor `0x4caace30`                                                       |
| `f138`                           | Constructor/runtime backlink to the actual caller profile; serialized only when `ctx874` is nonzero                                                                                   | Profile/sketch constructors `0x4c0ca780/0x4c495450`, sketch serializer `0x4c5916f0` |

Empty managers here represent the selected unconstrained construction. They
must not replace authored dimensions, patterns, blocks or other source content.
The final solver, coordinate-commit and save lifecycle remains distinct from
these constructor rules. Earlier polygon native measurements belong to their
exact historical revisions; they do not automatically qualify this SDK source.

## Real process proof and current status

The initial source freeze contains 42 executable files: 36 SDK constructor/validation
modules, four permanent process-test modules and two research process runners.
Its manifest SHA-256 is
`e2ecf8add8ebca73fa6ee9e43e66352746c7ec11761eaf0636f41bf2cf48bd7d`.
The forty normal Python files pass Black, Ruff, Mypy, Pyright and steering.
Both research scripts parse. The donor scan reports no recorded payloads.
The worker executed no constructor, codec, schema, test or vendor application.

`SdkPolygonProcess` receives only an authored neutral request through stdin.
It creates the complete fresh part using the existing research composition.
After existing research metadata operations finish, it installs the new plain
SDK sketch into the actual profile. The SDK Config/CMgr/Resolved/header writers
then compose five real native streams. Comparison bytes come from the same
neutral request generated in memory, never a saved file or template.
This installation order preserves the
[typed-node accessor boundary](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Construction/PlainArchiveNodesUseTypedFields.md).

`SdkPolygonPrepare` runs in another isolated interpreter. It imports only SDK
code and the input-read audit. It decodes the generated container, its standalone
header, independent CMgr map, Config graph and seeded Resolved graph. It checks
authored positions, ordered endpoints, degree, handle identities, independent
counters, actual profile-to-sketch, plane/component/model and dependency aliases,
and every inherited map slot.
It then writes all five streams and requires exact bytes. No live objects cross
the process boundary. Both phases deny runtime file and subprocess access after
initialization.

The permanent `TestPolygonFlow` uses independent four- and seven-sided authored
models and different depths. Four fresh interpreters cover their two build and
two preparation phases. Fourteen malformed inputs per build must reject.
The result must grow with topology, use complete admitted grammar and retain
explicit false native/public-writer qualification.

The parent's first independent snapshot binds 4,077 source files in code-manifest
SHA-256 `cdb3eb0e059cad96402c2cf3bcd7f191df8bde59ec9dda26e26a92cfbc37c485`.
Both guarded four- and seven-sided builds and their build assertions passed.
The first SDK preparation then failed with `KeyError: 'f138'` in its ownership
assertion. This was not a codec, format or native application failure. The
initial `Overlay01` and its source manifest remain unchanged.

The correction changes only preparation assertions and their matching report
contract. The build continues to check the actual runtime backlink. Preparation
requires its ordinary-context omission and verifies the actual mapped sketch
through profile `pd_f80`. Its model alias follows the serialized component-plane
chain. The profile, sketch, plane wrapper and unit component must each be the
actual object at its decoded map index. Existing extrusion dependency, inherited
map, geometry and all five exact stream comparisons remain required. No SDK
constructor, codec, field rule, emitted byte or archive context changes.
The second source freeze has SHA-256
`a68916e1f6d995596048a04f8ee8a9ce17b441bb7fc9d3bb48ec8d5881b639bf`.
The parent's second execution passed those serialized ownership checks, then
failed at the first compact handle with `KeyError: 'f18'`. That extension is
not present below its marker. An audit also found the analogous assumptions
for segment endpoint extensions `fc8/fcc`. All failed overlays remain unchanged.

Preparation now resolves and validates the actual wire form. Below a marker,
the compact value must equal the ordered target and the extension must be
absent. At the marker, the extension must exist, be an integer at least the
marker, and equal the actual target. No runtime field is synthesized and no
decoded value is changed. The checker reports observed compact and extended
handle/endpoint counts. The four- and seven-sided cases cover compact forms;
their passing result must not be reported as a new extended-width witness.
The prior large-ring width evidence remains bound to its original source.

The full prepare checker was audited against its actual SDK grammar:

| Checked owner or field               | Selected wire presence and semantic rule                                                                                             |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Profile `pd_f80`                     | Present in the ordinary `f3dc=0` branch, now required explicitly before dereferencing                                                |
| Profile `pd_f78`                     | Ordinary conditions zero select the stored plane-reference branch; the schema's absent `write_ref` control defaults to one           |
| Sketch `f138`                        | Absent with `ctx874=0`; construction retains its actual runtime backlink separately                                                  |
| Profile model owner                  | Follow serialized `pd_f78.f58.owner`; do not access constructor-only profile `owner`                                                 |
| Extrusion `f60.list.items`           | Resolved dependency list present in the selected non-`ctx874` mode; items retain actual profile identity                             |
| Point `pos`, `h1/h2`                 | Require ordinary `pflags=0x1e` first: 2D position bit set and omission bit `0x20` clear                                              |
| Point `f30/f34`                      | Require `dflt=0` before reading conditional status/colour fields                                                                     |
| Point IDs and degree                 | `f08/f0c`, `fe8` and point record kind are present in the selected modern point grammar                                              |
| Handle `idx/f18`                     | `idx` always present; `f18` only at marker `0x777f`; resolve and validate the semantic target                                        |
| Handle `f1c/f08`                     | Both scalar words always follow the selected index branch                                                                            |
| Segment `fc8_s/fc8`, `fcc_s/fcc`     | Compact fields always present; full endpoint extensions only at marker `0xffff`                                                      |
| Line IDs and contour state           | Common `f08/f0c` and segment `fd0` are unconditional on this selected path                                                           |
| Sketch counts, counters and statuses | The accessed array counts, all fifteen creation words, `f130/f56c`, `f128/f12c` and `f188` are present in the ordinary 19000 grammar |
| Archive object identities            | `ReadObjectMut` assigns actual mapped indices before body decoding; every checked node must match that map entry                     |
| Usage and context reports            | API-owned metadata from the SDK graph and complete selected linked context, not inferred runtime object fields                       |

The [compact-index gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Construction/CompactSketchIndicesOmitExtendedFields.md)
records the distinction. This correction again changes only the prepare runner,
its required report assertions and documentation. Constructor, codec, build
runner, archive context and all stream comparisons remain unchanged.
The corrected frozen source passes the independent parent execution below.

## Revision-bound process result

The accepted executable source manifest has SHA-256
`5254af429221cacf67852dbf7ea4415b9420e7ba409915760f9819c55d8ab3e5`.
All 42 executable files match both the active checkout and the parent's complete
4,077-file snapshot. That code manifest has SHA-256
`447db70a01c69a9819fe1cfdd143cb5cab887da2872e940f8a74ccead204c1d9`.
Its base is `00a61804b5e473eb5cdd19194b2f4848d3a83dc1`.
The complete private process receipt has SHA-256
`442790da10b5f9e3fdb913a889fe8061c30a595141fbab5cb4c406ccd6ed1e03`.
The worker independently checked both receipt hashes and all 42 source bindings.
No executable source changed after this run.

The parent ran `TestPolygonFlow` successfully on that frozen source. Separate
captured executions also passed both authored build/prepare pairs. Their four
guarded phases report zero runtime input-file reads. Each build passed five
fresh-graph stream comparisons, and each separate preparation passed five exact
byte comparisons. All 28 malformed construction cases rejected. Both builds
return plain `ArchiveNode` owners.

| Authored sides | Points/lines | Distinct endpoint handles | Resolved bytes | Actual Config/Resolved counters | Compact handles/endpoints | Extended handles/endpoints |
| -------------- | ------------ | ------------------------- | -------------- | ------------------------------- | ------------------------- | -------------------------- |
| 4              | 4/4          | 8                         | 14,064         | 82/198                          | 8/8                       | 0/0                        |
| 7              | 7/7          | 14                        | 14,826         | 82/204                          | 14/14                     | 0/0                        |

Both cases use 106 resolved schemas with complete usage and no missing or
provisional grammar. Their actual profile/sketch/map and plane/component/model
aliases survive independent readback. The extrusion retains the same profile
dependency. Constructor status, authored positions, ordered endpoints, creation
counters and permanent markers match. Resolved length changes with the authored
topology. These measurements are observed results, not emitted constants.

The [sanitized receipt](../measurements/2026/SdkPolygonConstruction01.json)
retains exact sources, artifact and stream hashes, counts, outcomes and both
earlier checker failures. It omits generated payloads and host paths. It reports
the permanent test as parent-confirmed; the separate captured pairs provide the
hashed detailed results. No new wide-index, native application or held-out
acceptance is claimed. All 42 executable paths remain frozen.

## Remaining construction work

The caller still owns the complete profile, model-to-sketch frame, separate
plane wrapper, feature allocation, origin, feature/history graph and native
stream/container policy. The shared part factory must compose these owners and
the existing blind-end primitive without relying on research helpers at runtime.
Source dimensions and relations need their own complete constructor paths.
Independent native controls, rebuild, driving edits, save/reopen and held-out
evidence remain necessary before public writer admission.

The CAD stopping conditions remain:

> The first is success under every criterion on this page.
> The second is the end of the available context.

This is an implemented bounded constructor component. It does not establish
complete conversion or general polygon-family acceptance.
