# SOLIDWORKS 2026 profile construction

Status: fresh polygon profile and live blind-depth graph implemented, no generated profile or pad accepted

This extends [PolygonConstruction2026.md](PolygonConstruction2026.md)
The eight schema ladder controls have contributed to derivation and are not held-out inputs
The oracle owner locked the new polygon corpus before the family construction path was implemented
The lock is commit `577a5127a`, `re/solidworks/v2026/heldout/polygon/Lock.json`, with lock SHA-256 `abc1724a8856083a9c5e7054cd85b3035dc7da8423063f0caabd07a3e6f9dc40`
Lower-level constructor and archive helpers existed before that lock, as its chronology states
The writer author read the lock manifest and neutral input descriptions, but did not inspect native held-out streams or saved field values

## Additional constructor rules

Binary hashes are bound by [Manifest2026.json](../v2026/Manifest2026.json)
Addresses use `sldmodu.dll` base `0x4b140000`, `sldmgu.dll` base `0x31dd0000`, and `sldmfcu.dll` base `0x3c800000`

| Field or operation | Rule | Evidence and confidence |
| --- | --- | --- |
| Normal profile entity `dflt` | `0`, because normal `moProfileFeature_c` virtual `+0x1ed8` returns zero | Constructor `sldmodu 0x4c0ca780` installs vtable `0x4d0e8e80`; slot target `0x4b27cbe0`; entity predicate `0x4c3e22e0`; confirmed static |
| Entity visibility | Layer `-1`, by-layer mask `31`, colour `0xffffffff`, line type `-1`, line width enum `-1`, visibility flags `3` | Entity constructor `sldmodu 0x4c3e1030` passes explicit arguments to `0x4c151050`; confirmed static |
| Entity line width | `f06=0`, `f00=-1.0` | `sldmodu 0x4c3e1085` passes enum zero to `sldmfcu 0x3c84a8f0`; confirmed static |
| Entity line type `f38` | Native constructor value one for the fresh branch; separate from constraint status `f34` | Serializer `0x4c583460` loads ASCII key `LineType` at `0x4d1c90b8` through instruction `0x4c58387a`, then reads `+0x38` at `0x4c5838a7` and emits u16 at `0x4c5838ae`; confirmed static |
| Visibility line width | `f06=-1`, `f00=-1.0` | `sldmodu 0x4c3e10f2` passes enum minus one to the same constructor; confirmed static |
| Deferred indices | Keep endpoint and handle targets as object references, resolve owning-array indices when the field is read for storage | Native point/line lookup and framing addresses in the polygon ledger; derived implementation |
| Transform | Basis rows, authored translation, scale one, no perspective extension | `sldmgu 0x31e26880`, `0x31f09820`, `0x31e03ce0`; confirmed static |
| Active compact transform keys | `has_matrix`, optional matrix `f08`, translation `f58/f60/f68`, scale `f70`, flags `f78` | Sorted registry loading installs the first provisional definition from `serial/defs/Definition.py`; later provisional definitions do not replace it |
| Sketch line display | A null sketch line-display pointer is serialized through the default line-display constructor: empty string, width enum `-1` and float `-1.0`, line type `-1`, final integer `1` | `sldmodu 0x4c5916f0` null-pointer branch; `sldmfcu 0x3c802910`; confirmed static |
| Sketch collections | Fresh entity, dimension, pattern, and auxiliary arrays are empty; counts derive from their current collections | `sldmodu 0x4c495450`; confirmed static |
| Relation manager | Relation list and equation-value map are empty | `sldmodu 0x4c603200`; confirmed static |
| Block manager | Block map, secondary map, and handle-data map are empty | `sldmodu 0x4c8f5ac0`, `0x4c8f9680`; confirmed static |
| Loop and slot managers | Loop collection is empty; slot counter `f10=0` and slot collection empty | `sldmodu 0x4c452ac0`, `0x4caace30`; confirmed static |
| Profile raw storage | The dynamic-array pointer at profile-data `+0x190` starts null; its serializer emits only u32 element size zero | `sldmodu 0x4c0ca000`, `0x4bb09f20`; confirmed static |
| Modification stamp | Starts at one, and line permanence increments the sketch stamp once per call; the canonical one-call-per-line construction gives `1+n` | `sldmodu 0x4c495450`, `0x4c5d1740`; point position-change logging `0x4c5d0b90` does not increment it; confirmed static for the stated sequence |

`ordinary_point` applies the native position setter and represents a two-dimensional ordinary point before segment use
`ordinary_line` represents its constructor before permanence and adjacency operations
These constructor operations are also used by the polygon construction path
They do not claim preservation of source dimensions or acceptance of a generated pad

`new_sketch` represents the native empty sketch constructor, including its managers
`new_profile` extends an allocated `moProfileFeature_c` supplied by the model factory
It binds a supplied `moCompRefPlane_c` node, constructs the empty sketch, and retains its owner link
Its profile cache is null and its raw dynamic storage is empty by the constructor rules above
This helper is the empty constructor graph used by the polygon-family emitter

