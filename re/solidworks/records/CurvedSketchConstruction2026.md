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

## Full external-reference scan for fresh local curves

The complete `sgSketch::hasExternalReferences` function at `0x4b94f7e0` was
checked directly in the hash-bound `sldmodu.dll` above
Its PE unwind extent is `[0x4b94f7e0,0x4b95055a)`; SHA-256 of those function
bytes is `7f320714e35591b29f83403d71ff126d4fc9e14f6f48cf74badb075a8a04465e`
This closes the previously unresolved **static scanner admission** question for
the following bounded graph, including nonempty arc arrays
It does not establish successful solve, contours, extrusion or native acceptance

| Scan stage                              | Native condition and sufficient local-graph rule                                                                                                                     | Evidence                                                                                                                                        |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Derived profile                         | `moProfileFeature_c::isDerived` returns false when profile definition `pd_f110` is null; the derived-reference external predicate is therefore not called            | Scanner `0x4b94f822`–`0x4b94f84a`; predicate `0x4c0de380` tests profile `+0x3d0` then definition `+0x110`, with the null return at `0x4c0de44b` |
| Offsets                                 | Empty sketch offset collection at runtime `+0x48` skips the loop; a populated offset with its `+0x68` equal to zero would instead return true                        | `0x4b94f850`–`0x4b94f88e`                                                                                                                       |
| Intersections                           | Empty intersection collection at runtime `+0x50` skips the loop; a populated item's `+0x68` equal to zero would return true                                          | `0x4b94f890`–`0x4b94f8c9`                                                                                                                       |
| Silhouettes                             | Empty silhouette collection at runtime `+0x110` skips the loop; a populated item's `+0x28` equal to zero would return true                                           | `0x4b94f8cb`–`0x4b94f908`                                                                                                                       |
| Hatches and lines                       | Empty hatches and local permanent lines with null entity `ext` take their normal loop exits                                                                          | Hatch scan `0x4b94f90a`–`0x4b94f9c0`; line scan `0x4b94f9c5`–`0x4b94fa72`                                                                       |
| Arcs, including circles                 | Every permanent arc is tested through the common external predicate with argument one; null entity `ext` advances the loop                                           | Arc scan `0x4b94fa77`–`0x4b94fb24`, detailed below                                                                                              |
| Remaining curve and surface collections | Empty parabola, ellipse, plane, cylinder, sphere, cone, parametric-surface and spline arrays skip their scans; the spline-only equation-driven branch is unreachable | `0x4b94fb29`–`0x4b9500f7`; equation flag tested at `0x4b950091`                                                                                 |
| Points                                  | Local permanent points with null entity `ext` advance without executing the optional external-origin/position exceptions                                             | Point scan `0x4b9500fc`–`0x4b95025a`; null-external result branches directly to handle destruction at `0x4b950168`                              |
| Text and final result                   | Empty text array reaches the false result; the function has no later geometry or dimension scan                                                                      | Text scan `0x4b95025f`–`0x4b9502fe`; zero return value set at `0x4b950303`                                                                      |

The arc iterator begins at index zero in `arcBegin` (`0x4c4a4170`) and ends at
the dynamic count of sketch array `+0x28` in `arcEnd` (`0x4c4a41d0`)
Their handle constructors set `f1c=-1` and retain this sketch as owner
The scan compares these handles, tests `isNotPermanent` at `0x4b94faa9`, then
makes a temporary arc-handle copy at `0x4b94fabc` through `0x4b738bd0`
Copy constructor `0x4c55d900` preserves the sketch pointer, array index and
`f1c`; it does not clone the referenced geometry

For `sgArcHandle`, vtable `0x4d1c5ae8` slot `+0x378` targets `0x4c562f20`
That method checks the sketch and index bounds, then resolves the arc through
`0x4c4b0df0`: array `sketch+0x28`, data pointer `array+0x08`, stride `0xf8`
Thus the external predicate reads the actual arc record, not a segment endpoint,
centre point, an adjacency clone or an unrelated handle cache
The iteration must still have valid owner and index relationships; a null
predicate result from an invalid handle would not establish a valid graph

The call at `0x4b94facc` is `sgEntHandle::isExternal(handle,1)`
That wrapper (`0x4c5ce0c0`) first requires `f1c=-1`, resolves the entity through
virtual `+0x378`, and calls entity predicate `0x4c3e2020`
The entity predicate returns false immediately if either low permanence bit of
`f54` is set; otherwise it tests entity runtime `+0x48`, the wire `ext` field
For a permanent local arc `f54=4` and `ext=null`, that test returns false
Argument one also bypasses the detachable-drawing exception, so no drawing
session state affects this result
The false branch at `0x4b94fad3` goes to `0x4b94faef`, destroys the temporary
handle, and advances the iterator through `0x4c4cd4a0` at `0x4b94fafe`
The arc handle's virtual type is two (`0x4b285dd0`), so this helper increments
the array index; its separate type-`0x11` special case is not taken
The arc's true-result cleanup begins at `0x4b950383` and returns one at
`0x4b9503a2`; null `ext` cannot reach it

