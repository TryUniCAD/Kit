# Document default and per-user transforms in SOLIDWORKS 2026

This record identifies the document default-transform owner, reports the earlier eight hidden-session derivatives, and correlates ten later visible-intervention derivatives with their native API poses. Orthographic orientation and pan/zoom correspondence is measured. Two subsequently frozen unseen camera predictions now pass controlled initial-load, rebuild, edit, save and fresh-reopen pose comparisons. Actual pixel-level viewport and full native acceptance remain unproven. Training observations and bounded unseen measurements are reported separately.

## Exact native boundary

The original external `slduiu.dll` is build `34.5.2.0604`, preferred base `0x48ea0000`, SHA-256 `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7`. Export names, original PE instruction spans and the import table were read directly. No vendor image, assembly listing or decompiled code is included here.

| Method | Original half-open extent | Code SHA-256 | Independently observed behavior |
| --- | --- | --- | --- |
| `uiModelDoc_c::getDefaultViewXform` | `[0x49787270,0x49787278)` | `5f97072a435f56a63ce9394e819a479062d70967dc65cbe31e6ec3424ceee834` | Returns the pointer at runtime `+0xae8` |
| `uiModelDoc_c::iSetDefaultViewXform` | `[0x48ee7f80,0x48ee7f8e)` | `5949a3a775520de7dc9bff803cbb63cd78ab6d87927dfa8d7c4acdcc2bca439f` | Reads that same pointer, then forwards to the imported transform assignment operator |
| `uiModelView_c::getModelViewXform` | `[0x48eee140,0x48eee148)` | `dd18a3fe8ab0efbef98c862223892743edb11a3243e9b2a95fea7b13f986f65b` | Returns the active model-transform pointer at runtime `+0x6d8` |
| `uiModelView_c::setModelViewXform` | `[0x49829850,0x498298e6)` | `e860bb0888b0f4edf30c45ad8e699f96303a4ba77ed6cf5d307c33b4efe9f6a3` | Assigns the active transform or allocates and copies it, updates optional state, then tail-calls `rebuildTransform` |
| `uiSplitterInfo_c::setDocViewingXforms` | `[0x497d68b0,0x497d6bb4)` | `cf3999162c9ad9d9870cf327477625b0f5f4ed44dc6cad354fd739353fa73eac` | Restores saved model and pan/zoom transforms into the selected active view |

The default setter import slot is `0x4a4718d8` in `sldmgu.dll`, symbol `??4mgXform_c@@QEAAAEBV0@AEBV0@@Z`. This resolves the forwarded operation as assignment. The inspected `uiModelView_c` primary table at `0x4a662880` has model-transform getter slot `+0x610` and setter slot `+0x630`. The splitter bridge reads its first transform pointer array at runtime `+0x28+8*index` into that setter, and its second array at `+0x48+8*index` into `setPanZoomXform` at `0x498299c0`. Grid bounds and active-view matching gate the assignments; optional tree zoom, perspective and camera paths are separate branches. The bridge's full original runtime-function span was inspected, rather than treating a short vtable inventory as the complete interface.

## Typed archive fields and remaining classification

The shared 2026 [definition grammar](../../tooling/sw2026/serial/defs/Definition.py) serializes these owners in field order. This table distinguishes wire ownership from unverified semantic roles.

| Typed field | Established knowledge | Classification boundary |
| --- | --- | --- |
| `uiModelDoc_c.fae8` | Embedded `mgXform_c`; the document default owner and measured orientation state | For the visible orthographic requests, matrix `m0..m8` equals `Orientation3.ArrayData[0:9]` in order; translation is zero and scale is one |
| `uiModelDoc_c.faf0` | Second embedded `mgXform_c`; measured pan/zoom state | `f58/f60/f68` equal `Translation3.ArrayData[0:3]` and `f70` equals `Scale2`, with no matrix in these requests |
| `uiModelDoc_c.faf8[].o` | Typed `uiUserModelEnv_c`, including a user name and two splitters | Per-user presentation state; user identity is hashed in observations |
| `uiUserModelEnv_c.f10`, `.fe0` | Typed splitter headers and row/column cells; each cell has two transforms, scalar states and a label | In the visible batch, primary `f10[0,0].xa/xb` exactly mirror `fae8/faf0`; the two secondary `fe0` cells remain identity. Other window/grid selection remains unqualified; captured rows must not become writer templates |
| `mgXform_c.has_matrix`, optional `.f08` | Explicit matrix-presence byte followed by nine doubles when present | Identity omits the matrix in this batch; standard isometric orientation stores the API's nine coefficients directly, without transpose/inverse |
| `mgXform_c.f58/f60/f68`, `.f70`, `.f78` | Translation triple, scale and transform flags; flags select optional perspective payloads | Visible observations vary two translation triples and two nonunit scales; all flags remain zero. Native API coordinate meaning is retained and perspective remains unqualified |

