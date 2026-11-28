# CString framing on SOLIDWORKS 2026

Status: **ordinary wire framing verified statically against pinned 2026 code; the new production primitive has not run**.
This is not native model, held-out writer or application acceptance.

## Identity and method

The build label is `34.5.2.0604` from the pinned manifest.
Both original module hashes were independently recomputed.
All addresses are preferred-image addresses in these exact files.

| Module | Bytes | Preferred base | SHA-256 |
| --- | ---: | --- | --- |
| `swccu.dll` | 252504 | `0x31a30000` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |
| `sldmfcu.dll` | 8274520 | `0x3c720000` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |

REA discovery found Hopper available for PE analysis.
Ghidra, IDA and Kuna were unavailable in that session.
The owned Hopper session inspected the exact `swccu.dll` hash and was closed afterward.
No CAD, VM, licensing, target code, codec or test executed.

Hopper supplied symbols, pseudocode and instructions.
Its procedure API does not expose complete body ranges.
Original PE runtime-function records therefore supply the extents below.
Their unwind records have no chained-function flag.
Apple LLVM 21.0.0 independently disassembled each exact original-file range.
Relative call operands and original imports resolve the actual call targets.
The accompanying JSON contains tool hashes, native function hashes, imports, call sites and REA evidence references.
No binary payload or vendor listing is included in the publication.

## Concrete 2026 boundaries

The `sldmfcu` IAT slots `0x3cb1d468` and `0x3cb1d470` import the wide CString read/write operators from `swccu`.
Their actual exported entries are `0x31a34100` and `0x31a34590`.
The [material/display record](MaterialDisplayArchive2026.md) already binds the PBR callers and their complete extents.
This record follows the primitive implementations rather than inheriting a 2025 address.

| Role in `swccu.dll` | Complete main function extent, end exclusive | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Wide CString reader | `[0x31a34100,0x31a34258)` | 344 | `82d5e52679cde6f04a4d3bb18c6910aad3982a2aa991025aeed10243c0337fac` |
| Wide CString writer | `[0x31a34590,0x31a346e8)` | 344 | `cb20f3695053bce787b0d1e40e89a9074913d8152acb6a4104e5a15f4a23d8d1` |
| Shared string length reader | `[0x31a37e00,0x31a37e64)` | 100 | `64088f680305b31935b117f780b3aa2db5eafc91161ce8c5a0745aead1b844a5` |
| Unsigned byte reader | `[0x31a34270,0x31a342cd)` | 93 | `e30b2af43e1fc68e7d3c480a748862b6f572271d86dee706b658171b9ce47e0d` |
| Unsigned word reader | `[0x31a342e0,0x31a34340)` | 96 | `55e86b83dbb8bdaff9cb98179060fcf76032fd58177fac7c3f7d090cb5e478dd` |
| Unsigned double-word reader | `[0x31a343b0,0x31a3440e)` | 94 | `d5329acf4b0e0d21145551775e655af6a85b63097addc5c22b4e327b59590c80` |
| Unsigned byte writer | `[0x31a34760,0x31a347b0)` | 80 | `3a117fa9e1d6c5cd7f057113e90d0a578e523c1f739dde6da44f5931e9631016` |
| Unsigned word writer | `[0x31a347c0,0x31a34812)` | 82 | `570ea1ae0fa7e8a3c8fdd25aefd70abb43d5bb487735845dcaa9da6d93a54163` |
| Unsigned double-word writer | `[0x31a34880,0x31a348d0)` | 80 | `ed5d3948dab0089bd0bac4b86b1b83a1d25ed1e29200a90c688d92a2a705e89c` |

These are complete main runtime-function spans, not a claim that external framework constructors or exception handlers were analyzed.

## Length grammar and sentinel handling

The helper reads one unsigned byte at `0x31a37e0e`.
Values below `0xff` return directly.
The `0xff` path reads a little-endian unsigned word at `0x31a37e24`.
Word `0xfffe` returns sentinel `0xffffffff` at `0x31a37e38`.
Word `0xffff` reads one unsigned double word at `0x31a37e55`.
Other words return directly.
There is no 64-bit length extension in this helper.

