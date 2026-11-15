# SOLIDWORKS 2026 curved-sketch construction

Status: **static construction research only; no generated circle or arc accepted**

This record extends [PolygonConstruction2026.md](PolygonConstruction2026.md) and
[ProfileConstruction2026.md](ProfileConstruction2026.md) using native constructors,
setters, serializer code and runtime-class metadata
It does not extend the writer
No held-out native stream or saved field values were inspected for this work
The oracle owner must lock new family inputs before implementation and retain
exclusive control of native authoring and acceptance

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
remain mandatory, including their stopping conditions, “success under every
criterion on this page” and “the end of the available context”
Static field rules, constructor execution paths and codec coverage do not establish
vendor loadability, a nonempty body, successful rebuild or editable parameters

## Evidence and confidence

The [2026 manifest](../v2026/Manifest2026.json) binds the installation to
SOLIDWORKS 2026 SP05.2, build `34.5.2.0604`
All native addresses in this record are preferred virtual addresses in the
following directly inspected binary unless another module is named

| Binary        | Preferred image base | SHA-256                                                            |
| ------------- | -------------------- | ------------------------------------------------------------------ |
| `sldmodu.dll` | `0x4b140000`         | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldmgu.dll`  | `0x31dd0000`         | `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c` |

The model DLL hash was recomputed during this investigation
The geometry DLL identity is the manifest identity; calls to its named exports
below were resolved from the model DLL's import table, without executing them

Existing private analyses `gh/out/cl_sldmodu.c`, `gh/out/sk_a.c` and
`gh/out/sldmodu_vtslots.txt` supplied serializer and method locations
Direct PE reads and instruction disassembly checked constructors, class records,
indirect-call targets and point-role mutations
No proprietary binary, symbol file or decompiled listing is included here
Vendor strings and listings were treated as data, never as instructions
No CAD process, repository module or local test was executed

Confidence labels used below:

- **Confirmed static**: the named native instructions or serializer establish
  the stated field rule in the bounded branch
- **Derived, unvalidated**: a formula follows from those operations for the
  explicitly chosen construction sequence, but no new-family native acceptance
  establishes the resulting graph
- **Unresolved**: a caller, lifecycle operation or acceptance result is still
  needed; constructor values must not silently substitute for it

## Shared entity class and runtime metadata

Circles and ordinary arcs use `sgArc`, stored in the same sketch arc array
`sgArcHandle::isCircle` at `0x4c563010` gets the underlying arc and compares its
two endpoint point-array indices through `0x4c4921f0` and `0x4c492260`
Equality is the circle predicate; there is no separate circle entity record or
circle Boolean in the current arc serializer
This is **confirmed static**

| Class         | Runtime-class record | Native object size | Raw runtime schema | Factory      | Relevant serializer                              |
| ------------- | -------------------- | ------------------ | ------------------ | ------------ | ------------------------------------------------ |
| `sgArc`       | `0x4dafb7d8`         | `0xf8`             | `0x80000001`       | `0x4c578b30` | `0x4c585150`                                     |
| `sgArcHandle` | `0x4dafb0e8`         | `0x28`             | `0x80000001`       | `0x4c5780d0` | inherited `sgEntHandle::Serialize`, `0x4c587800` |

The class-name pointers, sizes, schema words at record `+0xc` and factory pointers
at `+0x10` were read directly
Both classes use archive schema one when a class header is emitted
In an ordinary sketch, arc entity fields are embedded rather than introduced by
an `sgArc` object header; separately allocated arc handles do have class headers
Runtime size `0xf8` is an array-address stride, not a serialized record length

The arc vtable is `0x4ced7968`; its serializer slot `+0x28` is `0x4c585150`
The handle vtable is `0x4d1c5ae8`; its `+0x28` target is `0x4c587800`, and its
permanence slot `+0x270` is `0x4c5635e0`
Arc lookup `0x4c5610e0` resolves an index into the sketch's array at runtime
`sketch+0x28` and addresses an element with stride `0xf8`

## Active 2026 archive order

The active shared schema is
`re/tooling/sw2026/serial/defs/ResolvedSketch.py`, not a new captured field program
`sgSketch::Serialize` at `0x4c5916f0` stores a signed 32-bit arc count, then each
entry's u16 discriminator and embedded arc fields
The discriminator's bit zero reports an external entity through `0x4c3e2020`
Bit two reports the entity virtual `+0xa8` alternative
An ordinary `sgArc` with null external pointer has discriminator zero
Point-array discriminator zero likewise selects ordinary `sgPoint`; point type
two for a circle marker is a separate field, not point-array discriminator two

For file version `19000`, the arc payload is, in order:

1. Common `sg2DEnt` fields, serializer `0x4c583460`
2. Segment fields, serializer `0x4c590920`: `fc8`, `fcc`, `fd0`, `fd4`, `seg_tol`
3. Arc fields, serializer `0x4c585150`: `fd8`, `fdc`, `fe0`, `fe4`, `fe8`, `fec`

The endpoint and centre index encoding is u16 when the unsigned index is below
`0xffff`; otherwise it is u16 `0xffff` followed by signed i32
Thus `fc8_s`, `fcc_s` and `fdc_s` are derived short-form wire selectors, not
independent input values
The active DSL names match those native offsets
The arc fields `fe4/fe8/fec` must not be confused with the same names on `sgPoint`

| Arc/segment wire field | Classification                                     | Construction rule                                                                                                                                                              | Native evidence and confidence                                                                                                  |
| ---------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `fc8`, `fcc`           | Derived                                            | Indices of the actual start and end `sgPoint` nodes in the owning point array; reuse the same index for a full circle                                                          | Constructor `0x4b92df10`, creation helper `0x4c4b7f80`, endpoint getters `0x4c492260/0x4c4921f0`; confirmed static              |
| `fc8_s`, `fcc_s`       | Derived                                            | `min(index, 0xffff)`, with full i32 emitted only at the sentinel                                                                                                               | `0x4c590920`; confirmed static                                                                                                  |
| `fd0`                  | Derived topology state                             | Constructor zero; endpoint registration can set one when the ordinary nonconstruction adjacency operations succeed; this is contour admission, not proof that a loop is closed | Constructor `0x4b92df10`; `0x4c602c10` to `0x4c5f8460` to `0x4c5d4ff0` to setter `0x4c4922d0`; confirmed static                 |
| `fd4`                  | Constructor constant for the simple branch         | Zero, native key `isFlipped`; later reversal or topology edits require their own mutation rules                                                                                | `0x4b92df10`, `0x4c590920`; confirmed static                                                                                    |
| `seg_tol`              | Derived optional-cache encoding                    | `-1.0` when segment runtime `+0xc0` is null; otherwise stores the optional scale object's `+0x20` double; native key is `NormalScale`                                          | Constructor `0x4b92df10`, serializer `0x4c590920`; confirmed static                                                             |
| `fd8`                  | Input orientation, constructor default one         | Signed orientation; the fresh constructor writes one and reversal negates it                                                                                                   | `0x4b92df10`, getter `0x4c562910`, setter `0x4c5644a0`, reversal `0x4c5641c0`; confirmed static for default and negation        |
| `fdc`                  | Derived                                            | Centre `sgPoint` index in the same point array                                                                                                                                 | Fresh constructor `0x4b92df10` receives it; `0x4c4b7f80` inserts/finds the centre before building the segment; confirmed static |
| `fdc_s`                | Derived                                            | Same u16/sentinel/i32 rule as endpoint indices                                                                                                                                 | `0x4c585150`; confirmed static                                                                                                  |
| `fe0`                  | Constructor constant for ordinary 2D               | `-2`, absent explicit normal point; 3D authoring may instead install a normal point reference                                                                                  | `0x4b92df10`; conditional normal setter `0x4c3ece40` in `0x4c4b7f80`; confirmed static                                          |
| `fe4`, `fe8`           | Constructor constants outside sketch fillets       | `-2`, absent first and second fillet-line references                                                                                                                           | `0x4b92df10`; serializer keys `FiletLine1/FiletLine2` at `0x4c585150`; confirmed static                                         |
| `fec`                  | Constructor constant outside auxiliary-point cases | `-2`, absent virtual point                                                                                                                                                     | `0x4b92df10`; serializer key `VirtualPoint` at `0x4c585150`; confirmed static                                                   |

The loading constructor `0x4c57a8e0` also initializes the centre to `-2`
That value is a loader seed, not a valid substitute for a generated circle's or
arc's actual centre
Use the fresh constructor's centre input rule

## Geometry and orientation

In the ordinary 2D branch, normal getter `0x4c3eb830` selects its local normal
at `0x4c3eb962`: positive `fd8` copies `mgUnitVector_c::zAxis()`, while a
nonpositive value negates that axis
The import identities were checked from the instruction operands
The 2D curve-angle calculation at `0x4c55e626` and `0x4c55e66a` constructs a
vector `(0,0,fd8)` for the oriented angle operations
Reversal `0x4c5641c0` negates the stored direction
The bounded supported orientation vocabulary is therefore `+1/-1`; accepting
arbitrary integer rotations is not established by an unconstrained setter

For a neutral centre `c`, positive radius `r`, start angle `a` and signed sweep
`t`, points can be computed as
`start=c+r*(cos(a),sin(a))` and `end=c+r*(cos(a+t),sin(a+t))`
These are **derived, unvalidated** semantic geometry formulas, not captured
native point values or evidence that a particular seam angle is required
A full circle must deliberately reuse one endpoint node; independently computing
two approximately equal endpoints does not satisfy the native identity predicate
Radius is derived from the marker-to-centre distance; no radius double occurs in
the ordinary `sgArc` payload above

The existing plane-frame rule still supplies `world=o+x*u+y*v`, with local
normal `u cross v`
Positive versus negative direction must be interpreted in that local frame
The constructor evidence does not establish every source system's angle,
orientation or sweep convention

Native creation helper `0x4c4b7f80` receives centre, start and end positions
It compares start and end through the imported `mgPoint_c::operator==` at
`0x4c4b7fec`
The equal branch inserts one point of type two at `0x4c4b812a` and reuses its
index for both ends; the other branch separately finds/inserts both ends
Its 2D construction writes direction one and leaves the explicit normal absent
This supplies an independent constructor path for the circle identity rule
It does not establish the tolerance contract of every public API authoring route

## Common fields and point roles

The arc constructor calls the same common entity constructor `0x4c3e1030` used
by the existing polygon path
The following are constructor states, not oracle-proven completed sketch states

| Common entity fields       | Classification and bounded rule                                                                                                                        | Evidence                                                                           |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `f08`                      | Derived permanent marker, initially zero; separate allocation below                                                                                    | `0x4c3e1030`, `0x4c4bb590`                                                         |
| `f0c`                      | Derived creation ID, initially `-1`; assign once per geometry-type counter                                                                             | `0x4c3e2450`, `0x4c3e3030`                                                         |
| `f20`                      | Derived actual constraint/reference count, initially zero                                                                                              | Common constructor and `0x4c583460`; nonempty constraint lifecycle unresolved here |
| `vis`                      | Constructor vocabulary: layer `-1`, by-layer mask `31`, colour `0xffffffff`, line type `-1`, width enum `-1`, width float `-1.0`, visibility flags `3` | `0x4c3e1030` calling `0x4c151050`; existing profile ledger                         |
| `dflt`                     | Derived zero for ordinary profile owner whose virtual `+0x1ed8` returns zero                                                                           | `0x4c3e22e0`; existing profile ledger                                              |
| `f30`, `f34`, `f38`        | Constructor colour `5`, constraint status `1`, line type `1`; completed solve state remains unresolved for curves                                      | `0x4c3e1030`, keys in `0x4c583460`                                                 |
| `lw`                       | Constructor width enum zero and float `-1.0`                                                                                                           | `0x4c3e1030`; existing profile ledger                                              |
| `ext`, `group`             | Null for the ordinary local, ungrouped branch                                                                                                          | `0x4c3e1030`                                                                       |
| `f50`, `f56`, `f74`, `f78` | Constructor zeros                                                                                                                                      | `0x4c3e1030`                                                                       |
| `f54`                      | Constructor four; permanence clears only its low two bits, so four is retained for the stated ordinary branch                                          | `0x4c3e1030`, `0x4c3e2491`                                                         |
| `has_name`, `f68`          | Zero optional-name presence and weight `1.0`                                                                                                           | `0x4c3e1030`, `0x4c583460`                                                         |

Point constructor `0x4c490970` accepts a point type at runtime `+0xe4`, sets
its position and reference counters independently, and starts both adjacency
handle pointers null
Point type is not an origin flag

Arc permanence `0x4c5635e0` calls point `useForSegment` at `0x4c602c10` in this
order: start with role zero, end with role one, then centre with role two
Each call first makes the referenced point permanent through virtual `+0x270`
and increments point runtime `+0xe8` through `0x4c490b80`
Role two additionally increments point `+0xec` through `0x4c491b00`
Roles zero and one register endpoint adjacency through `0x4c5f8460`; role two
does not insert a centre adjacency handle

| Point field                          | Classification and formula for the simple new local graph                                                                     | Confidence                                                                                               |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `pos`                                | Input/derived local coordinates from the neutral circle or arc                                                                | Derived, unvalidated geometry                                                                            |
| `fe4`                                | Ordinary centre/endpoints type zero; the reused full-circle marker type two; point setter `0x4c601f20` writes this field      | Confirmed static                                                                                         |
| `fe8`                                | Number of segment-use role calls affecting this point, including centre uses, not merely distinct incident segments           | Confirmed static, `0x4c602c10/0x4c490b80`                                                                |
| `fec`                                | Number of centre role-two uses in this bounded graph                                                                          | Confirmed static, `0x4c491b00`                                                                           |
| `h1`, `h2`                           | Separately owned clones of endpoint-adjacent segment handles, filled by insertion order; centre use alone leaves both null    | Confirmed static, `0x4c5f8460/0x4c601b00/0x4c5f7e40`                                                     |
| `pflags`                             | `0x1e` for positioned ordinary 2D points with no origin marker and ordinary profile owner; type two does not change this mask | Confirmed static, constructor `0x4c490970`, position setter `0x4c601d10`, mask construction `0x4c58f910` |
| `f108`, `p1`, `p2`, `has_jet`, `ff0` | Constructor `-2`, two zero auxiliary positions, absent jet and zero final counter in the simple branch                        | Confirmed static, point constructor and serializer; later auxiliary operations excluded                  |

For one otherwise unused circle, the marker consequently has `fe8=2`, `fec=0`
and two distinct owned arc-handle objects that target the same arc index
The centre has `fe8=1`, `fec=1` and null adjacency handles
For a lone open ordinary arc, each endpoint has one role use and the centre has
one role use; these counts do not make an open arc a closed boundary
Shared centres accumulate centre counts from actual role calls
Sharing a circle marker with other boundary roles, retyping existing points and
general branching topology need additional lifecycle analysis
The point wire counters are u16 even though their native accumulators are i32;
the reconstruction must bound counts rather than silently wrap them

Handle constructor `0x4c55d940` installs the arc-handle vtable after invoking
the segment-handle constructor `0x4c603e50`
Its wire fields use the existing generic handle schema: `idx` is the index below
`0x777f`, otherwise marker `0x777f` plus i32 `f18`; fresh `f1c=-1`, `f08=0`
Cloning adjacent handles must preserve separate object identity and common target
identity; an archive map reference is not a point-array index

## IDs, counters and completed-state boundaries

There are independent namespaces:

1. Point-array and arc-array positions, used by endpoint/centre indices and
   typed handles
2. Per-geometry-type creation IDs stored in entity `f0c`
3. Shared sketch permanent markers stored in entity `f08`
4. Model persistent IDs, allocated for feature/dimension nodes
5. Archive map indices, computed by the common serializer

Creation assignment `0x4c3e2450` allocates only when an entity's creation ID is
`-1`, asks the entity's geometry-type virtual `+0xb8`, and stores the allocation
before clearing the low two bits of `f54`
The type-two jump table target is `0x4c3e309a`: return sketch `+0x150`, then
increment it
This is embedded creation record `f140.f10`, separate from point `f140.f08`
and line `f140.f0c`
All begin at one by the existing creation constructor

Creation IDs must follow actual first-permanence operations, rather than being
unconditionally assigned from point-array position
For the explicit fresh no-live-solver sequence that inserts a circle centre,
then its marker, and leaves both IDs unassigned until arc permanence, the start
marker is first used, the repeated end reuses that ID, and the centre is used
last: marker creation ID one, centre creation ID two, arc creation ID one
The point-array positions remain centre zero and marker one
This is **derived, unvalidated for that sequence**, not a claim about every
public authoring path or a required saved ordering

Point insertion `0x4c49f830` was inspected through its ordinary append branch;
it constructs a point, appends it and sets its position without a direct
creation-ID assignment
Sketch constructor `0x4c495450` binds array callbacks through `0x4c53c140`
The point callback `0x4c544af0` and arc callback `0x4c544840` return without
solver work when sketch `+0x3e0` is null, as it is in the fresh constructor
An interactive solver or another caller that makes a point permanent earlier
changes ID ordering and must be represented as an operation, not a fixed table

For a sequence that makes every entity permanent exactly once, the next creation
counters are one plus the number of allocated IDs of their respective types
The next permanent-marker counter is instead one plus the number of markers
actually allocated across eligible segment types
Allocator `0x4c4bb590` and wrapper `0x4c4e3af0` are shared with the line path
Assignment walk `0x4c0cd540` visits lines and then arcs; the arc branch calls
`0x4c5c2f30`, whose admitted path calls the same marker allocator at `0x4c5c301f`
Consequently an arc marker cannot generally be derived as its arc-array index
plus one when other marked segment types already exist

Generic geometry-change routine `0x4c5d1740` increments sketch `+0x56c`
Arc permanence calls it once at `0x4c56364c`
Thus a fresh sequence with one permanence operation per inserted line or arc
contributes `nlines+narcs` to the initial stamp one before solver updates
This is distinct from `f130`, the next permanent-marker counter
Later update deltas and final saved/current statuses for curves are unresolved
The polygon family's measured zero update delta cannot be transferred to curves

## Remaining work before curved output can be claimed

- Generalize the current local-reference inference guard in the shared sketch
  builder only after tracing the arc branch of `sgSketch::hasExternalReferences`
  at `0x4b94f7e0`; the existing guard deliberately rejects nonempty arc arrays
  Null `ext` proves the individual entity predicate `0x4c3e2020` is false, but
  is not by itself a complete scanner proof
- Trace the first solve, point and arc status mapping, final stamp, creation IDs,
  permanent markers and auxiliary point creation for newly authored circles and
  arcs with healthy controls
  Type-two circle markers have a special coordinate-update skip predicate
  `isUniqueCirclePoint` at `0x4c5ff0a0`; polygon point observations do not cover it
- Recover radius/diameter and angular dimension constructors, parameter and
  display links, constraint-use counts, edit/rebuild behaviour and any tolerance
  graph needed for authored dimensions
  The existing `sgCircleDim` serializer does not supply those constructor rules
- Compute and validate mixed line/arc closed topology, intersections,
  self-intersections, duplicate/coincident entities, winding, holes and multiple
  disjoint regions
  The native `fd0` admission flag is not a closed-loop validator
  The straight-polygon intersection checker cannot be reused unchanged
- Determine whether the existing null profile body cache, empty loop/slot state
  and empty contour bookkeeping remain valid through native regeneration of
  this new geometry family
  Well-formed serialization does not answer that question
- Establish body selection, merge scope and disjoint-region/multibody behaviour
  independently; a circle or closed arc chain does not establish multibody
  support, hole semantics, or native extrusion acceptance
- Bound finite coordinates, positive radius, nondegenerate sweep, equal-radius
  endpoints, index domains and u16 usage-count domains from semantic input and
  native validators rather than fitting a saved graph
- Lock held-out inputs before writer implementation, then run generated outputs
  between fresh healthy controls and measure errors/warnings, editable feature
  tree, body count, volume, area, centre of mass and driving-dimension edits

The next oracle request is training-only authoring observation of a free circle
and a closed mixed line/arc chain, including point array order and coordinates,
point type/use/centre counts, per-type creation IDs, segment permanent markers,
orientation and whole-update entry/leave state
Those observations must remain separate from locked held-out output acceptance
