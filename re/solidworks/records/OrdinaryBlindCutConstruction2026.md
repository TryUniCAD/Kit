# Native SOLIDWORKS 2026 blind-cut objects

The three disclosed [blind-cut sources](../v2026/heldout/OrdinaryBlindCutSourceLock.json) were independently authored as a rectangular boss followed by a blind circular pocket. The source tool qualified both features through native rebuild and a driving depth edit. The linked reader reached the following graph on all three source hashes. The two held-out payloads and their detailed observations remain sealed.

`moICE_c` and `moExtrusion_c` share serializer `0x4bb11640` in `sldmodu.dll`, whose pinned SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Slot 5 of the `moICE_c` vtable at `0x4cf4e530` verifies the shared dispatch. The `moICE_c` constructor at `0x4bad3f00` calls the typed extrusion constructor at `0x4bad3f0d`, installs its own vtables, and initializes `f810` to zero at `0x4bad3f2b`. The half-open constructor span `[0x4bad3f00,0x4bad3f3e)` has SHA-256 `1aa7be1814f6879a2d9e375f018e0f58e824a515434a06bec95878becccb701a`. The extrusion constructor sets its initial `f810` to −1 at `0x4bad3b3c`. [Bound 2026 class map](../../data/Serialization/SerializeMap2026.json)

| Owner | Verified on disclosed saves | Construction status |
| --- | --- | --- |
| ResolvedFeatures | User history is profile, `moExtrusion_c`, second profile, `moICE_c`. Persistent IDs are 26, 32, 33 and 40 in this ladder. The linked stream inherits the configuration map. | Derive history order and allocate each graph's required IDs. Observed map lengths are topology measurements. |
| `moICE_c.f810` | All three cut records store `1`. Side-by-side boss records store `−1`. | The typed cut constructor starts at zero. The concrete cut command and its dialog apply path set operation `1`. |
| `moICE_c.f818` | One active reversed blind end (`f08=1`, `f0c=0`, `f8c=1`). `f18` owns a `moDisplayDistanceDim_c` and there is no reverse distance or draft display. | Depth and reversal are authored inputs. Derive the active display and its linked driving parameter from the selected sketch and depth. |
| `moAtomFeature_c.f530` | A one-item array refers to the same `moAtom_c` in the inherited Config-0 map. | Derive the cut's affected body identity from the prior solid history and retain its live reference. |
| `moAtomFeature_c.f548` | A one-item array holds a `moCompSolidBody_c`. | The merge routine retains a wrapper with the actual surviving atom ID. Face and base-atom lineage still require separate construction evidence. |
| `moAtomFeature_c.f4c0` | Present embedded `moBodyChooser_c` with one `moPerBodyChooserData_c` and `f68` pointing back to the actual `moICE_c`. | The body chooser snapshots its one-row primary owner. The constructor pointers can start null. The cold reload path still needs evidence. |
| `moAtomFeature_c.f28` | `0x400201ca` in each cut versus `0x40000140` in each boss. | Compose the native cut flags with the inherited extrusion and base node flags. |
| `moEndSpec_c.f158` | Values differ substantially across the depth ladder. | The capped mid-plane surface extrusion flag initializes to zero and is inactive for the ordinary blind solid cut. |
| `swXmlContents/KeyWords` | The cut is an `Extrusion` row with no `Type`. `DissectableChildren` points to the semantic cut sketch ID. The D1 text is the authored depth in millimetres. | Derive rows, IDs, and displayed length using the actual history and presentation units. |

The private projection of these three source hashes has SHA-256 `6dd765bcf55306639a84bf303b1a2f8426e4af0434d1125b3a0a20326e26a396`. All 45 exercised linked streams re-emit byte for byte. The strict check accepts 42 streams, with two provisional owners in each optional visual-state stream. This evidence establishes the archived cut dependencies. Generated cuts require a separate construction model and native qualification.

`moAtomFeature_c::setFeatureScope` at `0x4b2924f0` writes `f544`. Both the disclosed boss and cut store `f544 = 1`. `setAutoSelect` at `0x4b291060` writes the separate runtime member `f558`. These saves have no standalone `f558` field in the reached wire layout. The `moBodyChooser_c` constructor at `0x4b75d590` constructs its empty array at `+0x48` and stores the supplied owner at `+0x68`. `setBodyChooserNew` writes `moAtomFeature_c +0x4a8`, which has its own serialized presence flag.

## Native creation and body selection

