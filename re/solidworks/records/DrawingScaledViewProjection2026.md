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

## Point transform

The ordinary affine point method at `0x31f09820` in `sldmgu.dll` SHA-256 `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c` applies the matrix by columns to the point. With the stored nine terms `m0..m8`, scale `s` and translation `t`, the first output component is `t.x + s * ((x*m0 + y*m3) + z*m6)`. The other components use `(m1,m4,m7)` and `(m2,m5,m8)`. The matrix uses the identity branch when all nine coefficients match the identity.

The matrix product is evaluated at `0x31f098b2..0x31f09920`. The scale block at `0x31f09925..0x31f09963` skips multiplication when `abs(s - 1) <= 1e-8`, using the doubles at `0x31f44828` and `0x31f44800`. Translation follows at `0x31f09968..0x31f0998e`. The SDK's row-major point matrix therefore uses transposed groups of the stored basis and applies the same effective scale. The authored view scale ratio remains available independently.

## Drawing-side routes

Hopper analyzed the pinned `slddrwu.dll` SHA-256 `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47`. The original PE import table identifies the two scale setter slots at `0x3e130270` and `0x3e130268`. The ordinary interactive `AddAView` at `0x3de490a0` and flat-pattern route at `0x3de492c0` call those setters before `finishCreatingView`. A separate route at `0x3def0780` uses them after constructing an absolute view and before the model-view virtual call. These paths establish the direct field bindings for creation. The COM decimal setter's ratio-selection policy still requires source or observed evidence.

The cache-restoration helper at `0x3decc880` passes separate values to `setModelGeometryOnlyBox`, `setBorderSize`, `setPosition` and `setCachedModelBBox`. Keep the model-local box, projected geometry, expanded border and sheet placement distinct during reconstruction.

REA evidence includes `ev_7c03c234dbb6feeb02a681f114d9de76ee50aaf461357534e6d98fbbe61e3c50`, `ev_5d33c6241cff702a83bc4562890494dd84a132bb7e6fc862cdd2876b692b576b`, `ev_7e37be82969970641fa8781a37a955f6b1f28167018d2af7d81f634bf96b588e`, `ev_2227386ab8df72f07fe7f14f849136ef25f6cc07014ceeaf899f799d3b5399c7`, `ev_9e2b6ae078f3cae9647b0cc9ceca7778b8180b7b67c87472176e094e42ddf234`, and `ev_a0db99b94801917eeec2f6795a58316864837a0c7c26465e04078dc9857fa070`. The task-owned Hopper analysis was closed after the evidence export.

## Disclosed comparison

The [four-case specification](../../tooling/sw2026/DrawingProjectionSpecs01.json) assigns changed scale and placement to each of Front, Top, Right and Isometric. It reuses the approved original template, linked part and control hashes. Compare the typed archive values with the native observations and the existing [canonical view rotation construction](../../tooling/sw2026/builders/Views.py).

The disclosed set passes ten native phases with both controls and immutable inputs. Each Definition and Header2 stream round-trips exactly. Across the four views, the saved basis agrees with the corresponding canonical part matrix. The view selector at `+0x1010` follows Front 0, Right 1, Top 2 and Isometric 7. The virtual `setViewFace` at `0x4b294910` writes that selector directly. The independently authored `ScaleDecimal` inputs 0.375, 1.25, 0.625 and 0.8 appear as the numerator with denominator one.

For the measured rectangular-child profile, the transform translation is sheet position minus the scaled, rotated child-box centre. In each projected axis, sum the corresponding absolute column coefficients times the three local half-extents, then multiply by view scale. The footprint extends that half-length from the requested sheet centre. Expanding the footprint by `0.02 * min(paper width, paper height)` reproduces the border. These computations match the stored transform offsets, both projected boxes and the border in all four cases at their recorded doubles.

`setIsOkayTo2DDimension` at `0x4c9b64e0` selects bit 4 of `+0x610` for the ordinary planar views and bit 5 for the measured Isometric view. The manual regeneration bit 8 is separate saved state. The native source measurement and the SDK opt-in reader's 36 transformed-point comparisons are bound in the [scaled drawing receipt](../measurements/2026/DrawingScaledViewSdkRead01.json). [Audit process](../../tooling/sw2026/serial/AuditDrawingProjectionSources.py)

The two original held-out drawing layouts remain sealed. Their public profile allows all four named orientations and positive explicit scales. The supporting sketch and plane rules need separate evidence before generating the expanded view profile.
