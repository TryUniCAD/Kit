# SDK fresh blank drawing model construction

The SDK now constructs the complete owning model graph for the bounded ordinary blank drawing from explicit neutral inputs. This includes styles, document units, canonical views, real self/relation ownership, presentation folders, the measured sheet/support family and fresh empty managers. Four blank and two linked designs match every independently generated logical stream. UI and metadata composition remain in research; public writing and new native acceptance remain disabled.

Task: **B04-SW2026-DRAWPROPS / SDK drawing model**. Owner: `/root/configuration_header`. Delivery: PR #121, with root owning Git and the vendor VM. Dependencies are shared model/node/style/unit/view construction, the [measured sheet factory](DrawingSheetConstruction2026.md) and complete blank/linked Definition codecs. The exit condition is fresh model construction, exact graph/byte checks, no runtime input reads and the existing part-root regression after the narrow common-owner extension. Full neutral drawing export and the CAD acceptance criteria remain unfinished.

## Construction contract

[MakeDrawRoot](../../../src/convert/adapters/solidworks/Drawing/Construction/Model/MakeDrawRoot.py) accepts `DrawBuild`. The input supplies the model name, sheet and support names, all six folder names, semantic style and unit settings, qualified target, creation time, independent UUID4 and dimension-text-link preference. `DrawRootGraph` returns the actual model, complete `SheetGraph` and persistent allocator.

The factory constructs its own parent model. It does not receive, clone or inspect an existing drawing. Shared `MakeDetails`, `MakeUnitTable` and `MakeStdViews` create its presentation owners. Shared model arrays/seeds create all empty collections and constructor state. The drawing has no analysis-unit or model-visual object. Its self component and relation manager point to the real newly allocated model.

The only existing production file changed is `Archive/Construction/Model/RequireModel.py`. Root authorized adding concrete schema-one `moDrawing_c` to the already qualified part/assembly owner set so `MakeSelfComp` and `MakeRelGraph` can serve their source-proved drawing constructors. External descriptors, schema two and the abstract model base remain rejected. Part-only system-folder admission is unchanged.

## Field and source authority