No arc-radius, start/end equality, direction, centre index, point type or
closed-loop test exists in this scan
Consequently an ordinary arc and a circle represented by equal endpoint indices
have the same local-reference admission rule
With the bounded empty auxiliary collections above and local points/lines/arcs,
the **full function** returns zero for `(1,0,0)`, the existing update call
It also returns zero for other values of the last two arguments in this graph:
their only additional branches are in the absent spline and external-point paths
This is a **confirmed static** control-flow conclusion, not a measured curve run

This function does not examine dimensions, pattern relations, groups, styled
geometry or blocks directly
Its result alone must not relax the separate constraint validators or prove the
inter-component reference result stored in sketch `f188` by `0x4c6fcfc0`
The current builder's conservative guards for those unsupported graph kinds
remain independent obligations

## Independent `f188` inter-component reference computation

The complete predicate at `0x4c6fcfc0` was checked separately from
`hasExternalReferences`
Its PE unwind extent is `[0x4c6fcfc0,0x4c6fdea2)`; SHA-256 of those bytes is
`662c64935b55a5f0e39b6e10c48ea66640c6ef2888c13fd77891abb8f1b56653`
The binary binding is the same `sldmodu.dll` hash above
It returns an actual qualifying reference-wrapper pointer, or null; its result
is not itself a Boolean or a sketch-constraint status

The ordinary `sgSketch::update` path calls it with arguments `(sketch,0,0)`
at `0x4c549d9b`, tests the returned pointer at `0x4c549da3`, and stores
`int(pointer != null)` to runtime sketch `+0x188` at `0x4c549da9`
The zero base register is established at `0x4c549b07`
The two intervening assignments of error results six and seven both leave this
path through the common update return; they do not contaminate the Boolean
The owner profile's virtual `+0x1ed8` must return zero at `0x4c549d85` to
reach this assignment, as it does for the ordinary profile branch already
recorded in [ProfileConstruction2026.md](ProfileConstruction2026.md)
An update that aborts before this boundary has not recomputed the field

The wire field is u16, not a pointer and not a four-byte archive integer
`sgSketch::Serialize` reads its low word at `0x4c593820` and calls the u16
store primitive at `0x4c59382a`
The current-format load reads a u16 and zero-extends it into runtime `+0x188`
at `0x4c598726`–`0x4c59872a`
The active shared schema emits this field for versions greater than `0x249`
The bounded computed result below is zero, which is represented without a
narrowing ambiguity

The full predicate has the following sufficient conditions for returning null
Every runtime array container must exist, as installed by sketch construction;
an empty data array is not permission to replace its container with a null
runtime pointer

| Stage                     | Bounded local condition and branch                                                                                                         | Evidence                                                                                          |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| Offsets and intersections | Empty arrays at sketch `+0x48` and `+0x50` skip reference-list collection and classification                                               | `0x4c6fcfe4`–`0x4c6fd1f1`                                                                         |
| Lines                     | Null entity `ext` makes common entity external predicate false; the line advances without making a reference wrapper                       | Entity predicate call `0x4c6fd257`, false branch `0x4c6fd25e` to `0x4c6fd36b`                     |
| Hatches                   | Empty array at sketch `+0x20`                                                                                                              | `0x4c6fd380`–`0x4c6fd4f6`                                                                         |
| Arcs and circles          | Null entity `ext` makes the same entity predicate false and advances; no endpoint, radius or orientation condition occurs before that exit | Arc array `+0x28`, stride `0xf8`; call `0x4c6fd557`, false branch `0x4c6fd55e` to `0x4c6fd666`    |
| Other geometry            | Empty ellipse array `+0x30`, the five geometry arrays `+0xe0` through `+0x100`, and spline array `+0x40` skip all their reference checks   | `0x4c6fd67b`–`0x4c6fdd22`                                                                         |
| Points                    | Null entity `ext` takes the false branch directly to the next point, including point type-two circle markers                               | Point array `+0x08`, stride `0x158`; call `0x4c6fdd87`, false branch `0x4c6fdd8e` to `0x4c6fde33` |
| Derived profile           | Null profile-data `pd_f110` makes `isDerived` false, as established above                                                                  | Final derived-profile test `0x4c6fde48`–`0x4c6fde56`; null return set at `0x4c6fde8c`             |

For a nonlocal arc, the longer branch would inspect the entity's external
reference, classify the wrapper through
`moRefWrapper_c::isReferenceFromComponentToComponent` at `0x4c32d4d0`, and
possibly return that wrapper
The zero third argument disables the separate
`isReferenceFromAssemblyToComponent` tests
The zero second argument does not discard a qualifying component-to-component
wrapper because it is broken; the broken-reference exception requires that
argument to equal one
These distinctions do not affect the local proof because null `ext` exits
before any wrapper or reference classifier is reached
No wrapper, create-version branch or reference cache must be synthesized to
force the null result for a local curve