## Remote observations

[SavedViewStates0da.json](../measurements/2026/SavedViewStates0da.json) records eight complete saved-file decodes: 72 archive byte comparisons, sixteen document transforms and 48 per-user transforms. Every graph has zero unresolved references. All 64 observed transforms use the identity representation. All 106 reader/dependency fingerprints and the original remote report/artifact hashes are retained.

These fixtures were saved in hidden sessions without an explicit orientation, scale or translation intervention. They therefore do not establish that an active view is stored in any of those fields. In particular, a native named-view table is a different owner from a currently displayed viewport.

The [visible API probe](../../tooling/sw2026/ProbeViewState.py) varies orientation, scale and translation on the same unchanged generated input, records immediate API readback, then saves and reopens in another owned native process. Its [native receipt](../measurements/2026/VisibleViewProbe02.json) passes all five requests and ten phases with exact fresh pose persistence, healthy controls and unchanged license process IDs. The [complete remote correlation](../measurements/2026/ViewProbeCorrelationA062.json) passes ninety archive comparisons, twenty document transforms, sixty user-cell transforms and 130 exact component correspondences. In the combined case the orientation matrix remains in `fae8`, while translation and scale remain in `faf0`; they are not stored as one combined affine transform in the first field. All primary user cells mirror the document pair; secondary cells stay identity. No frozen writer dependency or public adapter is changed by these observations.

This training batch supports deriving orthographic presentation fields from explicit orientation and native pan/zoom inputs. It does not itself qualify arbitrary rotations, perspective, multiple active windows or unseen generated camera files. The five training requests use only identity and native standard isometric orientation on one unchanged body. Saved previews remain separate evidence: four different API requests share the same PNG bytes.

## Frozen unseen camera measurements

The [354-file camera freeze](../v2026/heldout/ViewWriterFreeze.json) precedes access to the two independent trimetric/dimetric source API observations. Both complete neutral predictions pass sixteen remote archive comparisons and the runtime read guards in [ViewHeldoutProcessesFd08.json](../measurements/2026/ViewHeldoutProcessesFd08.json). Their receipt was committed before opening the private API observations; original native CAD payloads remain sealed. [ViewHeldoutReference01.json](../measurements/2026/ViewHeldoutReference01.json) finds all 26 written pose components and forty unedited source body/dimension comparisons exactly equal, with twelve exact body/direction comparisons also passing.

[ViewHeldoutInspection01.json](../measurements/2026/ViewHeldoutInspection01.json) records six fresh native candidate phases, healthy bracketing controls and eight distinct process creation identities. All 400 pose comparisons are exactly equal to the independent source through initial load, rebuild, radial/depth edits, save and edited fresh reopen. Another 200 geometry, frame, mass and dimension checks pass; maximum relative error is `5.910814648213976e-16`, zero targets are exact, and two repeated one-ULP centre-of-mass decimal formatting ties remain explicit. Input/reference hashes are unchanged, postflight finds no SOLIDWORKS process, and licensing process IDs are unchanged.

The generated definitions use `nenv = 0` and `faf8 = []`. Thus the measured initial poses establish restoration from the computed document pair without saved per-user rows for these two cases. The exact fallback caller, arbitrary rigid orientation, perspective, multiple windows, full tree parity and actual visible viewport equality remain outside this result. This bounded camera rung does not enable the read-only public adapter or count as production corpus acceptance.

## Evidence and execution scope

The earlier hidden-session reader revision is `0da16563cfdf951439a74c37fcfbcb4ad4e393de`; its tested merge is `72e0922880135db2d72ce99d32c87619f0acdc17` with tree `83743669e208c1a63980d3cb27b56ea992f6d330`. [That native-format job](https://github.com/TryUniCAD/Kit/actions/runs/43935960237/job/133540485854) passed 197 cases with 158 skips; its policy phase passed 171. Artifact `14261360401` is 23,125,020 bytes, independently verified SHA-256 `01bd03e34f692f26504b814c804caee52c11b6726727b0f16dc9ff938662d25e`. The 12,155,175-byte raw report has SHA-256 `adb8920a828d6dfcfd24e85ac2f4b9f7806605f7480f89e3f037b7f0e9b4f191`. The later visible correlation has its own complete provenance in `ViewProbeCorrelationA062.json` and the [correlation entry](../../../Documentation/Changes/Solidworks/Inspection/Presentation/SolidworksOrthographicViewFieldCorrelation.md).

Static original-image inspection and analysis of remote JSON reports ran on the host. No local test, archive schema, codec or writer verification was executed. Licensed binaries/listings remain external. The [change entry](../../../Documentation/Changes/Solidworks/Inspection/Presentation/SolidworksSavedViewStateInspection.md) documents the observer, and all [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) remain required.
