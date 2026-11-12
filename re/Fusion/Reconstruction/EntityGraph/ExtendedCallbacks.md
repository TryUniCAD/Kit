# Complete corpus Design record framing

The read-only [corpus inventory](../CorpusSemantics/Summary.json) now decodes all **261,141 indexed Design records in 712 archives**, consuming **25,458,293 of 25,458,293 payload bytes**. There are no archive failures or unexplained record suffixes. The compressed inventory retains source digests, class/version, record identity, payload offset, consumed length, and field count for every record. This is structural and typed-field coverage, not a claim that all 712 designs have independently regenerated geometry or vendor acceptance.

The initial inventory decoded 256,522 records. The remaining 4,619 were ordinary named metadata, three geometry value callbacks, ASM persistent selection recipes, and one lazily initialized auxiliary value. `InitialSummary.json` and `InitialInventory.json.xz` preserve that earlier measurement. The callbacks below close the gap; they do not replace the separate BRep journal and topology codecs.

## Evidence and method

[ExtendedCallbacks.json.xz](ExtendedCallbacks.json.xz) records 31 function excerpts from four locally installed arm64 libraries, with complete library SHA-256 digests. [ExtendedCallbackSummary.json](ExtendedCallbackSummary.json) hashes the compressed and uncompressed evidence. The native release is Fusion 2706.1.17. Addresses below are image-relative virtual addresses in the named thin arm64 images, not offsets in the universal binaries.

The evidence separates native runtime memory layout from persistence. Object vtables, pointers, allocator internals, and padding are not copied into the wire representation. The serializer's write calls establish each persisted field, while constructors, named getters, and matching algorithms establish its meaning. Corpus consumption then measures the reach of that grammar.

Research implementations are [CurveValues.py](CurveValues.py), [RecipeValues.py](RecipeValues.py), and [ProgenitorValues.py](ProgenitorValues.py), dispatched by [DecodeGraph.py](DecodeGraph.py). They serialize from named values and receive no retained field payloads.

## Common encodings

All numbers in these callback payloads are little-endian. `i32`, `u32`, `u64`, and `f64` have their normal fixed widths. A boolean is one byte, restricted to zero or one. A point or vector is three `f64` coordinates. A recipe collection has an `i32` nonnegative count; the research reader bounds it to one million elements. Recursive recipe payloads are limited to depth 64. Type names are an `i32` byte length followed by ASCII with no terminator.

These callback collections differ from the enclosing entity model's generic collection contracts. A reader must dispatch according to the declared metatype; it cannot infer a single universal container layout from a leading integer.

## AcGe geometry callbacks

`NsTypes10` registers callbacks that delegate to `AcGeFileIO::outFields`; native reflection alone therefore does not describe their serialized members. The three additional callbacks are:

| Metatype | Persisted fields in exact order | Native serializer |
| --- | --- | --- |
| `AcGeLineSeg3dValueMetaType` | `startPoint: xyz`, `displacement: xyz` | `libAcGe232` `0xba178` |
| `AcGeEllipArc3dValueMetaType` | `center: xyz`, `majorAxis: xyz`, `minorAxis: xyz`, `majorRadius: f64`, `minorRadius: f64`, `startAngle: f64`, `endAngle: f64` | `libAcGe232` `0xb9fcc` |
| `AcGeNurbCurve3dValueMetaType` | `evalMode: bool`, `isPeriodic: bool`, `degree: i32`, knot vector, weight array, control-point array, interval | `libAcGe232` `0xbaae4` |

A line segment stores **end minus start**, not the end point. The serializer calls `startPoint()` and `endPoint()` and subtracts the former before writing the second vector. This distinction matters for non-origin segments.

The knot vector is `tolerance: f64` followed by a geometry array of doubles. Each geometry array is:

1. `logicalLength: u32`.
2. `physicalLength: u32`.
3. `growLength: u32`.
4. Exactly `logicalLength` elements.