`closed_profile` constructs one ring of arbitrary `n>=3` ordinary lines from semantic 2D vertices
It preserves authored vertex order and binds the supplied plane frame
It rejects duplicate vertices, zero or nonfinite area, intersecting nonadjacent edges, and nonfinite transformed coordinates
Intersection validation uses an AVL sweep over exact rational representations of the emitted f64 coordinates
It checks adjacent edges for backtracking overlap, queries vertical edges against the active ordinate range, and checks newly adjacent sweep neighbors
Its comparison work is `O(n log n)` rather than checking every edge pair
This algorithm does not change the authored vertex order or emitted coordinates
Points and lines have separate creation-id sequences and line permanent markers derive from the immutable node order
Both wire record order and handle/endpoint resolution use that same `NodeOrder`
The identity-to-index map is built lazily once when fields are read for emission, giving linear total index-resolution work
Array counts read the active collection rather than a separate copied count or an obsolete list
The sketch is unconstrained because this input contract contains vertices and no authored sketch dimensions or relations
This does not claim support for a neutral sketch that contains additional authored dimensions or constraints

## Runtime schema audit

The initial complete-file rejection exposed an unrelated class whose runtime schema is zero, so a generic schema-one assumption is unsafe
This audit covers the 19 class types named by the sketch and dimension builder layer, including the allocated profile inputs
It reads each named `CRuntimeClass` record from the locked DLL, checks its class-name pointer, and reads `m_wSchema` at record `+0xc` and factory pointer at `+0x10`
Every audited type used with an emitted class header has the existing wire schema one
Shared model, plane, metadata and container classes require their own audits and are outside this table
The raw versionable runtime value is `0x80000001` for the listed model-DLL types and `1` for `suObList`
These are per-class native metadata rules, not values fitted to a saved file

| Class | DLL | Runtime-class record | Raw schema | Current archive role |
| --- | --- | --- | --- | --- |
| `sgSketch` | `sldmodu` | `0x4dafc108` | `0x80000001` | Header schema one |
| `sgPoint` | `sldmodu` | `0x4dafac08` | `0x80000001` | Embedded point fields in this path |
| `sgLine` | `sldmodu` | `0x4dafbe68` | `0x80000001` | Embedded line fields in this path |
| `sgPointHandle` | `sldmodu` | `0x4dafadb8` | `0x80000001` | Header schema one |
| `sgLineHandle` | `sldmodu` | `0x4dafc048` | `0x80000001` | Header schema one |
| `sgLogG1Dim` | `sldmodu` | `0x4d1c6c58` | `0xffff` | Embedded constraint fields only; no factory or class header |
| `suObList` | `sldmfcu` | `0x3ce6f5d0` | `1` | Header schema one |
| `moProfileFeature_c` | `sldmodu` | `0x4dad90f0` | `0x80000001` | Allocated input node, header schema one |
| `moOriginProfileFeature_c` | `sldmodu` | `0x4dad9210` | `0x80000001` | Allocated input node, header schema one |
| `moFavoriteHandle_c` | `sldmodu` | `0x4dad8c10` | `0x80000001` | Header schema one |
| `moLengthParameter_c` | `sldmodu` | `0x4daefb70` | `0x80000001` | Header schema one |
| `moAngleParameter_c` | `sldmodu` | `0x4daefba0` | `0x80000001` | Header schema one |
| `ParallelPlaneDistanceDim_c` | `sldmodu` | `0x4db03cd8` | `0x80000001` | Header schema one |
| `AngleDim_c` | `sldmodu` | `0x4db03dc8` | `0x80000001` | Header schema one |
| `moFeatureDimHandle_c` | `sldmodu` | `0x4db03f48` | `0x80000001` | Header schema one |
| `moDisplayDistanceDim_c` | `sldmodu` | `0x4db03768` | `0x80000001` | Header schema one |
| `moDisplayAngularDim_c` | `sldmodu` | `0x4db03828` | `0x80000001` | Header schema one |
| `moEndSpec_c` | `sldmodu` | `0x4dad9180` | `0x80000001` | Header schema one |
| `moFromEndSpec_c` | `sldmodu` | `0x4dad9150` | `0x80000001` | Header schema one |

The same records give native object sizes `0x158` for `sgPoint` and `0xf0` for `sgLine`
Those sizes matter when an observation hook resolves an entity from its native array and index
They do not change the serialized record lengths, which remain schema- and field-dependent

## Blind end-spec construction

