# Empty drawing sheet support objects in SOLIDWORKS 2026

This record covers one unformatted ANSI A landscape sheet with no annotation or format geometry. The vendor evidence is the pinned `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, image base `0x4b140000`, from SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. Three disclosed source controls independently verify the archive shapes and the measured transforms. They share an installation template. The constructor rules come from the pinned binary. [Source lock](../v2026/heldout/DrawingSourceLock01.json) · [Drawing Definition grammar](DrawingDefinitionGrammar2026.md)

## Construction and identities

`moDrSheet` constructor `0x4c9c6970` calls the owner-taking `moModelFeature_c` constructor and resets the sheet at `0x4c9d0650`. The reset first adds the sheet to its drawing at `0x4c9d07d5`. It constructs the detail folder and then an absolute sketch plane. `moRefPlane_c::createDefaultSketchRefPlane` at `0x4c2d3fe0` constructs the geometry at the origin with a +Z normal. It leaves the new plane's persistent ID unassigned. The reset takes the owning drawing's `moModel_c::getSelfComponent` and passes it, the sheet and the still-unassigned plane to `createProfileFeature` at `0x4c9d0856`.

`moCompRefPlane_c` constructor `0x4b7e7980` delegates the feature-handle fields to the reference constructor. The persistent handle observes the node's current ID and creation log at `0x4bb34370`. `moLoggedNode_c::getCreationTime` calls `ut_getUnsetTime` on the empty log branch at `0x4c03e0ce`. The wrapper keeps an inline `ff8` pointer when the plane's ID getter returns `-1` at `0x4b7e7a1e–0x4b7e7a2d`. It owns a distinct copy of the drawing's unit component via the shared component-reference constructor. After wrapper creation the reset adds the plane, profile and detail folder, in that order, at `0x4c9d08ad`, `0x4c9d08f0` and `0x4c9d0918`. Allocation gives the plane a later nonnegative ID while both wire references continue to resolve to the same plane object. [Plane alias gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/SheetPlaneHandlePrecedesPersistentId.md) · [Shared component copy and unset time](ModelConstruction2026.md)

| Field group | Classification | Construction evidence |
| --- | --- | --- |
| Sheet, plane, profile and folder names | Input | Four authored names enter the shared node constructor as native names. |
| Four persistent IDs | Derived | The owning model allocator provides IDs in sheet, plane, profile, folder order. The profile's UI record takes its actual feature ID. |
| Sheet `f408`, `f390`, `f60` and profile plane `ff8` | Derived identity | The native reset supplies the actual profile and detail-folder aliases, ordered concept children and inline plane alias. |
| Wrapper `ff0`, `f100`, `f58` | Derived from construction lifetime | Before plane allocation, reference ID `-1`, shared unset creation time `2592000`, absolute-plane kind `0` and a distinct owned unit-component copy. |
| Plane root, normal, feature `f6dc` | Derived and enum | The native helper constructs origin/+Z. The plane constructor stores the geometry flag `4` at `0x4c2ce612`. |
| Plane axes `f54/f58` | Derived | The absolute pose helper `0x4c2eaf80` selects axes at `0x4c2e9f72–0x4c2e9f8f`. For a +Z plane, the ordinary tie branch at `0x4c2ebd77–0x4c2ebd9e` writes X/Y selectors `1/2`. |
| Plane borders `b0`–`b3` | Derived display geometry | The absolute-plane table `0x4d0b9b30` maps `+0x188` to the border setter `0x4c2f67c0` and `+0x180` to `0x4c2dff30`. With both bbox/provider predicates false (`+0x178`, `+0x190`), the latter returns the default half-widths of 0.1618 and 0.1 metre spans as `[+0.0809,-0.0809,+0.05,-0.05]`. The store uses the border array in this order through `0x4c27b249–0x4c27b276`. |
| Remaining absolute-plane fields | Constructor state | `0x4c2dadb0` provides null references and zero options, with ordinary plane type `f5c=1`. The current serializer writes the compatibility byte at `0x4c27b2a8–0x4c27b2ad`. |
| Profile `pd_ff0`, plane `f20`, UI sketch `f80` | Derived scale | `updateSketchScale` applies `1/(numerator/denominator)` to both model frames. The UI sketch uses the forward ratio. [Scale evidence](DrawingEmptySheetConstruction2026.md) |
| Embedded sketch `f128`, `f188` | Empty sketch state | The sheet reset clears `f128` at `0x4c9d0872`. Shared local-reference inference emits `0` with an empty sketch and no inter-component references. |
| Detail-folder owned lists and optional state | Constructor state | The constructor at `0x4ba2bda0` initializes the embedded lists with `suObList` constructors, initializes the transform, and leaves the optional tail empty. The builder emits each list at the grammar's own field. |
| Sheet auxiliary objects and lists | Derived absence and constructor state | Reset sets `f418`, `f468` and formatting pointers null and constructs the empty `f438` list. Constructor sets `f3d8=1`, `f448=1`, `f4e0=1`, `f4f0=0`. Serialization emits `0xFFFF` at `0x4c9574e7` for absent `f368` detail state. Blank ink and print collections have count zero. |
| Sheet `f430` | Volatile viewport | Reset clears the pointer at `0x4c9d075b`. `getLastOrientation` at `0x4c9cdfa0` returns false for null. The generated profile emits presence zero. |
| Update and creation state | Constructor and authored time | Shared feature defaults provide the neutral fresh stamp, visibility and node flags. The zero-status update path clears the status mask via `0x4c03ed90`. The profile constructor calls the default feature constructor, which samples FILETIME. A caller-supplied creation second supplies that clock. |

The disclosed vendor saves retain a viewport, carry bit 31 on the sheet, plane and profile, and have advanced plane/profile stamp words. One plane also carries an atom-feature presence marker for a null auxiliary reference. The generated subtree uses the shared fresh feature state and an absent viewport. Finished-save lifecycle values and use of that fresh state inside a complete native document still require a measured trial.

## Verification

`CheckDrawingSheetObjects.py` opens only named disclosed hash-locked inputs. It verifies the native aliases, empty support classes, default borders and scale directions. In the same command two independently authored names, paper settings and allocator bases generate separate symbolic graphs. Encoding and fresh loading exhaust them at map next index 29. The digests cover 2,033 and 2,049 bytes. The isolated graph does not establish native opening or editability. [Subgraph receipt](../measurements/2026/DrawingSheetObjects01.json)

```sh
PYTHONPATH=src:re/tooling/sw2026 uv run --isolated --frozen --extra dev --python 3.11 \
  python -B re/tooling/sw2026/serial/CheckDrawingSheetObjects.py /private/disclosed-source-lock
```