The exact installed `sldbasegeomu.dll` has SHA-256
`206430acc09197ae9416446d56156f79fdb3aae9d615f32b771314a92a0ad36a`.
Its `uiCutCmd_c` table `0x329bf2f0` dispatches slot `+0xa38` to
`0x3294d070`. The modern branch requires the Instant3D manager, project
12794 enabled and document predicate `+0x1250` true. It constructs
`moICE_c` and writes `f810 = 1` at `0x3294d117`. Independent flag
calls at `0x3294d145`, `0x3294d153`, `0x3294d161` and `0x3294d16f`
add `0x8 | 0x2 | 0x80 | 0x20000` to the extrusion's `0x40 | 0x100`.
The extra `0x4` is conditional on command data `+0x140` being nonzero.
The ordinary cut source reaches the zero value for that field. The
bounded Hopper evidence is
`ev_43fdd77e6763301b80d5ebd8e6ff8a3761da0dfdb25d26a4018280e902cee0f9`.

`GetCreateSolidFrmCappedMidPlaneSurfExt` at `0x4b2c61e0` and its setter
at `0x4b2c67b0` own `f158`. The typed and copy constructors clear the
signed word at `0x4bad3693` and `0x4bad2fbb`. The surface update reads
it only with an end type of six and no face-extrude operation. Ordinary
blind solid cut construction uses zero. The version-19000 serializer
stores the signed field directly.

The source uses `UseFeatScope = True` and `UseAutoSelect = True`, with
only the sketch selected. The `slduiu` argument loader at `0x49264980`
enumerates selected solid bodies only with manual scope. The dialog apply
method at `0x493e5a80` sets the two separate scope values, clears
`f548` at `0x493e60f2` and inserts wrappers immediately only if the
manual selection array is present.

The extrusion update at `0x4bad58d0` calls
`moAtomFeature_c::mergeMultipleBodies` at `0x4bad652c`. The automatic
scope lane gathers actual candidate bodies. It constructs each
`moCompSolidBody_c` wrapper from the body-manager atom ID and the model's
self component at `0x4b70d18a`. A successful one-result merge collects
consumed atom pointers into `f530`. It moves a wrapper with the retained
body's positive ID into `f548` at `0x4b70e5b4` and clears the runtime auto
flag at `0x4b70e611`. The wrapper can derive face and base-atom lineage
from the live target. Atom IDs are assigned by the atom manager and
remain distinct from feature IDs and archive slots.

`chooseBodies` at `0x4b700970` calls the separate primary snapshot helper
`0x4b713150`. The helper creates a fresh `moBodyChooser_c`, copies a
one-row primary chooser and binds the same feature as owner. It installs
the snapshot at `0x4b71337e`. The helper has its own verified unwind
extent `[0x4b713150,0x4b713692)`. The constructor has both chooser
pointers and both body arrays absent. The direct ICE loading path still
needs a cause for runtime auto-scope activation before resolving a cold
part with no selected wrappers.

## Linked SDK archive

The version-19000 linked SDK codec verifies the shared `moICE_c` and
`moExtrusion_c` serializer at `0x4bb11640` and their matching
ResolvedFeatures callbacks at vtable offsets `0x3e8`, `0x3f8`, `0x4b8`
and `0x4c0`. Its schema-one entries preserve the two actual class tags.

The affected-body wrapper reads the current `moCompSolidBody_c` layout.
Its shared component-reference base is followed by the nullable face at
`ff0`, a signed element count and that many signed `f110` elements when
the count is positive, then signed `f108`, `f104` and `f100` words.
The historical members are gated at `0x49b`, `0x865`, `0x94e` and
`0x1040` respectively. Archive version 19000 reaches each group.

The two surface-identifier classes use `0x4bba41f0` through slot
`0x28` of their concrete vtables. Both preserve the common reference
base and the ordered signed `f38`, `f3c`, `f40` tail. The concrete
tail implementations are `0x4bbab920` for `moEndFace3IntSurfIdRep_c`
and `0x4bbab5b0` for `moFromSktEnt3IntSurfIdRep_c`.

Four fresh SDK processes re-emit Config-0 and ResolvedFeatures with
complete field coverage and exact byte identity. The three disclosed vendor
saves each advance map counters from 110 to 332 and contain one affected-body
wrapper and two of each surface identifier. The independently generated
discovery part advances from 82 to 231 with the modeled cut and empty saved
body lists. The archive receipt binds all four input hashes and the observed
source files. [SDK round-trip receipt](../measurements/2026/SdkOrdinaryBlindCutArchive01.json)
