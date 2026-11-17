# Native partition load and body ownership on SOLIDWORKS 2026

The generated cache-bearing child opened standalone with warning 32, a rebuild flag and zero solids on `34.5.2.0604`. One explicit rebuild recovered the solid and its six extrusion-owned faces. Opening the identical parent with this child also returned warning 32, although the first component inspection already reported a solid and clear rebuild flags. The standalone result localizes the failure to child load or initialization. The exact kernel or attachment predicate remains open. [Follow-up native receipt](../measurements/2026/GeneratedPrismPartitionNative04.json) and [2026 warning enumeration](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swFileLoadWarning_e.html?id=3b36a39206d34f468a0d2c24bef11595).

## Frozen archive evidence

Both generated children have identical pre-existing streams. Their model headers have update counter `f40=101`, body counter `f44=101` and time `f48=1794700000`. Configuration `f860=101`, model geometry stamp `f1300=101`, and the corresponding `CMgrHdr2` rows agree. The unchanged parent references this exact child path and has occurrence `f3e0=101`, `f3e8=1794700000`, and `f3f4=101`. The clean earlier native open reported child API update stamp 116. That is observed runtime state after loading, so the absolute difference from the persisted 101 also occurs in the passing lane. [Reference stamp field ownership](AssemblyConstruction2026.md#reference-update-state-after-insertion).

The experimental child has one `SCH_1200000_12006` partition with neither an accompanying delta payload nor the selected SOLIDWORKS body attributes. Native L1 and the synchronized A13 child have `SCH_3701250_37102_13006` payloads, a partition followed by deltas and separately bound body attributes. In each native partition, named attribute definitions resolve through typed pointers to positive integer values on the same body owner. Rows in this table describe observed source data for diagnosis.

| Native witness | `ATOM_ID_2001` | `ENT_TIME_STAMP_2001` | Model header `f44` | `LAST_BODY_MODIFYING_FEATURE_ID` | Real extrusion `f08` | `BODY_MATCH` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| L1 part | 101 | 105 | 105 | 34 | 34 | 1656 |
| A13 child | 101 | 107 | 107 | 34 | 34 | 599 |

Both reads find null pointers in the two `BODY_RECIPE_2001` fields. The `BODY_MATCH` variation occurs with the same rectangle dimensions. The timestamps and last modifying feature follow their observed header and feature owners. The atom allocation, match ID, delta construction, and general attribute legality still require proof. [Archive projection and exact hashes](../measurements/2026/GeneratedPrismPartitionOwnership03.json).

## Loader observations

The pinned model DLL is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` at preferred base `0x4b140000`. REA inspected the PE resources under `ev_7fc3ecfa02cbbd7d6067ca5c370b778582e5ddc85ae1940285a50b90bfc6ceec`. Hopper resolved procedures and callers against the saved model analysis. Exact original PE instructions, IAT targets and code ranges were checked with LLVM. The saved Hopper model window was closed after inspection.

| Owner or edge | Observed behavior | Confidence |
| --- | --- | --- |
| Part primary vtable `0x4d1252d8 + 0x1a58` | Resolves to `0x4c1b7600`. Its call at `0x4c1b7722` loads a named partition through `gcPartition_w::loadFromStorage` in `sldgcu.dll`. The routine reads the outer storage version first. | Confirmed vtable, PE call and IAT |
| Successful partition result | The pointer is tested at `0x4c1b772b`. With a configuration present, stores at `0x4c1b7764`, `0x4c1b7785`, and `0x4c1b77b4` update partition name `f970`, outer archive version `f990`, and ghost partition name `f980`. Exported getters/setters verify the member ownership. | Confirmed static |
| Assembly dependency update | Child update and stale-reference queries occupy separate walker paths. Their in-memory inputs include the resolved child model and stored reference state. | Confirmed static edge, public warning producer open |
| Separate partition restore entry `0x4c244290`, call site `0x4c243d30` | Attempts `gcPartition_w::restore` and delta restore, gets bodies, cleans attributes and sets model ownership. Reads body time stamp at `0x4c24439e` and atom ID at `0x4c2443de`, then calls `replaceBody` at `0x4c244402` only if atom ID is positive. | Confirmed for this restore helper. Invocation on the failing open is unmeasured. |

The body-restore helper establishes that native geometry attachment has an ownership step beyond geometric deserialization in this path. The normal open caller and kernel read result in the failed lane remain unobserved. The kernel transmit schema is distinct from the outer archive version stored at `f990`. [Existing warning-path map](AssemblyRebuildDecision2026.md) and [existing codec provenance boundaries](LegacyParasolidEmission2026.md).

## Measured open and rebuild states

The follow-up compared all four lanes at the original encoded paths with six distinct SOLIDWORKS process starts. Both bracketing controls opened, rebuilt and measured one solid with clean status. All trial opens returned zero errors. Each available solid had six faces owned by `Boss-Extrude1`, volume `8e-6 m³`, surface area `0.0028 m²`, and centre `(0, 0, 0.005) m`. The geometry queries left the observed stamps and rebuild flags stable. [Verified native receipt and source hashes](../measurements/2026/GeneratedPrismPartitionNative04.json).

| Input and open route | Open warning | Child solids at first inspection | Child rebuild flag | Child stamp after open → after explicit rebuild |
| --- | ---: | ---: | ---: | --- |
| Cache-free, standalone | 0 | 1 | 0 | 116 → 130 |
| Cache-free, through parent | 0 | 1 | 0 | 116 → 130 |
| Cache-bearing, standalone | 32 | 0 | 1 | 102 → 116 |
| Cache-bearing, through parent | 32 | 1 | 0 | 105 → 119 |

All four explicit rebuilds succeeded and ended with one solid and a clear rebuild flag. In both direct parent trials the parent's own flag was already clear at the first inspection, with stamp 103 before the explicit rebuild and 104 afterward. The cache-bearing child was available and had its owned faces by the first component inspection in the warning-producing parent open. The cache-free child's first standalone stamp of 116 also matches the recovered standalone stamp of the cache-bearing child. The first native comparison had stopped immediately at the parent warning gate. [Earlier comparison](../measurements/2026/GeneratedPrismPartitionNative02.json).

## Follow-up diagnostic

Use `python Tools/InspectPartitionOpen.py Job.json` from the external `NativeCacheOpenDiagnostic02` deck through the pinned Windows oracle transport. The unchanged job stages both exact child variants one at a time in `C:\Users\Public\Documents\KitOracle\GeneratedPrismPartition-6c31\Active\L1Single`. The parent filename, encoded path, and bytes are identical. Each variant gets a fresh standalone child open and a fresh direct parent open. The runner uses the same normal open flags as the first comparison, records warnings immediately, and continues observation after warning 32. It records update and rebuild state before and after geometry queries and an explicit rebuild, along with body count, mass properties and earliest owning feature per enumerated face when available. The run uses normal document close, keeps original files immutable, and archives copies after checking their hashes. Two healthy controls bracket six distinct process births. [Probe source](../../tooling/sw2026/InspectPartitionOpen.py) and [face ownership API](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFace2~IGetFeature.html).

The follow-up measured an isolated child failure. Zero exposed bodies leaves kernel restore, delta processing and model attachment as separate possibilities. The successful explicit rebuild preserves the original warning in the record. Native cache qualification requires warning-free open, controlled edits and fresh reopen.

| Frozen diagnostic input | SHA-256 |
| --- | --- |
| `Job.json` | `f2a8d9415a7d8fc03a8e9a602b77223b6be3babbb9f00129a3a27eef1a3d0a49` |
| `SourceManifest.json` | `7ffb5ca85ebe10aa2291e23c66f18c1c35ccc03bcdeb92b85b63fdb1ebe93883` |
| `InspectPartitionOpen.py` | `4bdbb913f1cba294ee50cb029eb6769b2a9566f3a7ef38d0efb89406a97723c6` |

The receipt binds the committed runner at `068a45538d384950282dcc7edbada4d473e668f2`, its eight helper sources from `cade27adc947bf4ee8c615465798993eec111043`, and hashes for the private inspection and host transport records. The host transport records its confirmed exit separately from guest inventory. This diagnostic observes the original generated L1 pair and does not contribute to held-out results.
