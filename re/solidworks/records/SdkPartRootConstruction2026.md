# SDK fresh ordinary part-root construction

Task `B04-SW2026-CONSTRUCTION`, owner `/root/flag_ownership`, delivery PR #121.
The bounded component constructs the ordinary 19000 `moPart_c` root and its
owned fresh dependencies. Configuration-manager, system-feature, origin,
profile and operation attachment remain separate construction steps.
No public writer is registered. The prior 47-path polygon handoff is unchanged.

Status: the frozen standalone root process proof passes. Full part composition,
native acceptance and held-out qualification remain open.

## Rule and dependency basis

This component uses the [model construction ledger](ModelConstruction2026.md#part-root-graph),
[standard-view construction](StandardViewsConstruction2026.md) and the current
SDK Config/header codecs. Model addresses refer to 2026 SP05.2 `sldmodu.dll`,
SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`,
base `0x4b140000`. No new binary analysis or vendor-file inspection contributed.

`MakePartRootMut` consumes `PartRootInput`, `PartRootRefs` and the shared
`PersistentIds` allocator. It allocates a plain schema-one `moPart_c`, initializes
its actual node/concept identity, constructs the complete model/part state and
returns that same node. Allocation consumes one persistent ID. Archive indices
remain the SDK serializer's responsibility. The name and hatch name are authored
strings; version must be 19000.

The shared `Construction/Nodes` initializer and allocator are owned by the
parallel assembly lane. This tranche consumes their stable contracts and pins
four required dependency files in its source manifest. It does not duplicate
node naming, ID allocation or concept-list construction.

The caller supplies actual generated document and analysis unit nodes, detail
fields, model visual properties and ten indexed view nodes. These are explicit
typed graph dependencies, not saved rows. The factory retains their identities
and preserves a mutable detail-field mapping without materializing lazy formulas.
Units must be distinct schema-one `moUnitsTable_c` objects. The model visual
record selects `f5c=1`. The current view profile requires effective detail
standard one, ten distinct schema-one `moView_c` objects and indices zero through
nine in order. This tranche does not claim to replace their separate generators.

Source-only AST inventory finds the same 140 unique root mapping keys as the
current research `part_root` path: nine inherited concept keys and 131 additional
unique keys. This counts mapping keys, separately from historical field-owner
partition counts. No field key is omitted or invented in the port. The private
census has SHA-256
`ce446547cd9df86bd1bc289caf997db696aa7c470e9102758a595eb06e3d78ed`.
This is a source inventory, not a newly executed native or codec result.

## Fresh ownership and active initialization

| Owner or field         | Classification and construction                                                           | Existing exact-build evidence                                                                                  |
| ---------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Root name and ID       | Authored name through the shared node constructor; actual allocator-derived `f08`         | Node constructor `0x4c03c250`, header allocator recorded in the model ledger                                   |
| Root `f0c/f28/f20`     | Node constructor update state one, mask `0x40000000`, empty text                          | Same node constructor                                                                                          |
| Root `f2c` bit `0x100` | Derived lightweight storage state applied to initialized node flags                       | Native model lightweight save before `0x4c17aa00`                                                              |
| Root `f990`            | Fresh unit self component whose actual owner is the root                                  | Active initializer `0x4c00d8f0`, unit construction/store `0x4c00e850/0x4c00e85a`, getter `0x4c0254c0`          |
| Root `f9d0`            | Fresh relation manager retaining the actual runtime owner                                 | Same active initializer; relation constructor `0x4c366bd0`                                                     |
| `f9d8/fa48/fa50`       | Three independently allocated empty `suObList` nodes from active new-model initialization | Active initializer described in the model ledger; typed pointer stores `0x3c8cceb0/0x31a45ef0`                 |
| `f9b8/f9c0`            | Explicit generated user and analysis unit graphs                                          | Setters `0x4c031e20/0x4c0318c0`; analysis assignment is an explicit caller policy after the active constructor |
| `f78/fae0`             | Explicit generated model visual and detail graphs                                         | Shared model LW/RES methods `0x4c22ec80/0x4c234150`                                                            |
| `f9f8`                 | Exactly ten actual generated view references, preserving indexed order                    | Model RES method and view construction ledger                                                                  |

The active new-part constructor `0x4c19f170` calls shared initializer
`0x4c00d8f0` at `0x4c19f1c7`. The new-assembly caller is `0x4b67efe0`,
call `0x4b67f037`. Accordingly, `MakeSelfComp` and `MakeRelGraph` support actual
schema-one part or assembly owners. They reject unresolved placeholders and
unproved drawing-root use. Part-specific scalar construction stays in the part
factory; its dictionary must not be renamed into an assembly.

The older research root uses the loading/default constructor's null
`f9d8/fa48/fa50` representation. This factory deliberately models the active
allocation sequence. An empty list pointer is not serialized as null. The loader
repairs null `fa48/fa50`, but equivalent absent `f9d8` semantics remain partial.
No missing-pointer fallback is added. See
[constructor paths](../../../Documentation/Gotchas/Conversion/Solidworks/Model/LoadingConstructorsDoNotDefineFreshGraphs.md)
and [concrete offset ownership](../../../Documentation/Gotchas/Conversion/Solidworks/Model/ModelOffsetsAreTypeSpecific.md).

The self component's `owner` is a real serialized reference, forming the actual
root cycle. Relation-manager `owner` is construction metadata; its serializer
contains the relation/value collections and scalar fields, not that runtime
backlink. Independent preparation checks the actual self cycle and relation
manager wire state without fabricating an absent owner field.

## Remaining complete constructor fields

The model constructor is `0x4c00edb0`; the derived part constructor is
`0x4c19e7b0`. Common fields follow their shared LW/RES boundaries, and part-only
fields follow `0x4c2309d0/0x4c2378b0`. Field groups below are native format
vocabulary, not captured field programs. All empty counts derive from fresh
empty collections. Known constructor values remain scoped to this operation
sequence, not universal saved-document defaults.

| Field group                    | Classification and rule                                                                                                                      |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Model arrays                   | Fresh `f168/f178/fcd8/f1310/fec0/f1288/ffe0/f10b0/f1d0` collections and their nine actual lengths                                            |
| Model embedded lists           | Fresh independent `fc90/fb08/f9c8/fb30/fba8/fb58/fb80/fbf8/fbd0/fc20/fc70/f240` list payloads                                                |
| Face properties                | Fresh `fdd0` face/property arrays and their actual lengths                                                                                   |
| Part collections               | Fresh `f1108/f1130/f1628/f16e8/f1640`, their three stored counters, `f938` body properties and `f1c70` list                                  |
| Cleared model scalars          | Explicit constructor clears named by `KModelZeroes`, including presence words, update-related flags and unsupported-cache absence indicators |
| Null optional model references | Explicit absent `fa70/f2f8/f1e0/fa88/attach/fe80/fa90/fed0/fe38/f12d0/f1338` until an actual owner is attached                               |
| Part scalar/reference state    | Explicit constructor clears named by `KPartZeroes`, with null `f1420/f13f8`                                                                  |
| `fdb0`                         | Fresh `moTransRefPlaneData_c` from constructor `0x4c6f3b30`: `f08/f0c=1`, masks `0xff00/0xff/0x5f`, final zero                               |
| `fa98`                         | Save-helper kind two, empty alias map, signed forms of native `0xaaaaaaaa/0xbbbbbbbb` markers from `0x4b4c7a40`                              |
| `fd88/fd90`                    | Fresh atom and ghost managers: actual empty collections, next IDs 100/10000 and clear flags from `0x4bced920/0x4bf03a90`                     |
| `ff80/ff88`                    | Direct model constructor binary64 values 1000 and `1e-8`                                                                                     |
| `f784/f7a4`                    | Computed sixteen-byte zero arrays from zero-initialized constructor members                                                                  |
| `fce8/fcec/fd44/fd50`          | Direct model constructor values 50/108/10/1                                                                                                  |
| `feb0/feb4/feb8`, `f760/f768`  | Constructor 199/199/zero and empty strings                                                                                                   |
| `f1104/f1128`, `f1300/f18d8`   | Independent constructor increment counters 20/20 and update stamps 101/101                                                                   |
| `f1418`                        | Fresh `gcXhatch_c` from authored hatch name, zero angle, scale one and documented constructor flags                                          |
| `f1588`                        | Fresh `uoModelData_c`, null light graph and zero flag from `0x4c3ba670`                                                                      |

The initial root leaves its configuration manager and concept feature list
unattached. This is an explicit construction stage, not a complete document.
The caller must attach generated managers, system features, origin, profiles and
operations before a full part is emitted. No empty body or mass cache is reported
as measured geometry.

## Process proof and status

The first frozen executable manifest has SHA-256
`9e8defda1827e6fcc2ed7a2f0ead7309408f3689697d3a333e4fb0a2ccc37b52`.
It contains 25 task-owned executable files and four shared node dependencies.
Eighteen SDK modules and five permanent process-test modules pass Black, Ruff,
Mypy, Pyright and steering. Both research scripts parse. The worker ran no
constructor, serializer, schema, test, CAD application or VM operation.

`SdkPartRootProcess` receives an authored JSON request on stdin. The test harness
generates its explicit detail/unit/view/visual dependencies with existing trusted
research helpers after the runtime-input guard begins. The production model
factory imports none of those helpers. The root itself, owned lists, self
component, relation manager, hatch and display data come from the SDK constructors.
The actual SDK writes the standalone ordinary Config root and its generated
model header.

`SdkPartRootPrepare` uses a separate interpreter with only the SDK and audit
imports. It reads both generated streams, verifies persistent/root/header IDs,
authored names, actual self-component cycle, distinct active lists, separate
unit owners, indexed view ownership and complete byte identity. It does not
recreate runtime relation ownership. Neither phase reads a saved part, donor,
template or external file after initialization.

The permanent `TestPartRoot` declares two distinct names, Unicode metadata and
different allocator seeds/reservations. Each model must reject ten malformed
constructor inputs without consuming another ID. Four fresh guarded phases
exercise two build/prepare pairs. The parent independently froze 4,166 source
files from base `4ba000f1ca170f167094d161394f6e130a36ff1d` and passed
`TestPartRoot`. The exact complete source manifest has SHA-256
`b242761082710154fab05a3aef32ac77fd5f6c808764092708a1f44a5ff938cc`.
The retained process-result text has SHA-256
`82c10de82fe501173849db12e99ba70e37794e513d139efe66630d1dac5ef844`;
stderr is empty. The worker checked all 29 executable/dependency bindings
against that source manifest and the active checkout. No frozen code changed.

The passing test checks model IDs one and nineteen from explicit allocator
seeds/reservations, with actual header next values two and twenty. It checks
three active auxiliary lists, ten independently owned indexed views, actual
self-component cycles and separate document/analysis unit ownership in both
models. Four prepare stream comparisons pass, twenty malformed cases reject,
and all four guarded phases report zero runtime input-file reads. The two
Config stream lengths differ with authored metadata.

The [sanitized receipt](../measurements/2026/SdkPartRootConstruction01.json)
binds the exact source and retained passing result. Detailed child JSON reports
were not retained by that test invocation. The receipt therefore records the
assertions exercised by the frozen passing test, without inventing exact stream
sizes, stream hashes, map counters or class counts. Native and held-out results
remain absent for this SDK source.

## Next integration boundary

The next factory step must bind the actual configuration manager, system-folder
and principal-plane graphs to this root, with correct feature registration and
header publication. The existing SDK Config, CMgr and Resolved codecs are the
serialization foundation. The existing SDK polygon and blind-end constructors
remain separate components. Detail/unit/view constructor promotion and complete
part Definition construction remain owned dependencies. This source does not
enable Core/Adapter writing or weaken an unsupported-profile diagnostic.

The CAD stopping conditions remain:

> The first is success under every criterion on this page.
> The second is the end of the available context.

Complete native synthesis and measured writer qualification remain work under
those criteria.
