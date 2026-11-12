# Fusion OGS scene grammar

The two controlled graphics caches are completely decoded into named values. This is evidence for a bounded native graphics codec, not a general OGS implementation. Complete native-document re-emission subsequently passed the native lifecycle checks described below.

| Source | World bytes | Mesh bytes | Simple meshes | World tail | Unaddressed mesh bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| `Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d` | 14,552 | 860 | 10 | 0 | 0 |
| `LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d` | 24,382 | 956 | 14 | 0 | 0 |

`DecodeOgs.py` parses these archives using research archive decompression. It does not load CAD binaries or call production codecs. `DecodedSamples.json.xz` contains every named world field with its exact byte interval and every mesh range with decoded vertices or indices. `SerializerCalls.json.xz` contains static call-site evidence from the installed ARM64 images. `BinaryFacts.json` binds the important serializer locations to image hashes. `EvidenceIndex.json` binds the compressed reports and summarizes coverage.

The sources contain the members `FusionAssetName[Active]/OGS.BlobFolder/OGS/DefaultScene/world` and `stream_mesh_000`. The world describes the scene and references ranges in the mesh streams. A mesh stream is a sequence of typed vertex and index buffers, without an independent record header. Its ranges, formats and lengths come from world metadata.

## Primitive wire values

All fixed-width numbers are little endian except explicitly serialized entity identities. A boolean is one byte, observed as zero or one. Native metadata type codes used here are 7 boolean, 9 byte, 12 signed 32-bit integer, 13 unsigned 32-bit integer, 16 float32, and 17 float64. The serializer knows each field's type and count; neither its field name nor a type tag is normally stored.

Strings contain a uint32 UTF-16 code-unit length followed by UTF-16LE code units, without a null terminator. This differs from the installed Mach-O property-name literals, which are UTF-32LE `wchar_t` arrays.

`EntityID` and `ACTEntityID` contain eight bytes in **big-endian numeric order**. Native `NodeDataSerializer::SerializeQ` constructs those bytes with shifts and narrowing at `0x1c60dc..0x1c6120`, then writes metadata type 9 with count 8. It does not call the uint64 primitive writer. The constants at `0x3a8890..0x3a88c0` provide shifts `(-40,-32),(-56,-48),(-8,0),(-24,-16)`; the subsequent interleaves produce the most-significant byte first. Treating these as ordinary little-endian uint64 values consumes the right number of bytes but gives wrong entity identities.

`Qualifier` and `SerializationID` are float64 on disk even though their native producers convert unsigned integers to double. The model should retain their numeric role and reject nonintegral or out-of-range values when applying entity/display identity semantics.

`Box3` is six float32 values, `SBox3` six float64 values, and `ADevMatrix` sixteen float32 values. Matrix storage is distinct from the Design segment's double-precision matrix callback.

## Object identity and root dispatch

Objects first write their interface name. Serializers marked unique then write an object identity string formatted with native `%p`. A repeated identity writes its interface name and identity but suppresses the body. These are serialized graph identities, not addresses that a reader should dereference.

Worlds and several small geometry values have no object identity string. Group nodes, geometry nodes, text nodes, vertex formats, index buffers and text-style resources do. A generic rule that every interface name is followed by a handle is wrong.

`PersistentObjectManager::SaveWorld(IDataDriver*)` asks the serializer cache for `IWorld::InterfaceID` at `libOGSGraphics 0xe1390..0xe139c`. The root therefore uses the base world serializer even when its stored interface name is `ARenderList`. It has no trailing `Accelerate` byte. Nested `ARenderList` objects use their derived serializer and do have that byte. The old heuristic of reading `Accelerate` whenever the class text says `ARenderList` overruns the complete root by one byte.

A world contains its interface string, `RevisionId:uint32`, `PublishMode:int32`, child objects, and the string `WorldSerializerEndMark`. Nested `ARenderList` adds `Accelerate:bool`; `SingleNodeWorld` adds nothing. These samples use revision 5 and publish mode 1.

