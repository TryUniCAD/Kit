# Ordinary SOLIDWORKS configuration field modes and supporting layouts

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-FIELD-MODES` |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch `codex/solidworks-config-field-modes` |
| Preparation base | `2759bcdb61c76c6b00fd467354cd85ace50f86bc` |
| Exit | Exact native support records and signed words, independently authored full field boundaries and refusals, current revision queue and review |

## Scope and ownership

The shared body executor reads `Equals` and `Greater` from the
owning field scope. `NotCondition` selects its body when the
specified bits are clear. A `Fixed` repeat gets its row count from
the field rule and retains the ordinary count bounds. It consumes
only the row fields.

`AtLeast` projects the greater of its signed i32 input and the
declared minimum. `Identity` retains the decoded signed i32 value.
Both preserve the original word in the `#wire` field. The common
normalization path retains the scene `Zero` and atom `AtomState`
rules exercised by the scene slice in #191 and accepted atom slice in #194. The tested atom rule
clears its unsigned state above one when mask `0x80` is clear.
The reader refuses unknown normalizations and unqualified widths
for the two signed modes.
[Pinned field predicates](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/src/convert/adapters/solidworks/Archive/Bodies/IsFieldBranch.py)
· [Pinned normalization formulas](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/src/convert/adapters/solidworks/Archive/Bodies/NormalizeWord.py)

## Physical evidence

The full archive reader pinned at
`9f0ccb5389c121e750ca3b73f8e5d248b34d2e15` traversed the two tracked
parts and the disclosed CircularProperties part. The source receipt
binds the original file, configuration and ModelHeader digests,
scope names and half-open intervals. Its reference cursor observations
come from the complete typed load. The new process reproduces the
selected exact field records through the shared body codec.
[Source receipt](../measurements/2026/ConfigFieldModesSource01.json)

| Verified record | L1 interval and result | ConcaveOwned interval and result |
| --- | --- | --- |
| `fd44` signed minimum 10 | [24289, 24293), 12 → 12 | [22488, 22492), 10 → 10 |
| `fd48` signed minimum 0 | [24297, 24301), 0 → 0 | [22496, 22500), 0 → 0 |
| `f152c` signed identity | [25147, 25151), 1 → 1 | [22650, 22654), 0 → 0 |
| Fixed `f9f8` native repeat | [22240, 24252), 10 rows | [20463, 22475), 10 rows |
| `moComponent_c` base | [2435, 2437), reference to part slot 2 | [1722, 1724), reference to part slot 2 |
| `mgBBox_c.restore` | [2572, 2652), ten doubles | Absent in the recorded profile |
| `su_CStringArray` | [3795, 3921), five Unicode strings | [2772, 2898), five Unicode strings |
| `utLineWidth_c.Serialize0` | [9275, 9281), signed selector and float | [7724, 7730), signed selector and float |

The bounded support probe uses the real part object and header
alias from the accepted part-start reader. It preserves those
inherited identities and the measured next counter. It independently
decodes the scalar widths and the observed CString frames. The unit
component resolves the exact part object at slot 2. The outer model
and its remaining graph fields stay outside this bounded invocation.

Three independently authored frames use below, equal and above
comparison values. Their archive flags distinguish the target mask
from unrelated set bits. Each frame exercises ten fixed rows and an
empty repeat, both signed normalizations, and the shared scene and
atom modes. The process compares the full decoded fields and exact
extent. It refuses unqualified branch and normalization rules,
invalid fixed counts, truncation and an absent component owner.
[Guarded process results](../measurements/2026/ConfigFieldModesReader01.json)

```sh
python -I -B re/tooling/sw2026/CheckCfgFieldModes.py ladder
python -I -B re/tooling/sw2026/CheckCfgFieldModes.py concave
python -I -B re/tooling/sw2026/CheckCfgFieldModes.py authored
python -I -B re/tooling/sw2026/CheckCfgFieldModes.py circle --disclosed-root /path/to/disclosed-controls
```

The queue cases use the two tracked native parts and the authored
frames. The disclosed circular source has a separately pinned
149-byte `f1018` owner at [25324, 25473), with counter 119 before
and after. It is a directly owned schema-one `moSheetMetalMaster_c`
with no archive slot. Its inherited feature and virtual targets
require their own bounded reader and process case. `DirectNode`
remains unsupported here. The complete model body and its public
property owner gate retain separate exits.
[Sheet-metal owner provenance](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/SavedPartMetadata2026.md)
