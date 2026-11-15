# SOLIDWORKS 2026 model construction

Status: **research constructors; no complete generated part or vendor acceptance**.
Constructor evidence does not prove that the application accepts a generated save.
The production adapter remains read-only.

## Evidence identity

All addresses refer to the 2026 SP05.2 build `34.5.2.0604` in the
[binary manifest](../v2026/Manifest2026.json).
The separate part UI module `sldprtu.dll` has SHA-256
`54c079c8bbbe13582d062787c07a13f91d91f2d7972715e5d647bb8a1802d494`.
REA Ghidra 12.1.3 evidence for its part constructor is
`ev_28279642599543a3ea2a95857dfc7680745c5513f5337e9c93e9f3558f81512d`.
Its reported target digest matches that module.
Other constructor decompiles were read from private copies of the existing
Ghidra projects, with `-readOnly -noanalysis`.
No CAD process was launched or attached to during this work.

## Identifier namespaces

| Record                 | Classification                   | Construction rule                                                                           | 2026 evidence                                                                  |
| ---------------------- | -------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Ordinary node `f08`    | derived persistent id            | Allocate the current header counter, increment it, and skip explicitly reserved ids         | `sldarchiveu` `0x31a052d0`; getter `sldmodu` `0x4b283ba0`                      |
| Header next id         | derived bookkeeping              | The allocator's final next value, not a function of visible feature count                   | same allocator                                                                 |
| Configuration `f08`    | derived configuration id         | Allocate the current manager `f40c`, then increment that manager counter                    | configuration constructor `0x4bdbf820`; exact helper instructions `0x4b8967a0` |
| Manager `f40c`         | derived bookkeeping              | Number of fresh configurations when allocated sequentially from the constructor's zero seed | manager constructors `0x4b8802f0`, `0x4b880dd0`                                |
| Component/archive tags | derived serialization references | Keep object pointers in the graph; compute archive map ids during storage                   | existing archive codec                                                         |

`PersistentIds.allocate(node)` binds the allocation to the node's identity.
Repeated allocation returns the same id; changing that id elsewhere raises an error.
Configuration construction does not consume a persistent id.
The manager's own constructor leaves its ordinary node id at `-1`.

## Shared feature constructors

The functions live in `re/tooling/sw2026/builders/Model.py`.
They construct field dictionaries for the existing generative schemas.
There is no recorded output offset, fixed stream length, donor file or captured payload.

| Fields                                               | Classification      | Rule and status                                                                               | 2026 evidence                                        |
| ---------------------------------------------------- | ------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Node name                                            | input               | Authored Unicode string in a fresh `moNodeName_c`                                             | node serializer `0x4c17adf0`                         |
| Node `f0c=1`, `f28=0x40000000`, `f2c=0`, empty `f20` | constructor state   | Direct initialization; canonical application save acceptance remains unmeasured               | node constructor `0x4c03c250`                        |
| Concept optional list and visual pointers            | derived absence     | No authored list or appearance produces absent optional nodes                                 | concept constructors `0x4bda5770`, `0x4bda5800`      |
| Node-list count                                      | derived             | Length of its object-reference list                                                           | node-list storage `0x4c1799b0`                       |
| Node-list trailer                                    | format constant     | Store writes literal signed zero after the object list                                        | same storage routine                                 |
| Feature version/date/kernel fields                   | input provenance    | Explicit target version, service pack, subservice pack, build code and Parasolid version      | feature constructor `0x4bb38350`                     |
| Feature `f2a0/f2a4`                                  | constructor state   | Owner-taking constructor writes zero; default constructor instead asks for FILETIME           | owner constructor `0x4bb38350`; default `0x4bb38710` |
| Feature visual record                                | constructor state   | Layer `65535`, second word zero, flags `3`; color and line style inherit; line width inherits | `moEntVisProp_c` constructor `0x4c151110`            |
| Inherited line width                                 | format vocabulary   | Enum `-1`, explicit width `-1.0`                                                              | `sldmfcu` `0x3c84a910`                               |
| Model-feature `f35c`                                 | constructor state   | High word of zero-initialized qword `f358`                                                    | `0x4be9ed00`                                         |
| Atom-feature arrays/maps/optional pointers           | derived empty state | Fresh arrays and maps have zero elements; optional data is absent; `f4a0=1`                   | `0x4b6feec0`                                         |
| Body-feature optional data and `f780`                | derived empty state | No assembly feature data, component-feature cache or generated-body references yet            | `0x4b76ef40`                                         |

