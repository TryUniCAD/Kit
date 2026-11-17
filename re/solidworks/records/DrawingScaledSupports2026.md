# SOLIDWORKS 2026 disclosed standard-view sketch supports

This is a source and offline correlation result for four disclosed discovery drawings. It does not qualify generated drawing output or held-out coverage. No vendor process was started and no hidden specification, saved case or author observation was opened.

## Custody

- Original `sldmodu.dll`, preferred base `0x4b140000`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
- Original `sldmgu.dll`, SHA-256 `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c`.
- Disclosed source lock.
- Prior projection audit.
- The source lock has ten independent native phases, both healthy controls, all four author/reopen cases passed and immutable inputs. Its four names are D00ScaledFront, D01ScaledTop, D02ScaledRight and D03ScaledIsometric; every split is discovery.

[Pinned source locations](../measurements/2026/DrawingScaledViewSourceBindings01.json) binds the native procedures to original PE export names, exception-directory ranges and code hashes, including the centre-mark factory's separate creation-body unwind range. A routine without an exception-directory entry retains only its explicit entry address and a labelled 16-byte hash; it does not receive an invented function extent. LLVM's nearest exported label is not treated as an unexported function name.

[Support comparison](../measurements/2026/DrawingScaledViewSupports01.json) records all four typed support graphs, exact Definition and Header2 round trips, native input/observation hashes and independently evaluated formula errors. The comparison derives eligibility from the geometric predicate and checks the ordinary absolute view owner.

## General frame rules within this disclosed profile

Let the authored sheet position be `p=(x,y,0)`, explicit view scale be `s`, generated model-box centre be `c`, and canonical model-to-view matrix terms be `m0..m8`. Native point application uses columns: `R(q)[j] = q.x*m[j] + q.y*m[3+j] + q.z*m[6+j]`.

| Owner | Construction rule | Confidence |
| --- | --- | --- |
| View `f7c8` sheet sketch support | Plane data is `moDrawingRefPlnData_c`. Root is `p`, normal is +Z, rotation is identity, scale is `1/s`, and translation is `-p/s`. Profile `pd_ff0` equals that plane transform. The extra `f88` rotation is identity; plane `f6c0` and the four display borders are zero. | Native source and all four disclosed saves agree. |
| View `fde0` model sketch support | This is the centre-mark sketch factory's plane/profile pair. Plane data is `moAbsoluteRefPlnData_c`. Root is `c`, rotation is `R`, scale is one, translation is `-R(c)`, and normal is `(m2,m5,m8)`. Profile `pd_ff0` carries the same geometric frame. | Native source and all four disclosed saves agree within floating-point recomposition error. |
| Model plane `f6c0` | This is the name/display location, not its geometric root. For these four canonical frames it is `c + b1*(m0,m3,m6) + b2*(m1,m4,m7)`. The ordinary default rectangle is `[+0.0809,-0.0809,+0.05,-0.05]`. | Native corner/name-location source and all four disclosed saves agree. |
| Plane/profile feature flags | All five support children have `f0c=0` in this cohort. Both profile-plane aliases point to their actual owned plane. Child order remains detail folder, sheet plane, sheet profile, model plane, model profile. | Exact graph observations; existing constructor/mask rules remain the source of emitted flags. |

The rectangle constants are independently constructor-proven at `moAbsoluteRefPlnData_c` vtable `0x4d0b9b30`, border getter `0x4c2dff30` and setter `0x4c2f67c0`, as recorded in `re/solidworks/records/DrawingEmptySheetObjects2026.md`; they are not fitted from these four drawings.

The geometric model root in saved records differs from `c` in low floating-point words in some cases. The Front profile translation also differs slightly from its own plane translation. Do not copy those saved words or introduce per-case corrections. The mathematical frames agree, and `setSketchXforms` composes and inverts transforms on the native path.

## Concrete native owner paths

The sheet-side route is `moDrView::createProfileFeature` at `0x4c9952b0`, not the model-side factory. It calls the drawing-plane factory `0x4c2d40d0` at `0x4c9952ff`. The scale block at `0x4c995330..0x4c995363` divides `view+780` by `view+788`, optionally multiplies the alternate owner factor and passes its reciprocal to `moDrawingRefPlnData_c::setDrawingScale` at `0x4c2bc360`. At `0x4c99556c..0x4c995576` it passes the actual `view+778` position to plane virtual slot `+1c8`; `0x4c99557f` calls `setSketchXforms`. `finishCreatingView` repeats the reciprocal-scale and position update for `f7c8` at `0x4c99848b..0x4c9984dd`. These cases have no alternate owner `fe60`.

