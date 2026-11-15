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
The new process-boundary check is prepared for remote PR CI: it constructs
different configuration counts and Unicode names from no input file, serializes
both components into a generated container, decodes and re-emits each stream,
checks object aliases and rejects runtime data-file reads through Python's audit hook.
It deliberately keeps both vendor-acceptance flags false.

Still required: the complete part root, native planes/origin/system features,
full detail-style and unit construction, source-native round trips, held-out target
measurements, rebuild and dimension edits, and production promotion.
No whole-part acceptance is established by these component constructors.

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
permit stopping only on success under every criterion, or at the end of the
available context.
