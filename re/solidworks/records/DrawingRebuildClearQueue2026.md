# Drawing rebuild clear queue and document invalidation, SOLIDWORKS 2026

Status: partial. Exact native source now explains the registered graphics messenger's clear-all predicate and following document invalidation. The disclosed runtime observations prove callback registration only. The queue successor is prepared, not executed, and no rendering or writer acceptance is claimed.

Task: DRAWING-NOTES-C10, PR #121. Owner: `flag_ownership`; root owns the VM, qualification, integration and publication. Dependencies are the immutable earlier messenger packet, its completed four-process receipt, three original exact-build modules and the same disclosed note inputs. This tranche's runtime exit condition is complete stable bounded queue observations with healthy controls. The rendering defect remains open.

## Exact source

The [numeric source record](DrawingRebuildClearQueueNative2026.json) pins three AMD64 images, 17 complete functions, five instruction windows, three RTTI data windows, 13 imports and four vtable cells. The original PE replay verified all of them without native, CAD, schema or codec execution. File-version words are `34,5,2,604`.

| Image | SHA-256 |
| --- | --- |
| sldgraphicsuiu.dll | `3948ce26833d053f9d4d0a8b4f8b1b9ed90662f4324aca2f4d002c7f3166edbf` |
| sldgfxu.dll | `eb0a385b396cd0abc03fd92afae26b9df8cab588a737a3b10c806cfe46282249` |
| slduiu.dll | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |

The completed earlier read-only run, result SHA-256 `2753a8d3fe258179119f13911d44a848511d468f9eda972549c39535cedefc2b`, observed the same `grUiMessenger_c` table RVA `0x166c40` and slot `+0x10` target RVA `0xd1e40` in all 16 snapshots. It did not read the handler or queue field.

## Message owner and predicate

The actual callback is `sldgraphicsuiu [0x32cc1e40,0x32cc1e8d)`, 77 bytes, SHA-256 `3a2eee93317b8e424aa0b53dbe20475475f99fe096cf84a756a5f330cb1f4591`.

1. It reads the message handler at messenger `+0x8` and returns if null.
2. It invokes the actual `sldgfxu!gfxSgMessageHandler_c::hasClearAllMessage` import and returns if that result is true.
3. Otherwise it calls `processClearAllMessage`, its own virtual `+0x38`, and the registered drawing interface's virtual `+0xa0`.

The complete predicate leaf `[0x338f27d0,0x338f27d9)` compares the qword at handler `+0x28` with zero. Its SHA-256 is `9d52413d08f660c9ff98255aa9958a2324e509449f5eddaf8774548ab6bfbad4`. The pending pointer is transient queue state, not a saved drawing flag or constructor field to copy.

The module installation function `[0x32d138e0,0x32d13af1)` obtains the actual static handler object at graphics-UI RVA `0x1ebde0`, stores that pointer at the messenger's `+0x8`, and registers the actual messenger at RVA `0x1ebe38`. The reached store leaf `[0x32c92fc0,0x32c92fc5)` writes the supplied pointer at receiver `+0x8`. The handler constructor `[0x32cc0fd0,0x32cc0ff7)` calls the core base constructor and installs the RTTI-backed concrete `grUiMessageHandler_c` table at RVA `0x166b68`.

`processClearAllMessage [0x338f3220,0x338f325c)` first calls `clearAllMessages [0x338f2530,0x338f2669)`, which tears down entries in the handler's two other owned message maps. If `+0x28` is still null, it allocates and constructs a 16-byte clear-all object and publishes its pointer there. `processAllMessages [0x338f2b80,0x338f30ca)` prioritizes a nonnull `+0x28`, dispatches that object's virtual method with the actual update engine, removes the clear-all message and clears other messages. Its complete update-engine action is a separate next boundary; a pending queue does not prove a scene was cleared at a particular COM observation.

## Actual document/view handoff

The messenger local phase `[0x32cc1ef0,0x32cc1f0e)` reads the imported `gfxSceneGraph_c::m_scenegraph`, then that object's `+0x8` external interface. When present it calls virtual `+0xf8`. The normal concrete interface table and import thunk resolve this to `slduiu!uiGfxSgInterface_c::invalidateLayerZero()`.

The drawing interface `+0xa0` target `[0x32cc0180,0x32cc01a8)` calls `gfxSceneGraph_c::endViewDrag` and then messenger `+0x38` again. Calling this target a per-document publication or note-registration routine would be unsupported.

The exact no-argument invalidation owner `[0x49ced340,0x49ced370)` obtains the active recipe document through `[0x49e2c2e0,0x49e2c31a)`: `am_GetApp`, nonnull app, `isPrimaryThread`, then `activeRecipeDoc(nullptr)`. A nonnull selected document is wrapped as a `modelDocInterface`, whose `documentDraw` manager receives `invalidateAllLayerZeros`.

`uiDocDrawMan_c::invalidateAllLayerZeros [0x49c21520,0x49c21615)` iterates the selected document's actual views, checks `uiModelView_c` type membership, obtains each layer-zero interface through virtual `+0x5e0`, and invalidates it via virtual `+0x78`. Further per-view conditions and fallback paths remain preserved in the complete function. No `moDrSheet` wire field is read in this recovered aperture.

This explains active document selection and invalidation ownership. It does not establish which native thread or active frame was used during a measured rebuild, nor prove that the note's render object is republished. No guessed per-document pointer is added to the successor observer.

## Prepared successor and limits

`OwnedMessengerQueue.py` extends the immutable earlier read helper. It requires the already measured graphics module/target/table identities and exact source-installed messenger/handler objects. It verifies the core module's complete disk digest and nine live predicate bytes before reading the queue. A null handler is preserved as an actual early-return state; an unexpected nonnull owner fails closed.

At open, pre-rebuild, post-rebuild and redraw, it reads handler `+0x28`, rechecks that field plus the handler and messenger chains, and allows at most three bounded attempts. It records pending/nonpending states without dereferencing the queued object, changing any byte or calling a native function. Target/pending differences are observations, not success gates. These sequential snapshots can miss a transient event entirely between stages.

The same query/read `0x410` process rights, PID/FILETIME ownership checks, fresh COM lifecycle and healthy controls are retained. All 11 earlier tools and disclosed CAD inputs are byte-identical. The two added tools contain no save, bitmap, text, preference, debug or remote-code operation. Runtime pointers remain in the private raw reports only. Native collection and full source/held-out acceptance remain pending.

[Preparation and custody receipt](../measurements/2026/DrawingRebuildClearQueuePreparation01.json)

## Native snapshots

The [native result](../measurements/2026/DrawingRebuildClearQueueNative01.json) completes four fresh processes with two healthy pristine brackets. A valid source-bound handler is present in all 16 snapshots. Its clear-all queue is empty after open, just before rebuild, just after rebuild and after redraw. The native source and generated drawing agree at all measured points. The reads are stable on the first bounded attempt. An entire in-call queue transition can fall between snapshots. The next scope is the active drawing's layer-zero invalidation and actual annotation publication. Raw result SHA-256 `6ccbd78f169b48cf169eb7f7be66759ce9802beef25c406aa679fd4db8e23a8d`.
