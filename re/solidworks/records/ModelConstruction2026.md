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

`PersistentIds.allocate(node, field="f08")` binds the allocation to object identity
and its actual serialized id field. Repeated allocation returns the same id;
changing that field elsewhere raises an error.
Native feature-dimension naming at `0x4c821c40` calls the header's allocator for
the dimension's `f50`. The profile builder therefore requests `field="f50"`;
its parameter node keeps constructor id `-1` unless another proven operation
allocates that node. No synthetic `f08` field is needed on a dimension.
Configuration construction does not consume a persistent id.
The manager's own constructor leaves its ordinary node id at `-1`.

Persistent allocation follows construction lifetime, including objects omitted
by a conditional serializer. The from-end-spec constructor `0x4bad3e00`
creates a role-19 parallel-plane-distance display dimension even when end type
zero causes its serializer to omit that dimension.
The parameter-naming routine `0x4c821c40` asks the owner model's virtual slot
`0x1250` with argument zero before allocating `dimension.f50`.
For `moPart_c`, vtable `0x4d1252d8` resolves that slot to
`moModel_c::isViewerModel` at `0x4c02d7d0`.
With argument zero, the result is `(~(model[0x2b0] >> 2)) & 1`.
The model constructor `0x4c00edb0` writes `0x0c` at that offset, so an ordinary
fresh part returns false and this naming path consumes the header id.
The profile builder must retain the actual transient dimension object through
allocation rather than add a numeric gap to the next-id counter.
See the [transient-dimension gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/TransientDimensionsConsumeIds.md).

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

## Target feature provenance

The owner-taking feature constructor `sldmodu` `0x4bb38350` obtains its date
through import `0x4cd3d580`, which resolves to `sldutu` `su_getFullDateCode`
at `0x3d0107b0`. That wrapper calls `su_getTaggedDateCode` at `0x3d014520`.
The latter constructs a wide string from the binary's ANSI literal at
`0x3d319248`: `$?153#548834?$2026306` followed by spaces.
It trims trailing whitespace, takes the rightmost `length - 14` characters,
then calls `_wtol`. The resulting tagged value is `2026306`.
The full-date wrapper normalizes only values from `1` through `99999`, adding
`2000000` below `9600` and `1900000` otherwise. It therefore returns
`2026306` unchanged for this target.
This is build metadata derived from a shipped binary, not a vendor-saved field.
The builder continues to require date provenance explicitly from its caller.

The imported string operations are MFC ordinals `14039` and `12600`.
A passive x64 runtime copy resolves them to `0x180012e60` and `0x18003c210`.
The former scans UTF-16 characters with `iswspace` and truncates the final
whitespace run; the latter copies `n` UTF-16 characters starting at
`length - n`, with negative `n` clamped to zero.
The studied `mfc140u.dll` has SHA-256
`fc9b1f94752d7080436824b480e83ba1ec930e3f7baa881f4e842b882e715cfc`.
The `sldutu.dll` digest is
`dbc147c10b658544e44a7c13d3ae656c26a0778e9241fe74d6ca9ecae8730933`.
The default PE parser omitted these high ordinals and warned that its export
budget was exceeded; the raw export-address table supplied their addresses.
See the existing [symbol-budget gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/PeSymbolBudgets.md).

The feature's Parasolid provenance follows a separate live-session rule.
Import `sldmodu` `0x4cd3a378` resolves to `sldgcu` `0x439d3e40`, whose
implementation `0x43e73730` reads the GCP environment's `0x27c` word.
The environment constructor `sldgciParau` `0x32f95920` initially clears it.
That initial zero is not the engine's established behavior version:
`gci_StartEngine` at `0x33012950` calls
`setSessionBehaviorUsingSWVersion(0, 0, ...)` at `0x330132e0`, then
`PK_SESSION_ask_behaviour` through thunk `0x330a21c7`.
On success it copies the result's word at offset `4` into environment `0x27c`
at `0x3301338d`.
The companion getter at `0x33014310` independently exposes that same result
word. Its REA evidence id is
`ev_ca4457ca262a70fa95d17d87837b42e3c2f8c203d7479c342689fac61ad210f4`;
the module SHA-256 is
`96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce`.
The matching primary `pskernel.dll` has SHA-256
`2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969`.
Its preferred image base is `0x180000000`; all kernel addresses below use that
base, independently of an application's relocated runtime address.
Normal successful engine startup derives feature behavior version `370108`:

