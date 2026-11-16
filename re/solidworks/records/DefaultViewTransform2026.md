# Document default and per-user transforms in SOLIDWORKS 2026

This record identifies the document default-transform owner and reports complete decoding of eight native-saved derivatives. The active-camera mapping remains unproven. These are training observations, not preferred writer values or held-out acceptance.

## Exact native boundary

The original external `slduiu.dll` is build `34.5.2.0604`, preferred base `0x48ea0000`, SHA-256 `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7`. Export names, original PE instruction spans and the import table were read directly. No vendor image, assembly listing or decompiled code is included here.

| Method | Original half-open extent | Code SHA-256 | Independently observed behavior |
| --- | --- | --- | --- |
| `uiModelDoc_c::getDefaultViewXform` | `[0x49787270,0x49787278)` | `5f97072a435f56a63ce9394e819a479062d70967dc65cbe31e6ec3424ceee834` | Returns the pointer at runtime `+0xae8` |
| `uiModelDoc_c::setDefaultViewXform` | `[0x48ee7f80,0x48ee7f8e)` | `5949a3a775520de7dc9bff803cbb63cd78ab6d87927dfa8d7c4acdcc2bca439f` | Reads that same pointer, then forwards to the imported transform assignment operator |

The setter import slot is `0x4a4718d8` in `sldmgu.dll`, symbol `??4mgXform_c@@QEAAAEBV0@AEBV0@@Z`. This resolves the forwarded operation as assignment; it does not trace a higher-level active-view getter or setter.

## Typed archive fields and remaining classification

The shared 2026 [definition grammar](../../tooling/sw2026/serial/defs/Definition.py) serializes these owners in field order. This table distinguishes wire ownership from unverified semantic roles.

| Typed field | Established knowledge | Classification boundary |
| --- | --- | --- |
| `uiModelDoc_c.fae8` | Embedded `mgXform_c`; the first document transform corresponds to the runtime owner returned by the named default getter | Default state; relation to neutral presentation input and first active viewport is unproven |
| `uiModelDoc_c.faf0` | Second embedded `mgXform_c`, immediately after `fae8` | Semantic role unresolved; identity in this batch is not constant evidence |
| `uiModelDoc_c.faf8[].o` | Typed `uiUserModelEnv_c`, including a user name and two splitters | Per-user presentation state; user identity is hashed in observations |
| `uiUserModelEnv_c.f10`, `.fe0` | Typed splitter headers and row/column cells; each cell has two transforms, scalar states and a label | Active-cell selection and camera relationship unresolved; captured header/window values must not become writer templates |
| `mgXform_c.has_matrix`, optional `.f08` | Explicit matrix-presence byte followed by nine doubles when present | Format structure established; API-to-wire matrix convention requires independent correlation |
| `mgXform_c.f58/f60/f68`, `.f70`, `.f78` | Translation triple, scale and transform flags in the registered grammar; flags select optional perspective payloads | This batch exercises only zero translation, unit scale, no explicit matrix and zero flags |

## Remote observations

[SavedViewStates0da.json](../measurements/2026/SavedViewStates0da.json) records eight complete saved-file decodes: 72 archive byte comparisons, sixteen document transforms and 48 per-user transforms. Every graph has zero unresolved references. All 64 observed transforms use the identity representation. All 106 reader/dependency fingerprints and the original remote report/artifact hashes are retained.

These fixtures were saved in hidden sessions without an explicit orientation, scale or translation intervention. They therefore do not establish that an active view is stored in any of those fields. In particular, a native named-view table is a different owner from a currently displayed viewport.

The [visible API probe](../../tooling/sw2026/ProbeViewState.py) varies orientation, scale and translation on the same unchanged generated input, records immediate API readback, then saves and reopens in another owned native process. Its native and later complete archive results must be correlated before assigning any of these fields an active-camera role. No frozen writer dependency or public adapter is changed by this record.

## Evidence and execution scope

The reader revision is `0da16563cfdf951439a74c37fcfbcb4ad4e393de`; the tested merge is `72e0922880135db2d72ce99d32c87619f0acdc17` with tree `83743669e208c1a63980d3cb27b56ea992f6d330`. [The native-format job](https://github.com/TryUniCAD/Kit/actions/runs/43935960237/job/133540485854) passed 197 cases with 158 skips; its policy phase passed 171. Artifact `14261360401` is 23,125,020 bytes, independently verified SHA-256 `01bd03e34f692f26504b814c804caee52c11b6726727b0f16dc9ff938662d25e`. The 12,155,175-byte raw report has SHA-256 `adb8920a828d6dfcfd24e85ac2f4b9f7806605f7480f89e3f037b7f0e9b4f191`.

Static original-image inspection and analysis of remote JSON reports ran on the host. No local test, archive schema, codec or writer verification was executed. Licensed binaries/listings remain external. The [change entry](../../../Documentation/Changes/Solidworks/Inspection/Presentation/SolidworksSavedViewStateInspection.md) documents the observer, and all [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) remain required.