**Confirmed static:** with the valid local graph above, this predicate returns
null and the normal update computes `f188=0`, both with no constraints and
with an owned local radius/diameter graph described below, provided that the
radial graph retains every stated geometry/reference condition
The function does not read the one-, two- or three-geometry value-dimension
arrays, logical constraint arrays, dimension parameters, display collection,
or entity constraint-reference count `f20`
Its added value/display/parameter nodes and incremented `f20` therefore cannot
change this predicate while the geometry `ext` pointers remain null and the
specified auxiliary collections remain empty
Consequently radius versus diameter and the nonnull invalid second dimension
handle do not add an `f188` admission condition

This is predicate invariance, not validation of dimension ownership, IDs,
parameters or display data
Those may still fail their independent validators while `f188` correctly stays
zero
The same restriction applies to unexamined graph kinds: this predicate does not
directly scan text, parabola, silhouette, pattern or group collections, so its
null result is not permission to accept those families
The complete local external-reference scanner and this separate inter-component
predicate are now both bounded statically for ordinary points/lines/arcs
Constraint validation, curve first-solve behaviour and final measured state
remain independent outstanding work

## Radius and diameter dimension construction, partial graph

Both radial cases use `sgCircleDim`, runtime-class record `0x4dafb268`, size
`0x1a0`, raw schema `0x80000001`, loading factory `0x4c5782c0`
Its fresh-construction vtable is `0x4cf79588`, whose serializer slot `+0x28`
is inherited `sgValG1Dim::Serialize`, `0x4c59ec10`
The active shared schema is `sgCircleDim -> VAL_G1 -> VALDIM -> SGDIM ->
Dimension_c` in `ResolvedSketch.py`; the radial class adds no separate payload
These metadata and dispatch facts are **confirmed static**

The semantic authoring path is `sgSketch::makeRadDim` at `0x4c4cb670`
Its whole PE unwind extent `[0x4c4cb670,0x4c4cb882)` has SHA-256
`d927cd60080ad87d9b9e0108361f2b2b1727fa07335eb0b2d541175e3be70fde`
It obtains arc centre through virtual `+0x180`, bound to
`sgArcHandle::center` at `0x4c55e800`, and a curve point through virtual
`+0x1c0`, bound to `sgSegmentHandle::secondPoint` at `0x4c607a40`
The subtraction, squared length and square root at `0x4c4cb6e6`–`0x4c4cb6f9`
derive `r=length(secondPoint-centre)` from geometry
No saved radius or fitted constant participates

The `DirDistOption` argument controls the representation:

| Authoring condition                             | Constructor radius selector | Parameter value | Persisted `sgDim.f80` |
| ----------------------------------------------- | --------------------------- | --------------- | --------------------- |
| Option `9`                                      | One                         | `r`             | `3`                   |
| Option `8`                                      | Zero                        | `2*r`           | `0x0f`                |
| Other option, distinct start/end point indices  | One                         | `r`             | `3`                   |
| Other option, identical start/end point indices | Zero                        | `2*r`           | `0x0f`                |

The explicit options are compared at `0x4c4cb72a` and `0x4c4cb736`
The fallback calls endpoint-index getters `0x4c6060d0` and `0x4c605f20`,
compares them at `0x4c4cb757`, and doubles the radius at `0x4c4cb75e` only
for the diameter case
The fresh `sgCircleDim` constructor `0x4c40fec0` selects type `3` for a nonzero
radius selector and type `0x0f` for zero, then calls base `0x4c411830`
Its bytes `[0x4c40fec0,0x4c40ff03)` have SHA-256
`4752ad20c6751f99417d898d0865edd42adcdaca65fdc73503d651ed0cd7dc06`
This proves the radius/diameter meaning of these two type values without fitting
an enum to a control file; it does not enumerate every legal `DirDistOption`

The fresh bounded base graph has the following field rules
These are constructor states, not a completed saved dimension graph

