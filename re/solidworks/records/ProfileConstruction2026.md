# SOLIDWORKS 2026 profile construction

Status: fresh polygon profile graph and end-spec helpers, no generated profile or pad accepted

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
This is an empty constructor graph, not a polygon-family emitter or an accepted document

`closed_profile` constructs one ring of arbitrary `n>=3` ordinary lines from semantic 2D vertices
It preserves authored vertex order and binds the supplied plane frame
It rejects duplicate vertices, zero or nonfinite area, intersecting nonadjacent edges, and nonfinite transformed coordinates
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
The complete display-dimension factory remains unresolved, so these helpers alone cannot produce a live pad
Native distance constructor `0x4c8a4840` calls display-dimension constructor `0x4c86f550` and initializer `0x4c889480`
Those paths require display-item, dimension-text, model-handle, units, naming and document-style construction before live output can be emitted

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

## Contracts

Helpers use keyword-only semantic inputs and return `Core.Obj` nodes or typed field mappings
`DerivedFields` keeps authored and derived fields separate and refuses to replace a derived field
Endpoint references and handle references retain node identity
The archive serializer remains responsible for archive class and object indexes
No helper reads a file, saved record, table, oracle, or fixture at runtime

## Remaining construction

Origin/frame-point construction when source semantics require them, dimensional parameter/tolerance/name/display links, post-insertion manager state, contour/chain regeneration, and unit conversion remain required
The profile serializer address is `sldmodu 0x4bb1bdc0`
Null cached body has constructor/store/load evidence at `0x4c0ca000`, `0x4c254640`, and `0x4c253660`; this does not establish regeneration acceptance

## Verification

No local tests, imports, reproductions, or oracle calls were run
The edited Python sources passed static AST syntax parsing without importing or executing them
Remote CI evidence will be recorded with the change
The success criteria remain unsatisfied until held-out generated files pass target opening, rebuild, geometry measurements, feature-tree inspection, and dimension editing between healthy controls
