# Active assembly root defaults and empty bounds

The original `sldmodu.dll` is build `34.5.2.0604`, image base `0x4b140000`,
SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
REA's section inspection matched the original `.text` and `.pdata` addresses.
Its evidence ID is
`ev_039080813e4811f6d7a52ae823dbdf1176dd0afe9d09200735f51c1fda4481ea`.
The independently checked original unwind ranges have no reverse-chained
fragments for the two entries below.

| Owner | Half-open range | SHA-256 |
| --- | --- | --- |
| Named assembly constructor | `[0x4b67efe0,0x4b67f8c9)` | `6f3fd9b1d011f298fa639e69e2210bc3334a59e17de62424c156baf8a1f6b103` |
| Assembly lightweight serializer | `[0x4b6746e0,0x4b674ae4)` | `a0f10a79235d2402fa09e44efa9218306a3fe6e6f2d9cd0a56b165f89160f470` |

## Initial allocation

The named constructor clears `r14d` at `0x4b67f002`. The ordinary initialized
path uses it for these scalar and pointer writes:

| Members | Instruction addresses | Initial native state |
| --- | --- | --- |
| `f1560`, `f1570` | `0x4b67f29d`, `0x4b67f2ab` | Zero reference counter and solve result before authored operations |
| `f1590`, `f1598`, `f15a0` | `0x4b67f2c7`, `0x4b67f2ce`, `0x4b67f2d5` | Null pointer, zero scalar, null zone array |
| `f1608` | `0x4b67f370` | Null mirror data |
| `f1740`, `f1748`, `f1750` | `0x4b67f4cc`, `0x4b67f4d3`, `0x4b67f4da` | Two null pointers and a zero scalar |
| `f1868` | `0x4b67f5f5` | Null pointer |
| `f1710`, `f1940` | `0x4b67f476`, `0x4b67f6b6` | Inactive replacement and X-ray branches |
| `f1a28`, `f1674` | `0x4b67f77a`, `0x4b67f3c5` | Bounding traversal option 1 and absent active ground-plane ID -1 |

These are initial values only. In particular the remaining meanings and later
transitions of the unnamed scalar and optional object states are not inferred
from the shared zero register. The map and array allocations, unit and relation
owners and explicit update clearing follow the [assembly construction trace](AssemblyConstruction2026.md).

## Persisted bounds

For `f1a18`, the lightweight store tests the pointer and calls IAT
`0x4cd3a6a8` at `0x4b67476d` before writing marker 1 and the complete box.
`f1a20` uses the same validity test at `0x4b6747ab`. The original import binds
that slot to `sldmgu.dll!mgBBox_c::isSet`; `0x4cd3b330` binds `mgBBox_c::save`.
Both null and unset boxes take the marker-zero branch, at `0x4b674799` or
`0x4b6747d7` respectively, and emit no box payload. The current constructor
helper emits absent boxes for an empty graph. It cannot manufacture a box
from the unset native seed or substitute a populated case's saved bounds.

This is an initial logical-root construction rule. Full configuration,
definition and component graphs and native output acceptance remain open.
