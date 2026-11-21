# Disclosed SOLIDWORKS 2026 thin boss revolve owners

The ordinary part archive codec reconstructs Config-0 and its linked ResolvedFeatures stream exactly for four independently authored thin boss revolutions and their four native edited saves. The two streams preserve the decoded owners and map indices. This is structural evidence for an internal archive route. Thin cut, alternate archive modes, portable thin semantics, generated output, and held-out acceptance are pending.

## Source and build custody

The authoring protocol created the four disclosed cases in [RevolveThinDiscovery.json](../v2026/corpus/revolve-family-models/RevolveThinDiscovery.json). The source-lock SHA-256 is `f851a26cc549433b5a342b2b7801171f56e356b50866b7f84929353966d6fe25`. The lock identifies source revision `fd18c4b0bc1e8a4a375b8ce96445d87252ed0bc1` and its `src` tree `2f3e868d96bc4de45202690fbbf9b1a36d687bf0`. Both bracket controls and all twelve author, reopen, and edited-reopen phases passed in fourteen distinct native processes. Both reopen phases report zero errors and warnings. The oracle was SOLIDWORKS 2026 SP05.2 `34.5.2.0604`, executable SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.

The [guarded receipt](../measurements/2026/ThinRevolveArchiveRead01.json) pins the controls, file and phase digests, codec changes, actual map indices, and half-open object spans. The edited saves are separate derivatives identified by the corresponding digest in each original reopen receipt. The packet is disclosed discovery evidence and adds zero held-out results.

## Typed layout closure

The [thin feature and specification](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/RevolveFields.py) use the [SP05.2 serializer and virtual evidence](ThinRevolveArchive2026.md). `moRevolutionThin_c` has schema 1 and composes the ordinary revolution base before `f8f0`, an actual `moThinSpec_c` reference. The thin specification's inherited ordinary object base consumes zero bytes. The following body fields are in wire order.

| Field | Encoding | Observed value or owner | Present knowledge |
| --- | --- | --- | --- |
| `f08` | Object reference | Distance display through handle and model dimension to `D3` | Live first wall input |
| `f10` | Object reference | Distinct distance display through handle and model dimension to `D4` | Live second wall input in unequal mode. Persisted latent owner with zero value in the other three modes |
| `f2c` | i32 | Zero | Native cap-ends switch. Only disabled state measured |
| `f30` | f64 | `1e-7` | Native end thickness, unrelated to the live wall edits. Initial C++ value is `-2.0`. Saved producer or default still needs proof |
| `f38` | f64 | `-2.0` | Same as the native initializer. Semantic role and active domain unverified |
| `f28` | i32 | `0`, `1`, `2`, `3` | First-side, opposite-side, mid-plane, and unequal two-side wall input. Matches the registered API enum in the four contrasts |
| `f40` | i32 | `1` | Static thin constructor supplies one for this call. Alternate states unmeasured |
| `f48` | Object reference | Null in original saves. `moDisplayRadialDim_c` with a `ThreeDRadiusDim_c` and zero-length `D7` in edited saves | Native lifecycle state. Zero `D7` is outside the editable source inventory |
| `f50` | i32 | Zero | Native add-bends switch. Only disabled state measured |
| `f54` | i32 | Zero | Native initializer agrees. Semantic role and active domain unverified |

Both distance references are populated in all eight files, with no shared display, handle, dimension, or parameter. The positive wall values are the metre values at `moLengthParameter_c.f58`. Mode 2 stores the full wall in `D3`. Its display endpoints are at plus and minus half of that value from the open profile. Mode 3 independently edits both positive wall parameters. The wall placement changes sign in mode 1 and stays distinct from angular reverse `f824`. For this disclosed Front frame, positive wall side is the direction of increasing local X.

All four source geometries have exactly one open profile line and a separately selected construction centreline. The two lines have distinct adjacent endpoint pairs. No sketch relation, value dimension, or closed region is present. `f830` resolves through the self component to the actual sketch and construction line. `f8d8` retains the ordinary single-direction angular end with `f08=1`, `f0c=f10=0`, `f18` pointing to live `D1`, and null `f20`. The feature retains the thin kind `f828=5`. Its actual `f528` atom is a backreference into the configuration map.

## Saved face references and radial display

On the pinned `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, `moThinOffsetSurfIdRep_c` vtable `0x4cf6b5b0` uses slot `+0x28` target `0x4bbaa6a0`. The shared surface-ID base precedes its i32 `f38`. `moThinClosingSurfIdRep_c` vtable `0x4cf70b08` uses the `+0x28` wrapper `0x4bba41f0`. It calls the same common base `0x4bba8790` then tail-dispatches through `+0x2a0` to `0x4bbabc20`. That tail calls the signed 32-bit archive operators for `f38` and `f3c` in both directions. Instruction digest for the wrapper span `[0x4bba41f0,0x4bba421f)` is `ebfc877dc8888646c253cbae52aaaf7e3e099d0bc92796b081bce9c8094593ec`. Tail span `[0x4bbabc20,0x4bbabc92)` is `a8826edfe74ba28eb8a4468e38d6c3c0ac3b306c2a0d7986ee293f105b39772a`. The identified vtables and top-level entries also match the [bound serialization map](../../data/Serialization/SerializeMap2026.json).

Each save contains two offset and four closing instances at `moFaceRef_c.f10[row].f08`. The paired face references reuse these exact six allocated instances by identity. Each keeper's `moFR_c` points to the actual persistent feature ID through its typed `f10` key. All six share one external self-document owner in the default configuration. `f38=2` for each offset ID and `(f38,f3c)` is `(0,0)` or `(1,0)` for the closing IDs in this one-line family. These measured numbers do not establish a general surface-index generator.

The post-edit radial display is a different branch. `ThreeDRadiusDim_c` vtable `0x4d18aa60` binds its schema to the same `0x4c833f00` feature-dimension body already used by the distance model dimension. `moDisplayRadialDim_c` already has a typed layout. No actual `moRevolvedRadiusDim_c` occurs in these eight saves. [Radial display lifecycle](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Revolve/ThinRadiusDisplayAfterEdit.md).

## Reproduction and scope

Use the four-case disclosed `Capture` directory and an unused report path.

```sh
python3.14 -B re/tooling/sw2026/revolve/ThinArchive/AuditThinArchive.py \
  --capture /absolute/path/to/disclosed/Capture \
  --report /tmp/ThinRevolveArchiveRead.json
```

Each of eight host processes checks its input digest and the verified native phase observations before installing an external-access guard. The shared SDK links actual ModelHeader, Config-0, CMgr, and ResolvedFeatures inputs, then re-emits the two fully decoded Config and Resolved streams in memory. All sixteen are exact. The Config counter remains 109. On this corpus the Resolved counter is 279 at initial save and 287 after edit. Every ordinary revolve projection still refuses the unqualified feature, and newer schema words, thin cut, and the unrelated revolved-radius class remain unregistered in this part context. The probe launches no CAD process.

Construction needs the signed open-profile ownership, independently generated display geometry, and constructor evidence for the remaining scalar states. Saved face references require their own generation rule or independently demonstrated neutral omission. A later generated native acceptance trial must compare the editable tree and numeric geometry against the separately pre-writer locked sources with healthy controls. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).