All model addresses below refer to `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The existing findings retain the other exact module identities. This tranche reuses those source facts and opens no binary, saved native document, held-out or vendor runtime.

| Owner | Classification and construction rule | Source and confidence |
| --- | --- | --- |
| Root node/concept | Authored name, actual model ID from a fresh allocator, source-defined node state and real ordered children | **Confirmed** [model constructors and ID namespaces](ModelConstruction2026.md), node `0x4c03c250` and concept constructors `0x4bda5770/0x4bda5800` |
| Common model arrays/seeds | Shared constructor clears, empty rows, explicit display/cache bookkeeping and ten generated named views | **Confirmed** [shared model construction](ModelConstruction2026.md), [part root boundary](SdkPartRootConstruction2026.md) and [canonical views](StandardViewsConstruction2026.md) |
| Self/relation managers | Actual newly allocated drawing owner, separate empty relation containers and three distinct concrete auxiliary lists | **Confirmed** model constructor `0x4c00d8f0`, self assignment `0x4c00e85a`, relation allocation `0x4c00e7a2`, list allocations `0x4c00de68/0x4c00decc/0x4c00defa`; [drawing root facts](GeneratedBlankDrawing2026.md) |
| Drawing-specific model state | `f78` and analysis units absent, completed model state and drawing `fd50=0` | **Confirmed** drawing predicate `0x4c22ee5d` and retained [root construction](../../tooling/sw2026/builders/DrawingRoot.py) |
| Styles and units | Generated from explicit semantic input through the shared factories, with the qualified effective detail standard and matching sheet/model length units | **Confirmed** shared [style](StyleConstruction2026.md), [model](ModelConstruction2026.md) and [sheet](DrawingSheetConstruction2026.md) rules |
| Cabinet and persistent folders | Cabinet, binder and comments register before the sheet; ink registers afterward. Generic feature provenance/appearance and folder state follow their actual constructors | **Confirmed** [drawing folders](GeneratedBlankDrawing2026.md#model-and-definition-owners), insertion/allocation paths `0x4beb52b0`, `0x4beb53b0`, `0x4c0162e0` and shared feature construction |
| Transient folders | Block and review-markup folders keep unregistered ID `-1`; names and FILETIME come from explicit input | **Confirmed** same drawing construction and `moFolder_c` base at `0x4beae110` |
| Sheet/support registration | The measured factory creates four actual objects from the current allocation boundary. Bind those same objects into the surrounding allocator, preserving the pre-registration plane handle | **Confirmed** [sheet lifecycle](DrawingSheetConstruction2026.md), actual allocation/alias checks and exact stream proof |
| Layer/mask/property managers | Empty owners, no active layer, unset layer index, zero-length mask and actual drawing backlinks | **Confirmed** [manager table](DrawingEmptyManagers2026.md), layer `0x4bbe6fc0`, mask `0x4bbe7011..0x4bbe705a`, property manager `0x4c96ba20` |
| Block manager | Fresh explicit UUID4 in Windows byte order, empty map, actual manager backlink and unregistered unnamed feature state | **Confirmed** `0x4c926c50`, map binding `0x4c926edd`, GUID allocation `0x4c926efc..0x4c926f03`; [GUID gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingBlockManagerAllocatesGuid.md) |
| Active sheet and drawing tail | Actual sheet pointer, mode 1, source bit 8 plus authored dimension-link bit 0, empty link/preview/name maps and first XML index 1 | **Confirmed** drawing `0x4c96b5fc`, `0x4c96b602/0x4c96b8d8`, setter `0x4c97c160`, [tail fields](DrawingEmptyManagers2026.md) |

All fields come from shared documented constructor vocabulary, explicit inputs or derived collections/identities. No saved row, field program, template, copied span or runtime CAD dependency is added.

## Allocation and ownership

The fresh model receives ID 0. Cabinet, binder and comments consume the next three registrations. The measured sheet factory receives that actual next ID and constructs sheet, plane, profile and detail folder. `BindSheetIdsMut` registers those same objects with the common allocator; it does not advance a numeric counter over missing nodes. Ink consumes the final registration. Block/review folders remain transient.

The final allocator value is 9. Serialized root children are comments, blocks, binder, cabinet, ink, reviews and sheet, with IDs `[3,-1,2,1,8,-1,4]`. This order differs from allocation lifetime and follows the source insertion path. The active-sheet field aliases that actual last child. Plane/profile aliases and exclusive component copies remain the measured sheet factory's own objects.

The block manager is an unnamed, unregistered feature. Generic initialization receives the authored block-folder name, then removes the unreachable name owner before any archive write. That temporary node consumes no persistent ID or archive slot. No installed localized name or saved string supplies its output.

## Complete-process proof

[DrawingModelProcess.py](../../tooling/sw2026/DrawingModelProcess.py) creates its candidate model with SDK code alone. The [compatibility projection](../../tooling/sw2026/DrawingModelBridge.py) preserves live graph identity while the existing research UI/metadata composer supplies the remaining owners from the same neutral request. It reads no saved payload. Only the independent comparison invokes the old model factory.

The candidate must match complete Definition bytes, final map, every surrounding logical stream, full SDK read/re-emission and public drawing projection. Two additional jobs attach an ordinary generated child and view to the new root, then verify both external references, support pairs and real child identity through complete linked readback. Construction-time relation ownership remains distinct from the nonpersisted runtime member described in the [owner gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingRuntimeOwnersFollowContainment.md).

| New neutral design | Scope | Definition bytes | Map index | Variation |
| --- | --- | ---: | ---: | --- |
| `ModelAlpha` | Blank | 23,953 | 131 | All new folder/support names, 9:14 scale and clock |
| `ModelBeta` | Blank | 24,645 | 131 | Long Unicode property text and independent creation epoch |
| `ModelGamma` | Blank | 23,953 | 131 | Imperial units, 21:5 scale and dimension text linking disabled |
| `ModelDelta` | Blank | 25,572 | 131 | ISO UI vocabulary and authored alternative font |
| `ModelLinkedAlpha` | Linked Front | 29,312 | 172 | Independent generated rectangular child |
| `ModelLinkedBeta` | Linked Front | 29,256 | 172 | Different child dimensions, identity and support names |

Each design passes two fresh processes with identical stdout. Eighteen additional complete jobs reject invalid names/contracts, paper/scale/unit choices, time, block identity, preference type, styles and target. The original part-root regression also passes its two build/prepare pairs in four fresh processes, with 23,608/24,040-byte configurations, real reserved-ID behavior, exact read/re-emission and all original malformed-input assertions.

All 34 processes pass. The drawing workers and both part phases retain zero runtime input reads. All 22 named-codec predecessor paths remain unchanged. The 26-file code/test source manifest SHA-256 is `bc4845f524651186209af23919d4df598f7c523e59d33bb2957a99fce797ecf9`; the private process proof SHA-256 is `315db6d5c0555703628183926239fc0aa0c9a3db54011146e8c8b0e91c8ab058`. The [sanitized receipt](../measurements/2026/SdkDrawingModel01.json) carries exact source, neutral request and generated artifact hashes.

Steering, Black, Mypy and Pyright pass for all 23 production/test modules. The donor scan is recorded separately in the receipt. The existing Pyright configuration messages stay visible. No public writer is enabled. UI/header/history/property/container construction and revision-bound native/held-out acceptance remain unfinished dependencies for complete SDK export.
