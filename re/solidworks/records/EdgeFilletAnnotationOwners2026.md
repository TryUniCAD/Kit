# Explicit annotation ownership for a constant-radius edge fillet

Task `B04-SW2026-EDGE-FILLET-SOURCES`, PR #121. The private model-only
fillet compiler now accepts an explicit catalogue of signed principal
annotation views and the name of the radius display's actual member.
The scope is the existing ordinary one-stock, one-edge fillet compiler.
The change carries authored display ownership separately from the live
D1, selected edge, result keepers and rollback. The SDK source tree is
`29441de5a755d8b217f4c5067726776a3fad5f97` at base
`f835b1395a6e0159e2e08ae45d26a3239e0151ed`.
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Writer model](../../Playbook/WriterModel.md) ·
[Prior fillet compiler and lifecycle](EdgeFilletModelCold2026.md)

## Exact source and model rule

The four verified original and edited SOLIDWORKS 2026 SP05.2 saves at
build `34.5.2.0604` have the same archive map slots 101 and 102 for two
distinct `moAnnotationView_c` objects in `moPart_c.fa48`. Their stored
view IDs are 200 and 201. `moDisplayRadialDim_c.f2b0` holds view ID 201
in each archive. The real owner is `*Back` on the axial model and
`*Left` on the transverse model. `*Top` is the earlier view in both.
The radius edits retain the same names, signed frames and owner links.
The active and shown selections both retain reserved ID 199. These
integers are observed identities, allocated from actual catalogue order.
[Disclosed archive pins](../measurements/2026/EdgeFilletArchiveRead01.json)

The exact `sldmodu.dll` SHA-256 is
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`,
REA identity `ev_7fc3ecfa02cbbd7d6067ca5c370b778582e5ddc85ae1940285a50b90bfc6ceec`.
`moDisplayItem_c` initializes its member set empty in
`[0x4ba657a3, 0x4ba657d4)` (code SHA-256
`d671ec3bf1888d68276eafcae552c754174c1235049215a630c7fe4e00bc5757`).
`moDisplayItem_c::getAnnotationView` at `[0x4ba69760, 0x4ba697a6)` checks
its count and reserved value 199, finds the actual model, and calls
`moModel_c::getViewWithThisId` at `0x4c026e90` with the stored member. The
getter span SHA-256 is
`9b72f0eb0245c4b649825cecb02f83e4f5ee8ade302856a82df66b339116f4ea`.
This is the same physical form as the independently proven annotation
catalogue used by chamfer and angular pattern displays.
[Shared catalogue proof](LocalLinearPatternAnnotationCatalog2026.md) ·
[Chamfer drivers](ChamferDriverConstruction2026.md)

This work accepts an optional `annotations` object on the existing
neutral fillet worker request. Its `views` contains one to three ordered
`name` and `basis` pairs in signed principal model axes. Its `driver_view`
names a single registered view. `active_view` and `shown_views` name
actual entries or explicitly use `null` for the reserved identity. The
compiler uses `PutAnnoCatalog` and `ReadAnnoView` to bind the radial
display to the actual newly allocated view. The paired decoder checks
the inherited catalogue and confirms the named view is the same stored
member. Standard cameras are separate. Automatic view choice, warm
arc-frame and witness placement, and first native processing of these
new outputs remain unqualified.
[Typed compiler binding](../../tooling/sw2026/edge_fillet_source/cold/ColdFilletAnno.py)

### Shared edge reference and first wire occurrence

The intact archives and prior cold output have distinct selected and
radial `moCompEdge_c` wrappers sharing the same `moEdgeRef_c`. On the
ordinary part branch of the exact `sldmopartu.dll`
`edgeRadiusObject_c` constructor, the calls at `0x18026b9a3` and
`0x18026b9af` obtain the actual self component and prior selected
wrapper's reference. The call at `0x18026b9be` constructs the new
wrapper using those owners. The installed module SHA-256 is
`aa3fa88eeb5349c8ac2161ce9b3f18ab4e23417598c6b57719c88d5d6c178da9`.
In the saved graph the populated edge keeper precedes `f848` and first
allocates the common reference at map slot 284. In the cold graph that
keeper is legitimately empty and `f848` first allocates it at slot 212
in the two pinned candidates. The actual alias across both wrappers
is the invariant. First occurrence follows the graph's serialized
order. The earlier static trace explains why the pending reference
moves to the keeper only after a successful solve.
[Exact saved owner and alias layout](EdgeFilletArchive2026.md) ·
[First-solve keeper assignments](EdgeFilletResultOwners2026.md)

## Guarded proof

The worker reads and re-emits the actual Config-0 bytes for all four
disclosed saves, checks both physical catalogue owners in the inherited
map, and checks the driver name, rotated axes, independent shown and
active identities. No vendor save enters a compiler process. Twelve
guarded construction calls use neutral stdin. They reproduce the two
prior no-catalogue whole files and both radius-only whole-file digests.
Each annotated model compiles twice. The four generated files are
decoded in separate workers and replay both their exact Config-0 and
ResolvedFeatures bytes. All data workers log zero external access after
setup. The two catalogue-only comparisons change exactly Config-0 and
ResolvedFeatures. Their map base moves from 89 to 92 with the shared
descriptor and two view objects.

| Neutral case | Joined driver view | Allocated view ID | Whole archive SHA-256 |
| --- | --- | ---: | --- |
| Axial, source orientation | `*Back` | 201 | `8122e38a9b94d396f789395e2f0eaeea2aa085dcd0b7dad093d2770c6e449393` |
| Transverse, source orientation | `*Left` | 201 | `7bb49510159be9da0148ab5d2fbedf57d39aa3d12ceb4467e441fda9e43a32ea` |
| Independent axial geometry and catalogue order | `*Back` | 200 | `cc567243e8156044400ecb082cf3ba3e0a8b2c73442a34116b18f99707f516d9` |
| Independent transverse geometry and catalogue order | `*Left` | 202 | `db238fdfb64bed1a0ae6e51e34eb42962671f7e3aa501d733b941561f54ed150` |

Four additional neutral requests refuse a missing driver name, a
duplicate view, an unknown shown view and a left-handed basis. The
existing default and saved resolved scopes still refuse the cold
fillet graphs. These are offline archive and semantic results. They
add zero native acceptance, held-out credit or public writer capability.
The cause of the prior incomplete native lifecycles remains unknown.
[Numeric evidence](../measurements/2026/EdgeFilletAnnotationOwners01.json)

```sh
python3.14 -I -B re/tooling/sw2026/edge_fillet_source/cold/ProveFilletAnno.py \
  --capture /absolute/path/to/disclosed/EdgeFilletSource03/Capture
```

The proof consumes only the four exact disclosed filenames and uses the
previously pinned typed archive reader. The general research CLI does
not expose the opt-in fillet graph or a guarded model-only writer
worker, so this proof reuses the existing fillet worker and emits a
digest-and-metadata receipt to standard output. It creates no new CAD
file on disk.
