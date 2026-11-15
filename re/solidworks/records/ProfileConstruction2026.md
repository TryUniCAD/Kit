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

## Blind end-spec construction

| Subject | Rule | Evidence and confidence |
| --- | --- | --- |
| Extrusion constructor | Two distance display nodes are created with IDs 1 and 2 using `ParallelPlaneDistanceDim_c`; two angular display nodes use IDs 3 and 4 with `AngleDim_c` | `sldmodu 0x4bad3ab0`; confirmed static |
| End conditions | The fresh extrusion passes type zero for both ends to the end-spec constructor; the constructor uses single-end flag one | `sldmodu 0x4bad3ce5`, `0x4bad35c0`; confirmed static |
| End-spec remaining fields | Null direction/reference pointers, empty reference arrays, zero disabled draft/reverse flags, `f128=1`, and other zero constructor flags | `sldmodu 0x4bad35c0`; confirmed static |
| Feature fields | Node flags add `0x140`, `f810=-1`, `f838=0.0`, and `f818` refers to the constructed end specification | `sldmodu 0x4bad3ab0`; confirmed static |
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

The builder records the native subsequent `sgSketch::update` at `0x4c549ab0` as unresolved regeneration work
Its `_requires_update` metadata is explicit and does not claim post-solver cache/status identity or an accepted origin graph

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

No local tests, imports, reproductions, or oracle calls were run
The edited Python sources passed static AST syntax parsing without importing or executing them
Remote CI evidence will be recorded with the change
The sweep change has not been executed locally; its process-boundary regression coverage must run remotely with the assembled builder
`PolygonProcess.py` now constructs fresh profiles and dimensional graphs in an isolated subprocess, writes their binary object archives into a container, decodes them, verifies byte identity and reference identity, then edits and re-encodes the live forward parameter
The sketch component explicitly seeds its external profile owner in the archive map; it is not a complete part or a vendor-loadability check
Its cases cover variable N, a 10,000-line ring, crossings, touches, vertical overlap, adjacent backtracking and valid collinear edges
It checks actual decoded dimension IDs and leaves parameter node IDs at their constructor value `-1`
An audit hook rejects non-code file access and process launches during construction
This coverage has only been syntax-checked locally and is pending its remote execution
The success criteria remain unsatisfied until held-out generated files pass target opening, rebuild, geometry measurements, feature-tree inspection, and dimension editing between healthy controls