The factory's `owner` entry is a symbolic relationship used during construction.
It is not an extra serialized field.
Callers must establish the native serialized child lists when composing the model.
The zero geometry-cache state is constructor-backed, not oracle-proven rebuild neutrality.

## Configuration construction

`configuration_manager` accepts authored names, the current configuration index,
an owning part node, and explicit version/timestamp provenance.
Each configuration is a new object with its own property lists and invalid mass cache.
All collection counts derive from their collections.

The base configuration constructor `0x4bdbf820` initializes its options, maps,
empty feature lists and mass-property cache.
The derived part configuration constructor `0x4b595780` adds its body maps,
density manager and part selectors.
The default embedded part-configuration object follows `0x4bdc24d0`:
id `-1`, flags `1`, empty lists and absent optional chooser/visual objects.
The mass record follows `0x4bc1d500` and `0x4bc1cc20`:
zero mass scalars, identity principal axes and an invalid-cache flag.
No zero mass value is reported as measured geometry.

The variable-table presence flag is false for the newly empty variable-control maps.
The native save at `0x4c21ef40` calls `hasRefOrFeatCntrlbyVarTable` before emitting them.
Manager `f658` starts zero; the resolved-feature stream context must derive from it,
instead of forcing the corpus's saved value.
The manager constructor finishes by calling `setNeedsUpdate(0,1,null)`;
`0x4bb515c0` delegates to node routine `0x4c03ed90`, clearing update bits
with mask `0xfffd7ff8`. This produces `f0c=0` from the fresh node state.
Manager `f830` starts at the constructor's signed `-1` sentinel, written as an
all-ones qword by both manager constructors; its saved unsigned low word is
`0xffffffff`. No saved build-number value is used.

## Plane wrappers

`component_plane` requires a real allocated `moRefPlane_c` node, an explicit
`moUnitComponent_c`, a creation time and a semantic principal normal or `None`.
The underlying plane graph is a separate obligation.
The default `moCompRef_c` constructor at `0x4b7e8390` uses the same serialized
state as the component-taking constructor, with a null component pointer.
`component_reference_fields` exposes these fields for native derived handle
classes without creating a redundant archive object.

| Field          | Classification                | Rule                                                                                               | 2026 evidence                                           |
| -------------- | ----------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Wrapper `f58`  | derived reference             | Unit component's owning part relationship                                                          | `0x4b7e8250`, unit component `0x4b8281a0`               |
| FRData `f00`   | derived id                    | Referenced plane's persistent id                                                                   | `0x4bb34370`                                            |
| FRData `f08`   | volatile/input provenance     | Referenced node's creation time                                                                    | same constructor calling `0x4c03e070`                   |
| Wrapper `ff8`  | derived conditional ownership | Null for an allocated plane; inline geometry is retained only when the referenced plane id is `-1` | `0x4b7e7980`                                            |
| Wrapper `f100` | derived principal-plane kind  | Principal positive X/Y/Z normals map to `1/2/3`; custom geometry maps to `0`                       | plane vtable `0x4d16f278 + 0x2130` targets `0x4c2d5750` |

The native principal-kind routine first checks the plane's semantic type and
byte `f34c`, then compares its normal to the positive canonical axes with
tolerance `1e-12` at `0x4cdf2b88`.
The current constructor accepts exact canonical principal normals only.
It does not guess a principal kind from a display name.

