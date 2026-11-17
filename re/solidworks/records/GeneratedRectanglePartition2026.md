# Fresh rectangular boss partition projection

The [rectangle projection](../../tooling/sw2026/para/rectangle/RectanglePartition.py)
starts from the neutral model's generated sketch and extrusion, the resulting
prism, and an explicit model-update and mark history. It builds linked active
and rollback graphs for the pinned SOLIDWORKS 2026 SP05.2 partition grammar.
The standalone projection has no document emission path. A separate
enclosure tool prepares one bounded native discovery pair with matching
configuration, feature and partition objects. It requires independent
vendor open, edit, save and reopen before archive qualification.

## Native ownership rules

| Record or relationship | Construction and 2026 authority |
| --- | --- |
| Body resolution | Kernel `RES_set_precision` at `0x1804fa74f–0x1804fa7d4` divides the linear scale by the session precision and stores the quotient. The body initialization at `0x181b2f769–0x181b2f79f` stores that quotient and the actual linear scale. For the modeled session the inputs are (10^{-8}) and (10^{-11}). The quotient in binary64 is `1000.0000000000001`. |
| Tolerance, topology, and optional geometry | The body initializer at `0x18144c6d0` seeds ordinary null owners and the missing-parameter sentinel. Vertex construction at `0x181452dbf–0x181452dd9` uses the same sentinel. The linked geometry is constructed from the actual sketch and blind depth via `BuildPrism`. The solid and void shell uses and terminal fin semantics follow the [partition grammar](PopulatedPrismPartition2026.md#topology-and-ownership). A vertex owns one cut of its incident fin rotation. For this projection, the first authored incident fin starts the list and `fin.forward.other` steps to the next fin at the same terminal vertex. |
| Definition fields | SOLIDWORKS calls `gciAttribDef_w::make` `0x330390a0`, which supplies owner and field selections to `PK_ATTDEF_create` at `0x18009bba0`. Internal user type 9000 and null field names are established at `0x18009c408` and `0x18009c3e4`. Owner dispatch begins at `0x18009c1f0`, field-kind translation at `0x18009c380`, and operation actions at `0x18009c12c`. The body, face, and appearance definitions are enumerated below. |
| Owner and type links | Kernel `ASS_attach_attribute` at `0x180567b7c–0x180567c0a` inserts at the head of its entity owner. `ASS__a_at_chain` at `0x180a863d0–0x180a86467` finds the existing type, inserts the new head and sets the old head's back-link. `0x180a86568` supplies type 4 and capacity 20 for a new body list. `0x1804ce553–0x1804ce560` initializes type, capacity, length and finger index. `0x180a86688–0x180a866ae` appends a newly seen type and increments both counts. In all six disclosed controls the `WORLD` definition chain is the reverse of that first-use order. |
| Nontransmitted fields | Class `POINTER_VALUES` is marked nontransmittable at `0x1814391d6`. `PK_ATTRIB_set_pointers` routes through `0x180afd2c` to the attribute writer, whose positive-count and absent-node path allocates kind 95 at `0x180a87204–0x180a8721b`. It copies the supplied elements at `0x180a87260`, including any null element. The typed fields in the projected wire graph hold null references at these positions. |
| Face identities | `moExtrusion_c::iAssignFaceIds` walks the end and sketch-owned cases at `0x4b784c36` and `0x4b784c53`. `moEntityIdHelper_c` routes the face representation through virtual slot `0xd0` at `0x4c6c32e0`. Cap and side builders at `0x4c6c78a0` and `0x4c6c8030` pack the feature ID, creation time, and flags without local-reference flag bit 4. Cap ID kind 40 carries the cap role and contour ID. One ordinary closed contour uses index zero. Side ID kind 74 carries the persistent ID of the sketch line selected by the lateral surface relationship. The creation time belongs to the feature log, or the native unset time when there is no feature log. |
| Face identity sequence | `moFace::assignNewPermId` at `0x4be97a34` supplies zero to the normal allocator. `gcFaceIdAttrib_w::makeFaceIdAttribute` at `0x43b39c56–0x43b39c63` uses and postincrements the session face ID counter. Its image seed at `0x4415bc10` is one. Slots zero and one have one pointer element, and slots two and three carry the integer representation and identity mirror respectively. The external model belongs to the local part, so its converted pointer reference is zero at `0x43b39d00`. |
| Body recipe and lightweight identity | `mo_SetBodyModel` at `0x4c02e000` assigns a runtime model pointer using the recipe attribute. It has no integer mirror. The ordinary visible solid selects the previous lightweight identity with its low bit set at `0x4bb2dd89–0x4bb2dd9a`. Its absent value starts at zero, and `0x32f83502` writes the result to the persistent integer field. |
| Rollback | Selected geometry deletes the newly allocated local body, geometry, topology, lists, and attribute values. Kernel `0x1819e9eeb–0x1819e9f0c` selects the runtime counts independently of transport direction, while the record walk at `0x1819ea1d8–0x1819ea266` filters and remaps the emitted references. The six face identities each allocate two pointer fields. The body allocates one pointer field each for recipe, stamp, atom ID, last modifier, and lightweight identity. The projection counts those actual allocations separately from its transmitted deletion references. Initial and activation marks use the body-free history. |
| Archive-side objects | Manager allocation at `0x4bcf0cb2–0x4bcf0cf8` advances the manager ID and registers the new atom. The prepared atom shares the body tag with `BODY_MATCH` and owns the modifying and base feature IDs. `moAtom_c::getDisplayMode` at `0x4bcf5a06` reads `f19c`, seeded with six at `0x4bcedf89` and `0x4bcee139`. The prepared model and extrusion mark records share the activation and selected kernel mark IDs respectively. The mark serializer at `0x4bb1a840` writes those IDs. |

The generated transmit indices, body-local node identifiers and face and body
tags occupy separate domains. The research projection allocates dense
identifiers in its own construction order and builds reciprocal links. The
native writer has additional allocation and filtering traversal that may
produce gaps or reorder the same records. Equivalent traversal and rollback
behavior in the target reader remain unmeasured.

## Attribute definition sources

| Definition | Constructor evidence |
| --- | --- |
| `BODY_MATCH`, `SWEntUnchanged` | `0x32f9f0ae–0x32f9f0b5` registers body integer with propagation. `0x32f9c330–0x32f9c374` registers the propagating face/edge integer. |
| `DOWNSTREAM_FACE_ID` | `0x32fa090a–0x32fa0911` registers three ordinary integer fields for a face. The established ordinary local value is in field zero. |
| `LAST_BODY_MODIFYING_FEATURE_ID`, `BODY_IN_LIGHTWEIGHT_PERM` | `0x32f9eee9–0x32f9eef0` and `0x32f9f241–0x32f9f248` call the ordinary body pointer/integer constructor at `0x32f9c820`. |
| `BODY_RECIPE_2001`, `ATOM_ID_2001` | `0x32fa069e–0x32fa06ac` and `0x32f9ed43–0x32f9ed51` select the current definitions through `0x32f9d010`. The inner calls at `0x32f9d04e` and `0x32f9d075` use ordinary body pointer/integer fields. |
| `ENT_TIME_STAMP_2001` | `0x32f9e758–0x32f9e799` constructs the same ordinary body field shapes directly. |
| `FACE_ID_2001` | `0x32f9dd60–0x32f9dd90` builds two pointer fields followed by two integer fields, with the persistent-ID actions. |
| `SWIMPLICITBODYNAME_ID_U` | `0x32f9f6bf–0x32f9f6e5` selects the Unicode string definition, whose owner class vector is installed at `0x32f9cba0` and whose two Unicode fields occur at `0x32f9cbb2–0x32f9cbb6`. |
| `SDL/TYSA_COLOUR_2`, `SDL/TYSA_TRANSLUCENCY_2`, `SDL/TYSA_DENSITY` | Kernel built-in registrations use IDs 8040, 8041 and 8004 at `0x1806d7d45–0x1806d7d4e`, `0x1806d83c4–0x1806d83cd`, and `0x1806d7f73–0x1806d7f7c`. Colour and translucency use real fields and instance/assembly/body owners. Density uses a real and an optional character field on the body. The supplied RGB bytes project as channel values divided by 255. Translucency and positive density come from the input. |

Addresses use the preferred PE bases. The exact module SHA-256 identities
are `2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969`
for `pskernel.dll`,
`96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce`
for `sldgciParau.dll`,
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`
for `sldmodu.dll`, and
`77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594`
for `sldgcu.dll`. The pinned kernel and bridge are the same targets as
the [effective schema analysis](PopulatedPrismPartition2026.md).

## Reproduction and evidence

```sh
PYTHONPATH=src:re/tooling/sw2026:re/tooling/sw2026/serial:. \
  python3.14 -m para.rectangle.CheckProjection --disclosed
```

The process builds both neutral parts before comparing any disclosed source.
The file-open guard surrounds model-to-partition construction, emission,
wire readback, and a second emission. The optional `--disclosed` pass checks
all six populated sources already declared in the [grammar ledger](PopulatedPrismPartition2026.md#reproduction).
It supplies no data to the projection. The
[sanitized receipt](../measurements/2026/GeneratedRectanglePartition02.json)
contains analytic dimensions, stream and payload digests, and allocation
counts. It contains no native or generated payload.

| Generated model | Volume (mm³) | Area (mm²) | Active records | Runtime new nodes | Rollback deletions |
| --- | ---: | ---: | ---: | ---: | ---: |
| Translated rectangle with two driving dimensions | 7605.1171875 | 2471.375 | 173 | 165 | 148 |
| Translated rectangle with cyclic sketch start and explicit density | 18049.1015625 | 4166.375 | 177 | 167 | 150 |

The two fresh active graphs are link-complete and byte-identical to their
decoded and re-encoded representations. Both match independent bounds,
volume, area, centroid, vertex incidence and outward winding. The standalone
discovery pair adds the archive side of the shared identity.

## Standalone archive attachment

| Record or relationship | Construction and 2026 authority |
| --- | --- |
| Atom-manager registration and version | `0x4bcf0cb2–0x4bcf0cf8` advances the model atom ID and registers the new atom. On the population/update path, `0x4bcf0a0f–0x4bcf0a25` writes the active archive version if manager `fa8` is unset. Its imports identify `moVersionManager_c::get` and `getCurrentFileVerion`. The constructor at `0x4bced920` starts the count and version at zero. |
| Blanking snapshot | `sldprtu` `0x3339d3a8–0x3339d47c` gets current bodies from the actual atom manager, clears the prior map for a new snapshot, resolves each body to its atom by `gcBody_w::getAtomId` and `moAtomManager_c::getAtomFromId`, and records `moAtom_c::isBlanked(nullptr)` under that same atom pointer. The null-context accessor at `sldmodu` `0x4bcf8e2e` branches to the read of atom `f170` at `0x4bcf910c`. The snapshot sets `moPart.f1010` to one at `0x3339d474`. Archive save at `0x4c2365f7–0x4c23668d` writes initialization, count, atom object and normalized boolean. Load at `0x4c2366ee–0x4c23675c` restores the map with archive object identity. |
| Part and feature marks | `0x4c036910` sets the model mark pointer and `0x4c23658e` stores it in the ordinary model stream. `moAtomFeature_c::saveBodyTagForRollback` at `0x4b7159cc–0x4b715a0a` selects the feature mark. Its optional extra-atom updates at `0x4b715940–0x4b7159bf` require `f538`. The ordinary generated boss has no extra atom and retains the three constructor values seeded at `0x4b6fef47`, `0x4b6fef4e` and `0x4b6fef9c`. |
| Ordinary boss regeneration state | `moExtrusion_c` vtable slot `0x2090` at `0x4cf3f518` dispatches to `0x4bad58d0`. Normal geometry regeneration reaches `0x4bad5b0a`. The non-null result path writes status `3` at `0x4bad5b24`. The constructor initializes zero at `0x4b6ff05e`. Save at `0x4bb0b4b2` serializes the status. The ordinary load at `0x4bb0b878–0x4bb0b890` recognizes the range 0–3. |
| Feature and model update state | The model header counter advances separately from the body counter. `moFeature_c::postUpdate` calls the current-header stamp getter at `0x4c1ce74b` and the feature setter at `0x4c1ce756`. The setter at `0x4bb4a4b0` writes `f29c` and samples `GetSystemTimeAsFileTime` for `f2a0/f2a4` on the non-frozen model branch. The standalone recipe names each completed feature event and its clock. The selected events add one geometry increment per published notification, modeled from the direct increment at `0x4b55f0ed` and the tracker increment at `0x4b56457e`. The live configuration and `CMgrHdr2` use the active update and geometry stamps. Generated `Header2` and ModelHeader both have an owner in this modeled save context. |

The pinned UI module `sldprtu.dll` has SHA-256
`54c079c8bbbe13582d062787c07a13f91d91f2d7972715e5d647bb8a1802d494`.
The four disclosed standalone controls have an initialized empty snapshot.
The two disclosed synchronized children retain one visible-body entry. Its
key aliases the existing manager atom. The experiment chooses the explicit
captured state. All six sources use the modeled ordinary boss status and
the same feature- and model-mark attachment rules. [Blanking snapshot gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/ModelBlankingSnapshotUsesAtomIdentity.md).

```sh
PYTHONPATH=src:re/tooling/sw2026:re/tooling/sw2026/serial:. \
  python3.14 -m para.rectangle.CheckAttachment /absolute/empty-output \
  'C:\Users\Public\Documents\KitOracle\RectangleCacheConstruction-816b\Active\PartitionProbeChild.SLDPRT'
```

The paired probe generates the same 23.25 × 14.5 × 8.75 mm rectangle with
and without the modeled attachment. The entire in-memory write and readback,
including the ordinary part, compound container and map checks, executes
under a file-open guard. The partition adds one body with six attributed
faces and two distinct owning archive marks. The manager and snapshot share
one atom object. The configuration archive map grows from 83 to 87 and
the resolved stream starts at the new map count. Configuration, feature,
manager and header graphs re-emit byte-for-byte. Independently calculated
volume is 2949.84375 mm³, area is 1334.875 mm², and centroid is
`(14.25, -5.5, 4.375)` mm. [Offline attachment receipt](../measurements/2026/GeneratedRectangleAttachment03.json).

The [standalone oracle](../../tooling/sw2026/InspectRectanglePartitionOpen.py)
opens each variant at the same encoded Windows path in a fresh process,
bracketed by the previously measured healthy L1 file. It records native
warnings, rebuild state, extrusion ownership, volume, area and centroid
before and after an explicit rebuild. The copy's digest must survive the
process. This first probe changes the complete attachment together and
localizes any failure to that intervention as a whole. The candidate uses
fresh-part constructor flags outside the modeled update and snapshot paths.
Native kernel acceptance, ordering and rollback behavior, dimension edits,
and synchronized saves remain open.

## Standalone native comparison

Four fresh SOLIDWORKS 2026 SP05.2 processes measured both generated
variants at the encoded path and the L1 control on each side. Both
controls passed and all inputs stayed immutable. The variant without the
partition opened with zero warnings and one solid before and after
explicit rebuild. The attached variant opened with warning 32 and zero
bodies. Explicit rebuild then exposed one solid whose six faces reported
the generated extrusion as owner. Both rebuilt solids matched the
independent volume, area and centre exactly. The attachment still fails
the initial native cache gate. This comparison did not edit or resave the
part. [Matched native receipt](../measurements/2026/GeneratedRectangleAttachmentNative04.json)

The existing SDK B-rep decoder also accepts the generated cache and
validates one solid, six faces and the expected absolute geometry. Its loop
orientation is inward for this cache and for the L1, A13 and A14 vendor-saved
controls. All four typed walks find outward loops. The SDK pairs `HALFEDGE`
backward-link traversal with treating each fin's terminal vertex as its
start, preserving closure and reversing the signed volume. [SDK fin orientation gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/CurrentParasolidFinsStoreTerminalVertices.md).
