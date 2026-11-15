# SOLIDWORKS 2026 polygon-sketch construction

Status: **historical constructor ledger; restricted polygon geometry and depth
edit measurements now pass**.
The [current native measurements](PolygonNativeMeasurements2026.md) bind the
three generated cases and their tested revisions. Later view bytes still await
remeasurement. This constructor record is not complete family or production
acceptance.
The rules below come from 2026 constructors and insertion methods.
They are not captured records and are not a complete builder.

## Binary identity

The [2026 manifest](../v2026/Manifest2026.json) binds the DLL hashes.
Addresses below are from `sldmodu.dll` at base `0x4b140000` and
`sldmgu.dll` at base `0x31dd0000`.
The transform primitive writes use the `swccu.dll` archive interface.

## Independent namespaces and topology

| Subject                   | Rule                                                                                                                                             | Binary evidence in `sldmodu`                                                                   |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| Ring topology             | With distinct vertices `p[i]`, line `i` uses point-array indices `i` and `(i+1) % n`                                                             | add-line `0x4c49cc30`; setters `0x4c44f1b0`, `0x4c44f010`                                      |
| Point lookup              | Point address is array base plus `EntIndex × 0x158`, after bounds checks                                                                         | `0x4c5fba60`                                                                                   |
| Line lookup               | Line address is array base plus `EntIndex × 0xf0`, after bounds checks                                                                           | `0x4c5dc250`                                                                                   |
| Array record kinds        | Ordinary point kind 0; plain line flags 0; counts derive from collection lengths                                                                 | point creation `0x4c68ffb0`; sketch serializer `0x4c5916f0`                                    |
| Segment endpoint encoding | u16 below `0xffff`; otherwise marker `0xffff` and i32                                                                                            | `0x4c590920`                                                                                   |
| Handle encoding           | u16 below `0x777f`; otherwise marker `0x777f` and i32; fresh handle has `RefId=-1`, `DimOnCM=0`                                                  | constructors `0x4c5bcd50`, `0x4c5f7da0`; serializer `0x4c587800`                               |
| Creation ids              | Entity starts with creation id -1; permanence assigns once; point and line counters are independent and begin at 1                               | constructors `0x4c1e4a40`, `0x4c3e1310`; assignment `0x4c3e2450`; allocator `0x4c3e3030`       |
| Sequential creation       | In first-use order, point and line creation ids are each `i+1`; each corresponding next counter is `n+1`                                         | geometry-type virtuals `0x4b27cbe0`, `0x4b27e150`; allocator increments sketch `+0x148/+0x14c` |
| Permanent markers         | Separate namespace; counter starts at 1, returns then increments; an explicit marker below `0x1000000` advances it to at least `marker+1`        | sketch constructor `0x4c495450`; allocator `0x4c4bb590`; wrapper `0x4c4e3af0`                  |
| Sequential line markers   | Fresh ring lines assigned in order have markers 1..n and next counter `n+1`; point constructor marker stays 0 until another operation assigns it | reuse check `0x4c4b3d10`; assignment walk `0x4c0cd540`                                         |

These are three different namespaces: array indices, creation ids and permanent
markers. Archive-map indices form a fourth namespace and are computed by the
shared serializer. An endpoint is not an archive object reference.

## Entity construction candidates

Constructor seeds are listed to identify the rule's source. They have no fresh
target acceptance yet and cannot be copied into a production default table.

| Record               | Construction or insertion state                                                                                            | Binary evidence in `sldmodu`                                                    |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Common entity        | `f20=0`, `f30=5`, `f34=f38=1`, `f50=0`, `f54=4`, `f56=0`, `f68=1`, `f74=f78=0`; external entity/group/name pointers null   | constructors `0x4c3e1030`, `0x4c3e1220`; serializer `0x4c583460`                |
| Ordinary point       | Authored position; `fe4=0`, `fec=ff0=0`, `f108=-2`, `has_jet=0`; auxiliary points begin at zero                            | constructors `0x4c490970`, `0x4c57ab00`; serializer `0x4c58f910`                |
| Point geometry count | `fe8 = degree(point)`, giving 2 in the ring                                                                                | `0x4c602c10`, increment helper `0x4c490b80`                                     |
| Point flags          | Native set-position establishes memory `fe0=1`; ordinary 2D ownership and constructor state yield serialized `pflags=0x1e` | `0x4c601d10`, serializer `0x4c58f910`                                           |
| Adjacency            | Insertion fills `h1`, then `h2`, with cloned incident-line handles                                                         | `0x4c5f7e40`, `0x4c5f8460`                                                      |
| Sequential adjacency | `p[0]` has `h1=l[0]`, `h2=l[n-1]`; other `p[i]` have `h1=l[i-1]`, `h2=l[i]`                                                | same insertion path                                                             |
| Plain line           | `fd4=0`, line `fe8=0`, direction pointer absent and direction-presence bit clear                                           | constructor `0x4b92dfc0`; direction clear `0x4c44d700`; serializer `0x4c58ac90` |
| Contour state        | Constructor `fd0=0` becomes `fd0=1` through ordinary nonconstruction insertion with available endpoint adjacency           | `0x4c5dde50`, `0x4c5f8460`, setter `0x4c4922d0`                                 |
| Segment scale        | Current schema name `seg_tol` is misleading; native key is `NormalScale`, and absent optional scale stores -1.0            | serializer `0x4c590920`                                                         |