| Subject | Rule | Evidence and confidence |
| --- | --- | --- |
| Extrusion constructor | Two distance display nodes are created with IDs 1 and 2 using `ParallelPlaneDistanceDim_c`; two angular display nodes use IDs 3 and 4 with `AngleDim_c` | `sldmodu 0x4bad3ab0`; confirmed static |
| End conditions | The fresh extrusion passes type zero for both ends to the end-spec constructor; the constructor uses single-end flag one | `sldmodu 0x4bad3ce5`, `0x4bad35c0`; confirmed static |
| End-spec remaining fields | Null direction/reference pointers, empty reference arrays, zero disabled draft/reverse flags, `f128=1`, and other zero constructor flags | `sldmodu 0x4bad35c0`; confirmed static |
| Feature fields | Node flags add `0x140`, `f810=-1`, `f838=0.0`, and `f818` refers to the constructed end specification | `sldmodu 0x4bad3ab0`; confirmed static |
| Runtime-only from-offset dimension | After `D1` through `D4`, from-end constructor creates zero-length `D19`; retain its graph and allocator identity even when type zero omits it from storage | `sldmodu 0x4bad3e00` calls `0x4c8a4840` unconditionally; confirmed static |
| Profile dependency | Sketched-feature profile lookup scans its node list at `+0x60` and recognizes profile children | `sldmodu 0x4c5aa750`, add-profile call `0x4bad2bb0`; confirmed static |
| Length parameter | Runtime class `moLengthParameter_c`, schema 1, size `0x70`, reuses double-parameter serializer `0x4c177fe0` | Runtime record `sldmodu 0x4daefb70`, factory `0x4c1764c0`, constructor `0x4c19bbe0`, vtable `0x4d123bf0`; confirmed static |

`blind_end_spec` requires four actual display-dimension nodes
It follows their model handles to the feature dimensions and driving length/angle parameters
It requires matching positive depth values and zero draft angles
`blind_extrusion` receives an allocated body-feature node from the model factory, adds its profile dependency, and checks its authored depth against the driving parameter
Neither function replaces a dimension with a scalar, null pointer, captured record, or incomplete stand-in
Native distance constructor `0x4c8a4840` calls display-dimension constructor `0x4c86f550` and initializer `0x4c889480`
`feature_dimension` now constructs those objects and their live parameter connection
`live_blind_extrusion` builds four such graphs, constructs their end specification, and attaches the profile dependency to the supplied extrusion node
The result retains separate parameter, dimension, handle, display, end-spec, profile and feature object identities
Changing the first length parameter changes the graph's live forward depth; target rebuild and dimension-edit acceptance remain unproved
`ExtrusionGraph.dimensions` and `dimension_count` describe the four serialized display graphs
`from_offset` retains the fifth constructed graph for `D19`, and `constructed_dimensions` includes it
Its display remains at from-end `f28`, which the serializer omits when `t=0`
This is an actual constructor-lifecycle object, not an arithmetic adjustment to the allocator
Ordinary part vtable `0x4d1252d8`, slot `+0x1250`, targets `moModel_c::isViewerModel` at `0x4c02d7d0`
With argument zero it reads `(~(model[0x2b0] >> 2)) & 1`; constructor `0x4c00edb0` initializes that word to `0xc`, giving false
The naming path therefore consumes the normal header ID for the transient `D19` dimension

The fresh `moFeatureDimHandle_c` local dimension is schema key `ff0`, corresponding to runtime member `+0xf0`
`moDimHandle_c` constructor `0x4c83c220` sets `+0x100=null`
Its `f100` serializer branch is an optional external/cache dimension, not the fresh local dimension
`moModDimHandle_c::Serialize` at `0x4c8346c0` writes the actual local dimension when its global reference pointer is null
An initial helper lookup through `f100` alone was refuted and corrected before full dimensional construction
The native display-dimension serializer writes a null backup definition for non-drawing models at `0x4c82e16d`, even though the constructor allocates a runtime backup object
The part writer can therefore emit `fef8=None` from the serializer rule rather than copying that runtime allocation

`moDisplayItem_c::Serialize` at `0x4ba4bc10` writes four point records and two vector records unconditionally in its 2026 store branch
Its constructor `0x4ba656a0` creates four zero points and two Y-axis vectors
The session preference at index `0x387` controls display flag `fb60 & 0x100`
The exported getter `isDesignIntent` at `0x4b28d700` and setter `setDesignIntent` at `0x4c895cc0` identify this as a semantic design-intent choice rather than a universal constant

## Live dimension construction ledger

All addresses in this section belong to the locked 2026 binaries named above
The constructor branches used here accept a null document pointer while retaining the supplied feature owner
The builder uses those branches for display style and does not copy ambient document or session settings
The explicit design-intent input replaces the native session lookup
This constructs a new presentation choice; it does not preserve an imported document's annotations or style

