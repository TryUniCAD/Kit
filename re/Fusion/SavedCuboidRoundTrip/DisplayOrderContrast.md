# Saved cuboid history and display order contrast

This experiment isolates the physical history order finding from
[PR #303](https://github.com/TryUniCAD/Kit/pull/303). The generator examines
persisted typed JSON and resolves the modeled body's zero-LOD edge and face
bounds to geometry roles. It then regenerates the history with each role
in the graphics traversal order. An old-to-new index map updates every
typed ASM entity reference. Both candidates reconstruct the source model
and differ in one history member. The source archive is used separately to
compare the original physical roles and is not a generator argument.

Windows Python 3.14.6 and SDK base `78f3d6d16cf85388408bf01a8b94e43d4318240d`
produced these candidates. The baseline was regenerated in a separate
process and both complete archive hashes repeated exactly. The 28.3 mm
case is an already vendor-edited source, so it does not prove offline
height editing. Both cases reproduced the source physical edge and face
role sequences. Canonical emission reproduced neither sequence. Both
archives in each case passed complete typed and strict neutral equality.

| Source | Source SHA-256 | Canonical SHA-256 | Display-ordered SHA-256 |
| --- | --- | --- | --- |
| 13.8 mm baseline restored | `b6726c11bd4e67155035de7fc6bcda3b559682fc9c4f496c2b35a05d84184752` | `c05251997755d8c68a0e8ba14db5ccf248a6ca5b1a610434f51a9801b4d0ce32` | `d2ec7841e93ba6ce0cd3376119fbf63722b7e90d899f20e04775186e0a86687d` |
| 28.3 mm native edit | `1e7584c59f898b41af2ea3d5accf0c5c44e793bcd0ab7c5486a08feb55443aa2` | `3d1d056e5f263e414759eae82f0f869bd22b6867cc5fdcc02cc5bc0851bbe3e5` | `177d724b62355f2e1db4950131f68d6a909fef1ae623aa1fd95cb853fa0626c3` |

The unrelated historical independent holdout control `850b1a76…` has no
unique solid world selected by the expected body link. The probe refused
before generating a candidate. This is a research scope refusal, not a
reader defect or an acceptance result.

The baseline ordered archive is staged in an independent before/candidate/
reopen/after geometry bracket using the existing
[replay preparer](../LocalOracle/SavedCuboidRoundTrip/README.md#replay-an-existing-native-candidate).
The already measured canonical candidate does not provide acceptance for
these new ordered bytes. The geometry bracket alone also does not resolve
role picking, per-face styles, or presentation parity with a same-style
independently authored reference. A distinct native face appearance and a
fixed-view comparison before rebuild must resolve whether this physical
role order matters to Fusion. Keep public writing disabled pending this
and the other saved-source writer requirements.

## Height-edit leaf bounds

[InspectHeightLeafGeometry.py](InspectHeightLeafGeometry.py) regenerates the
18 zero-LOD bounds from the analytic target prism frame. The bounds are
derived from each leaf's solved topology role. A height edit changes the
bounds without moving the other typed leaf fields to a different role.
The isolated predictor takes strict persisted JSON and the frozen target
height. It refuses native-archive opens. The parent process opens the saved
native control after the predictor finishes and compares role-bound boxes.
A graphics re-encode/re-read verifies the typed result and unchanged
non-world streams. Original leaf bounds fail the changed-frame check.

| Input | Saved control | Target height | Generated world SHA-256 |
| --- | --- | ---: | --- |
| Baseline restored `b6726c11…` | Baseline edited `1e7584c59…` | 28.3 mm | `d1d18df433b7d2213e22b69159aa398678823b0c72849863607962814528510c` |
| Baseline edited `1e7584c59…` | Baseline restored `b6726c11…` | 13.8 mm | `8fb1caba4044ecfffe1bbbfeb35dcad46c11353c3ee16663e82cf42e6ab9b6dc` |
| Independent restored `7a4d4a4a…` | Independent edited `71c13916…` | 29.5 mm | `aa139ff561b7509ab615950e45b05f0f8ef591d1d4120399333d9a2d15b76e47` |

The baseline pair is in the checked-in corpus. The independent pair is
from PR #307's earlier post-freeze native batch. Every role, bound and
order matched in the three comparisons. The historical negative control
`850b1a76…` refused on the unique live graphics owner check.

The experiment updates leaf bounds only. The preserved aggregate model
box can differ from the target capture, and all three inputs contain
one distinct face attribute set. Full graphics generation, per-face
presentation, picking and the fresh native acceptance bracket remain open.

## Source-free body scene contrast

The `GenerateBodySceneContrast.py` probe reuses the exact #337
modern material and appearance generator, plus #307's structural
graphics grammar. The scene derives edge and face bounds from the
solved prism. It uses the physical history slots and actual extrusion
body reference, with a separate scene-local handle. Only one typed
graphics world is added. Complete strict document and neutral
readback verify that the added world leaves the other typed fields
and authored graph intact.

The requests were frozen against `d49614c7f15b092b645a25d4467d005f009fd1fd`
before scene generation. The manifest SHA-256 is
`a755dee9fcc81e3951771dfb424cf89ac719f33f40a43cab2fb84c13d148e380`.

| Request | Dimensions in mm | No-scene control SHA-256 | Generated scene candidate SHA-256 |
| --- | --- | --- | --- |
| Baseline | 24.625 × 16.375 × 8.875 | `40a748922a067f81370e1ffd99049a8cfa19d78340e617e48e5409a6d3c6a5a0` | `11ea093d009775708bfc48eb28d7ee792b0a52d41f0d00f9ae796917be4b6c89` |
| JSON height edit | 24.625 × 16.375 × 19.125 | `50b230df4802cf9c21f823aaa2e27ec84fae0a1acadbd223f1b575f3653a5774` | `37826d503ac08c16a39bf437cd263f3e488ef237104dfe20814f80397a90b0e9` |
| Independent authored request | 12.375 × 44.625 × 33.875 | `c8acf380c4dedd7d23bc783408f98d8153c5322ce438908e88daca6fcf5ced40` | `d44600455c283ce2d87e5ccc561fa480edba51474e04c0bd607518ffc311c9b5` |

Each variant retained the three-root snapshot, named parameters, one
camera, empty configuration envelope and distinct directly owned
modern material appearances. The #337 appearance preparation still
refuses documents carrying graphics. The new probe compares the
complete typed state and strict neutral projection across the isolated
scene addition. The generated zero-LOD scene remains structural. Native
style inheritance, role picking, full saved scene, preview regeneration
and proprietary application acceptance are unresolved.

## Strict SDK JSON height edit

The research command [RegenerateSdkHeightEdit.py](RegenerateSdkHeightEdit.py)
consumes the public reader's persisted JSON after changing one independent
height driver. It first decodes the original typed state, reprojects its
neutral document and checks that the only neutral mutation is the driver's
positive millimetre literal and matching value. The source request's scoped
projection omits graphics from extraction. A separate full-source
regeneration must match the complete typed state including graphics,
all other neutral semantics and the original archive digest. If the
projection omits any source information, this comparison fails.

The source-free edit from `riseGauge = 8.875 mm` to `19.125 mm` used
the baseline archive digest `11ea093d009775708bfc48eb28d7ee792b0a52d41f0d00f9ae796917be4b6c89`
and edited JSON digest `160fd8dacbbbb70ccca8056e4d054bd4db19767087a925807d63ac8ef82b9274`.
The output matched the already frozen exact native candidate
`37826d503ac08c16a39bf437cd263f3e488ef237104dfe20814f80397a90b0e9`.
The emitter did not read native archives. The exact preflight also
verified the registry and direct writer preserve an existing pathname,
a missing parent directory and caller stream contents on refusal.

Public registry staging can create directories before writing. Require
complete source qualification, edit validation, full re-read and exact
native receipt verification before this point, and before the direct
writer mutates a caller path or stream. Keep the broad read-only guard
for other saved histories. A scoped candidate needs independent control
comparisons for authored and rebuilt geometry, history, material and
appearance assignments by role, picking, viewport and previews. The #318
native snapshot receipts cover three earlier archives without these
generated graphics bytes. No receipt is inherited from them.

### Face assignment observations

The instrumented native control demonstrates why
[appearance IDs alone are insufficient](../../../Documentation/Gotchas/Conversion/Fusion/Api/FaceAppearanceSourceIdentity.md).
The older contrast stopped before capturing a styled archive. In the
instrumented repeat, only the top face had the requested RGBA and
`FaceAppearanceSource`. Fusion returned the same appearance ID for the
copied finish and for the five inherited assignments. The diagnostic
archive was saved with the control marked unqualified because the
local checker had expected a different API source enum.

The diagnostic top face's typed journal prefix points to a
`NEUTRON_Material_attrib_def` record. That record refers back to the
same face. Its UUID is the exact key in the live Design body's
`faceVisualMaterialByAttrTagID` map. The map value resolves a visual
asset through the body's material manager. The [older independent cut
control](../Reconstruction/BoundaryCuts/Findings.md) carries the same
reciprocal links. The plain cuboid has an empty face assignment map.
These observations establish the binding in two sources. The public
journal reader at the time refused this attribute family. The field grammar,
fresh allocation and full graphics role correlation require the
other controlled face case and a fresh native bracket.

The corrected controls captured all three independent documents in Fusion
2706.1.17 with zero documents at entry and exit. Their receipt SHA-256
is `828b9f5dc89e82e48a10180e819e6082d6980066076d890073a8aa2651a89579`.
TopRed and WrongFaceRed changed only positive Z and positive X,
respectively. Both applied RGBA `226,29,41,255` in the Protein
asset's `metal_f0` property. The face journal, Design map and graphics
leaf named the same asset through the typed joins. Both graphics leaves
use a `FProteinEffectAttribute` in a kind-2 attribute set with flags
`0x20`, priority 3 and ties enabled. Repeated top-face controls and the
side contrast allocate different UUIDs and asset IDs. Those slots,
IDs and qualifiers are evidence and do not act as writer constants.
The renderer produced distinct images, but fixed-view metrics, picking
and extended property measurements remain open. Extended inspection
failed unit validation in all three controls.

### Observed Design owner record

The two controlled cuboids above and the independent cut each contain one
622-byte Design `VMBrepRef` v0 group. The plain cuboid has none.
The Design codec now reads the feature reference, typed visual material
and UTF-16 face tag followed by the existing `BrepRef` lineage. A
separate `ManagedEntity` continuation supplies the parent reference.
Both groups re-emitted byte-identically for all three styled archives.
The four-source verification report SHA-256 is
`765c0537b5021e23986fe2c5be6cf0bbd906b3d9e3de6896195d063e65d5ad6d`.
Matching serialized values in the associated typed records establish the
following observations.

| Observed byte offset | Cross-checked field |
| ---: | --- |
| 1, 28 | Immediate feature and Protein asset manager references |
| 43, 119, 199, 297 | Asset identifier, library identifier, inherited alias, face-tag UUID |
| 372 | `ASMRecipe` link to a v3 `BoundFaceRecipe` |
| 390, 466, 538, 542 | Scope asset, component persistent identity, scope type and segment |
| 555, 596, 610 | `DcBody`, status and reciprocal dynamic update references |

The cut separates the immediate feature from the body producer. Both
coincide in the cuboids. The dependency graph tracks them with separate
edge roles. The inheritance and existing codecs give typed owners to every byte. Compute and dependency joins
remain required at the strict semantic reader boundary. Generation from a neutral appearance request remains open.

Before implementing further rules, two geometry holdouts received frozen
style intents. The manifest SHA-256 is
`19617ea0a0603a39fbc0831a427362795f621e9e957616ab9234a071dd77b298`.
The first retains the negative-Y face at RGBA `37,181,89,255` while
changing 21.75 to 48.825 mm. The second retains the positive-X face at
RGBA `108,47,211,255` while changing 29.125 to 15.675 mm. Four
experimental archives regenerated the journal and typed material and
scene joins, retaining all written semantic fields on typed reread.
They remain in private scratch. The typed Design reference still has
no generative rule and the body-scene baseline stopped during Fusion
import. Neither result establishes native writer acceptance.

The exact graphics and no-graphics baseline archives have identical
existing member bytes. The graphics variant adds only
`OGS.BlobFolder/OGS/DefaultScene/world`. The minimal world has no leaf
links or mesh records, while the independent native control has 18
linked, mesh-bearing leaves. The starting control passed and the candidate stalled in archive import.
The scheduled closing check stopped before opening a control because
the candidate receipt had no completion field. A fresh independent
control for the same batch restored and closed successfully, with
receipt SHA-256 `6d2fd08992dd10295bd71f8d379d73c1fe6de51f57432a97f3cbbae4db3d4831`.
The candidate published no measured acceptance.

### Fixed-corner line plane normal

The native holdout capture completed on Fusion 2706.1.17 with
healthy controls before and after. Capture receipt SHA-256
`3b11510fe94c7138428c2ca2f3f9597f3b18d224731818c41687bdf232393a24`.
The original frozen probe, at `bccdb7562b`, recovered matching
history and graphics order in both edited saves. The two initial
saves have no unique graphics world linked to the live body. This
qualification refusal remains. The report SHA-256 is
`461e9c4ae2de644f41b351e97e7733716e9f52245c98027e97142b85ddc79041`.

The unchanged reader refused all five newly captured archives before
it reached the qualifying geometry. They store positive Z on every
line. The existing `BaselineRestored.f3d` stores negative Z.
All cases have identity support and sketch matrices, no matrix Z
inversion, strictly counterclockwise signed area and saved endpoints
in the XY plane. Each carrier normal is perpendicular to its own
saved tangent. The [plane sense evidence](../../../Documentation/Gotchas/Conversion/Fusion/Sketch/FixedRectangleLineNormalSense.md)
keeps Z sense distinct from the sketch support and ordered profile.
Basis comparison SHA-256
`3cb5e8caca05ecee83f7d7114931f07c296d50e7a1ae2a045f46730ee21e3357`.

After the scoped reader change, all five native saves retain complete
typed state through strict SDK JSON. Volumes match the native
measurements within the declared reader tolerance.

| Native case | Archive SHA-256 prefix | Native volume in mm³ |
| --- | --- | ---: |
| Independent control | `efe3f8e0` | 4736 |
| A initial | `017fe8bc` | 10190.473125 |
| A edited | `67117fef` | 22875.8551875 |
| B initial | `f7b3c04f` | 14557.94921875 |
| B edited | `1802ab75` | 7835.05078125 |

Changing one normal to the opposite sign or every normal to a
different axis refused before a neutral result for every source.
SDK verification SHA-256
`3472c925059f5732f391def16d13cb1121c5884fd49d638e2a2c50fad69e10ef`.
The result establishes readback of these saved geometries. The
writer still needs native acceptance of exact independently
generated archives.

### Native scene omission

The frozen same-source request SHA-256 is
`566d85d4fca7a59b177712fdf8e1f6ec64113395c02d4ac6c1aedca3244c928c`.
Repacking changes the archive envelope. Omission additionally removes
only `OGS.BlobFolder/OGS/DefaultScene` and its parent directory entries.
All retained member contents match the original. Each archive ran in
its own Fusion 2706.1.17 process with zero documents at entry and exit.

| Variant | Archive SHA-256 prefix | Observation SHA-256 |
| --- | --- | --- |
| Original | `ee2a2beef5a5` | `3d3112e6a07f0c68588098d69611bc62f55aeacbe039d564234148ea0cb6f425` |
| Repacked | `f6f17020a92d` | `b666f6bccc40aad0c5296333dd70ca8f9cbf1cfc3a22079e924909e1de52ce68` |
| Without OGS | `067f4fb66a23` | `0338a5292446f5d013401f23f869ba3fbc91e5108891a47b45ed09e54aa0c68d` |

The loaded camera, body and sketch visibility, material and all six
face roles, appearance sources and colors matched both controls.
The positive-Z face retained its native override and RGBA
`226,29,41,255`. All three loaded images had SHA-256
`0c109cf8b810ba254a8bc1073f54a2eaaa0f2d49e464eb562b389af1e681120b`
before viewport intervention. All three rebuilt successfully. This
comparison leaves actual viewport picking, archived previews and
native lifecycle for independently generated archives open.
