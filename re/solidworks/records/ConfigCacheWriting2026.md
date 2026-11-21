# Emit bounded SOLIDWORKS part cache fields

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-CACHES` emission |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch `codex/solidworks-config-cache-writing` |
| Base | `7d1e8be708116840984084611b1d10f2f419cd6a` |
| Dependencies | The accepted cache reader, ordinary part map guard and shared archive field writer |
| Exit | Exact physical replay and independent model emission with stable maps, guarded refusals and current revision review and queue acceptance |

The internal `WriteCfgCache` writes one exact version-19000 inline cache
fragment under an actual mapped ordinary part. It reuses the same typed rules
as `ReadCfgCache` and the shared body field executor. It accepts zero through
two signed mass-cache slots. The lengths follow the actual modeled slots and
atom rows. A populated slot owns its property record. Only two slots carry
the signed `f1638` selector. An empty bounds cache emits its zero count. A
populated bounds cache still requires separate tagged-owner evidence.

The encoder accepts a typed field model and an existing map snapshot. It
computes the field bytes and preserves the caller's part and map entries. It
rejects unknown cache groups, missing or unexpected nested members, misplaced
properties or selectors, unqualified owners and versions. Mass property
values originate in the supplied model. The rest of the configuration,
vendor application acceptance and public writer selection have separate
exits.
[Native field and address evidence](ConfigCacheSlice2026.md) ·
[Selector framing](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Configuration/MassCacheSelectorFollowsTwoSlots.md)

## Process evidence

| Source | Scope | Exact bytes and map |
| --- | --- | --- |
| Tracked L1 boss | Two empty fields | 4 + 4, counters 108 and 110 |
| Tracked ConcaveOwned | Two empty fields | 4 + 4, counter 94 |
| Disclosed CircularProperties | One populated mass slot and empty bounds | 278 + 4, counters 120 and 122 |
| Disclosed PropertyPolygonDiscoveryEdited | Two mass slots and empty bounds | 286 + 4, counters 120 and 122 |
| Authored | Empty mass, one and two populated slots, changed selector and empty bounds | 4, 305, 329, 329 and 4, counter 41 |

Five fresh guarded processes checked all thirteen records. Native interval
replays bind the file, configuration and ModelHeader hashes and compare
each emitted frame with the original interval. The two authored populated
models supply explicit typed values to the writer and use separate struct
framing and field projections as references. They also prove that changing
the signed selector changes the last four bytes only. Thirteen malformed
cases refuse. The original files, modeled values and parent map identities stay
intact, and the direct reader and writer attempt zero runtime data accesses.
The host run starts no CAD process. The two optional disclosed controls
remain external to the repository.
[Exact receipt](../measurements/2026/ConfigCacheWriting01.json)

The normal queue discovers the focused three-process integration boundary
with the tracked controls and authored models. A scoped research replay can
also verify the two disclosed sources.

```sh
python -I -B re/tooling/sw2026/CheckCfgCacheWrite.py measure
python -I -B re/tooling/sw2026/CheckCfgCacheWrite.py measure --disclosed-root /path/to/disclosed-controls
```