| Fields or operation | Role | Rule and binary evidence |
| --- | --- | --- |
| Forward and reverse length values | Input | Both constructors receive the authored depth; `moDoubleParameter_c::setValue` at `0x4c19cae0` writes `f58` directly and clears its alternate-value state |
| Draft values | Constant for this supported branch | Both `AngleDim_c` parameters receive zero; nonzero draft fails closed |
| Very short lengths | Domain restriction | `Dimension_c::SetValue` at `0x4c81fe00` clamps magnitudes below the binary constant `1e-14` at `0x4cdf9468`; the builder rejects those depths |
| Parameter class | Derived from dimension kind | Feature-dimension vtable `+0x3d8` targets `0x4c8214b0` for lengths and `0x4c821470` for angles; these create the corresponding runtime class and retain it at dimension `+0x28` |
| Parameter name | Derived | `Dimension_c::genParamName` at `0x4c820f20` formats the binary prefix `D` from pointer `0x4db03700` with the constructor's integer ID; blind extrusion uses `D1` through `D4` |
| Parameter node `f18` | Derived object reference | `moParameter_c::setName` at `0x4c19c9b0` calls `0x4b555250`, which creates or updates `moNodeName_c` at node `+0x18`; it does not place the name at `f48` |
| Parameter node `f08`, `f0c`, `f28`, `f2c`, `f20`, `f48` | Constructor state | Native node starts ID `-1`, flag `1`, mask `0x40000000`, secondary mask zero, empty string and null `f48`; parameter constructor `0x4c19baf0` calls flag routine `0x4c03ed90` with zero and clears `f0c` to zero |
| Parameter runtime reference count | Derived, not serialized by the current node schema | Factory call through parameter `+0x4d8` targets `0x4b2fe0b0`, incrementing runtime `+0x10` only |
| Parameter `f68` | Constant | Setter `0x4c19cae0` clears alternate-value flag `f68`; no `f60` alternate value is emitted |
| Dimension `f50` | Derived | `setParameterName` at `0x4c821c40` requests the model header's new ID for a new named dimension; `allocate(dimension, field="f50")` binds the shared allocator directly to this serialized field, without an extra node-ID proxy |
| Dimension `refcount` | Derived | Constructor `0x4c81f6d0` starts runtime `+0x20=0`; handle constructor `0x4c83c220` invokes `addRef` at `0x4c8205e0`; serialization at `0x4c8295c0` writes `+0x20`; the field reads the constructed handle collection length |
| Dimension `f48`, `f30`, `f54`, `f5c`, `f60`, `f68`, `has_f78` | Constructor state | Null tolerance and attachment pointers, zero design-table and mask fields, and no name-extension string from `0x4c81f6d0` |
| Feature-dimension points and optional geometry | Constructor state | `0x4c389df0` creates three zero points and null vector, transform and optional point pointers; flags derive from those null pointers |
| Angular `ff8` | Constant for this branch | Angle factory `0x4c825a70` sets runtime `+0xf8=1` |
| Handle base | Constructor state | Shared `component_reference_fields(component=None)` follows `moCompRef_c` default constructor `0x4b7e8390`; the actual local dimension remains an object pointer |
| Handle optional transforms, tags and cache | Constructor state | `0x4c83c220` sets null pointers, `f150=0`, `f154=-1`, and `f118=0`; fresh parts omit the drawing-point branch |
| Display object visibility and lists | Constructor state | `0x4be75d40` sets layer `-1`, by-layer mask zero, colour `0xffffffff`, line type and width enum zero, empty reference lists and null owner/view/cache links |
| Display item fields | Constructor state | `0x4ba656a0` supplies zero points, identity transforms, absent optional data, empty collections, three enum-zero line widths, flags `0x80080` and the serialized four-point/two-vector arrays |
| Display text | Constructor and initializer state | `0x4c852230` supplies empty text, null font, zero cached geometry and a `1e-6` by `1e-6` box; initializer `0x4c889480` calls text vtable `+0xa8`, target `0x4c859b50`, setting `f10` to display kind 2 for distance or 13 for angular and clearing the font pointer |
| Display precision, strings, points, flags and absent caches | Constructor state | `0x4c86f550` and `0x4c88a1e0`, using their null-document branch; the builder preserves their explicit assignments and flag expressions |
| Display `f5b0` | Derived native allocation description | Base display vtable `0x4d251808`, slot `+0xb10`, returns zero at `0x4b27cbe0`; initializer appends one zero double to `suDynArrayAlloc(8,16,1,8)`; `suDynamicGetStats` at `sldmgu 0x31def650` yields element size 8, growth 16, mode 1; count is one |
| Display compact identity transforms | Constructor state | Active compact transform schema plus native default transform `sldmgu 0x31f1d560` |
| Display raw identity transform | Derived canonical encoding | `sldmgu 0x31f1d9a0` writes 30 u32 words from matrix, identity flag, translation, scale, flags and zero tail; builder computes these words by packing numeric components, not from saved bytes |
| Raw transform padding | Computed neutral bytes | Reader `sldmgu 0x31f20fa0` reads all words, constructs the matrix from its nine doubles through `0x31e26970`, and ignores the padding word between matrix state and translation; the builder writes zero there; the native writer also explicitly zeros its final tail word |
| Display design-intent flag | Input | Explicit `design_intent` controls `fb60 & 0x100`; the remaining flag expression follows `0x4c86f550` |
| Display `ff80` / `SelLeader` | Input; neutral value unresolved | Store instruction `0x4c82e7ef` emits runtime `+0xf80`, which the inspected constructors do not initialize; setter `0x4c896990` writes an explicit leader index and shifted point without changing `SetPoint`; the builder requires a signed 32-bit input and supplies no default |
| Distance display fields | Constructor state | `0x4c8a4840` creates empty temporary contour holders, a zero shifted point and zero local counters; no radial-reference pointer |
| Angular display fields | Constructor state | `0x4c85a8d0` calls arc constructor `0x4c85aae0`; initializer `0x4c862790` sets X/Y vectors, fractions `0.1/0.9`, selectors one and arc flags `0x18`; zero draft remains unchanged by selector adjustment `0x4c862810` |
| Part backup object | Derived store rule | Non-drawing store path at `0x4c82e16d` emits null, even when the runtime constructor allocated a backup |