The model-side route is `moDrView::getOrCreateCenterMarkSketch` at `0x4c9a3b10`. It creates the absolute default plane at `0x4c9a3b6b` and reframes it using the separate helper at `0x4c9b4740`, called at `0x4c9a3b79`. The helper obtains the 3D view frame, removes its scale at `0x4c9b47a0..0x4c9b47c8`, removes alignment rotation at `0x4c9b47ea..0x4c9b4818`, and assigns the result to the plane data's transform at `0x4c9b4837`. It derives +Z through the inverse frame at `0x4c9b4845..0x4c9b4878`, writes the normal at `0x4c9b4896` and updates the plane at `0x4c9b48b1`. The factory stores the profile at `view+fde0` at `0x4c9a3bde`, clears sketch mode `+128`, calls `setSketchXforms` at `0x4c9a3c02`, then inserts the plane and profile into the actual view.

`moProfileFeature_c::setSketchXforms` at `0x4c0e5280` gets the support plane transform at `0x4c0e53cc`, stores it through profile data `+f0`, applies an optional extra transform at `0x4c0e53ff`, and computes the inverse at `0x4c0e5418`. This explains why geometric equivalence, rather than copied saved floating-point words, is the correct construction rule.

`moRefPlnData_c::getFourCorners` at `0x4c2e57c0` uses the plane root, border array and transformed basis. `updateNameLocation` at `0x4c2f72c0` selects a corner using the plane's basis/sign tests and calls `moRefGeom_c::setNameLocation` at `0x4c2f73f3`. That setter at `0x4c2cf0c0` writes the actual plane `+6c0`. The four-frame simplification above is not a claim that every arbitrary plane orientation selects the same corner.

## Eligibility flags are a separate derived cache

Observed `f610` is `0x998` for Front, Top and Right, and `0x9a8` for Isometric. Their only difference is the mutually exclusive cached 2D-dimension result: bit `0x10` means true and bit `0x20` means false. `moDrView::isOkayTo2DDimension` at `0x4c9aeaf0` immediately returns true for the former at `0x4c9aeb2b`, and false for the latter at `0x4c9aeb33`. The setter at `0x4c9b64e0` sets one and clears the other.

When neither result is cached, `0x4c9aeb91..0x4c9aebd2` transforms +Z by the inverse view frame and invokes `mgVector_c::isOrthogonal` through IAT `0x4cd3be10`. The original imported export is `sldmgu.dll` `0x31f1b170`: exactly one absolute component must be greater than or equal to `1e-8`, and the other two must be smaller. The threshold is the original double at `0x31f44800`. The native code has additional parent/unfolded/virtual-override routes; the four ordinary resolved standard views take the predicted geometric outcomes. The `moAbsoluteView` override is vtable `0x4ce83fb8` slot `+2060`, target `0x4b745630`; this observation does not qualify its special branches.

Explicit-scale bit `0x8` remains set for all four nonunit ratios. Saved manual-regeneration bit `0x100` is a separate transition. Do not copy the complete saved `0x998/0x9a8` into a fresh graph. The existing fresh alignment/insertion/custom-scale baseline remains `0x800|0x80|0x8`, with the independent eligibility result added or left to a source-justified uncached path.

All four saved `f614` values are `0x710504`, including Isometric, with face-valid bit `0x100` set. Face validity is independent of 2D-dimension eligibility: `setIsViewFaceValid` at `0x4c9b6530` updates `f614` bit 8 only. Changing it merely because the view is Isometric would contradict this cohort. `f618=0x8000` and `f61c=0xf` are also identical across the four saves; their saved-only lifecycle bits must retain the existing fresh-state classification.

## Builder consequence and boundary

[DrawingViewSupports.py](../../tooling/sw2026/builders/DrawingViewSupports.py) now constructs the sheet inverse-scale and model unit-scale oriented frames. The model normal and display origin follow the chosen canonical axes. [DrawingFrontProjection.py](../../tooling/sw2026/builders/DrawingFrontProjection.py) obtains those axes from the actual generated child model's named view. It derives the centre, projected extent and border from the neutral child geometry and sheet size.

The comparison passed 76 formula-check groups and eight exact stream round trips. Existing source/native controls establish the saved-source facts; they do not measure the expanded writer. The original blind mapper remains frozen and the two sealed drawing source specifications remain unopened.

## Reproduction

Run [AuditDrawingViewSupports.py](../../tooling/sw2026/serial/AuditDrawingViewSupports.py) with the PR121 worktree as `--root`, the disclosed `DrawingProjectionSource01/Native` directory as `--corpus`, its parent `ProjectionFields01.json` as `--projection`, and a new `--output` file. Run [CollectDrawingViewSupportEvidence.py](../../tooling/sw2026/CollectDrawingViewSupportEvidence.py) with `--binaries` pointing to the licensed module directory and a fresh `--output` to verify the exact original PE identities and source locations. Both scripts run offline and emit no CAD files.

The attempted saved Hopper database route is unsupported by the current REA launcher. Opening the original model target succeeded logically, but its first provider query reported an older foreign owner session. No foreign document was closed. This task's logical target was closed, and all source facts above were independently checked using the pinned original PE and LLVM. No task-owned Hopper document remains open.