## Principal-plane graph

`principal_planes` takes names keyed by canonical positive normal axis and
constructs actual plane and plane-data objects in native creation order.
The 2026 `moModel_c::makeDefaultRefPlanes` at `0x4c02d830` passes these bases
to the default-data constructor `0x4c2d9ba0`, all at the zero origin:

| Normal | First basis | Second basis | Construction         |
| ------ | ----------- | ------------ | -------------------- |
| Z      | X           | Y            | cross product X × Y  |
| Y      | X           | −Z           | cross product X × −Z |
| X      | −Z          | Y            | cross product −Z × Y |

The constructor computes the normal by crossing the bases.
Its setter `0x4c2eaf80` calls `sldmgu` coordinate transform `0x31f21220`,
then takes the inverse before storing the plane transform.
The coordinate routine constructs rows from the first basis, normalized
`(first × second) × first`, and normalized `first × second`.
Matrix constructors `0x31e26c10` and `0x31e26880` establish the row storage.
The inverse of the orthonormal zero-origin frame is its transpose.
The builder computes those entries and omits the identity matrix for Z.

Plane borders, display origin and optional references follow fresh constructor
`0x4c2dadb0`: zero borders/origin, absent references, selector sentinels `-4`,
`f5c=1`, and zero remaining option flags.
The plane serializer `0x4c27b1b0` writes literal zero for the legacy byte.
The geometry base follows `0x4c2ce5d0`.
Creation calls `setBlankStatus(1,1,1)` at `0x4c2ceec0`; retaining constructor
bit 4 depends on environment member `0x138`.
The builder requires that boolean explicitly and never copies a saved flag.

## Part-root graph

`part_root` and `part_graph` construct the base part and its principal planes.
They require generated detail definitions, explicit document and analysis unit
graphs, a crosshatch name, configuration names and version provenance.
They do not read preferences, a saved part, a template or a field program.
`part_graph` returns object references through `ModelGraph`; its system-feature
tuple is separate from the part's fresh empty concept list.
Origin/profile construction and the separate resolved-stream composition remain
required before this graph is a complete native part.

The model constructor is `0x4c00edb0` and derived part constructor `0x4c19e7b0`.
Every emitted root collection starts from their fresh containers and derives
its serialized count from its elements.
The following additional rules close their nonempty structural state:

| Fields                 | Classification                   | Construction rule and 2026 evidence                                                                                                     |
| ---------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `f990`                 | derived self reference           | Fresh `moUnitComponent_c` points back to the part; getter `0x4c0254c0` returns this slot                                                |
| `f9d0`                 | derived relation graph           | Fresh `moRelMgr_c`, constructor `0x4c366bd0`: empty relation/value lists, `ff4=f1b0=-1`, other stored scalars/string zero/empty         |
| `f9b8/f9c0`            | authored unit graphs             | Document/user and analysis tables respectively; setters `0x4c031e20` and `0x4c0318c0` assign these exact slots                          |
| `fd88`                 | constructor bookkeeping          | Atom manager `0x4bced920`: next id `f260=100`, empty atoms, zero flags                                                                  |
| `fd90`                 | constructor bookkeeping          | Ghost manager `0x4bf03a90`: next id `f80=10000`, no objects or packed flags                                                             |
| `fa98`                 | format/constructor state         | Save helper `0x4c22ec20` writes literal kind `2`; alias constructor `0x4b4c7a40` creates empty maps and markers `0xaaaaaaaa/0xbbbbbbbb` |
| `fdb0`                 | constructor state                | `moTransRefPlaneData_c` constructor `0x4c6f3b30`: `1,1,0xff00,0xff,0x5f,0`                                                              |
| `f1418`                | authored hatch/constructor state | Part constructor calls `gcXhatch_c` with authored name, angle zero, scale one, flags `0,0,1,-1,-1,0`                                    |
| `f1588`                | derived empty display data       | `uoModelData_c` constructor `0x4c3ba670`: null light graph and zero flag                                                                |
| `ff80/ff88`            | constructor state                | Model constructor writes `1000.0` and `1e-8` directly                                                                                   |
| `has_f7f8`             | derived cache absence            | Native save checks `mgBBox_c::isSet`; an unset fresh box emits false, even though the runtime pointer exists                            |
| `f784/f7a4`            | constructor state                | Fixed 16-byte fields are generated from the constructor's zero-initialized members, never read from a document                          |
| `fce8/fcec/fd44/fd50`  | constructor state                | Model seeds `50,108,10,1`                                                                                                               |
| `feb0/feb4`            | constructor state                | Model seeds `199,199`                                                                                                                   |
| `f1104/f1128`          | constructor bookkeeping          | Model initializes both dimension-increment counters to `20`                                                                             |
| `f1300/f18d8`          | constructor bookkeeping          | Model/part initialize update stamps to `101`                                                                                            |
| root `f2c` bit `0x100` | storage state                    | Native lightweight save sets this bit before `0x4c17aa00`; other saved-state bits are not inferred from controls                        |