The native default `mgUnitVector_c` constructor at `sldmgu 0x31f19380` produces the zero vector
It does not produce the X axis
Only fields explicitly assigned `xAxis()` or `yAxis()` use those axes

`SelLeader=0` is not claimed as a proven neutral constant
The current graph requires an explicit presentation choice until its semantic no-selection state or a neutral value is independently established

## Origin profile construction

`origin_profile` constructs the separate document-origin profile from an allocated `moOriginProfileFeature_c`, the first plane wrapper and a frame at model origin
Native caller `0x4c02e060` constructs that profile, then invokes sketch initializer `0x4c49b980`
Origin constructor `0x4c0c9f80` delegates to the ordinary profile constructor and clears bits `2|4` in profile-data `f11c`
Its primary vtable `0x4d0ef510`, slot `+0x1ed8`, still returns zero, so ordinary point serialization keeps `dflt=0`

Initializer `0x4c49b980` creates `sgPoint(sketch,1,0)`, makes it permanent, sets it to `(0,0,0)`, constructs an `sgLogG1Dim` of type `0x11` and appends that constraint
The point remains the ordinary archive kind zero; sketch serializer `0x4c5916f0` assigns special kinds only to external points and `sgFramePt`
Point constructor `0x4c490970` supplies `fe4=1`, its separate point type
The constraint points to an actual `sgPointHandle` rather than a copied point index
Its point reference count derives from that constraint reference, following `sgEntHandle::addConstraintReference` at `0x4c5bd330` and common increment `0x4c3e1510`
`sgLogG1Dim` constructor `0x4c4103c0` and base `0x4c410070` supply constraint type `0x11`, `f90=2`, other zero status fields and `fa0=0xfffe`
Append routine `0x4c4a2b90` invokes reset `0x4c822050`, leaving serialized dimension refcount zero and parameter/tolerance pointers null

After sketch update, the initializer calls `setNeedsUpdate(0,1,null)` on the origin and its owner
Origin vtable `0x4d0ef510`, slot `+0xb8`, targets the feature wrapper at `0x4bb515c0`
That status-zero path invokes the prior-state query at virtual `+0xc0`, then unconditionally calls node setter `0x4c03ed90` with status zero
Instructions `0x4c03edf8` through `0x4c03ee99` store `f0c & 0xfffd7ff8`
The builder applies this proved mutation to the origin node
The wrapper's later nonzero-status side effects are skipped by branches `0x4bb5169c` and `0x4bb51770`
This does not close every indirect query or the preceding solver update
The owner operation belongs at this point in model composition; later polygon and extrusion insertion can dirty the owner again
It is not a rule to clear the final part's update state after those operations

The builder records the native subsequent `sgSketch::update` at `0x4c549ab0` as unresolved regeneration work
Its `_requires_update` metadata is explicit and does not claim post-solver cache/status identity or an accepted origin graph

## Sketch update dataflow

This pass applies the field, loop, handler and constraint analysis described in [Tupni, sections 3.3–3.6](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tupni-ccs08.pdf)
Operand consumers establish field roles, loop bounds establish record counts, handler targets distinguish record kinds, and branch expressions establish dependencies
This is static decompilation and disassembly analysis, not a dynamic taint trace or a Tupni execution
Runtime path coverage and target acceptance remain separate evidence

