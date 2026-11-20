# Bounded SOLIDWORKS 2026 configuration atom manager emission

| Delivery item | Scope |
| --- | --- |
| Task | B04-SW2026-CONFIG-ATOM-EMISSION |
| Owner | PR #121 takeover team |
| Delivery | Main-target branch codex/solidworks-config-atom-codec |
| Dependency | The bounded manager reader and condition evidence accepted in [PR #194](https://github.com/TryUniCAD/Kit/pull/194) |
| Exit | Exact native manager records and map identities, independently modeled count and condition contrasts, guarded refusals, and current-revision queue and review |

The encoder takes the existing mapped part and typed manager rows. It
runs the accepted layout under version 19000 and the measured archive
condition bits. An embedded inheritance rule shares the original field
scope. The two concrete runtime virtuals select the accepted concept bodies.
The model determines the signed row count and map progression. The caller
supplies native semantic fields for each atom as well as the manager's
f260 and fa8 values. These two fields have no general generation formula
in this slice.

The f144 unsigned word remains a separately typed property when decoded.
Its runtime value depends on bit 0x80. If the retained word no longer
represents a requested edit, the encoder derives a candidate from the
edited value and checks the native projection again. An unrepresentable
requested value refuses. Atom rows use the same class and reference maps
as the reader. A private map prevents failed emission from changing the
caller's prefix. The ordinary manager still requires unique kind-zero atom
IDs, fresh objects, empty concept lists and absent linked visual owners.

| Native input | Config-0 interval | Emitted bytes | Map before to after |
| --- | --- | ---: | ---: |
| L1 | [3062, 3174) | 112 | 57 to 59 |
| ConcaveOwned | [2115, 2227) | 112 | 50 to 52 |

The guarded saved probes read each complete original record, re-emit its
typed fields, and compare both bytes and object identities. Six separate
model-authored inputs match independent scalar framing for zero, one or
two atoms. The spans range from 12 to 194 bytes. The authored rows exercise
ANSI and Unicode names, all four condition combinations, an edited value
with a stale wire word and signed identity fields. They deliberately supply
a stale row count to test the derived prefix. Eleven malformed or
unsupported inputs refuse. All runs disallow external accesses after
loading the input and importing the engine.

Run the disclosed process evidence through the local research tool.
The queue uses the same subprocess entry point.

```sh
python -I -B re/tooling/sw2026/CheckAtomEmission.py ladder
python -I -B re/tooling/sw2026/CheckAtomEmission.py concave
```

[Exact source map](../measurements/2026/ConfigAtomSource01.json)
· [Emission receipt](../measurements/2026/ConfigAtomEmission01.json)

This scope covers emitted manager records. Full Config-0 generation,
nonzero body kinds, arbitrary concept owners and complete native output
admission remain open. The native reads supply disclosed controls. They
receive zero held-out writer or FCStd benchmark credit.