`physicalLength` and `growLength` are persisted allocation descriptors, not extra element counts. The file contains no inactive capacity values. The point array uses XYZ elements; knot and weight arrays use doubles. Logical length must not exceed physical length. Serializer addresses are `0xbc5fc` for knots, `0xbc6e4` for double arrays, and `0xbc338` for point arrays.

The NURBS definition getter exposes a rationality flag, but this callback does **not** write that flag. Weights convey the rational representation. Inventing a rationality byte would shift every following field. The supported interval is `tolerance: f64`, `boundedBelow: bool`, `boundedAbove: bool`, `lowerBound: f64`, `upperBound: f64`; its native serializer is at `0xbc4f8`. A native geometry-version comparison controls interval presence. The observed corpus profile includes the interval; older geometry-library layouts require their own qualification.

### Matrix callback

`NsTypes10:0xb6464` writes a boolean identity marker for binary streams. True ends the value; false delegates to `AcGeFileIO::outFields` at `libAcGe232:0xbc138`, which writes exactly sixteen doubles from consecutive matrix offsets `0x00` through `0x78`. There is no extra row count or affine-only truncation. The independent author uses identity matrices; broader readers must explicitly qualify and retain all sixteen nonidentity coefficients.

## ASM persistent selection recipes

The GUID `B28C1CCE-7FBD-43D2-8313-02BEC60F73FD` identifies `SMI_TAGGING_TRACKING::RECIPEValueMetaType`. Its callback at `NsEntityTracking10:0x6524c` creates an `ASMRecipeStreamer`, then dispatches the recipe's native serializer. This value records persistent selection/tag relationships. It is not the body's BRep topology or the `.smbh` modeling journal.

`ASMRecipeStreamer::writeInt` at `0x653fc` passes a four-byte integer to the underlying saver. `writeBytes` at `0x65464` passes an explicit byte length. `SMI_TAGGING_TRACKING::RECIPE::save` at `NsASMEntityTracking10:0x1f030` writes:

1. `version: i32`, obtained from the native tagging version.
2. `tags: counted<tag_info>`.
3. `lwdTags: counted<tag_info>`.
4. `payloadType: counted ASCII`.
5. The payload selected by that exact type name.

All **1,763** top-level recipe values in the corpus use version **3**:

| Payload type | Corpus values |
| --- | ---: |
| `body_recipe_data` | 289 |
| `bounded_face_recipe_data` | 171 |
| `edge_recipe_data` | 844 |
| `face_recipe_data` | 243 |
| `vertex_recipe_data` | 216 |

`base_recipe_data` is a real native dispatch case but does not occur as a top-level value in this inventory. Nested face, edge, and vertex payloads carry no repeated type-name string because the containing vector fixes their type.

### Tag tables

A `tag_info` is a counted vector of `tag_data`, emitted by `0x30c50`. Each `tag_data`, emitted by `0x2fc0c`, contains:

| Field | Wire type | Meaning established by native API |
| --- | --- | --- |
| `primaryId` | `i32` length, then bytes | Primary tag identifier, exposed by `get_primary_id` |
| `secondaryId` | `i32` | Secondary identifier, exposed by its setter/getter |
| `operationIds` | `i32` count, then `i32[]` | Operation lineage, exposed by `get_operation_ids` |
| `approachId` | `i32` | Tagging approach, exposed by `get_approach_id` |

The primary identifier is a typed variable-length identifier. It is not an unparsed recipe payload. It need not be treated as a null-terminated string. The restore routine at `0x2fccc` reads `approachId` only when the tagging version is at least 3. The implemented research profile explicitly admits version 3; the existence of older conditional layouts does not establish old-version acceptance.

### Payload inheritance and topology context

`base_recipe_data::save` at `0xdf70` writes one `i32` from object offset `0x0c`. Native debug output calls it `p`; this model calls it `primaryTagIndex`, denoting the primary tag-table selection. The object's version at offset `0x08` is not serialized again. The outer recipe version carries version context.