| Stage                        | Native rule                                                                                                   | Address                                                        |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Select behavior kind         | `setSessionBehaviorUsingSWVersion(0, 0, 0)` selects kind `0x64f1`                                             | `sldgciParau` `0x33016650`                                     |
| Set kernel mode              | Kind `0x64f1` becomes internal mode `1`                                                                       | `PK_SESSION_set_behaviour` `0x1803ea470`; branch `0x1803eaba1` |
| Select latest index          | Helper clears `ecx` and jumps to a leaf that returns `0x185` when `cl` is zero                                | `0x180a917b0` to `0x1814306d0`                                 |
| Read behavior result         | Mode `1` reads table index `0x185` from base `0x184394ffc`; entry `0x184395610` is `370108`                   | `PK_SESSION_ask_behaviour` `0x1803e1600`; branch `0x1803e1a97` |
| Establish feature provenance | Successful startup copies result word `4` to GCP environment `0x27c`; the feature constructor reads that word | `sldgciParau` `0x3301338d`, then the getter chain above        |

The independent kernel-build leaf at `0x1814306f0` instead returns `3701250`.
`PK_SESSION_ask_kernel_version` at `0x1803f7520` splits that full build number
into its reported components. It is not the behavior-version value emitted by
this feature-construction path.
Neither number comes from a saved feature, an estimated marketing version, or
the environment's pre-engine zero seed.
The builder still accepts an explicit version from the caller, so a different
target or deliberately selected compatibility behavior requires its own provenance.

## Feature-reference creation time

`moFRData_c` construction at `0x4bb34370` takes its id from the feature and its
time from `moLoggedNode_c::getCreationTime` at `0x4c03e070`.
This is independent of feature FILETIME words `f2a0/f2a4`.
The getter calls virtual slot `0x4f8`; for the ordinary profile feature this
resolves to `0x4bb466a0`. Principal-plane primary vtable `0x4d16f278` resolves
the same getter and its `0x500` slot to constant true.
With that true slot, the getter returns the feature's runtime log pointer at `0x48`.
When the log has stamps, the creation-time getter reads the first stamp's
`moStamp_c::timestamp` through import `0x4cd356b8`.
When no log or no stamp exists, it calls `ut_getUnsetTime` through
`0x4cd3d590`. Export `sldutu` `0x3d03ebb0` returns `0x278d00`, or `2592000`.

`logged_creation_time(timestamps=...)` implements that rule from ordered authored
creation-log timestamps. `component_plane(created_at=...)` requires the resulting
time to match the referenced node's actual log state.
Composition must either emit the matching creation log or use the absent-log
sentinel. Supplying the document's authored creation date only in the wrapper
does not establish that relationship.
See the [reference-time gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/FeatureReferenceCreationTimes.md).

## Post-origin owner update

The native origin initializer `0x4c49b980` invokes zero-status update on the
origin and then its owning model. Those receivers have different dispatch:
origin vtable `0x4d0ef510` slot `0xb8` resolves to feature wrapper `0x4bb515c0`,
whereas both model vtable `0x4d0c70e0` and part vtable `0x4d1252d8` resolve that
slot to model wrapper `0x4c0363c0`.
For arguments `(0, 1, null)`, the model wrapper skips its nonzero-status branch
and tail-jumps node routine `0x4c03ed90`.
The node zero-status path applies `f0c &= 0xfffd7ff8`.
`clear_model_update(model=...)` implements precisely that operation for the two
classified model classes. Composition calls it after constructing the origin.
It does not establish the origin sketch's solver state or remove its unresolved
update marker. The feature wrapper's virtual query path requires separate evidence.

## Dirty flags and update stamps