The wide reader calls that helper at `0x31a3411c`.
An ordinary result selects one byte per payload unit.
A sentinel result calls the same helper again at `0x31a34136` and selects two bytes per unit.
A second sentinel branches at `0x31a34143` to the archive-exception path at `0x31a3424b`.
Thus a repeated inner `ff fe ff` marker is not a literal length of `65534`.
The prior research `Core.Load.string` accepted that case and requires correction.

An escaped double-word value `0xffffffff` produces the same helper sentinel.
At the outer level, native code can therefore treat it as an alternative Unicode indicator.
At the inner level, it reaches the repeated-sentinel rejection.
The strict codec rejects the reserved double-word value at either level.
It does not claim support for that ambiguous outer alias.

The payload reader uses the derived byte count and rejects short reads at `0x31a341b1`.
The new decoder checks the complete buffer boundary before payload allocation or decoding.

## Canonical wide save

The ordinary wide writer emits byte `0xff` at `0x31a345b6` and word `0xfffe` at `0x31a345bd`.
This produces the explicit Unicode marker `ff fe ff`.
It then reads the CString length from the signed 32-bit field at buffer minus `0x10`.
Signed comparisons at `0x31a3461b` and `0x31a3464d` select these forms:

| Unit count | Length bytes after the Unicode marker |
| --- | --- |
| `0..254` | `u8 count` |
| `255..65533` | `ff`, then `u16 count` |
| `65534..0x7fffffff` within the supported CString domain | `ff ff ff`, then `u32 count` |

The long branch calls the actual unsigned-long writer `0x31a34880` at `0x31a346a5`.
The payload byte count doubles the stored unit count at `0x31a346c0`.
The payload write excludes any terminator.
This wide overload always writes Unicode on its ordinary path.
No native narrow CString save overload is admitted by this finding.

The supported codec domain is nonnegative signed 32-bit CString lengths.
The buffer-length call at `0x31a3414e` uses framework import ordinal `4954`, IAT slot `0x31a50370`.
Hopper identifies its external signature as `GetBufferSetLength(int)`.
The original PE independently binds the slot and ordinal, while the signed save comparisons are directly observed.
Values above `0x7fffffff` are excluded before allocation.
This bound does not claim that every permitted size can be allocated or accepted by a model field.
The external framework setter body and its exact failure behavior were not inspected.

## ANSI wire text and runtime semantics

The native reader's ordinary branch uses one payload byte per unit.
It reaches the narrow text constructor at `0x31a341ee` through framework ordinal `290`, IAT `0x31a50348`.
The Unicode branch reaches ordinal `286` at `0x31a341cd`, IAT `0x31a50350`.
Those pointers are passed to text constructors after a terminating zero is appended to the temporary buffer.
This record does not establish semantic code-page conversion or embedded-NUL normalization equivalence.

The typed wire value maps ANSI bytes through Latin-1 solely to preserve their source representation.
That mapping is not the runtime locale code page.
Default `EncodeString` output is restricted to the proven wide Unicode form.
Explicit `IsSourceFrame=True` additionally reconstructs ANSI source frames from their supplied typed text.
Its count widths invert the accepted narrow framing while avoiding the reserved markers.
This source-reconstruction contract is separate from native narrow canonical save or fresh ANSI semantic construction.

## Mode gates and confidence limits

The wide writer tests native archive flag `0x10` at receiver offset `0x20`, at `0x31a345a0`.
The set branch dispatches to the separate DB writer at `0x31a420b0`.
All six byte/word/double-word primitives likewise test flag `0x10` before their ordinary memory operations.
The read tests are at `0x31a3427a`, `0x31a342ea` and `0x31a343ba`.
The write tests are at `0x31a3476a`, `0x31a347ca` and `0x31a3488a`.
The pure memory codec represents ordinary byte streams only.
It does not interpret DB/MsgPack archives or unrelated research condition flags.
No document-version comparison occurs in the inspected framing functions.
This does not claim compatibility with uninspected historical builds.

Native branches, markers, widths and ordinary mode gates are **confirmed statically for these exact 2026 functions**.
Signed length support is a **bounded codec contract** tied to the observed CString storage and external setter signature.
ANSI semantic conversion, external allocation errors, model-field text domains and new native boundary measurements remain **unmeasured or excluded**.
The new primitive needs actual remote source-corpus process verification before admission.
Held-out native payloads remain sealed.

The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and full [instruction book](../../Playbook/README.md) remain binding.

> The first is success under every criterion on this page.
> The second is the end of the available context.
