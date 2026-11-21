# Drawing scene-view observer retry in SOLIDWORKS 2026

The first run is incomplete: exit 3 after the native source's sixth `GetFirstView` call failed with `RPC_S_UNKNOWN_IF`. Both controls and the generated phase passed. All 16 guarded memory snapshots were persisted before that failure, but all original layer-field reads remained unqualified. The successor is prepared only; no new native result is claimed.

Task: DRAWING-NOTES-C10, PR #121. Owner: `flag_ownership`; root owns the VM, integration and publication. Dependencies are the frozen scene-view observer, exact disclosed inputs, original 2026 images and the first failed report. The exit condition is a fresh complete observer run with the real drawing override source-bound and all ordinary controls/COM checks intact. Renderer and full-source acceptance remain open.

## First run: equal versus unknown

The complete raw report is SHA-256 `8b72327abb9fa7b73fc5b1b1f880b8c7f0f0be750b7736393bef39cb425e716e`, bound to job `37af7688381042f795b5489b5eef4132eaf96dbca1e6e737f323ecec8af71c5b`. Four distinct owned processes opened errors/warnings `0/0`, returned true from rebuild, retained input hashes and completed clean owned-handle/application cleanup.

All 16 tree snapshots are stable and contain exactly two unique role/type identities: `uiDrawingView_c` with `gfxSgDrawingView_c`, and that same UI type with `moDrSheet` plus `gfxSgSheetView_c`. No `moDrView` is present in these keys. The actual getter in every row is `slddrwu.dll` RVA `0x39d360`, image SHA-256 `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47`. The first guard admitted only the independently proven `slduiu` getter, so it correctly refused every `+0x478` read.

Therefore the normalized role/type groups, count and getter identity are equal across source/generated/control samples. Layer presence, layer class and invalidator values are unknown. Their null JSON fields are not measured null native pointers. No layer-state equality can be credited to this run.

For NativeSource, initial ordinary annotation state is complete. Rebuild and all memory stages finish. During the post-redraw ordinary state check, `GetAnnotations` returns one annotation, then nested note reacquisition calls `GetFirstView` again and fails at zero-based API call index 150. This is the sixth such call; the previous five succeeded. The HRESULT is `-2147023179`, `0x800706b5`. Post-redraw full text/name/position/geometry verification remains unknown. A failing source document, a renderer cause or a stale-interface cause is not established.

The [sanitized first-run receipt](../measurements/2026/DrawingSceneViewObservation01.json) preserves all phase/report hashes, exact successful versus failed calls and the 16 snapshot summaries. The original packet and every raw result remain immutable.

## Real drawing override

The [numeric source record](DrawingSceneViewRetryNative2026.json) binds both current getter bodies and the real drawing dispatch type. Exact original PE replay verified two images, two complete leaf functions, two RTTI data windows and one virtual cell.

- `uiModelView_c` base support remains `slduiu.dll`, RVA `0x6bc600`, `[0x4955c600,0x4955c608)`.
- The observed drawing override is `slddrwu.dll`, RVA `0x39d360`, `[0x3df5d360,0x3df5d368)`.
- Both complete eight-byte bodies read receiver `+0x478` and return; both hash to `433f057b3a2a2d095b24323134043fd23141170ae6e582b5dd8f6974d2ebec24`.
- Real primary `uiDrawingView_c` table RVA is `0x6230e0`, preferred VA `0x3e1e30e0`; cell `+0x5e0` is `0x3e1e36c0` and selects the drawing getter.
- The RTTI locator is `0x3e24e300`, with this-offset zero and type-descriptor RVA `0x800f88` for `.?AVuiDrawingView_c@@`.

The additional lane requires all of the drawing module hash, getter RVA, live body hash, actual class, zero this-offset and actual table identity. The original base lane and every tree guard remain unchanged. This is an independently established concrete branch, not an arbitrary acceptance of another identical-looking getter.

## Bounded observer-only retry

The fresh packet preserves all 15 earlier tool files and all CAD inputs. Three new tools implement the exact drawing lane, a scoped ordinary read helper and the successor entrypoint. At each ordinary state the helper obtains a fresh registered `DrawingDoc` interface, acquires its actual sheet view once, and reuses one annotation collection for the existing count and note checks. It keeps the prior sheet/view/tree/dependency, text/name/position, attachment, extent, visible-display, glyph and preference assertions. The note-geometry body is AST-identical after replacing its repeated view lookup with the already obtained annotation.

This reduces redundant `GetFirstView` calls; it is not a proved repair for the RPC failure. No failed call is retried automatically, swallowed or reported as pass. Any ordinary COM failure still leaves `data_collected=false`, `ordinary_com_verification_complete=false` and exit 3.

The new report separately exposes `independent_memory_observations_complete` and `source_generated_memory_comparison` only when all four stages in all exact owned processes have complete input/ownership custody and healthy controls. These do not substitute for full ordinary verification. A later COM failure cannot erase already collected memory evidence, and memory equality cannot turn a failed phase into success.

The same read/query rights, process identity checks, maximum 64 nodes/depth, three consistency attempts, class/getter validation, refusal paths and ambiguity rules remain in force. No native function is executed by the memory reader. No model/bitmap save, note edit, setting, debugger, injection, VM action, hidden payload or shared edit is added. Runtime pointers stay private. [Preparation receipt](../measurements/2026/DrawingSceneViewRetryPreparation01.json).
