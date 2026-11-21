# Drawing profile-display retention in SOLIDWORKS 2026

Both disclosed original Definition streams now pass complete typed read/store with identical bytes, maps and object identities. Portable display semantics and the original complete-source writer remain unqualified. The public adapter still offers explicit layout inspection and rejects strict drawing reads.

Task `B04-SW2026-DRAWING-PROFILE-DISPLAY`, owner PR #121 drawing-reader lane, delivery PR #121. Dependencies are the [rendering-state boundary](DrawingViewRendering2026.md), [component-profile archive](DrawingComponentProfileArchive2026.md), shared body graph, native object maps and current Definition grammar. The scoped exit is revision-bound native profile-display retention, unchanged prior profiles and complete malformed-state rejection. This exit does not complete the CAD success criteria.

See the [native identities and field proof](DrawingProfileDisplayRetention2026.json) and [actual sanitized receipt](../measurements/2026/DrawingProfileDisplayRead01.json). No vendor binary or decompiled instruction listing is included.

## Actual rejection owner

The preceding rendering candidate preserved `blank drawing Definition excludes sheet annotations` for both original sources. The independently executed [detail-folder observer](../../tooling/sw2026/InspectDrawingDetailFolders.py) followed actual graph aliases and all 34 declared collections in each concrete `moDetailFolder_c`.

Each source has two such folders. The actual active sheet's `f390` folder has all 34 collections empty. The actual view's `f630` folder has one nonempty collection: `f8f8`, containing one concrete schema-one `moDisplayProfileFeature_c`. Native `getProfileFeatures` returns precisely this member. The generic empty-folder guard was therefore rejecting a profile-display record while reporting sheet annotations. Actual notes, dimensions and the other collection families remain excluded.

The source observer records folder indices 133 and 138, view index 136, display index 141 and component-profile reference index 143. These indices identify the measured inputs only. SDK selection follows actual nodes and references, with no numerical-index lookup or captured row.

## Exact native binding

