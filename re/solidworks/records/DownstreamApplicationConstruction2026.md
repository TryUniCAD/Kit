# Application downstream initial assignment, SOLIDWORKS 2026

The actual executable `CAmApp` constructor explicitly assigns zero to runtime downstream-enable member `+0x464`. This closes the constructor assignment only. It does not establish the value after startup, preferences, callbacks or the already documented save activation.

Task: `B04-SW2026-DOWNSTREAM-ID-DATA`; owner: `/root/flag_ownership`; delivery: PR #121. This additive [numeric record](DownstreamApplicationConstruction2026.json) retains two complete functions, six instruction windows and actual RTTI spans. The earlier [save activation](DownstreamSaveActivation2026.md) and [standalone part store](DownstreamStandaloneStore2026.md) deliveries are unchanged.

## Exact original owner

Pinned `sldworks.exe` is 718,936 bytes, machine AMD64, version 34.5.2.604, SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`. Its complete constructor is `[0x140009a10,0x14000a892)`, 3,714 bytes, SHA-256 `7adf7bf6accbe54910736de23cd3962d2b2c8635af3adde94d64f793f9aab2c0`. Bounds use the declared PE exception directory and complete unwind group.

At `0x140009af0..0x140009afa` it installs primary table `0x14001cda8`. That table's locator `0x14001f740` identifies actual `CAmApp`, with subobject offset zero, type descriptor `0x14002a750` and valid self-relative locator. The earlier application-DLL candidate was the destructor; its refutation remains recorded in [save activation](DownstreamSaveActivation2026.md).

The constructor retains incoming `this` in RDI at `0x140009a44`, clears retained R15D at `0x140009a65`, then writes the zero R15 qword to `this+0x464` at `0x140009d9e`. The seven-byte store spans both runtime i32 `+0x464` and adjacent `+0x468`. The independently bound [getter/setter](DownstreamDateAndEnable2026.md) identify `+0x464` as downstream enable state. This is an explicit constructor assignment, not inference from a zero-filled image or captured CAD row.

The complete direct body contains no subsequent overlapping direct store. It performs later member initialization and a virtual call on embedded member `this+0x7d0` at `0x14000a7fe`. This record does not infer that arbitrary transitive callees, globals or later lifecycle owners preserve the value. Initial assignment and final observed runtime state remain distinct.

## Actual construction argument

Complete executable helper `[0x1400065e0,0x140006600)`, 32 bytes, SHA-256 `7312ed1c3beef1970ce7d1e6f8f307f941503e29c89b01d3909b826ff6a1e58b`, supplies static executable object `0x14002c510` and calls the actual constructor at `0x1400065eb`. No process was launched to inspect its later state.

## Kept boundaries

The save path can subsequently set the member to one under its actual part, setting and feature guards. A constructor zero is not permission to change a preference, disable cache generation or claim that a saved downstream stream is absent. The exact internal setting name, selected UI document manager installation, complete post-startup mutation history and actual standalone saved stream remain separate work. No populated-cache constructor or wire default follows from this application field.

Verification was original-PE hashing, declared-bound recovery, RTTI validation, complete LLVM body review and metadata/Markdown checks only. No CAD, COM, VM, preference or license change, saved CAD payload, hidden input, schema, codec, test or product execution occurred. No REA/Hopper target was opened. No vendor listing or binary is included. Native loadability, usability and held-out acceptance are not measured by this tranche.

The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) remain: “The first is success under every criterion on this page.” “The second is the end of the available context.” This bounded source checkpoint does not complete the CAD objective.
