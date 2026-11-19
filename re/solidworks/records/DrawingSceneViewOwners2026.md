# Actual drawing scene-view owners in SOLIDWORKS 2026

Status: partial. The exact source now supplies a bounded direct route from the scene graph to real view keys and the layer-zero getter. The new read-only observer is prepared, not run. Neither actual callback invocation nor detail-scene republication or rendering has been established by the pending field reads.

Task: DRAWING-NOTES-C10, PR #121. Owner: `flag_ownership`; root owns native execution, integration and publication. Dependencies are the prior queue packet, its completed disclosed result, the same three CAD inputs and exact original 2026 images. The immediate exit condition is a complete bounded view inventory with healthy controls and honest per-view field coverage. The remaining rendering and full-source acceptance gates stay open.

## Previous queue result

The independently hashed `DrawingClearQueueObservation01` result is `6ccbd78f169b48cf169eb7f7be66759ce9802beef25c406aa679fd4db8e23a8d`. Four healthy fresh processes and all 16 snapshots found the expected installed handler and a null pending-clear pointer. This refutes a persistent pending-clear difference at those sampled stages only. A clear message can be created and consumed entirely between COM-return observations.

## Direct native view-key route

The [numeric source record](DrawingSceneViewOwnersNative2026.json) pins 15 complete functions, five instruction windows, five imports and three virtual cells across four exact AMD64 images. Original PE metadata replay passed every item. It executes no vendor, SDK, schema, codec or test code.

| Source owner | Proven rule |
| --- | --- |
| `sldgfxu!gfxSceneGraph_c::m_scenegraph` | Exported pointer RVA `0x265a98` in image SHA-256 `eb0a385b396cd0abc03fd92afae26b9df8cab588a737a3b10c806cfe46282249` |
| `getAllViews [0x337c1680,0x337c174b)` | Reads its actual map header at scene graph `+0x1e8`, starts at the header's leftmost node and advances through native left/right/parent links |
| Tree node | Left `+0`, parent `+8`, right `+0x10`, nil byte `+0x19`, actual `gfxViewKey` at `+0x20`, actual `gfxSgView*` at `+0x38` |
| `getView [0x337c2a20,0x337c2b0c)` | Independently uses the same map, compares the actual key and returns node `+0x38`; its nonnull key domain and sheet/view fallbacks remain intact |
| `gfxViewKey::getModelView` | Complete leaf `[0x337b0380,0x337b0384)` reads key `+0` as `uiModelView_c*` |
| `gfxViewKey::getDrSheet` | Complete leaf `[0x337a5ab0,0x337a5ab5)` reads key `+8` as `moDrSheet*` |
| `gfxViewKey::getDrView` | Complete leaf `[0x337a6310,0x337a6315)` reads key `+0x10` as `moDrView*` |
| Concrete model-view getter | Primary `uiModelView_c` table `0x4a662880`, slot `+0x5e0`, selects `[0x4955c600,0x4955c608)` |
| Actual getter result | The complete eight-byte leaf returns view `+0x478`; its SHA-256 is `433f057b3a2a2d095b24323134043fd23141170ae6e582b5dd8f6974d2ebec24` |
| Selected invalidation | `invalidateAllLayerZeros` tests this returned pointer and, only when nonnull, invokes its actual virtual `+0x78` |

The new observer uses the actual scene-view map, not a guessed active frame or archived view order. It checks the real getter target owner, RVA and all eight live bytes before reading `+0x478`. An unsupported actual getter is retained explicitly; the field is not read. A nonnull returned object supplies only its runtime class/vtable and actual slot `+0x78` target module/digest/RVA. That target's full behavior is the next source boundary.

## Selected document path remains distinct

The normal no-argument invalidation path selects `activeRecipeDoc(nullptr)` only on the application's primary thread. `modelDocInterface::documentDraw` dispatches through the actual selected document's virtual `+0x2de0`; the manager constructor retains its actual `uiModelDoc_c*` at manager `+0x10`.

For the ordinary drawing type, table `0x3e1d6b78` selects MFC imports 5408 and 5981 for view iteration via `+0xe0/+0xe8`. The retained system `mfc140u.dll` is ARM64X on disk, SHA-256 `88beebf73667ab0d603355f54562aa9cf9316f4d585a40ec93430c6715ffc8d1`; these particular mapped targets have not been independently bound. A bounded raw LLVM attempt rejected the hybrid export layout, and that failure stays private. No MFC field layout, active document address or TLS state is guessed for the observer.

The view constructor initializes `+0x478` to null. That initial state does not prove that a loaded drawing should lack the object. The source-bound getter and selected native consumer justify measuring actual presence and owner, not manufacturing a saved default.

## Observer bounds and identity

The complete packet preserves all 13 prior tools and three input drawings. Two new research tools add the direct per-view read. The process uses the same `0x410` query/read rights and owned PID/creation-FILETIME checks, with no debugger, breakpoint, remote call, patch, save, bitmap export or setting change.

At each of the same four stages, the traversal permits at most 64 nodes, depth 64 and three consistency attempts. It rejects noncanonical/misaligned pointers, duplicate nodes, cycles, foreign sentinels, inconsistent parent links, wrong extrema and duplicate actual keys. It rereads the header, every node and the field/target pointer cells after collecting rows. Unstable or inaccessible state is retained as a partial failure. The reads are sequential, not atomic.

Comparisons use actual key roles and runtime class identities. Heap address, native traversal index and pointer order never select matching source/generated instances. A repeated or unresolved role/type identity is reported as selection ambiguity, preserving every state without per-instance equality. Even a unique role/type group is narrower than full model identity. The normal COM document count is recorded; multiple open documents also make selection ambiguous. No geometry, sheet-name correspondence or rendering pass is inferred from these groups.

The raw runtime pointers and installation paths stay private. The [preparation receipt](../measurements/2026/DrawingSceneViewPreparation01.json) binds source, methods and input custody. Runtime collection, the concrete invalidator body and full detail-scene republication remain pending root work.
