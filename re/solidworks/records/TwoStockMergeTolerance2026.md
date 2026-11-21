# Saved Boolean merge tolerance in SOLIDWORKS 2026

The independently generated two-stock archive starts the extrusion
scalar `f838` at zero. In the edited derivative saved by SOLIDWORKS
2026 SP05.2, the second stock's schema-one `moICE_c` owns binary64
`1e-5` at `Contents/Config-0-ResolvedFeatures` bytes
`[15978,15986)`. Native feature 22 is the independent MovingStock
owner. Its actual D1 separately resolves to 29 mm. The original
disclosed native-authored source has `f838=0` for this operation.
[Generated native pair](../measurements/2026/TwoStockColdNative01.json)

## Pinned native branch

Two local licensed modules outside the repository report file version
`34.5.2.0604`. Their SHA-256 values are
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`
for `sldmodu.dll` and
`77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594`
for `sldgcu.dll`. REA established the PE identities. LLVM instruction
decoding and the PE unwind and import tables bound the actual method
ranges and external kernel call.

| Evidence | Observed path |
| --- | --- |
| Constructor and storage | The inherited constructor initializes `this+0x838` at `0x4bad3cf6`. The `moICE_c` constructor reaches it at `0x4bad3f0d`. The shared serializer begins at `0x4bb11640`. It stores binary64 at `0x4bb11700` and reads it at `0x4bb117a9` at archive version `0x998` or newer. |
| Actual independent stock dispatch | The `moICE_c` dispatch at `0x4baeb030` reaches the `f810` reader at `0x4b2bd1d0`. Mode zero selects the unite path from `0x4badb162` to `0x4badb190`. Mode one branches at `0x4badb15b` to subtraction. |
| Initial kernel state | In the unite path, a zero last-update version at `this+0x2b8` and a stored tolerance below `1e-8` permit a store of exact binary64 `1e-5` at `0x4badb24d`. An alternate handling path contains the corresponding store at `0x4badbfb7`. |
| Live consumer and update | The unite path passes the addressed tolerance to `sldgcu.dll!ram_UniteMany` at `0x4badb36e`. The imported function forwards it to the actual body unite implementation. A retry can supply `2.5e-5`. Successful native status and a feature creation version of at least `0x998` permit writeback of the effective tolerance at `0x4badb4ed`. |

The dispatch range `[0x4badb0f0,0x4badb189)` is SHA-256
`312e3778f98c2084ebe3e8c5ba9369c82d525318ba6673c26031374568f6e623`.
The independent unite range `[0x4badb190,0x4badb52b)` is
`681d5ab158eb2769b8ab9e7fdeadffd012e13fda22ace00da5e97c2820631ed3`.
The serializer range `[0x4bb11640,0x4bb11888)` is
`c5a878eddfee6d1a099f896cb01229c738f9dca684a60d8428ab115ef171d2ef`.
[Part chronology](PartChronologyConstruction2026.md)

These branches classify `f838` as persisted Boolean merge tolerance
state. The reported edited save is compatible with the measured
native setter. The exact dynamic write for that save remains
unobserved. The fresh constructor's zero remains the documented
initial state, and the complete saved SDK admission still requires
the bounded body and selection checks. The retry and writeback
paths allow other tolerance values and require their own evidence.

## Controlled save contrast

Each contrast starts from the exact 8,574-byte generated source.
One arm rebuilds and saves it without a dimension edit. Another
changes the selected stock from 12 to 18 mm, rebuilds, saves and
reopens in a fresh process. The earlier arm changes the other stock
from 10 to 29 mm. Both controls and all five contrast processes passed.

| File state | Selected D1 (mm) | Independent D1 (mm) | Independent `f838` (m) | `f2b8` / `f2bc` |
| --- | ---: | ---: | ---: | --- |
| Generated before native rebuild | 12 | 10 | 0 | 0 / 0 |
| Native rebuild and save | 12 | 10 | 0.00001 | 19000 / 2026306 |
| Native independent-stock edit | 12 | 29 | 0.00001 | 19000 / 2026306 |
| Native selected-stock edit | 18 | 10 | 0.00001 | 19000 / 2026306 |

The decoder observed zero in the other two feature roles in all four
files. The unchanged native save establishes that a D1 edit is
unnecessary for the measured transition. The native app retained the
selected cut across each edit and fresh reopen. Four separate guarded
archive workers read all typed values with zero external accesses.
[Native and wire receipt](../measurements/2026/TwoStockSaveTolerance01.json)

The strict SDK saved lane accepts the measured independent-stock
word with its exact generation and update date. It retains the
observed value in the typed lineage evidence. The original source
and all three native derivatives now resolve both editable D1s,
both design bodies and the selected cut. Five altered inputs,
including the unqualified retry value and the same scalar in a
cold graph, refuse. The established no-B-rep route is preserved.
[Guarded public readback](../measurements/2026/TwoStockSavedSdkRead01.json)