## First group and global schema registry

`FusionGroupNodeSerializer` overrides the generic OGS group serializer. Immediately after the first group's interface and identity, it calls `Ns::Scene::SerializationData::Serialize` once. This contains:

1. `Size:uint32`.
2. `Size` pairs of `InterfaceID:string`, `Version:uint32`.
3. `EnvironmentVersion:string`, obtained from `IEnvironment::ActiveEnvironmentID`.

The environment string is `RiverRubicon` in both samples; it is a named environment identity, not an unexplained signature. The nine registry entries are `TextureMappingAttribute:1`, `TextureEffectAttribute:1` in the older control and `2` in the saved cuboid, `NodeData:2`, `GraphicsBlobFeatures:1`, `F360InstanceNode:1`, `BillBoardAttribute:2`, `GroupNode:1`, `GraphicsGlobalVersion:1`, `OGSBlobVersion:0`. Registry order is persisted and is retained as an ordered semantic collection.

Every group then writes `HasWorldMatrix` and an optional 16-float matrix; `ClippingPlaneSave`; `StyleGraph`; `LocalGraphicScheme`; `NoCulling` and a float64 world box when culling is enabled; `SaveWorld`; and a conditional world branch. A saved world has `SerializationType:uint32`. Type 0 is a normal optional world link, type 1 is the BRep body callback, and type 3 is the sketch callback. Other native branches exist for T-spline, mesh and lattice bodies and are not qualified here. The group ends with `NodeDataType:uint32` and the selected quick node-data serializer when nonzero.

## Node-data graph and attributes

The ordinary node-data path writes an interface name, `NodeType:uint32`, a `RenderNode` identity string, and `AttributeType:int32`. The quick path omits the interface and render-node identity but otherwise uses the same field groups.

Attribute type 0 is an empty ordinary attribute set, type 1 an empty extended set, type 2 a populated ordinary set, and type 3 a populated extended set. Native branches at `NsScene10 0xa89c8..0xa8abc` prove that empty type 1 adds no extended-set payload. It must not be mistaken for a one-element attribute collection.

An ordinary set writes `HasAttributes:uint32`, `mRemoveAttributes:uint32`, `AppendTypeCount:uint32` and appended type IDs, then `AttributeCount:int32`, followed by attribute-name strings and attribute payloads. Each attribute starts with `Priority:int32` and `WinTies:bool`. Its named derived fields are identified by its native serializer. The decoded set includes visibility, selectability, depth priority, transforms, colors, textured/occluded effects, line styles, pixel scaling, billboards, grouping and texture mapping.

An extended set adds `TargetExternalNode:bool`. A true value writes `EntityID:big-endian uint64` and `SegmentID:uint32`; a false value writes `Node:string`. Then `AttributeSetCount:int32` describes nested sets. Each nested set writes `IsTypeAttribute:bool`, an ordinary set, and, for type-specific sets, `ApplyTypeCount:uint32` with its type IDs.

The remaining node-data suffix is:

- `EntityStatus:int32`. Status 1 means `hasEntity`; status 2 means `hasAppendixEntity`. Only those statuses include `SegmentId:uint32` and big-endian `EntityID`. Status 0 includes neither. The exact predicates are `NsScene10 0x1bc790` and `0x1bc7a0`.
- `Qualifier:float64`.
- `ClientTypeNameSaved:bool` and optional client-name string.
- `SubClientTypeNameSaved:bool` and optional subtype-name string.
- `SerializationID:float64`, `DoubleSided:uint32`, `CyclingColor:float32[4]`.
- `ConsolidationFlags:uint32`, `ImmediateConsolidationFlags:int32`, `RenderNodeFlags:uint32`, `SceneInfoFlags:uint32`.

