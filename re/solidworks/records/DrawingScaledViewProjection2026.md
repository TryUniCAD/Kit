# SOLIDWORKS 2026 drawing scale and orientation source rules

The disclosed drawing writer currently persists a single unit-scale Front view. This investigation extends the source evidence for the view scale fields, the selected orientation and their geometric consequences. It uses the same pinned model loader and shared part/view graph.

## Scale ownership

All model method addresses refer to SOLIDWORKS 2026 SP05.2 (34.5.2.0604) `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.

| Owner | Source rule |
| --- | --- |
| View `+0x780` and `+0x788` | `setScale1` at `0x4c9b6fa0` and `setScale2` at `0x4c9b6fb0` independently write the supplied doubles. The two stored fields are the ratio terms. The setters perform no reduction or decimal conversion. |
| Effective scale | `getScale` at `0x4c9a48a0` divides the two stored terms. When the call selector is zero and the view has a separate owner at `+0xe60`, it also multiplies by that owner's factor at `+0xb0`. |
| Explicit scale | `setUseCustomScale(true)` at `0x4c9b80d0` sets bit 3 of the view flags at `+0x610` and clears bits 26 and 27. |
| Inherited scale | `setUseParentScale` at `0x4c9b8130` clears bits 3 and 26 and sets bit 27. `setUseSheetScale` at `0x4c9b8150` clears bits 3 and 27 and sets bit 26. |
| Named view | The constructor at `0x4b744590` stores selector zero at `+0x1010`, the supplied name at `+0x1018` and absolute role one at `+0x1030`. It invokes `setUseSheetScale` initially. An independently scaled view takes the explicit scale transition. |

The named constructor and scale flags distinguish the initially inherited view from its authored explicit ratio. The view transform, support plane state and projected outline need their own comparison at the selected orientation and scale.

## Drawing-side routes

Hopper analyzed the pinned `slddrwu.dll` SHA-256 `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47`. The original PE import table identifies the two scale setter slots at `0x3e130270` and `0x3e130268`. The ordinary interactive `AddAView` at `0x3de490a0` and flat-pattern route at `0x3de492c0` call those setters before `finishCreatingView`. A separate route at `0x3def0780` uses them after constructing an absolute view and before the model-view virtual call. These paths establish the direct field bindings for creation. The COM decimal setter's ratio-selection policy still requires source or observed evidence.

The cache-restoration helper at `0x3decc880` passes separate values to `setModelGeometryOnlyBox`, `setBorderSize`, `setPosition` and `setCachedModelBBox`. Keep the model-local box, projected geometry, expanded border and sheet placement distinct during reconstruction.

REA evidence includes `ev_7c03c234dbb6feeb02a681f114d9de76ee50aaf461357534e6d98fbbe61e3c50`, `ev_5d33c6241cff702a83bc4562890494dd84a132bb7e6fc862cdd2876b692b576b`, `ev_7e37be82969970641fa8781a37a955f6b1f28167018d2af7d81f634bf96b588e`, `ev_2227386ab8df72f07fe7f14f849136ef25f6cc07014ceeaf899f799d3b5399c7`, `ev_9e2b6ae078f3cae9647b0cc9ceca7778b8180b7b67c87472176e094e42ddf234`, and `ev_a0db99b94801917eeec2f6795a58316864837a0c7c26465e04078dc9857fa070`. The task-owned Hopper analysis was closed after the evidence export.

## Disclosed comparison

The [four-case specification](../../tooling/sw2026/DrawingProjectionSpecs01.json) assigns changed scale and placement to each of Front, Top, Right and Isometric. It reuses the approved original template, linked part and control hashes. Compare the typed archive values with the native observations and the existing [canonical view rotation construction](../../tooling/sw2026/builders/Views.py).

The two original held-out drawing layouts remain sealed. Their public profile allows all four named orientations and positive explicit scales.