The positive node-update path under normal regeneration uses
`f0c = (f0c & 0xfffd7ff9) | 1` in `0x4c03ed90`.
For the classified model/part receiver, virtual slot `0x320` resolves to constant
false leaf `0x4b27cbe0`, so its optional context-notification tail is not entered.
Model wrapper `0x4c0363c0` only adds a sensor-folder notification when both the
status is nonzero and the options argument has bit one set.
The generic insertion routine `moConcept_c::addFeature` at `0x4bda62a0` uses
status `0x0b`, options zero and the child as source when its dirty argument is
nonzero. Thus that insertion branch skips the sensor notification.
When the dirty argument is zero, it instead clears the child's update state and
preserves the owner's prior low flag bit.
`mark_model_update(model=...)` implements the positive serialized flag mutation
for normal regeneration. It does not simulate debug-no-regeneration mode,
sensor callbacks, feature insertion itself, or a completed body update.

Stamp advancement is a separate operation, not an effect inferred from that
flag mutation. `moModel_c::updateSessionStamp` at `0x4c03a810` calls
`moHeader_c::getNextUpdateStamp` through import `0x4cd357f0` at `0x4c03a916`,
then assigns the result to the active configuration's `f860` when one exists.
The header getter at `sldarchiveu` `0x31a05350` increments header word `0x40`,
stores current `su_CTime` at `0x48` and returns the new counter.
The independent body-stamp getter `0x31a05340` increments header word `0x44`.
The model wrapper returns void; its raw return register is not a semantic stamp.
The model's `f1300` increments only when virtual slot `0x16d8` returns true;
both classified model and part vtables resolve it to constant false.
Feature `postUpdate` at `0x4c1ce660` can call
`updateSessionStamp(owner, 1, -1)`, then helper `0x4bb4a4b0` writes the current
stamp to feature `f29c` and obtains new `f2a0/f2a4` FILETIME words.
Body stamps advance through separate `getNextBodyStamp` calls on actual body
and regeneration paths. None of these counts is derived from visible feature count.
The ordinary geometric command's complete insertion/post-update caller sequence
and completed body/cache state remain unresolved; a flag helper does not close them.

The part vtable overrides `addFeature` slot `0xfb8` with `0x4c1c5040`.
For primary profile vtable `0x4d0e8e80` and extrusion vtable `0x4cf3d488`,
its predicates `0xd18/0xd20/0xc48/0xd10` return false and `0x1450` returns true.
The part override delegates the base insertion and updates runtime insertion
cursor `0x58`; its special-folder branches do not apply to these two classes.
The base callback `0x11a8` resolves to `0x4bdacc50`, which updates the feature
name map and linked insertion list. The feature owner callback `0x1288` resolves
to `0x4bb51930`, which leaves the already matching constructor owner unchanged.
Its linked-list helpers `0x4c03d1c0` and `0x4c03e4c0` call the child connection
slot `0x4d8`; both ordinary child classes resolve that slot to `0x4b2fe0b0`,
which only increments runtime reference count `0x10`.
Neither callback advances header ids or stamps on those ordinary paths.

The fresh part's update query follows an explicit constructor path too.
Part vtable `0x4d1252d8` slot `0xc0` resolves to `0x4c1b8a60`.
Model constructor `0x4c00edb0` writes qword `0x0c` at runtime offset `0x2b0`,
so its upper word `0x2b4` is zero and the query's cached-update shortcut is
absent. It calls node getter `0x4c03e5e0`, which returns `1` immediately when
node `f0c` bit `1` is set. Derived-part traversal is reached only after a zero
node result. This closes the pending constructor query for the fresh ordinary
part; it does not prove completion of a rebuild or every cleared-state query.

## Header counter and save lifecycle

Status: **partial — code-derived rules, without generated-header native acceptance**.
These rules refer to the manifest's `sldarchiveu.dll`, SHA-256
`5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48`.
The serializer evidence is REA
`ev_99ce3579fb4002b5f0f926a20a8691b3b10de7c06da3b548f8649cdc37297589`.
Its subject digest matches the manifest.