All addresses are from original `sldmodu.dll`, version 34.5.2.604, 46,536,280 bytes, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`.

`moDetailFolder_c` constructor `[0x4ba2bda0,0x4ba2c1ae)` installs vtable `0x4cef4a00`. Its serializer slot `+0x28` reaches `[0x4ba4a520,0x4ba4ad31)`, 2,065 bytes, SHA-256 `61fcfccf508015bf754e7b663c1b80c60280c07d2841c9254e6a5131927a2e13`. The actual current `SerializeMap2026.json` agrees. The older `SerializeMap.json` entry was not used as current-build evidence.

The exported `getProfileFeatures` at `[0x4b288ab0,0x4b288ab8)` returns the address of `folder+0x8f8`. From effective version `0x459`, the serializer calls this embedded `suObList` through its actual slot `+0x28` at `0x4ba4a881`.

The concrete display vtable is `0x4d039e40`, serializer slot `+0x28 -> 0x4ba4dea0`. Direct RTTI gives `moDisplayProfileFeature_c -> moDisplayFeature_c -> moDisplayObject_c -> su_CObject -> CObject`. The display serializer calls the shared object serializer directly; the intermediate feature serializer contributes that same base and no additional own fields.

| Function | Complete range | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Profile-display serializer | `[0x4ba4dea0,0x4ba4e1b9)` | 793 | `0be8f85a39a463a5d1f3c454617c2b5fc9367bd206832f2a8e7dd40afb8faeed` |
| Shared display-object serializer | `[0x4ba4d3c0,0x4ba4de98)` | 2776 | `536c87e8149609edafca6c1f173d23f0fe9df700acfd02b9a157d0ce530f470d` |
| Runtime profile-display factory | `[0x4ba45390,0x4ba453be)` | 46 | `ebc9355b8a76a1ae8acddb0d2e258eeb1cc97df883d77405026d60393b82f8e8` |
| Default profile-display constructor | `[0x4be74e60,0x4be74f02)` | 162 | `e40e8f4e9dbdd3673cc8b5355367ff7265942e50167168e06ef9e1a501de3449` |

The machine record includes twelve complete function spans, native accessor fingerprints, RTTI and read/store sites. Bounds use the exact PE exception directory with full chained-fragment closure; the five small leaf accessors have independently checked complete return bounds. Static inspection does not imply native execution.

## Selected field rules

| Field | Actual native role and encoding | Selected admission | Confidence |
| --- | --- | --- | --- |
| Folder `f8f8` | `getProfileFeatures`, embedded ordered object list | Actual view-owned folder; concrete profile-display objects; exact counts; unique actual display identities | Confirmed owner and grammar |
| Display `f30` | `getOwner` at `0x4b289d30`, object reference | Same actual detail folder | Confirmed accessor and measured alias |
| Display `f40` | `getDrView` at `0x4b285fe0`, object reference | Same actual view; its `f630` aliases that folder | Confirmed accessor and measured alias |
| Display `f48` | Component-feature reference used by actual virtual `+0x310` resolver `0x4be75480` | Concrete current `moCompProfile_c`, retained as its actual object | Confirmed native role; child-profile semantic join partial |
| Display `f1e0` / `n1e0` | Native integer set: signed 32-bit count and signed 32-bit keys, loaded from version `0x105f` | Empty only; explicit count must agree | Confirmed selected empty boundary; populated meaning excluded |
| Display `f200` | Signed 32-bit flag word, loaded from version `0x371a` | Exact integer 0 or 1; other bits rejected | Bit 0 confirmed; other bits excluded |
| Auxiliary `f68`, `fb0`, `linked`, `ff8` | Existing shared display-object lists and linked/optional state | Empty lists with consistent counts, exact zero linked state and explicit null optional field | Selected ordinary inherited branch only |

`getCanHideSuppressedSketch` at `[0x4be75470,0x4be7547a)` returns `f200 & 1`. Its setter `[0x4be75520,0x4be7553f)` sets bit 0 for nonzero input and clears it for zero input while preserving other bits. The runtime factory reaches the default constructor, which initializes the native integer sets empty and sets `f200` to 1 at `0x4be74eed`. These are native facts; the reader supplies no input default from either the constructor or a saved source.

The selected reader requires ordinary archive version 19000, concrete schema-one descriptors, actual reference identity, empty auxiliary/linked state and the known suppression bit. Existing common-display exclusion of alternate context mask `0x10000001` remains in force. Raw wire values and their field order are unchanged; native runtime fixups are not replayed during raw serialization.

## SDK and public boundaries

[ReadProfileSet](../../../src/convert/adapters/solidworks/Drawing/Definition/Profiles/ReadProfileSet.py) validates the actual view-owned collection. [ReadProfileItem](../../../src/convert/adapters/solidworks/Drawing/Definition/Profiles/ReadProfileItem.py) binds folder/view/component-profile aliases. [CanHideProfile](../../../src/convert/adapters/solidworks/Drawing/Definition/Profiles/CanHideProfile.py) validates the selected auxiliary state and projects only the proved bit.

`NamedRead.ProfileDisplays` and `FrontRead.ProfileDisplays` expose each actual detail folder and retained display objects. Nonempty collections add `drawing.profile_displays` to `Unprojected`, alongside `drawing.detailing_edges` and `drawing.occurrence_colours`. The SDK does not resolve the component-profile reference to portable child sketch geometry. No native values, names or indices are copied into a fresh constructor.

Only view-owned `f8f8` leaves the all-empty folder profile. The other 33 collection guards and annotation-bucket guard remain. No class schema or wire layout is added, and no public adapter hook or original drawing constructor changes.

The normal internal `ReadNamedDef` / `WriteNamedDef` boundary now completes both disclosed Definition streams. The public `ReadDrawing` path remains separate: `strict=False` uses the existing `ReadConcept` prefix plus layout projection and retains its `slddrw.layout_inspection` diagnostic; `strict=True` still rejects. Full Definition retention does not turn that partial portable projection into a lossless drawing read.

## Exact-source verification

Root ran candidate manifest `66b81576ae9424372bb89f70369b90f28727e3cd6fa39e8070f5270bb5ff4a33`, binding 4,389 source files and 13 SDK deltas. All 43 prior workers passed. Both exact originals pass complete internal normal Definition read/store byte, map and actual object-identity comparison, as well as an independent raw comparison with zero tails.

The [full-process observer](../../tooling/sw2026/InspectProfileDisplayRead.py) also passed 86 malformed full-store cases. These include counts, missing and unknown fields, external-class placeholders, wrong schemas, duplicate display objects, foreign aliases, unknown suppression bits, nonempty sets/links, sheet-owned profile collections, note collections and annotation buckets. Every malformed case returns no successful output.

Four authored flag variants, two per original, run complete normal write/read/store with both native suppression-bit states and preserved aliases. These are SDK process proofs, not native measurements. The unchanged generated Front control retains empty display collections and exact bytes. Source and input custody are checked before and after execution.

Raw process report SHA-256 is `c029e5b50efed8b5c8e2467c4255af09225de02f97f36f7fe10938f596db5d70`. Prior-cohort report is `89ce1c354b7211b544f7f7278a54f8c27ee8fd287771d2c4ecf26a3da2f7a56b`. The separate original normal-codec report is `cb30a5a446f9f5e07b07237e216c6a24d0b94e1b707e653ef5bfdb139cf017b4`. The public-route probe is `766a8cad92c29bc930b8867efb375f21f8f6540b234f04c540a931f4b32bd15b` and retains both strict rejections.

## Remaining conversion and writer work

The exact external component-profile to portable child-sketch join, native detailing-edge join and occurrence-colour appearance join remain explicit. Other profile flag bits, populated integer sets, linked displays and actual annotation families remain unsupported.

The existing fresh linked candidate route is `MakeLinkedFile` from neutral `DrawingData` plus an actual SDK `PartCandidate`. Its qualified geometry subset remains separate from this retained source graph. The original frozen writer does not construct these profile-display records, and its original child folder/name-link differences remain recorded in [the failed original admission](SdkOriginalDrawingAdmission2026.md). Any new generative family needs independent disclosed controls and a new writer/method lock before a new held-out evaluation.

Complete source semantics, public strict read, native conversion acceptance, full original writer equivalence and original held-out acceptance remain false. The mandatory stopping conditions are “The first is success under every criterion on this page.” and “The second is the end of the available context.”