| Sink | Native dataflow | Result for the constructed graph | Status |
| --- | --- | --- | --- |
| Sketch `f188` | `sgSketch::update` at `0x4c549ab0` stores whether `0x4c6fcfc0` returns an inter-component reference | Zero for the current local point/line graphs with absent extension pointers, empty other geometry/reference arrays and `pd_f110=null`; origin's local logical point constraint does not add such a reference | Closed by static predicates; builder derives the value and fails closed when unsupported references are introduced |
| Derived-profile predicate | `moProfileFeature_c::isDerived` at `0x4c0de380` requires nonnull profile-data `+0x110` before testing a derived reference | False from the constructed null pointer | Closed static dependency |
| Constrained-status getter and setter | `0x4c53d2c0` reads sketch `+0x12c`, except for the session's special mode returning seven; setter `0x4b2a77c0` writes the supplied status to that field | Constructor state is known, but a complete post-solver status rule remains unproved | Unresolved post-update state |
| Separate saved status | `getConstrainedSavedStatus` at `0x4b2a74f0` reads sketch `+0x128`; serializer `0x4c5916f0` emits `f12c` followed by `f128`; `saveSketch` at `0x4c5a6170` delegates to that serializer | The store path does not copy the solver aggregate into `f128`; constructor one is retained separately rather than treating the two statuses as aliases | Closed field distinction; other lifecycle writes remain separate |
| Entity constraint state | `0x4c502b70` queries solver virtual `+0x218` for each point and line, then passes the result to `0x4c5077f0`; `setConstraintStatus` at `0x4c5d5370` writes entity `+0x34` | The solver result is a required dependency; constructor `f34=1` is not independent proof of its final value; adjacent `f38` is line type, not another solver status | Unresolved solver dependency |
| Entity colour | `setConstraintColor` at `0x4c5d5260` uses mapping `0x4c3e15b0`, then setter `0x4c3e29e0` writes entity `+0x30` | With the current `f54` mask, status one maps to colour five and status two maps to four; current `f30=5` matches status one, but does not prove the solver chose it | Closed mapping; final input unresolved |
| Dependency reset | `clearDependancyFlags` at `0x4c538d10` calls `0x4c5d3100`; for local handles it calls `0x4c3e2bd0(entity,0)` and `0x4c3e24a0(entity,0)` | The first masks `f56` with `0x3fff`; the second clears bit `0x8000`; constructor `f56=0` is unchanged | Closed static mutation for local geometry |
| Point cleanup | `cleanOutSketchPoints` at `0x4c4a6e30` considers removal only when a permanent point is invisible, local and has degree zero | Polygon vertices have degree two; origin type one is visible because point vtable `0x4cdd2d48`, slot `+0x190`, targets `0x4c491cb0` and tests mask `0x138a02` | Closed preservation predicate |
| Constraint validation tails | `0x4c4bbf40` iterates sketch `+0x58`; `0x4c4bbc60` examines offset dimensions and display dimensions | The current graph has empty block, offset and sketch-display collections; origin's one logical point constraint still requires its own validation and solver path | Closed empty loops; origin handler unresolved |
| Modification stamp | `0x4c5195d0` adds the results of `0x4c5167d0` and `0x4c516600` to sketch `f56c`; update `0x4c549ab0` has a separate model-reference increment at `0x4c54ad3c` | The separate increment is excluded for the current local graphs by the branch proof below; the point helper still depends on finite solved coordinates and the plane helper has an empty bound; insertion stamp remains separately derived as `1+n` | Model-reference increment excluded; solver coordinate delta unresolved |
| Pattern/spline/styled helpers | `0x4c46f1b0`, `0x4c5483f0` and `0x4c52f470` iterate their corresponding collections | Empty collections make these loops inactive for the polygon and origin inputs | Closed static loop bounds |

The jump table at `0x4c507948` maps raw solver status eleven to sketch/entity status one, raw one or ten to two, raw three to three, and raw zero/four/five/eight/nine to four
`0x4c5077f0` then applies validity, external-reference, underlying-offset and visibility predicates before storing the result
These are native branch rules, not evidence that a fresh free polygon or origin produced a particular solver result
The final aggregator at `0x4c502b70` prioritizes invalid geometry, status four and status three, then returns one when any contributing entity is status one, otherwise two when a nonzero status was seen
The `0x4c507b30` caller stores that aggregate in sketch `f12c`, except when its current state is the special mode seven

### Local update branch and stamp boundary

This proof uses static native control flow, independently of saved document values
`sgSketch::hasExternalReferences` at `0x4b94f7e0`, called with `(1,0,0)` by update, first tests the derived-profile reference, then offsets, intersections, silhouettes and the geometry collections
The current profiles have null `pd_f110`, empty non-point/line collections and local point/line entities
For each point and line, `sgEntHandle::isExternal` at `0x4c5ce0c0` delegates to `0x4c3e2020`; the latter returns false when entity `+0x48` is null
That pointer is the constructed `ext=None`
The origin's local logical constraint does not appear as an additional external-reference case in this scanner
The scanner therefore reaches its false return at `0x4b950303`

Update's selector at `0x4c54a446` clears `f37c` and its transform-work flag when the external-reference predicate is false
Tests at `0x4c54a537` and `0x4c54a543` then select the direct-solver target `0x4c54b10e` for both null and nonnull transform arguments
If the separate cached-solver/drawing condition is true, it also selects the direct branch
The alternate model-reference branch containing the explicit `f56c` increment at `0x4c54ad3c` is consequently unreachable for the current local graphs
This excludes that one increment; it does not prove solver success, unchanged coordinates or an accepted final stamp

The constructor at `0x4c495450` sets saved status one at `0x4c495cf8`, current status one at `0x4c495d02`, cached-solver pointers null at `0x4c495e8c` and `0x4c495ee9`, and initial stamp one at `0x4c4960bf`
These are offsets relative to the `sgSketch` object, not its separate profile pointer at sketch `+0x138`
The profile constructor `0x4c0ca780` initializes its own `+0x3e0` as integer `100000`; equal offset names do not make these fields aliases
Both profile vtables, `0x4d0e8e80` and `0x4d0ef510`, use target `0x4c0d71d0` for virtual `+0x1ee8`; that target returns only a drawing-view owner, so the constructed part owner does not activate its drawing-view flag