| Operation                   | Rule                                                                                                                                                            | 2026 address |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| Constructor                 | Seed independent update/body counters `f40/f44` with `101`; initialize `f48` through local calendar time `1990-01-01`, and `f50` through the unset-time utility | `0x31a02540` |
| Next update stamp           | Increment the 32-bit `f40` word, replace `f48` with current wall time, return the new counter; both formal arguments are unused in this build                   | `0x31a05350` |
| Current update stamp        | Return `f40`; the optional name argument does not select a separate counter                                                                                     | `0x319f9810` |
| Next body stamp             | Increment the independent unsigned `f44` word and return it                                                                                                     | `0x31a05340` |
| Body stamp synchronization  | Replace `f44` only when the supplied unsigned value is larger                                                                                                   | `0x31a05680` |
| Explicit update replacement | Store the supplied `f40` value and return the previous value                                                                                                    | `0x31a06100` |
| Update rollback             | Decrement `f40` without changing `f48`                                                                                                                          | `0x31a04f20` |
| Storage wrapper             | Select the header stream and call serialization without advancing either counter                                                                                | `0x31a05d00` |

The loader normalizes the constructor update seed. After reading `f40` for
versions above `150`, instructions `0x31a03fed`–`0x31a03ff3` change `101` to
`102`. A temporary current-time assignment follows. For versions above `3676`,
including `19000`, the later read at `0x31a0440a`–`0x31a04411` overwrites that
temporary `f48` with its stored value. No corresponding body-counter
normalization appears in this serializer.
The lossless research codec preserves the original wire value; it does not
simulate this native in-memory fixup.

The clock name is misleading. Imported `su_CTime::GetTickCount` resolves to
`swccu.dll` `0x31a4c5d0`. That function calls `_time64(NULL)` and copies its
result into the returned time object. It is wall time in seconds, not the
Windows millisecond uptime counter. REA evidence
`ev_30b8661a0b8051b1107966b2e0e9d1fa2e04f257ef3d5c8216ef7cb4e37e9d30`
records the exact module SHA-256
`d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c`.

Save-time `f50` normalization is conditional rather than an unconditional clock
write. The serializer compares its local-calendar year to the unset-time
sentinel's year. When those years match and archive condition `0x80` is absent,
it chooses current `_time64` time for calendar month zero; otherwise it uses
`f70`, falling back to current time if `f70 == -1`.
The decision and assignment occupy `0x31a035a6`–`0x31a03612`.
An authored modification time outside that sentinel year passes through this
branch unchanged. This does not establish every higher-level save caller.

The model's session operation and body lifecycle remain separate.
`moAtom_c::setBody` at `sldmodu` `0x4bcfb360` returns immediately for a null body
or feature. It allocates a body stamp only when its third argument is nonzero
and its manager/model/header path exists.
`moFeature_c::iUpdatePreviewBodyTimeStamps` at `0x4bb4a890` iterates actual preview
bodies and allocates one body stamp per body. An empty preview array takes no
allocation path there.
The model-update completion routine `0x4c1c8320` contains an additional session
update call at `0x4c1c88ba`, conditional on its update work and prior status.
These paths explain why visible-feature counts cannot determine either counter.
No fixed increment count is inferred for fresh generation.
See [initial update normalization](../../../Documentation/Gotchas/Conversion/Solidworks/InitialUpdateStampIsNormalized.md)
and [the header clock](../../../Documentation/Gotchas/Conversion/Solidworks/HeaderClockIsWallTime.md).

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
It now requires ordered authored `folder_names`, `cabinet_name` and `created_at`
in addition to the existing part/plane/configuration metadata.
The supported construction profile names all twelve classified folder classes;
this is an explicit graph request, not a claim that every vendor template uses
the same set or order.
The returned `folders` mapping and `cabinet` retain their actual object identities.
Its system-feature tuple follows the authored folder order, then the cabinet,
then native principal-plane creation order `z/y/x`.
The selected generic insertion order is authored; the automatic UI reordering
callbacks are separate operations and are not silently approximated.
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

## System folders and annotations

`folder` constructs a supported native folder class from an authored name,
owner, allocator, version provenance and Unix-seconds creation time.
`system_folders` consumes an ordered class/name mapping and returns the actual
object tuple, preserving pointer identity without a captured feature table.
It does not invent a mandatory default-folder order.
`detail_cabinet` constructs the separate annotation-cabinet model feature.

Native folder `addToModel` callbacks use the owning model's slot `0xfd0`,
`moConcept_c::addNewFeature` at `0x4bda66c0`, which assigns the owner, invokes
the new-feature hook and delegates insertion through slot `0xfb8`.
For a part that slot dispatches to `0x4c1c5040` as described above.
The callbacks also bind model caches to the actual folder objects:

