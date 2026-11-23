# Assembly default motion study archive

Task `B04-SW2026-MATES-CONCENTRIC/default-motion` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). The typed motion codec covers a single inactive English `Motion Study 1` in the ordinary version-19000 `ThirdPty/Animator` member. The [receipt](../measurements/2026/D01AssemblyMotion01.json) binds twelve complete disclosed members, two model-generated variants, and the exact local module evidence.

## Binary owners

The opening version word starts an independent object map. In the ordinary profile the manager owns its inactive signed index and one filtered live study. Its zero-length extension follows the study body. The [previous cache record](AssemblyPresentationCaches2026.md) traces the default study allocation and records native omission for the earlier radial lifecycle.

| Owner | Scoped rule | Authority |
| --- | --- | --- |
| `moAnimationManager_c` | Signed active index `-1`. The unsigned object count derives from the actual study list. Its separate extension map is empty. | Store at `0x4ca29a9c`, filtered study object loop at `0x4ca29ae0`, and extension count at `0x4ca29d49`. |
| `moAnimKeyData_c.f0f8/f108/f110` | Wide display caption, braced uppercase version-four UUID, and empty wide secondary name. Independent generation uses the model-supplied UUID. The source reader retains the existing study's own identity. | Store at `0x4ca2735e` through `0x4ca27388`. The default constructor calls `CoCreateGuid` and `StringFromGUID2` at `0x4ca5843f` and `0x4ca5845f`, then assigns `f108`. |
| Study state | The native store writes the eight-byte word `f118` and binary64 `f128`, then component and attribute counts, signed `f1b4`, the flag word, and an optional viewpoint. The default study uses zero for both values and both counts, `-1` for `f1b4`, and a null viewpoint. The constructor initializes the two relevant flags, giving `4 + 2` in the stored mask. | `0x4ca2738e` through `0x4ca274e5`. The empty component key count is computed at `0x4ca26cfb`. The constructor initializes fields at `0x4ca57fc1`, `0x4ca57fc8`, and `0x4ca580f3` through `0x4ca58114`. |
| Solver and late state | Selected solver code zero, zero serialized solver entries, standalone scalars and empty collections in the native store order. `f0e8` and `f148` hold the constructor's binary64 `-1`. The bounded shape retains zero-valued state fields without admitting other solver and track data. | Solver selection and entry count at `0x4ca7abbf` and `0x4ca7abe0`, scalar and collection dispatch at `0x4ca274e5` through `0x4ca27646`, and the default constructor assignments. |
| Embedded `moAnimController_c` | The controller points back to the same study object, with zero tasks and its usual trailing signed word zero. The graph allocator emits the real object reference. | Key data controller virtual at `0x4ca27659`, controller `f08` constructor assignment at `0x4ca4a64b`, and serialization at `0x4ca4b42d`. |
| Extra holder | The measured store uses the enabled selector, one empty holder word, and the separate trailing scalar `f1c8` initialized to zero. | Outer session option `0x37d` at `0x4ca27662`. The actual holder runs the `0x31` option branch and emits zero at `0x4ca28c19`. Other option combinations remain outside the profile. |
| Caption directory | Observed at offset 308 in all twelve members. A canonical compact count of one precedes one wide CString identical to the one attached to the actual study. The source classifier checks exact consumption. The research candidate derives the count and text from its single generated study. | Complete byte comparisons establish the observed form. The independent native publisher of this terminal directory remains unresolved. |

The exact-build `sldmodu.dll` has SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Its PE identity was checked with REA evidence `ev_9bfcca546a90b1270c75953c6f6818fa1d10981d8b1e90a78e5bcd753506ae9e`. The bounded publisher search checked the disclosed `doccplu.dll`, `sldasmu.dll`, `slduiu.dll`, and `sldanimationengineu.dll` images. It found the generic third-party storage and motion XML entry points, and checked the related animation engine imports. The binary caption-directory writer remains unresolved. The recorded hashes and call windows allow the search to resume at the separate named-stream publisher.

## Guarded comparisons

The shared codec accounts for all 308 bytes of each native manager body and checks the following 34 bytes as the singleton caption directory. The types distinguish an actual study backreference from a numerical tag preset. A research-only composition reproduces all 342 bytes in twelve saved parents and confirms all three D01/D02/D03 edit pairs retain their study identity. Two independently supplied UUID4 values each produce a 36-stream D01 research parent. Both variants retain all 35 previous parent streams, the exact prior baseline bundle digest and the complete child. Two fresh workers agree with zero external accesses. Seven malformed settings and graph cases refuse.

Run from the repository root with the five exact licensed module images outside the checkout.

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01AssemblyMotion.py \
  --disclosures /absolute/path/to/Oracle121Takeover \
  --native-dir /absolute/path/to/licensed/modules \
  --output /tmp/UnusedD01AssemblyMotion.json
```

Ordinary assembly writing retains the exact prior 35-stream behavior. The research variants have zero new native launches or held-out credit. The terminal publisher and motion-study lifecycle remain open alongside lightweight, display, tessellation, preview and license-owned coverage for the full D01 source.
