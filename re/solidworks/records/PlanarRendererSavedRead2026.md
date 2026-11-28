# Disclosed planar renderer native-save readback

Workstream `B04-SW2026-MATES-PLANAR/source-root-projection`, post-save observer owner `format_proofs`, native owner `/root`, delivery PR #121. This supplement uses only the disclosed A20 and A21 generated pairs and the native saves tied to those pairs. It adds no native launches, held-out credit or whole-source admission. [Paired native method](PlanarRendererNativeMethod2026.md) · [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

## Original result and saved inputs

SOLIDWORKS 2026 SP05.2 `34.5.2.0604` ran eight distinct processes, including healthy A22 bracket controls, with 834 numerical checks, zero open errors or warnings and no dialogs. Both cases passed the native paired tree, geometry, edit, save and fresh reopen comparisons. The original aggregate still has `passed: false` because both SDK saved observers stopped at the generated parent context-order check. The immutable `Inspection/Result.json` SHA-256 is `215f24271caf6c3289cc56ae12f4f8e02b45d98b01329ec61b309a16b7b184e1`. The packet SHA-256 is `a8776d5de20ee7c691cb088a5bb589944ef0c24bf7e57b908b7d088177be989c`. The executable SHA-256 is `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.

| Case | Native-saved parent SHA-256 | Native-saved child SHA-256 | Edited depth |
| --- | --- | --- | --- |
| A20 | `aef71584722bd0bb6a054b07b753b391dbc603bac04e3d92fa01db7fdeeab1a2` | `f075a2a4d8a1fb432576c2f4e489c75cc38c0f10e36fbc6b8f4c4b118217f2ac` | 16.375 mm |
| A21 | `1ad8fc0aa67936b4961b7fc5d4231331edd831992c9157ae6b95a7715cfcf907` | `2c5fe2dedef2b41a3763569618cb3da64cfc698a861126c8a234dc252c6358e8` | 23.625 mm |

The frozen writer revision was `6c48ec66ba5b8a2ff75a4920bf414d988399a267`, with `src` tree `13d50879fea6470271c7a9b79e5a48a1168d8d35` and zero runtime writer file reads. The new replay uses base `fb3efea12dab0d19dd7cc9a0b37be5d9007f336d`, unchanged `src` tree `5bb76b33b5faafcb15a2f18289e005ed7e9e157f`, and the supplemental tool digests. Each fresh isolated SDK worker verifies the saved child was persisted at update stamp 158 and opens at that stamp. The separate explicit native rebuild advances the loaded child to 172 with both saved file hashes unchanged. [Original preflight](../measurements/2026/PlanarRendererNativePreflight01.json) · [Rebuild stamp ownership](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Assembly/AssemblyRebuildCanAdvanceLoadedChildStamp.md)

## Parent occurrence contexts

Both parent `Contents/VisualStates` graphs re-emit exactly. The complete typed comparison, including graph aliases in both directions, shows changes to two fields in each detached occurrence context. `moContextChainComponent_c.f30` changes from 203 to 101 while the linked live `moReference_c.f3f0` stays 102. The nested `moContextChainComponent_c.f40 → moExtObject_c.f58` changes from 0 to 8. All target persistent IDs, six independent slots per occurrence, pooled file identities, shared visibility attributes, and reverse occurrence ordering remain consistent.

| Case | Occurrence targets in wire order | VisualStates bytes and terminal map | Parent f30 byte offsets | Nested f58 byte offsets |
| --- | --- | --- | --- | --- |
| A20 | 25, 24 | 1489, 38 | 590, 995 | 637, 1025 |
| A21 | 26, 25, 24 | 1677, 44 | 586, 991, 1183 | 633, 1021, 1213 |

The five nested flag changes agree with the independently studied version-19000 external-reference flag normalization. This comparison establishes the actual saved `f30` state for the two disclosed pairs. Its producer and the general applicability of the reset still require evidence. The constructor equation and its default observer stay in force for frozen generated files. [External-reference flag normalization](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ExternalReferences/ReferenceFlagsNormalizeOnLoad.md)

## Child density, renderer and labels

Both saved children contain the previously absent `moPart_c.f1420` material owner. The physical `Config-0` window is `moMaterial_c` slot 51 at `[2868, 2945)`, with `f08 → moDensityParameter_c` slot 53 at `[2886, 2945)`. The parameter holds `f58=1000.0` and `f68=0`. The actual selected configuration keeps `fc50=-1.0` and the assigned material rows remain empty.

Each child `Contents/VisualStates` remains byte-identical to its frozen version, with length 1789 and terminal counter 26. Each saved `Contents/Definition` re-emits exactly. The live model and selected configuration keep distinct appearance objects sharing one numeric ID. Those two objects differ only at the RealView low word `f20.f90.f00`. The detached holder keeps its separate ID, renderer payload and resource alias. The shared renderer constructor projection matches all mapped appearance values. The independent Definition manager records the next live appearance ID.

| Case | Frozen model / configuration / holder | Saved model / configuration / holder | Definition next ID |
| --- | --- | --- | --- |
| A20 | 11 / 11 / 10 | 14 / 14 / 10 | 12 → 15 |
| A21 | 12 / 12 / 11 | 15 / 15 / 11 | 13 → 16 |

The original generated allocator-retention predicate still fails for both pairs. The exact two-case transition does not establish the general allocation rule. Both saved sketches keep the actual width and height label owners through D1 and D2, with zero differences under the existing label comparison against the original and frozen child. The strict SDK read summaries match the original and frozen controls, including the existing informational `sldasm.native_record_unresolved` diagnostic. Both saved pairs account for 26 exact linked core stream replays. Strict ordinary Definition refuses the alternate renderer and whole-source assembly writing refuses unprojected model content. Full strict saved readback remains unqualified.

## Reproduce the supplement

Use the disclosed completed packet on the host. Each worker reads the frozen and saved pair locally, with no CAD runtime imports. The result contains checksums, typed windows, count and alias evidence, and no source paths. The packet remains unchanged.

```sh
python3.14 -I -B re/tooling/sw2026/planar_registry/ProvePlanarRendererSaved.py \
  --packet /absolute/path/to/PlanarRendererNative01 \
  --output /new/path/PlanarRendererSavedRead01.json