| Folder         | Model slot | 2026 binding evidence               |
| -------------- | ---------- | ----------------------------------- |
| Environment    | `0x1e0`    | `0x4beb3ca0`; getter `0x4b2863b0`   |
| Documents      | `0x1f0`    | `0x4beb3b90`; getter `0x4b285f80`   |
| Comments       | `0x1f8`    | `0x4beb39d0`; getter `0x4b284d50`   |
| Sensors        | `0x200`    | `0x4beb4240`; creation `0x4c016ab0` |
| Favorites      | `0x218`    | `0x4b63e180`; creation `0x4c015bb0` |
| Selection sets | `0x220`    | `0x4b641240`; creation `0x4c016a30` |
| History        | `0x228`    | `0x4b6453c0`; creation `0x4c016260` |
| Surface bodies | `0x1500`   | getter `0x4b289bd0`                 |
| Solid bodies   | `0x1508`   | getter `0x4b2899f0`                 |

Environment `f1e0` is serialized in the configuration graph. `part_graph` binds
it to the same environment object also present in the system-feature tuple.
The remaining cache relationships are retained as semantic pointer bindings,
not invented archive-index fields. The relation-manager/equation-folder backlink
also preserves the actual graph objects.
System nodes receive the proven zero-status initialization mask, while the part
retains its constructor's pending-update state until composition performs an
explicit later operation. This does not complete origin solver state or body caches.
See [system-folder bindings](../../../Documentation/Gotchas/Conversion/Solidworks/SystemFoldersHaveModelBindings.md).

The folder base at `0x4beae110` calls the default feature constructor
`0x4bb38710`, then assigns its owner.
That constructor calls `GetSystemTimeAsFileTime`, whereas owner-taking geometric
feature construction initializes the same two fields to zero.
The builder derives those signed low/high 32-bit words from the authored time:
`ticks = (unix_seconds + 11644473600) * 10000000`.
This is volatile provenance, not a value copied from a saved folder.

| Class                    | Constructor                     | Stored additions to the common feature fields                             |
| ------------------------ | ------------------------------- | ------------------------------------------------------------------------- |
| `moFolder_c` base        | `0x4beae110`                    | `f360=1`, `f370=0`                                                        |
| `moCommentsFolder_c`     | `0x4beadcb0`                    | `f360=0`                                                                  |
| `moDocsFolder_c`         | `0x4beadef0`                    | Base stored state                                                         |
| `moEnvFolder_c`          | `0x4beadfb0`                    | Base stored state                                                         |
| `moEqnFolder_c`          | `0x4be86710`                    | Owning model's relation manager; no additional stored payload             |
| `moFavoriteFolder_c`     | `0x4b63c9a0`                    | Empty `f3c8/f3e8` arrays, `f408=1`                                        |
| `moHistoryFolder_c`      | `0x4b644960`                    | Empty `f3c8` array                                                        |
| `moMaterialFolder_c`     | `0x4beae310`                    | Empty material string, zero material flags                                |
| `moNotesAreaFtrFolder_c` | `0x4bebdab0`, base `0x4bebd600` | Null `f388`, zero `f37c/f394`, `f378=f39c=1`                              |
| `moSelectionSetFolder_c` | `0x4b6404b0`                    | Empty `f3c0` array, `f3e0=1`                                              |
| `moSensorFolder_c`       | `0x4beae440`                    | Base stored state                                                         |
| `moSolidBodyFolder_c`    | `0x4beae530`, base `0x4beadbc0` | `f360=0`, zero `f37c/f380`, null material/sort references                 |
| `moSurfaceBodyFolder_c`  | `0x4beae570`, same base         | Same fresh body-folder state                                              |
| `moDetailCabinet_c`      | `0x4ba2b850`                    | Model-feature base, empty `f368/f388/f3d8`, unit `f370/f378`, zero `f3f0` |

Material assignment, equations, body membership and annotation contents require
their own generated semantic subgraphs; these factories describe fresh empty
instances. They do not claim accepted caches or full family coverage.

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