| Payload type | Fields after `primaryTagIndex: i32` | Native serializer |
| --- | --- | --- |
| `body_recipe_data` | `lwdTagIndex: i32` | `0xeb38` |
| `face_recipe_data` | `lwdTagIndex: i32` | `0x14350` |
| `bounded_face_recipe_data` | `lwdTagIndex: i32`, counted edge payloads | `0xf314` |
| `edge_recipe_data` | `lwdTagIndex: i32`, counted face payloads, counted vertex payloads, `referenceFaceIndex: i32` | `0x12998` |
| `vertex_recipe_data` | counted face payloads, counted edge payloads, ordered UV map | `0x356c4` |

`lwd_tag_index()` and `ref_face_index()` provide direct names for the edge members. Native debug output labels the matching body/face field `lwd`. The acronym is retained without inventing an expansion. Edge/vertex nesting is finite on disk but recursive in the type model. The edge restore routine omits `referenceFaceIndex` for version zero; version 3 includes it.

### UV order map

The vertex payload's map is `count: i32`, followed by entries of `key: i32` and seven `i32` values. The key's exact semantic role is not asserted solely from its map position. The seven values are:

1. `faceVertexCount`.
2. `uOrder`.
3. `uLowerOrder`.
4. `uUpperOrder`.
5. `vOrder`.
6. `vLowerOrder`.
7. `vUpperOrder`.

The serializer at `0x32e38` writes these in object-offset order `0x08` through `0x20`. `set_u_order(int,int,int)`, `set_v_order(int,int,int)`, and debug labels `u`, `ul`, `ur`, `v`, `vl`, `vr` identify the six order fields. `uv_order_data::make` at `0x32778` calls `getVertices(FACE*)`, computes `(end - begin) / sizeof(pointer)` at `0x32814`, and writes that count to object offset `0x08` at `0x32a40`. This resolves the first integer as a face vertex count, rather than a version or opaque flag. The order triples describe position and equal-coordinate range in sorted surface parameter coordinates; they support persistent vertex matching after regeneration.

## Lazily initialized progenitor metadata

The GUID `BE7E2847-FBC4-4898-A6E7-632A559A7F89` identifies `ProgenitorAuxDataValueMetaType`. The runtime reflection capture listed its version-zero member set as uninitialized. That state is not evidence that the value is empty.

[ProgenitorEvidence.json](ProgenitorEvidence.json) traces native registration at `NsEntityTracking10:0x9f6f0`: the sole member is `tag`, with `IntrinsicMetaTypeuint32`, native C++ type `unsigned int`, and the ordinary persistence option mask. There are no custom value callbacks or version branches. The wire value is exactly `tag: u32`. The native constructor initializes it to `UINT32_MAX`; that default does not replace values actually read from a file.

All 38 previously unresolved named metadata values now decode: 36 in `SweepFaceProgenitor` records and two in `EntityProgenitor` records. The native object size of 32 bytes includes runtime structures and is unrelated to this four-byte wire size.

## Acceptance boundaries

This inventory consumes every indexed Design record in the supplied corpus. It does not prove semantic correctness of every feature algorithm, regenerate arbitrary NURBS BRep bodies, interpret every auxiliary package, or vendor-load every rewritten archive. The independent parameter, circle, and extrusion documents have separate native load/edit/rebuild/rollback/save/reopen evidence in [DocumentAuthoring/Acceptance.md](../DocumentAuthoring/Acceptance.md).

The interpretation also retains explicitly named uncertainty in earlier sketch/profile callbacks and in the UV map key. Knowing every byte's type and boundary is stronger than preserving residual payloads, but weaker than knowing every algorithm that uses those values. Production support must state its qualified schema and geometry profile, reject unsupported cases, and carry its own acceptance evidence.