The point delta helper's skip cases are also explicit
`isUniqueCirclePoint` at `0x4c5ff0a0` tests point type two, `isVertexPoint` at `0x4c5fff80` tests type thirteen, and the helper excludes type eighteen separately
`getType` at `0x4c5fbff0` reads point `+0xe4`; it does not read `pflags`
Polygon points use `fe4=0` and the origin point uses `fe4=1`, so neither graph skips its points through these type cases
Their actual solved coordinates remain required evidence; a type rule alone cannot establish the changed-coordinate count returned by `0x4c5167d0`

The exported update signature fixes the observation ABI
On Windows x64, argument zero is the sketch in `rcx`, followed by transform in `rdx`, an `int*` in `r8`, and the update engine in `r9`
At entry, stack slots `rsp+0x28` and `rsp+0x30` contain the two integer arguments, `rsp+0x38` the constraint-balance pointer, and `rsp+0x40` the final double
The `sgConstrainedStatus_e` return is a signed 32-bit enum; instruction `0x4c54c4c0` moves it into `eax`
The internal coordinate helper has no exported formal prototype, but instruction `0x4c517278` writes its counter with `mov eax,r12d` before return `0x4c5172c8`
Its observed counter should therefore retain raw `rax` and a separate unsigned 32-bit interpretation; the decompiler's inferred `ulonglong` is not evidence of a wider counter

The next requested observation arms hooks before first authoring/rebuild on unrelated free polygons with three, eight and eleven lines
It records actual update entry/leave status and stamps, the coordinate helper's returned count, solver-commit deltas and point/line status-map entry/leave fields
Those training observations remain distinct from the locked held-out generated-output acceptance gate

Both polygon and origin graphs retain `_requires_update=True` until the remaining state rules are established

## Native boundary training observation

The oracle owner supplied capture `ladder-L1-retained.json`, SHA-256 `cda33fba8a5c340f08f31ff96ff0faeea7f69d23ec1fce551baaff03ce06a1d0`
Its authority is native API boundary observation, with `instruction_taint=false` and no absolute logical stream offsets
It records 2,693 events, zero dropped events, zero script errors and successful detach
The instrumented training control opened and rebuilt with one body and no reported errors or warnings
This control result is not acceptance of a generated file

The two sketch serializer calls observe constructor state on entry and loaded saved state on leave
Those transitions are loader observations, not evidence that sketch update computed those saved values
After loading, nine calls to status mapper `0x4c5077f0` observe one raw solver status one and eight raw statuses eleven
The control contains two authored sketch dimensions, so these observations do not establish the free-polygon solver result for arbitrary N
They do not supply constructor defaults or a captured modification stamp to the builder

The first `0x4c5195d0` hook read its solver-wrapper argument as a sketch and therefore produced invalid sketch-field snapshots
The actual sketch is the pointer at solver-wrapper `+8`, as the static decompile establishes
Those snapshots are excluded from status and stamp conclusions
The return value is a solver-success result, not the modification-stamp delta
Whole-update entry and leave observations at `0x4c549ab0`, with the corrected inner signature, remain needed across unrelated free-polygon inputs

## Contracts

Helpers use keyword-only semantic inputs and return `Core.Obj` nodes or typed field mappings
`DerivedFields` keeps authored and derived fields separate and refuses to replace a derived field
Endpoint references and handle references retain node identity
The archive serializer remains responsible for archive class and object indexes
No helper reads a file, saved record, table, oracle, or fixture at runtime

## Remaining construction

The semantic no-selection value for `SelLeader`, preservation of imported annotation/document style, post-update origin status, additional authored sketch dimensions/relations, post-insertion manager state, contour/chain regeneration, and neutral-document unit conversion remain required
The profile serializer address is `sldmodu 0x4bb1bdc0`
Null cached body has constructor/store/load evidence at `0x4c0ca000`, `0x4c254640`, and `0x4c253660`; this does not establish regeneration acceptance

## Verification

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md#stopping-conditions) define the stopping conditions:

> There are two acceptable stopping conditions.
> The first is success under every criterion on this page.
> The second is the end of the available context.
> Missing grammar is the work. It is not a blocker.

The current research does not meet those product criteria; unresolved native graph state remains active work

No local tests, builder/serializer imports, reproductions, or oracle calls were run
The edited Python sources passed static AST syntax parsing without importing or executing them
Process-boundary regression coverage executes remotely with the assembled builder
`PolygonProcess.py` now constructs fresh profiles and dimensional graphs in an isolated subprocess, writes their binary object archives into a container, decodes them, verifies byte identity and reference identity, then edits and re-encodes the live forward parameter
Its generated startup, input, construction, codec, reference, edit and report stages reside in focused modules under `tests/convert/solidworks/research/Polygon/`; `PolygonProgram.py` composes their exact declarations
The sketch component explicitly seeds its external profile owner in the archive map; it is not a complete part or a vendor-loadability check
Its cases cover variable N, a 10,000-line ring, crossings, touches, vertical overlap, adjacent backtracking and valid collinear edges
An additional 65,537-line case crosses the native handle threshold `0x777f` and endpoint threshold `0xffff`
The component archive also stores a later reference to the actual final adjacency handle and requires that decoding retain the same handle identity
For that large case it checks the native `0x7fff` large-map tag and six-byte reference width, in addition to full archive byte identity
This width-boundary case was not executed locally
It checks actual decoded dimension IDs and leaves parameter node IDs at their constructor value `-1`
The shared `BuildAudit` hook starts before builder/schema imports, permits actual import-loader code access and the bounded source-package/schema discovery needed during startup, then rejects runtime file access and child-process launches during construction

