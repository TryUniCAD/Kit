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