Do not use a constructor state after a later insertion method changes it.
The contour flag is a concrete example of that failure.

## Profile ownership, frame and cache

| Subject             | Rule                                                                                                                                                              | Binary evidence                                                                                   |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Ownership           | Profile `f3d0` owns profile data; data `pd_f80` owns sketch; sketch `f138` points back to profile                                                                 | `sldmodu` profile constructors `0x4c0ca780/0x4c0ca9f0`; data constructors `0x4c0ca000/0x4c0ca250` |
| Profile constructor | `f390=f3dc=f3c0=f42c=0`, `f3e0=100000`; chooser and axis handles null; contour containers initially empty                                                         | same profile constructors                                                                         |
| Data constructor    | `f10=3`, `f100=f104=4`, `f110=null`, `f118=0`, `f11c=-1`, `f2a0=101`; chain list initially empty                                                                  | `sldmodu` `0x4c0ca000`                                                                            |
| Plane               | Native reference is `moCompRefPlane_c`, not a captured plane enum; constructor obtains its transform, computes inverse and optionally composes an extra transform | `sldmodu` data constructor `0x4c0ca250`; plane-transform getter `0x4c2d5820`                      |
| Profile serializer  | Correct serializer address is `0x4bb1bdc0`; an earlier working note naming `0x4bb1bb20` was refuted                                                               | `sldmodu`, retained `cl_sldmodu.c` function identity                                              |
| Frame               | Matrix basis vectors are consecutive rows; point transform is `scale × (x×row0+y×row1+z×row2) + translation`                                                      | `sldmgu` matrix constructor `0x31e26880`; point transform `0x31f09820`                            |
| Planar placement    | Orthonormal rows `(u,v,u×v)`, translation `o`, scale 1 give `world = o+x×u+y×v`                                                                                   | same matrix construction and multiplication                                                       |
| Transform encoding  | u8 matrix-present flag; optional nine f64 entries; three f64 translations; f64 scale; u8 flags; optional flagged extension                                        | `sldmgu` `0x31e03ce0`, `0x31e039b0`, `0x31e00bb0`                                                 |
| Identity transform  | Constructor creates identity basis, zero translation, scale 1, flags 0, null extension                                                                            | `sldmgu` constructors `0x31f1d560/0x31e26e50`                                                     |
| Null cached body    | Data constructor sets `f198=null`; store derives u8 `empty=1` and emits no body payload; loader preserves null and skips raw load                                 | `sldmodu` constructor `0x4c0ca000`; store `0x4c254640`; load `0x4c253660`                         |

The null-cache rule establishes well-formed framing only. It does not establish
that SOLIDWORKS rebuilds a generated profile or pad without that cache.

## Remaining obligations

- Recover the stored `dflt` calculation and visibility/line-width construction.
- Construct origin and frame points; the ring's n vertices need not be the final
  editable sketch's complete point array.
- Recover dimensional construction from `sgSketch::iAddValG2Constraint` at
  `0x4c4b99a0`, distance constructors `0x4c411360/0x4c4113b0`, and entity-use
  updates at `0x4c5bd330`.
- `getOriginPointH` at `0x4c4b40e0` searches an origin predicate and can return
  null. It does not create an implicit origin.
- Prove archive-coordinate units; the frame multiplication alone does not prove metres.
- Construct native plane references, contour/chain state, profile raw storage
  `f188`, manager defaults and modification counters.
- Recover parameter, tolerance, naming, display-dimension and solver-state rules.
- Link the profile to a generated pad and obtain held-out rebuild and edit evidence.

An empty dimension array represents an unconstrained constructor state.
It does not prove preservation of source dimensions or parametric acceptance.
