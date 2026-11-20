# Ordinary SOLIDWORKS part ModelHeader handoff

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-HEADER-LINK` |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch `codex/solidworks-config-model-header-link` |
| Preparation base | `fda31a2679995db48aad4fd2ff54d86966fd272d` |
| Dependencies | [Standalone header codec](StandaloneHeaderSlice2026.md), [typed maps](ArchiveObjectMapSlice2026.md) |
| Exit | Exact named role, root and map handoff in real processes, malformed physical starts through the standard queue, current revision CI and configured review |

## Native rule

The ordinary configuration starts a fresh map at one. Its tagged
`moPart_c` schema-one descriptor and object occupy slots 1 and 2.
The first unsigned little-endian section length follows the descriptor.
Its body begins at byte 18 in the measured parts. The exact native
path at that cursor is `moPart_c / moPart_c.FUN_4c2309d0 /
moModel_c.FUN_4c22ec80 / moModel_c.FUN_4c17aa00`.

At entry to that method, direct registration consumes zero bytes.
The selected objects are `moHeader_c.f38` when present, followed by the
`f30` directory's entries in physical order. Registration advances the
configuration counter and inherited base to the end of the batch. The
selected objects retain their standalone indices, fields and spans.
Each current part control has one self object and an absent directory.
Shared header decoding and map registration retain the established
directory order rule.
[Pinned native calls and exact module hashes](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/ConfigHeaderHandoff2026.md)

| Rule | Confidence | Evidence |
| --- | --- | --- |
| Load and store register the self and directory objects without a wire tag | Confirmed | `sldmodu.dll` load `0x4c17c3c2` and `0x4c17c3f2`, store `0x4c17c0d8` and `0x4c17c11b`, plus the six original cursor traces |
| The destination slot comes from the current configuration counter | Confirmed | `swccu.dll` direct helpers `0x31a39d00` and `0x31a39d20`, plus exact aliases and lookup identity in each disclosed part |
| The prefix establishes complete part or active configuration ownership | Refuted | A valid start leaves the model fields and physical active directory binding unread |

## Process cases

The reference execution pins the complete aggregate reader at
`f4fc8744235448c0ff6048e4447440bb7927a6d1`. It observes the cursor and
configuration state on both sides of `Direct`. All six controls went
from `(offset 18, base 1, counter 3)` to
`(offset 18, base 4, counter 4)`.

| Control | Header self file | Standalone index | Config slot | Lightweight span | First model words `fb0, fb4` |
| --- | --- | ---: | ---: | --- | --- |
| L1 boss | Part1 / Default | 69 | 3 | [18, 3052) | 0, 19000 |
| ConcaveOwned | ConcaveOwned / Default | 15 | 3 | [18, 2105) | 0, 0 |
| CircularProperties | CircularInput / modeled default | 25 | 3 | [18, 3058) | 0, 19000 |
| PropertyPolygonDiscoveryEdited | PropertyPolygonDiscovery / modeled default | 25 | 3 | [18, 3080) | 0, 19000 |
| PropertyCircleDiscoveryEdited | PropertyCircleDiscovery / modeled default | 25 | 3 | [18, 3078) | 0, 19000 |
| Advanced rectangle | RectangleInput / Default | 70 | 3 | [18, 3070) | 0, 19000 |

The new probe parses the root descriptor and section length independently
with `struct`. It calls `ReadPartStart` through the actual extracted
container, resolves the registered object through `FindObject` and
requires the standalone header to serialize to the original named
ModelHeader bytes after attachment. L1 has equal ModelHeader and
`Header2` digests. ConcaveOwned has a useful distinct header role. Its
standalone role stays present in missing or invalid ModelHeader cases.
The short `Config-0` control preserves the intact ModelHeader and the
rest of the in-memory archive.
[Stream, field and source hashes](../measurements/2026/ConfigHeaderLinkReader01.json)

```sh
python -I -B re/tooling/sw2026/CheckCfgHeaderLink.py ladder
python -I -B re/tooling/sw2026/CheckCfgHeaderLink.py concave
python -I -B re/tooling/sw2026/CheckCfgHeaderLink.py circle --disclosed-root /path/to/disclosed-controls
python -I -B re/tooling/sw2026/CheckCfgHeaderLink.py authored
```

The twelve authored refusals exercise missing or malformed streams,
an assembly root or wrong schema, truncated and out-of-range
section framing, and unsupported container format. The six original
files stay unchanged. An audit hook prevents external access after
container intake. The queue cases use the two existing tracked parts.
[Queue cases](../../../tests/Convert/Solidworks/Configuration/HeadLinkTests.py)

### Authored directory and logical version contrast

The authored process builds its header fields and two physical format-4
containers in memory. Its independent self file is `AliasSelf`. Its
ModelHeader directory stores `ZuluRef` before `AlphaRef`. Distinct
names, configuration names and raw `f48` values separate all three
records. A distinct standalone header serves as the role contrast.
The builder uses the typed header and container field rules. It
requires zero external access and consumes no source file.
[Authored field inputs](../../tooling/sw2026/MakeHeadAliasCase.py)

The standalone indices are 12, 6 and 10 in the required configuration
order. The original nodes resolve at configuration slots 3, 4 and 5,
with the shared path handle intact. The base and counter both reach 6.
The lightweight cursor remains 18. The probe checks exact standalone
header bytes again after the handoff. A reversal, sort, copied node
or reuse of standalone indices would change the observed result.

The second physical container keeps every common stream byte
identical and changes the logical version marker to
`_MO_VERSION_18900`. Both containers decode as format 4. The
production reader refuses version 18900 before interpreting the
header or model body. These are physical container and typed start
checks. Complete model body consumption remains a separate gate.
[Process evidence](../measurements/2026/ConfigHeaderLinkReader01.json)
· [Queue case](../../../tests/Convert/Solidworks/Configuration/HeadAliasTests.py)

## Remaining physical admission

The scoped output carries a root with undecoded fields and an unset
end offset. It places the logical cursor inside the first section
after its length word. On a whole-record reader, select the same named
ModelHeader through `ReadModelHead`, pass its aliases into the shared
body context and execute the zero-wire registration where the model
layout declares it. A complete parser must bind the batch once.

The three literal-property controls `circle`, `circle_saved` and
`polygon_saved` exercise a union of 142 layout names in the full
reference reader. Adding the two tracked controls gives 144. The
advanced rectangle adds `moGhostBodyObject_c.FUN_4bf05390` to that
union. The receipt includes the exact action modes and 87 absent paths
of the broader aggregate static import closure. That static closure
includes generic layout, assembly, resolved and expression owners.
The ordinary part port can select the exercised schema and operation
subset when building its own concrete registry.

Complete physical admission still requires the part and model bodies,
every exercised nested class and virtual target, exact lightweight and
resolved section consumption, and validation of the terminal cursor.
Separate executor work owns section, mutable context, packed ghost
counts and direct-body framing. The cache slice owns mass properties
and the proved empty bounds field. Branch predicates, fixed repeats
and additional wire normalization modes must match their actual native
field rules. Final property scope must link the actual active CMgrHdr2
row to the fully consumed named physical configuration. These host
prefix checks establish the header handoff only.
[Full aggregate configuration field grammar](https://github.com/TryUniCAD/Kit/blob/f4fc8744235448c0ff6048e4447440bb7927a6d1/re/solidworks/records/ConfigBodyGrammar2026.md)