```

[Guarded saved comparison](../../tooling/sw2026/planar_registry/ProvePlanarRendererSaved.py) · [Typed parent and child delta checker](../../tooling/sw2026/planar_registry/PlanarSaveDelta.py) · [Sanitized saved-read receipt](../measurements/2026/PlanarRendererSavedRead01.json) · [Save lifecycle gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Assembly/PlanarRendererSaveChangesVisualOwners.md)

## Matched save behavior on both original pairs

The original-only resave gives both parent contexts the same
`f30` change from 203 to 101 and the same nested `f58` change from
0 to 8 as the generated saves. The live occurrence word remains 102.
The relocated original parents also split a shared name handle so
the stored assembly title can coexist with the earlier `Assem1`
name. Each split adds one map slot and accounts for the only other
typed parent difference. The generated parents already own their
final names.

The two original live child appearance IDs and their Definition
cursors advance by three. The detached holder and complete child
VisualStates stream stay fixed. The original child already owns
the default physical density, which remains unchanged. This
matches the independently decoded generated save behavior for those
rendering owners. The previous strict result remains recorded
alongside this disclosed comparison.
[Original native resave](../measurements/2026/PlanarOriginalNativeResave01.json) ·
[Offline typed original comparison](../measurements/2026/PlanarOriginalAllocationParity01.json) ·
[Relocated name owner](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/ResavingRelocatedParentSplitsNameHandle.md)

```sh
python3.14 -I -B re/tooling/sw2026/planar_registry/AuditPlanarOriginalSave.py \
  /absolute/path/to/Oracle121Takeover \
  /absolute/path/to/Oracle121Takeover/PlanarRendererOriginalResave02 \
  --output /new/path/PlanarOriginalAllocationParity01.json
```
