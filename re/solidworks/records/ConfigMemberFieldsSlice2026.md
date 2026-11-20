# Ordinary SOLIDWORKS relation and color members

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-MEMBERS` |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch `codex/solidworks-config-member-fields` |
| Preparation base | `1e2a77b27759b3336fc04e965bf45a4098e71e84` from PR #185 |
| Delivery base | `0f370556841480763030c9e8af523ec982cb0807` after [PR #185](https://github.com/TryUniCAD/Kit/pull/185) |
| Prerequisites | [Unit tables](ConfigUnitTableSlice2026.md), [object maps](ArchiveObjectMapSlice2026.md), [body values](BodyValueSlice2026.md) |
| Exit | Exact record and field readback, map and invalid-shape cases, queue execution and verified current revision review |

## Wire and owner rules

The narrowed reader reuses the proven ordinary archive version 19000
field order for SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`.
`ReadLengthMut` stores the scalar length independently of the collection.
`ReadRepeatMut` finds that named count in its field scope and applies the
existing bounded count interpretation. This stage executes sequences
whose lengths have already been read. Fixed and expression counts have
their own later qualification.
[Aggregate field and map evidence](https://github.com/TryUniCAD/Kit/blob/8302c824a15830b837c72db75f79cabe5693d200/re/solidworks/records/ConfigBodyGrammar2026.md)

The schema-one relation manager stores two empty object lists in the
disclosed profile, with a separate CString and binary64 cache. Its
`f150` word differs between the two physical controls. The `n1c0`
scalar counts `f1c0` rows. Each row decodes its own node tag. The bounded
profile supports null member rows and refuses non-null links until their
owners qualify. The read retains raw words and cache rows.
[Native relation field ownership](https://github.com/TryUniCAD/Kit/blob/8302c824a15830b837c72db75f79cabe5693d200/re/solidworks/records/PartEquationConfig2026.md)

For a present color owner, `moFeatColorTab_c` uses schema zero with a
stored unsigned 32-bit count and signed-positive traversal. A positive
row count requires the visual property layout and fails closed in this
scope. The optional null owner allocates no slot. The caller's exact
member role selects which shape can be admitted. Both concrete roots
require a newly decoded object, including when the descriptor comes
from the inherited class map.
[Native color table serializer](https://github.com/TryUniCAD/Kit/blob/8302c824a15830b837c72db75f79cabe5693d200/re/solidworks/records/CommonPartOwners2026.md)

The layout, field order and physical read outcomes are confirmed for the
disclosed controls. Populated relation owners, material and appearance
semantics, neutral projection and native writes remain separate work.

## Exact process controls

The existing fixtures are a disclosed native-authored ladder part and a
generated concave part with prior native observations. The verifier checks the exact
original and configuration digests before selecting the measured owner
intervals. The offsets remain in research evidence.
[Ladder native source](../measurements/2026/ReverificationCountOwners01.json)
· [Concave fixture provenance](../measurements/2026/LocalImportReadbackFixtures01.json)

| Control | Owner | Exact Config-0 interval | Map counter | Observed body |
| --- | --- | --- | --- | --- |
| [L1](../v2026/corpus/ladder/L1_boss.SLDPRT) | `f9d0` | [3182, 3232) | 59 to 61 | `moRelMgr_c` schema 1, `f150=1` |
| L1 | `fa88` | [24261, 24287) | 95 to 97 | `moFeatColorTab_c` schema 0, count 0 |
| [ConcaveOwned](../v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT) | `f9d0` | [2235, 2285) | 52 to 54 | `moRelMgr_c` schema 1, `f150=0` |
| ConcaveOwned | `fa88` | [22484, 22486) | 90 to 90 | Null tag |

The independent wire control frames a fresh relation body using the
measured prior class slot, a typed cache value, distinct signed and
unsigned words, and two explicit null rows. It also frames a separate
schema-zero color record whose `0x80000000` count yields zero rows while
retaining the original word. These are isolated wire controls. The
refusals cover wrong or missing seed slots, truncation, surplus bytes,
wrong version and schema, a null relation, a reused object, oversized
counts, and unresolved object and visual row owners.

```sh
python -I -B re/tooling/sw2026/CheckCfgMembers.py ladder
python -I -B re/tooling/sw2026/CheckCfgMembers.py concave
python -I -B re/tooling/sw2026/CheckCfgMembers.py authored
```

[Exact receipt](../measurements/2026/ConfigMemberFieldsReader01.json)
· [Native queue case](../../../tests/Convert/Solidworks/Configuration/MemberNativeTests.py)
· [Authored wire queue case](../../../tests/Convert/Solidworks/Configuration/MemberWireTests.py)

## Remaining configuration scope

The next measurable executor group uses branch selection, virtual
dispatch and fixed-width fields on the disclosed sketch block manager
and exploded-view owner. The larger annotation, material and scene
layouts follow. Full physical configuration admission then requires the
ModelHeader aliases, both root sections, direct owners, caches and
cursor exhaustion over all 142 exercised layouts. Complete configuration
validation remains open until those dependencies are in the read path.