Quick selector 2 is ordinary `NodeData`. Selectors 3, 5, 6 and 7 delegate to the same suffix through native F360 serializers; the installed symbols spell these classes `Serilizer`. Selector 4 is an F360 instance and adds `IsXRef:bool`, conditional big-endian `ACTEntityID`, and `InstanceID:uint32`. `GetNodeDataSerializer` at `0x2bae40` selects their vtables; serializers at `0x1060fc..0x106c4c` establish the suffixes.

## Geometry, mesh formats and streams

A geometry node uses the standard render-node framing, including its transform, optional presentation links and ordinary node data. It then writes an optional render geometry, its float64 world box, and an optional effect-instance link. All nonempty optional clipping/style/effect links outside the sampled profile remain unsupported.

Fusion's `Ns::Serialization::OgsSimpleMeshSerializer` at `NsScene10 0x163a90` differs from the generic OGS `SimpleMeshSerializer`. It writes:

1. Interface name `OgsSimpleMesh`, without an object handle.
2. `Modelbox:float32[6]`, `PrimitiveType:int32`.
3. Vertex-buffer presence boolean. When present: `DynamicResource:bool`, an optional vertex-format link, `StreamCount:int32`, and three `Props:int32` values.
4. Index-buffer presence boolean. When present: the `AIndexBuffer` object and its identity, `DynamicResource:bool`, and four `Props:int32` values, unless already defined.
5. `Planarity:bool`.

Vertex `Props` are stream number, byte offset and byte length. Index `Props` add a boolean-valued integer that says the native index stride equals two; false selects uint32 indices, true uint16. Native mesh-stream methods at `libOGSGraphics 0xd5350` and `0xd580c` establish range construction and actual byte writes. Stream files use the native `stream_mesh_%03d` naming scheme.

A vertex format has an identity and `VertexFormatTableCount:int32`. Each field is six signed 32-bit integers, sourced from native `VertexField` members at offsets `+0x10..+0x24`:

| Word | Semantic role | Native corroboration |
| --- | --- | --- |
| 0 | Element type enum | Constructor and Metal format conversion |
| 1 | Usage enum | Constructor and `GetUsageName` |
| 2 | Offset in 4-byte words | `Offset` and Metal `setOffset(field << 2)` |
| 3 | Vertex stream index | `StreamCount`, `ToSingleStream`, `ToMultiStream`, Metal `setBufferIndex` |
| 4 | Usage index | `IndexOf(usage,index)` and constructor `(usage >> 8) & 15` |
| 5 | Instance control | Positive selects Metal `PerInstance`, nonpositive `PerVertex`; portable nonzero integer semantics remain unqualified |

Observed type 1 is float32x2 and type 2 float32x3. Native Metal translation maps them to enum values 29 and 30, respectively; the installed Metal SDK names those `MTLVertexFormatFloat2` and `Float3`. Observed usage 0 is `POSITION`, 1 `NORMAL`, and 2 `TEXCOORD0`, from native wide-string literals and `GetUsageName` branches.

The sampled formats are position-only triples and interleaved position/normal/texture-coordinate octuples. Their stream index, usage index and instance control are all zero. The decoded buffers cover every stream byte; there is no unexplained padding. Buffer offsets and allocation order remain semantic storage descriptors rather than a license to carry original bytes forward.

The saved cuboid has four additional 24-byte position-only sketch-line buffers, accounting for its 96 additional mesh bytes. Its body display branch references BRep entities through node data and bounds; its 12 edge and 6 face LOD masks are zero. The remaining buffers describe origin/work geometry. No inference that all Fusion body tessellation is absent follows from this sample.

## BRep and sketch callbacks

Type-1 group worlds call `SerializeBrepBody` at `0xaefac`: `ValidBody:bool`; when true, a quick body-child group for edges, `EdgesCount:uint32` and edge LOD nodes, another body-child group for faces, `FacesCount:uint32` and face LOD nodes. Finally `HasModelBox:bool` controls a **float64** box. Quick body-child groups contain transform and presentation flags followed by node data; they omit the ordinary group world and culling fields.