| Field or relationship          | Classification and rule                                                                                                                | Native evidence                                                                                                                                               |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sgDim.f80`                    | Input-derived representation type `3` for radius, `0x0f` for diameter                                                                  | `0x4c40fed0`–`0x4c40fee0`; base store at `0x4c41009d`                                                                                                         |
| `sgDim.f90`, `f94`, `f98`      | Constructor constants `2`, `0`, `0`                                                                                                    | `0x4c4100aa` stores the first two as one eight-byte store; `0x4c4100b7` stores the third                                                                      |
| Runtime sketch link            | Actual owning sketch at dimension `+0x88`; it is independent of the dimension's parameter and display links                            | `0x4c4100a3`                                                                                                                                                  |
| `VALDIM.fa0`                   | Constructor zero, so the current-version serializer omits the optional transform; the live `+0xa8` transform is constructed separately | `0x4c41172d`–`0x4c41173e`; serializer `0x4c59ea80` and active shared version condition                                                                        |
| `VAL_G1.h1`                    | Independent handle object with the supplied arc handle's target, owner, index and concrete runtime type                                | `0x4c4118ac`–`0x4c4118b6`; assignment `0x4c5bf760` copies all `0x28` bytes, including the vtable                                                              |
| `VAL_G1.h2`                    | A nonnull default `sgEntHandle` object with native index `-2`, `f1c=-1`, `f08=0` and null runtime sketch pointer                       | Array construction at `0x4c41187a`–`0x4c411893`, callback `0x4b27d470` and constructor `0x4c5bcd50`; no later assignment to the second element on this branch |
| `VAL_G1.g1`, `g2`, `dir`       | Constructor zero, zero and positive unit X vector                                                                                      | Combined zero store at `0x4c4118bd`, axis getter and assignment `0x4c4118c4`–`0x4c4118d4`                                                                     |
| Parameter                      | New `moLengthParameter_c` for both radial type values; value is the computed `r` or `2*r`                                              | Base `0x4c411700` selects the length runtime class at `0x4c411762`, calls `Dimension_c::createNewParameter` at `0x4c41177b`, then `SetValue` at `0x4c4117a3`  |
| Dimension parameter ownership  | The created parameter is assigned to dimension runtime `+0x28`; it is not a borrowed sketch-entity value                               | `0x4c820e10`, assignment `0x4c820e37`                                                                                                                         |
| Initial dimension ID           | `f50=-1` before subsequent registration/naming; do not emit this seed as a proven final persistent ID                                  | `Dimension_c` constructor `0x4c81f6d0`, store `0x4c81f717`                                                                                                    |
| Arc constraint reference count | One additional valid local arc reference contributes `max(previous+1,1)` to entity `f20`                                               | Authoring call `0x4c4cb7c0`; handle `0x4c5bd330` local branch to entity increment `0x4c3e1510`                                                                |

The second handle must not be replaced by a null archive pointer merely because
it represents no selected second geometry
The native store passes the addresses of both embedded handles to `WriteObject`
at `0x4c59ed00` and `0x4c59ed0c`
For the default second handle's negative index, the **unsigned** comparison at
`0x4c5878d4`–`0x4c5878db` selects the extended encoding: u16 marker `0x777f`
followed by signed i32 `-2`, then `f1c=-1` and `f08=0`
It does not store u16 `0xfffe` as a short index in the current format
After loading, the serializer restores each handle's runtime sketch owner from
the dimension at `0x4c59ee85` and `0x4c59ef18`
These ownership fixups do not turn the second object into a null pointer

The stack dimension is appended to the sketch's one-geometry value-dimension
array at runtime `+0x68` through `0x4c49aea0`
The full append body continues past its first PE unwind fragment and returns
at `0x4c49afc4`; treating fragment end `0x4c49aec9` as function end would miss
the transfer/reset lifecycle
It appends the constructed `0x1a0` record, resets the temporary through
`0x4c822050`, and uses the resulting array index for the following display path
This is an operation-derived graph, not a serialized dimension template

`sgArcHandle::createDispDim` at `0x4c55ebc0` constructs a
`moSkDimHandleValG1_c` through `0x4c83d4a0`, using the owning sketch and that
value-dimension index
The ordinary `sgCircleDim` branch allocates a `moDisplayRadialDim_c` of size
`0x1140` and invokes constructor `0x4c8bfc10` at `0x4c55f14a`
It appends the display object to sketch `+0x118` through `suObList::AddTail`
at `0x4c55f164`
When the caller supplies a presentation point, branch `0x4c55f042` uses that
point; the geometry-derived default placement calculations are a different path
The lower-level `sgSketch::makeCircleDim` at `0x4c4c5770` instead always passes
radius selector one and creates only the value-dimension entry plus the arc's
constraint reference; it is not a substitute for this display construction

The following sections close a bounded retained registration path and map the
radial display constructor seeds separately from later presentation mutations
Completed reference counts, final presentation state, tolerance ownership,
first-solve changes and editable/rebuild acceptance remain unresolved
No radial writer, dimensioned native family acceptance or neutral-value fallback
is established by this partial graph

## Retained radial registration, parameter names and persistent IDs

The fresh-profile authoring path at `[0x4c552950,0x4c553e30)` has SHA-256
`23b377359d2456e7bc10043424e380311ad78ab9a401f4e2b7915c047b50b2d3`
It constructs the profile through `0x4c0ca780` at `0x4c552b42`
Its radial branch calls the index overload of `makeRadDim` at `0x4c553143`
The model argument is explicitly null at `0x4c55313e`
Wrapper `[0x4c4cb890,0x4c4cb907)` preserves that argument and forwards it
unchanged at `0x4c4cb8e2`
Thus a native retained authoring path uses the null-document presentation
constructor branch while still retaining a real profile and model for ownership
and subsequent registration
It is not necessary to reinterpret a null style/document argument as a null
feature owner

After a successful display construction, the same branch performs these
operations in order:

1. Obtain the display's actual model-dimension handle at `0x4c553162`
2. Assign the newly constructed profile as its feature owner through
   `moDimHandle_c::setFeatureOwner` at `0x4c553170`, with null component argument
3. Obtain the same display handle again and call
   `moModelFeature_c::nameParameter(handle,1)` at `0x4c55318b`

This branch retains the created display in the sketch's display collection
It is distinct from the caller at `0x4c4db612`, which names a temporary radial
dimension and subsequently removes its display through `deleteDispDim` at
`0x4c4db6da`
A constructor's existence or an ID allocation does not establish that its
object survives in the final graph

For an ordinary `sgCircleDim`, `setFeatureOwner` resolves the dimension through
handle virtual `+0x730` and writes the actual feature pointer to dimension
runtime `+0x40` at `0x4c84c2b8`
The dimension's virtual `+0x2c8` and this handle's `+0x468` both use the zero
return target for the ordinary radial branch, skipping the extra reference/3D
owner propagation
This operation does not write handle `fe8`
At this owner-assignment boundary, the local handle keeps its absent
global-feature reference; its
ordinary `moSkDimHandle_c` wire branch contains `ff0` as an archive reference
to the **same owning `sgSketch` object**, followed by value-dimension index
`ff8`
It does not embed a second independently constructed sketch or replace this
reference by the `sgCircleDim` object
The current shared schema records the distinction in `handle_has_gfr`

The naming and ID dataflow is **confirmed static** for this bounded branch:

| Operation or field        | Rule                                                                                                                                                                                       | Native evidence                                                                                                                                                      |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Candidate name            | Ask the actual dimension to generate a name for integer candidates beginning at one                                                                                                        | `nameParameter` starts at `0x4bea144b`, calls handle `genParamName` at `0x4bea1470`; `0x4c840ed0` dispatches to dimension virtual `+0x1e0`                           |
| Name vocabulary           | Ordinary `sgCircleDim` uses the shared `Dimension_c::genParamName`, whose recorded prefix is `D` followed by the decimal candidate number                                                  | Circle vtable `0x4cf79588`, slot `+0x1e0` to `0x4c820f20`; prefix pointer `0x4db03700`, also bound in the profile construction record                                |
| Collision handling        | Retry increasing integer candidates when the feature's existing display-handle names or additional registered name objects fail the native comparisons; ignore the very handle being named | `0x4bea14f0`–`0x4bea1566`, self-handle comparison `0x4bea150f`, additional feature-name walk `0x4bea157d`–`0x4bea15bb`, retry branches `0x4bea161d` and `0x4bea1637` |
| Fresh first name          | `D1` when the profile has no other named display dimensions or additional registered name objects                                                                                          | First candidate one and empty collision walks; derived from the stated new-profile operation, not a saved dimension                                                  |
| Apply chosen name         | `moDimHandle_c::setName` resolves the dimension and invokes virtual `+0x220` with the chosen name and flag one                                                                             | Call `0x4bea15e4`, dispatch `0x4c84c77a`                                                                                                                             |
| Sketch-dimension override | `sgCircleDim` slot `+0x220` targets `0x4c430bc0`; it delegates to shared `Dimension_c::setParameterName` at `0x4c430c20`                                                                   | Direct circle vtable read and override instructions                                                                                                                  |
| Parameter name object     | Apply the chosen text through `moParameter_c::setName`, retaining the parameter's actual node-name object at `f18`                                                                         | `0x4c821c67`; shared name-object construction already mapped in the profile ledger                                                                                   |
| Dimension persistent ID   | Allocate through the owning non-viewer model's shared header only when dimension `f50==-1`, in the ordinary allocation mode; write the returned ID to `f50`                                | Test `0x4c821c6c`, owner/model chain `0x4c821c7c`–`0x4c821ca3`, viewer test `0x4c821cbe`, ordinary `getNewID` call `0x4c821d0b`, store `0x4c821d11`                  |
| Repeated naming           | Preserve an already allocated `f50`; changing or reapplying the name does not allocate another ID through this branch                                                                      | Non-`-1` branch at `0x4c821c70`                                                                                                                                      |
| Parameter node ID         | Retain the independent parameter-node constructor ID; dimension ID allocation above does not write parameter `f08`                                                                         | Parameter-name call followed by allocation into the dimension's `+0x50`, not into the parameter                                                                      |

The native name-collision comparison and substring conventions have not been
fully classified here; `D1` for the bounded empty-name case is proved, but an
unqualified general collision policy must not be invented from that case
The header allocator is shared with feature IDs and other dimensions; neither
the name suffix nor the sketch value-array index is a persistent-ID formula
The special global allocation mode, viewer path and detached/external ownership
paths are outside this branch
After the normal new-ID allocation, the native routine may also mark all
configurations for rebuild at `0x4c821d54`, according to its model/configuration
and flag predicates
Completed configuration progress must account for actual allocated IDs

The sketch override checks whether the name changed and scans equation-driven
splines before marking the profile dirty
That spline walk is empty for the stated local circle/arc graph
The handle's earlier rename helper at `0x4c84aec0` enumerates opened models and
their equation relations to rewrite existing dimension-name references
With no such equation elements in the bounded fresh graph, its mutation body
does not run; this is not a hidden global-feature-reference allocation rule
It does not establish a complete general equation-registration lifecycle
Dimension reference counts must still follow actual handle construction,
cloning, attachment and destruction; one display entry alone is not proof of a
serialized reference-count constant

## Fresh radial display fields and later-mutation boundary

`moDisplayRadialDim_c` has runtime-class record `0x4db03798`, size `0x1140`,
raw schema `0x80000001`, loading factory `0x4c825270`, vtable `0x4d255be0`
Its serializer slot `+0x28` is `0x4c8320a0`, the active `RADIAL` schema in
`ResolvedDims.py`, following the shared `DISPLAY_DIM` base
Fresh constructor `[0x4c8bfc10,0x4c8bfe5a)` has SHA-256
`bc2bbf09a91cdcb5c68b134df358fb3c8b7e61c83fecf2b1096249c1012e90ba`
It calls the actual handle-and-position display base constructor
`[0x4c86ede0,0x4c86f54c)`, SHA-256
`8578099b606653b94a334183a2a0ce7708c83a17e357628634477f414d61eebc`
It must not be substituted by the feature-dimension overload without checking
their different handle and presentation operations

The following table classifies the radial-specific **constructor state at the
direct initialization boundary**, before style/update helper effects
It does not classify the final saved/current display as an all-zero structure

| Current 2026 wire field, in radial serializer order | Constructor classification and rule                                                                                                  | Direct evidence                                                                                                               |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `ffd8`                                              | Constructor flag vocabulary `0x80086` initially; subsequent flag operations remain ordered mutations                                 | `0x4c8bfc7f`; later constructor OR operations `0x4c8bfe0f` and `0x4c8bfe27` add `0x100000` and `0x200000` respectively        |
| `ffe0`, `ffe8`, `fff0`, `fff8`, `f1000`, `f1008`    | Six constructor zero doubles; not a proved universal post-update cache value                                                         | Zero stores `0x4c8bfc89`–`0x4c8bfcac`                                                                                         |
| `f1010`, `f1028`                                    | Two constructed zero points initially; derived witness-point state after later update, unresolved as final values                    | Two-element point construction `0x4c8bfcb3`–`0x4c8bfcd8`; actual later writes described below                                 |
| `nfc0`, `ffc0`                                      | Count and entries from an initially empty string collection                                                                          | Collection members zeroed at `0x4c8bfc6a` and `0x4c8bfc71`; no captured string rows                                           |
| `f1050`                                             | Null Hole Wizard callout-data pointer initially                                                                                      | `0x4c8bfcf3`                                                                                                                  |
| `f1048`                                             | Constructed empty string                                                                                                             | `0x4c8bfce5`–`0x4c8bfcec`                                                                                                     |
| `f1068`                                             | Null auxiliary display-list pointer initially                                                                                        | `0x4c8bfd0b`                                                                                                                  |
| `has_f1060`, optional `f1060`                       | Presence zero from null transform pointer in this ordinary caller; caller-supplied-transform alternative has its own allocation rule | Null store `0x4c8bfd04`; conditional copy allocation `0x4c8bfd6b`–`0x4c8bfdac`; ordinary caller supplies null at `0x4c55f130` |
| `f1090`                                             | Null mirror helper initially                                                                                                         | `0x4c8bfd27`                                                                                                                  |
| `ffd4`                                              | Constructor zero from the upper half of the eight-byte `+0xfd0` store                                                                | `0x4c8bfc78`                                                                                                                  |
| `f10a8`                                             | Null Hole Wizard information initially                                                                                               | `0x4c8bfd35`                                                                                                                  |
| `f10a4`                                             | Constructor false byte, serialized by the current schema's integer field                                                             | `0x4c8bfd2e`                                                                                                                  |

The retained null-document path above can reuse the shared, independently
computed null-document display initialization rules, with explicit semantic
presentation choices such as design intent and selected leader
It does not require copying a document's saved dimension-style data
When a real model is supplied instead, initializer `0x4c88a680` reads its
`moDimDefs_c` at `model.getDetailDefs()+0x13b0`, rather than assigning universal
precision constants: `f870/f874` come from definition `+0x6c`; centre-text flag
`f8a4 & 0x10` comes from `getDimCenterText`; `ff00` comes from definition
`+0xc0`
Type-specific definition lookup supplies `fb68/fb6c` from definition `+0x0c/+0x10`,
`f8ec` from `+0x84`, `ff10` from `getShowDualSplit`, `fb64` bits `0x1000/0x2000`
from nonzero definition `+0x78/+0x9c`, and `fe40` from definition `+0x08`
Those are style-input formulas, not constants learned from saved controls

Text display kind is also computed, rather than copied from a public enum
Initializer `0x4c889480` calls radial virtual `+0xae0`, target `0x4c8c9f30`,
then the text object's virtual `+0xa8`, the already mapped kind setter
Under its explicit valid-handle, no-callout, null-special-data, ordinary-radial
conditions, that function selects text kind `0x11` for diameter and `0x14` for
radius
The diameter test dispatches through `0x4c8d2020` to handle `isDiametric`
(`0x4c847730`) and circle-dimension virtual `+0x268`, target `0x4c42a7f0`,
which compares `f80` to `0x0f`
The radius branch's ordinary-radial condition is `ffd8 & 0x40 == 0`
Different callout or linear-display predicates select other text kinds
These are **confirmed static conditional rules**, not a measured final text
kind or a promise that later formatting preserves it

The display base's `SelLeader` field `ff80` is not initialized by the inspected
handle-and-position constructor either
The existing [uninitialized-leader gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Profile/UninitializedDisplayLeaderSelection.md)
therefore remains relevant: an explicit signed-32-bit presentation choice or
a separately proven neutral state is required
Allocator contents and zero found in a save are not defaults

**Unresolved final-state boundary:** fresh radial construction invokes
`updateDimension(position)` at `0x4c8bfddc`
That routine at `0x4c8db220` computes reference/text placement and invokes the
virtual engine-update method at `0x4c8dbc27`, bound to `0x4c8dbcf0`
The latter can write `f1010/f1028` through `0x4c841110` at `0x4c8dc171`, then
transform and further update those points at `0x4c8dc198`–`0x4c8dc1dd`
Constructor zero points therefore cannot be emitted as a proven final witness
rule
The following section closes the explicit full-circle witness assignment and
bounds the non-full-arc endpoint path
Selected later graphics-update branches, radial flag mutations, final
prefix/formatting, tolerance ownership and remaining presentation coordinates
must still be closed before a radial display writer is justified

## Full-circle zero witnesses and bounded arc endpoint ordering

All addresses below use the hash-bound model DLL named above
The relevant complete PE unwind extents and function fingerprints are:

| Function or boundary             | Extent                    | SHA-256                                                            |
| -------------------------------- | ------------------------- | ------------------------------------------------------------------ |
| `moDimHandle_c::getArcEndPoints` | `[0x4c841110,0x4c84121e)` | `45675724d2357abdeefffc10d7729060f852a2f03ff1f4ce5e7567954321f401` |
| `sgCircleDim` virtual `+0x140`   | `[0x4c41ccd0,0x4c41cf1b)` | `749c08df8e557aecf980d3fc80b267bc836b4c159be9df1c8e2d7f52553be6c6` |
| Radial engine-update method      | `[0x4c8dbcf0,0x4c8dda24)` | `236de00145cb837b66d1f0e91f1a414d646e3a04c39ecf847d713732111bcf11` |

The caller reaches the ordinary radial witness block only when its earlier
update-state checks permit continued graphics work and `ffd8 & 0x40 == 0`
The explicit gates include display runtime `+0xae0 == 0` at `0x4c8dbf7e`,
the false virtual `+0xd20` result tested at `0x4c8dbf97`, and the radial/linear
flag branch at `0x4c8dc153`
No final result is inferred for a path that skips this block
At `0x4c8dc171`, `getArcEndPoints` receives `&display.f1010` as its first point
output and `&display.f1028` as its second

The handle wrapper resolves its actual dimension through virtual `+0x730`
and calls that dimension's virtual `+0x140` at `0x4c841157`
The `sgCircleDim` vtable `0x4cf79588` binds this slot to `0x4c41ccd0` for both
radius type `3` and diameter type `0x0f`
That method first requires its `h1` at runtime `+0x130` to be an `sgArcHandle`
and valid, then calls `isCircle` at `0x4c41cd36`
For a valid full circle, the identical endpoint-index predicate returns true
and branch `0x4c41cd3d` goes directly to the false return at `0x4c41cefc`
It does not assign either output point or execute its plane/endpoint work
Point type two and the radius/diameter dimension type are not used by this
circle admission test

The handle wrapper tests the false result at `0x4c84115a` and returns zero
through `0x4c841207`, skipping all abbreviated-view and view-tag conversions
The caller's false branch then explicitly constructs the point `(0,0,0)` at
`0x4c8dc187`, from three scalar registers cleared immediately beforehand
It assigns that point to `f1028` at `0x4c8dc198` and then to `f1010` at
`0x4c8dc1a8`, and jumps over its plane-transform branch at `0x4c8dc1b9`
Therefore the operation-derived rule **at this boundary** is:

`valid full circle + reached ordinary radial witness block ->`
`f1010 = f1028 = (positive-zero, positive-zero, positive-zero)`

This is an explicit native assignment, not retention of constructor seeds and
not a value observed in a saved stream
The rule does not depend on circle centre, radius, seam/marker coordinate,
dimension parameter value, presentation position or plane transform
It applies to both radius and diameter representations of the full circle
No null-component or identity-transform assumption is needed for this particular
zero branch: all handle conversions and the caller's final transform are skipped
The owning local graph must independently prove handle validity and full-circle
identity; the same helper also returns false for invalid/non-arc inputs, so false
alone is not validation of a generated circle

For an ordinary **non-full arc**, the dimension method has a different proven
branch
It obtains native start/end point handles through arc virtual `+0x1f0/+0x1f8`,
bound to `0x4c606160` and `0x4c605fb0`
Let `S` and `E` be their native `firstPoint` results, and let `T` be the
dimension plane returned through dimension virtual `+0x198`
For a 2D sketch, the method computes the native inverse of `T` at
`0x4c41cd9a`; for a 3D sketch it takes a different branch outside this bound
The direction test at `0x4c41cdc1` determines the pair:

| Arc direction | First helper output             | Second helper output            |
| ------------- | ------------------------------- | ------------------------------- |
| Positive      | `S` transformed by `inverse(T)` | `E` transformed by `inverse(T)` |
| Nonpositive   | `E` transformed by `inverse(T)` | `S` transformed by `inverse(T)` |

The method returns one only after those assignments, at `0x4c41cef5`
The supported constructor vocabulary remains `+1/-1`; this native branch test
does not justify accepting arbitrary direction integers

For the bounded local handle with runtime `+0x168/+0x170` both null,
`checkNapplyTransformforAbbrView` (`0x4c83edf0`) exits through `0x4c83ee94`–
`0x4c83ee96` without changing either helper output
For null view tag at handle `+0x130`, each `convertWithViewTag` call
(`0x4c83fd00`) exits at `0x4c83fd75`–`0x4c83fd78`
The handle constructor `0x4c83c360` initializes these three context pointers
to null at `0x4c83c3fd`, `0x4c83c404` and `0x4c83c45a`
These are explicit local-context conditions, not a claim that all drawing or
component contexts are equivalent

When the helper succeeds, the caller transforms both outputs at
`0x4c8dc1c9` and `0x4c8dc1dd` by its own current plane transform
The ordinary no-override path uses the dimension plane; optional display
`f1060` and handle `+0x120` transforms require their own composition rules
The inverse-then-forward sequence must not be silently replaced by an identity
matrix, a transpose, fitted witness coordinates or a different arithmetic order
This pass has not fully bound native `firstPoint` coordinates and the plane
lookup to every neutral 2D frame, nor classified nonnull context transforms
It therefore records the proven endpoint ordering and operations without
claiming a complete general arc witness formula

**Remaining boundary:** the caller continues after `0x4c8dc1e3` into later
presentation calculations
This finding does not prove that every later lifecycle path preserves the two
points, that every other serialized display field is complete, or that a new
generated circle opens/rebuilds/edits correctly
Full-circle zero witnesses are **confirmed static at the stated update
boundary**; persisted final-state and held-out native acceptance remain open

## Type-two circle marker and solver-coordinate boundary

The exact `sgPointHandle::isUniqueCirclePoint` function is
`[0x4c5ff0a0,0x4c5ff0d8)`, SHA-256
`d97745784478b33284403a972607d37c39f1c4a1e289942df5c042eb215a9471`
The same hash-bound model DLL supplies this function and the caller below
It resolves the point, returns false when point `f54 & 1` is nonzero, and
otherwise returns whether point `fe4 == 2`
It does not inspect point usage counts, arc endpoint indices, radius or centre
The name alone is not a proof that a point belongs to exactly one circle
For the valid local permanent type-two marker already described, the result is
true; the owning graph must independently establish the actual circle identity

The solver routine at `[0x4c5167d0,0x4c5172c9)` has SHA-256
`df3e770b70119f8c3347baaf4a2c84ea821035c8cff8c4ca766aafd25856b4da`
Its initial point loop calls this predicate at `0x4c516915`
A true result branches at `0x4c51691c` to write one into the point's temporary
skip mask at `0x4c51697e`–`0x4c51698a`
The later ordinary point-coordinate loop tests that mask with `0xfffffffd`
at `0x4c516bd7` and skips to the next point when the test is nonzero
Thus this type-two marker does not take the ordinary coordinate-write calls
at `0x4c516d44` and `0x4c516d93` in that pass
This is a **confirmed static** branch result, not a measured solver run

Skipping the ordinary loop does not prove an unchanged final marker coordinate
The same routine has a later branch that calls
`sgArcHandle::findUniquePointOnCircle` at `0x4c5170c8` and, when that call
returns true, writes a point coordinate at `0x4c5170dc`
The [marker placement record](CircleMarkerPlacement2026.md) derives the
angular search, creation fallback and conditional rebuild rule from the native
helpers, while retaining unresolved collision and numerical boundaries
An arbitrary constructor coordinate or a polygon update rule is not a substitute
No circle marker coordinate, final point status, geometry stamp or solve result
has been accepted from generated output

## Remaining work before curved output can be claimed

- After the native family lock, extend the shared builder's conservative guard
  for local arcs only where the complete graph satisfies the scanner conditions
  above and the separately proven `f188` conditions
  Prove the independent constraint-validator paths before broadening their guards
  The scanner's static false result does not establish a finished curve update
- Trace the first solve, point and arc status mapping, final stamp, creation IDs,
  permanent markers and auxiliary point creation for newly authored circles and
  arcs with healthy controls
  Type-two circle markers have a special coordinate-update skip predicate
  `isUniqueCirclePoint` at `0x4c5ff0a0`; polygon point observations do not cover it
- Finish radial name-collision conventions, handle reference counts, final
  display and tolerance lifecycle left unresolved above, and recover angular
  dimension construction
  Measure edit/rebuild behaviour and completed constraint-use counts
  The existing serializer and the partial constructor graph do not supply those
  remaining rules
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