For PR head `4cb6785739079d6ebe1b745a21a8e63e49862b2d`, [native CI job 132714706575](https://github.com/TryUniCAD/Kit/actions/runs/43682093985/job/132714706575) passed all five existing `PolygonConstructTests.py` cases, including the 10,000-line ring, invalid geometry, editable depth and allocation assertions
The same job passed `FreshPartTests.py`, `LockedPartTests.py` and `ModelBuilderProcessTests.py`
It reported 138 passes and 158 skips in 40.09 seconds, after the shared model codec initialization repair
Its tested PR merge snapshot was `0d3d057f4eab945d708e12dbda3cfb0fadb9485d`
The origin-node lifecycle mask was included
At subsequent head `22a78891631498e176274289b2cafb00abc6b764`, [native job 132723081423](https://github.com/TryUniCAD/Kit/actions/runs/43684854129/job/132723081423) passed all six polygon cases, including the 65,537-line case, and reported 139 passes, 158 skips and one separate assembly-round-trip failure in 94.87 seconds
Its assembly failure was `bad class ref 32512 at 297` for the A0/A1 assembly CMgr and linked streams
At head `ee2eed2e4732e995fb8b0a7b281b8834cdf9a7f6`, the naming and focused-directory gates passed, and [native job 132729524301](https://github.com/TryUniCAD/Kit/actions/runs/43687022248/job/132729524301) again passed all six polygon cases
The job reported 139 passes, 158 skips and one separate assembly failure in 96.33 seconds
The assembly CMgr repair advanced the controls to 12 of 14 identical streams; both remaining resolved-feature streams stopped at offset 635 because `moHistoryCompItemData_c` had no schema
After the shared history/live-section and external-input repairs, [native job 132749668250](https://github.com/TryUniCAD/Kit/actions/runs/43693750759/job/132749668250) passed at head `af38f10bdecd5dee77375d8cbad7a1f68ee66660`
It reported 158 passes and 158 skips in 56.97 seconds, including `AssemblyRoundTests.py`, `FreshPartTests.py`, `LockedPartTests.py` and all six polygon cases
The tested synthetic merge was `783db24c98580b609b434bfdab0210900d80acbd`
Its generated construction artifact `14153212981` contains ten files, is 144,352 bytes, and has uploaded ZIP SHA-256 `6b3c5ee495570cef54ddec496eff349c83fae27d4e2d097c422fd6e31ec47c13`
These process results establish container/archive construction and decoding, not native application acceptance, rebuild correctness or body measurements

The first complete generated H3 candidate from parent revision `8e44d0eb5` was rejected during clean native opening
Candidate SHA-256 is `0c66da89db4d8f8386f0e597e14f69a5dfd6b6c0d4e82ffdd88cf7277726121c`
The oracle owner's `inspect-first.json`, SHA-256 `acf27f6dfdbefec4795bee97b93f0295d12a72d999fec4bcd2ab89d95cb15ddc`, records RPC failure `-2147023170` between two fresh, passing L1 training controls
Both controls opened and rebuilt with no reported errors or warnings and one body
This establishes a candidate failure, not its cause; the report does not isolate a profile, dimension, model or container defect
Native fault-boundary recovery remains required before any generated-output acceptance claim
It does not exempt arbitrary reads by filename suffix
The sketch-info component test selects `ctx874=1`, so its external profile-owner reference is actually present in the encoded grammar and its identity assertion remains meaningful
This coverage has only been syntax-checked locally and is pending its remote execution
The oracle owner's subsequent `candidate-H3-first.json`, SHA-256 `31ba472a3c00d8539f85a805bdf5c088df8c4f7aafbc148831d81fe677d6b625`, records six native exceptions and no events from the configured feature-constructor or sketch-serializer hooks
The owner-taking feature constructor `0x4bb38350` and the separate default constructor `0x4bb38710` are distinct observation boundaries; absence of one hook does not exclude every feature factory
No invocation of the hooked sketch serializer was observed, so that capture does not isolate the owned profile-load rules or establish whether their generated state is correct
The later native schema probe `candidate-H3-schema.json`, SHA-256 `78c581343341446555c9c02da5872ca3c6a08c665dcd9dc3eae2c9001f43e4dc`, identifies the first rejection at `uoJournal_c`: the runtime schema is zero while the candidate emitted one
The probe accepted the preceding History, Biography, ISO and line-font manager schema-one records
The shared definition repair uses exported native runtime-class metadata at `slduiu!0x4aef6660+0xc`, independently proving schema zero
This isolates the first observed schema mismatch; it does not establish that later generated graph state is accepted
Later documentation revisions require their own current-head CI and review evidence
The success criteria remain unsatisfied until held-out generated files pass target opening, rebuild, geometry measurements, feature-tree inspection, and dimension editing between healthy controls