The journal's archive class schema is the format constant `0`, not the archive
object helper's generic default `1`. The exact 2026 `slduiu.dll` exports
`uoJournal_c::classuoJournal_c` at `0x4aef6660`; its `CRuntimeClass` word at
offset `0x0c` contains four zero bytes. The class name pointer resolves to
`uoJournal_c`, and its object-size word is `0x48`.
The module SHA-256 is
`025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7`.
The constructor now supplies `schema=0` explicitly.
This rule was located with a native loader observation, then proved statically:
the parent-owned candidate trace `candidate-H3-schema.json`, SHA-256
`78c581343341446555c9c02da5872ca3c6a08c665dcd9dc3eae2c9001f43e4dc`,
observed runtime schema `0` versus file schema `1` at `swccu` relative address
`0xa3a7`, followed by the nonversionable bad-schema exception path.
It is a negative candidate result and not native acceptance.
No saved document supplied the corrected value.
See [runtime class schemas](../../../Documentation/Gotchas/Conversion/Solidworks/RuntimeClassSchemasDiffer.md).

The owned-constructor class audit also checks every concrete model, folder,
plane, configuration, self-component and display-data record against its exported
registered class metadata. Those concrete records use wire schema `1`.
The standalone `moCompRef_c` base is different: exported class metadata at
`sldmodu` `0x4cf68440` has schema `0xffff` and a null create-object function.
`component_reference` therefore fails closed. Its field initializer remains
available for the base portion of concrete dimension and feature references;
that base portion does not emit a standalone class header.

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
Later runs below cover the expanded principal-plane and part-root checks.
The original suffix-based audit allowed unrecorded reads whose filenames looked
like code. It does not establish an unqualified zero-runtime-read claim.
The current harness imports its trusted bootstrap and `ConstructionGuard` first,
then installs `BuildAudit.InspectEvent` before builder imports and schema discovery.
Permitted code-loader reads and directory scans are recorded in `ModuleReads`.
`BeginBuild` ends that phase before any model or stream construction and blocks
all covered file opens, directory enumeration and process-launch events.
The result reports both recorded imports and actual denied attempts; the test
also checks that the construction phase is active and the builder import was seen.
The repaired strict audit passed the actual subprocess/container boundary at
`5b546278f` in [run 43681676456](https://github.com/TryUniCAD/Kit/actions/runs/43681676456),
job `132713453212`. Both the native-file step and its enclosing policy job passed.
This is component codec/access evidence, not native application acceptance.
The expanded process check now also constructs the full requested base graph
from generated style/unit dependencies, serializes Config and Resolved streams
through one shared archive map, and verifies the environment alias and native
self-component identity after decoding. It exercises zero/positive owner update
flags through that file boundary. This expanded subprocess check passed at
`6c8f92431` in [run 43688828337](https://github.com/TryUniCAD/Kit/actions/runs/43688828337),
job `132734920405`. The job reported `5 failed, 134 passed, 158 skipped`;
the model process was among the passing cases. Other signature-fixture,
assembly-schema and composed-part callers kept the enclosing job red.
The passing component process does not qualify those failures or establish
native generated-part acceptance.
The first strict-audit remote run at `236ccd510` correctly denied a lazy import
of `encodings/utf_16_le.py` during Unicode string storage. The harness now resolves
the native string codec names during its recorded initialization phase, before
`BeginBuild`; construction retains the same unconditional file-access ban.
See [lazy codec imports](../../../Documentation/Gotchas/Conversion/Solidworks/LazyCodecsAfterAudit.md).
The expanded check also passes all twelve supported folder classes and the
annotation cabinet through a separate generated stream in the container,
then checks class identity, id allocation and recovered creation times.
That actual subprocess/container test passed in
[run 43677223605](https://github.com/TryUniCAD/Kit/actions/runs/43677223605)
at `e26a6d095`; the workflow remained red because pytest separately collected
its `Check*` assertion helpers as tests. Helper names, JSON-report typing and the
weaker audit were corrected for the next remote run.

Still required: complete origin/system-feature composition,
full detail-style and unit construction, whole-part round trips, held-out target
measurements, rebuild and dimension edits, and production promotion.
No whole-part acceptance is established by these component constructors.

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
permit stopping only on success under every criterion, or at the end of the
available context.