The part's fresh node retains constructor `f0c=1`, requesting update.
A completed native control's cleared update bit does not prove that constructor
geometry has already been rebuilt.
No empty atom, mass or bounding-box cache is reported as measured body geometry.

## Definition construction

`part_definition` constructs `Contents/Definition` from authored density,
drafting standard, display bit positions, tessellation settings and a journal name.
The caller supplies the native boolean preference `0x7a` explicitly.
Its higher-level meaning and the three tessellation preference domains remain
unresolved; they are not described as inferred constants.
The remaining persisted scalar seeds follow the 2026 UI constructor `0x497486b0`.
The PhotoView document-options record follows `0x4a3082c0`.
The notebook follows `0x4a01d940`, its reset `0x4a023f30` and journal initialization
`0x4a01d6b0`; the journal name is authored instead of copied from a localized resource.

The part-specific density field `f1688` comes from `uiPartDoc_c` constructor
`sldprtu` `0x33374980`.
The base UI density virtual at slot `0x11c0` resolves to `0x3338a480` for that class;
the getter reads `f1688` directly.
The vendor's [material-property API reference](https://help.solidworks.com/2020/English/api/swconst/DP_MaterialProperties.htm?format=P&value=)
specifies density in kilograms per cubic metre.
This unit interpretation combines that API contract with the 2026 getter evidence.

An empty authored style set and no authored rendering material produce empty
line-style/font maps and absent rendering-material data.
These are candidate fresh-document choices, not accepted neutral cache values.

## Verification and remaining work

Static syntax parsing has completed for both builder modules.
No tests were run locally.
The first remote process run exposed conflicting provisional names for the
transform schema. The registry preserves its first definition, so the builder
uses the `Definition.py` field names `f08/f58/f60/f68/f70/f78`.
This result is a codec-construction failure, not target acceptance evidence.
The new process-boundary check is prepared for remote PR CI: it constructs
different configuration counts and Unicode names from no input file, serializes
both components into a generated container, decodes and re-emits each stream,
checks object aliases and rejects runtime data-file reads through Python's audit hook.
It deliberately keeps both vendor-acceptance flags false.
Remote run [43675419713](https://github.com/TryUniCAD/Kit/actions/runs/43675419713)
passed this configuration/definition process boundary at commit `07b9ce403`.
The expanded principal-plane check and part-root additions await a new remote run.
The audit hook is installed before builder imports and registry construction in
the expanded check, rejecting data-file reads during those phases as well.

Still required: complete origin/system-feature composition,
full detail-style and unit construction, whole-part round trips, held-out target
measurements, rebuild and dimension edits, and production promotion.
No whole-part acceptance is established by these component constructors.

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
permit stopping only on success under every criterion, or at the end of the
available context.