Each body LOD node contains `NodeDataType`, quick node data, `HasLODs:uint32`, an optional render payload, a float64 world box and `UseClosestLOD:bool`. The populated sampled masks contain one set bit. A populated mask adds `DisplayItemType:uint32`; selector 0 uses an optional ordinary render-geometry link. Nonzero display-item serializers are outside this sample profile. `SerializeForBody` at `0xb4180` derives masks as `1 << level`, including fallback level 11; this is not an arbitrary count field.

Type-3 group worlds call `SerializeSketch`: `HasFaces:bool` and optional BRep-body callback, `LODGeoNodeCount:int32`, `RegularNodeCount:int32`, the LOD nodes and regular optional links, then `NoCullingNodeCount:int32` and its links. The saved cuboid has nine LOD nodes, zero regular nodes and zero nonculling nodes. Five sampled LOD payloads are `FatPointMesh`, consisting of its class string, `Width:int32`, `Height:int32`, and `BBoxSize:float32[3]`; the four remaining payloads are simple line meshes. The last sketch attribute, `HWSelectionPostProcessingAttribute`, has no derived bytes: its serializer directly tail-calls the base attribute serializer at `0x5b438`.

## Texture cache and text

`TextureMappingAttribute` adds a saved-reference flag, asset-name string, segment ID and big-endian entity ID, then `TextureMappingCache`. That cache contains `CacheIsLayered:bool`, primary cache data, `CacheHasSecondary:bool`, and optional secondary data.

Each cache data record has `Mode:int32`, `Axis:float64[3]`, `BBox:float64[6]`, `BakedTfm:float64[16]`, and `MappingTfm:float64[16]`. Mode 4 adds two cylindrical-cap booleans. Mode 6 adds procedural-wood origin and board-face-axis triples. Native `SerializeCacheData` at `0x5f47c` chooses the primary/secondary property-name tables at `0x4bf630` and `0x4bf658`. The saved cuboid uses primary mode 0 and secondary mode 6. These are named values even when zero or otherwise unused by the active material.

`FTextNode` delegates to `TextNodeSerializer`. Standard render-node framing precedes a float32 world matrix, a two-float envelope, optional text, global alignment and escapement, optional text/paragraph/block-style resources, then anchor point and priority. Style fields are native font, color, spacing, alignment, indentation and baseline properties. The sampled paragraph tab-stop lists are empty; nonempty lists are not admitted by this decoder. Resource identity reuse is retained.

## Qualification and remaining work

Both sampled world streams and all mesh bytes are consumed. The production semantic codec subsequently regenerated both world/mesh pairs byte-identically as part of complete ReadDocument → EmitParsed archive reconstruction. Fusion 2706.1.17 accepted both complete reconstructed archives and their original controls through initial geometry/material/appearance/mass inspection, rollback, restore, rebuild, height editing, save and reopen. See ../../LocalOracle/NativeDocuments/Preparation.json and NativeAcceptance.json. This establishes the recorded profile and lifecycle, without claiming a pixel-level image comparison or other native callbacks.

The profile must reject unsupported class names, registry versions, nonempty clipping/style/effect links, nonzero display-item serializers, unsupported mesh formats/instancing, nonempty paragraph tab stops, and regular/nonculling sketch-node branches until their complete contracts are promoted. The native type-2, type-4/5 and type-6 group-world branches remain outside the qualified BRep/sketch profile. No residual spans, original graphics byte buffers, or installed-library calls may enter production.

No additional native capture is required to promote the two solved controls. Later expansion should capture one changed rendering variable at a time: nonempty paragraph tabs, nonempty style/clipping links, populated body tessellation LODs and instanced vertex streams. Those controls should verify already traced callbacks, not replace the static field evidence with size matching.
