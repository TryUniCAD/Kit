# Ordinary SOLIDWORKS configuration atom manager

| Delivery item | Scope |
| --- | --- |
| Task | `B04-SW2026-CONFIG-ATOMS` |
| Owner | PR #121 takeover team |
| Delivery | Separate main-target branch `codex/solidworks-config-atom-manager` |
| Preparation base | `66cbe26d65568e17cbb689e7d2720f00c1e68dc7`, accepted #189 |
| Dependencies | [Archive map](ArchiveObjectMapSlice2026.md), [standalone header](StandaloneHeaderSlice2026.md) and [feature and concept field actions](ConfigFieldActionsSlice2026.md) |
| Exit | Both disclosed managers and feature links, the authored state contrasts and refusals pass the guarded queue processes, followed by current revision CI and review |

## Exact native rules

The ordinary current-version model resolved method `0x4c234150` reads
embedded `fd88` at the manager's virtual `+0x28`. The bound build is
SOLIDWORKS 2026 SP05.2 `34.5.2.0604`. Its model module SHA-256 is
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.

| Serializer | Half-open image range | SHA-256 |
| --- | --- | --- |
| `moAtomManager_c` | [0x4bcef8d0, 0x4bcefbab) | `760c62cb464604f94675e1806a61e63b65f9f2125f4dbe1a9890f7696007664b` |
| `moAtom_c`, schema one | [0x4bcefbb0, 0x4bcf02e1) | `e3cb61c2a22a231a8d9b05b36e6dd1ec52a4ecf2de76c4ac012d605c2a888974` |

The manager stores signed `f260`, signed `n6c`, that many
tagged atom links, then unsigned `fa8`. The load path attaches the
actual atoms to their manager and indexes them by their sign-extended
`f140` IDs. The manager record itself introduces no tagged owner.
The archive counter, manager last-issued ID and feature ID occupy
separate domains. [Manager and atom provenance](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/AtomManagerBodyEnumeration2026.md#current-reload-creates-both-indexes-and-restores-the-owner)

Each concrete `moAtom_c` uses the existing node base and its
lightweight and resolved concept virtuals `+0x4b8` and `+0x4c0`.
The current body order is `f140`, `f144`, `f130`, `f12c`,
`f158` and the signed body discriminator. Kind zero leads directly
to `f170`, `f18c`, `f198`, the conditional stamp words `f180`,
`f188`, `f1b0`, then `f19c`. The three stamp words appear when
the archive condition is zero or contains `0x400000`. Alternate
discriminators select an inline body or a signed handle in separately
owned native cases. The bounded reader refuses every nonzero kind
before traversing its payload.

The typed wire model retains unsigned `f144#wire`. The shared
`AtomState` action stores zero in the runtime projection for a word
above one when archive condition mask `0x80` is clear. With that mask
set it preserves the unsigned number. The shared handler also retains
the `Zero` mode used by the later scene owner. This slice carries the
stored fields, independent of runtime body and name publication.
[Exact field definition](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/tooling/sw2026/serial/defs/ConfigPart.py#L533-L566)

The native reconciliation at `0x4bcf98c0–0x4bcf9b15` resolves
`f12c` as the base feature ID and `f130` as the last-modifying
feature ID. Later Resolved readers can refer to the same Config atom
through feature `f528`. The integer array `f498` retains the atom ID
independently of the object link.
[Feature ID reconciliation](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/NamedBodyColdReuse2026.md#pinned-implementation-rules)

## Disclosed source and link evidence

The [source manifest](../measurements/2026/ConfigAtomSource01.json)
pins both parts, four linked stream identities per part, native image
ranges, source dependencies and the recorded offsets. The exact
reference source `9f0ccb5389c121e750ca3b73f8e5d248b34d2e15` was
exported to isolated scratch. Its Config, CMgr and Resolved readers
traversed both disclosed originals with the actual header and manager
context. In-memory observations record field spans and the actual
objects retained by the maps.

| Source | Embedded `fd88` interval | Counter | Class and atom slots | Feature ID and exact `f528` object link |
| --- | --- | --- | --- | --- |
| L1 boss | [3062, 3174) | 57 to 59 | 57, 58 | `moExtrusion_c` slot 234, ID 34, [11441, 11443) |
| ConcaveOwned | [2115, 2227) | 50 to 52 | 50, 51 | `moBaseBody_c` slot 154, ID 18, [5303, 5305) |

Both managers carry one kind-zero atom, ID 101, and stored and
effective state zero. Their concept links are null and their
inherited lists are empty. Both resolved feature links alias the
same Config atom by object identity. L1 retains stamps `1656`
and `1656`. ConcaveOwned retains zeros in those positions.

The new bounded process decodes the actual part descriptor into
slots 1 and 2 and binds the actual independent ModelHeader self
object in slot 3. Its standalone header slot remains 69 or 15.
The full reference showed native base 4 and 56 or 49 incoming
entries. The scoped process seeds the actual measured counter and
these three verified entries, leaving unused intermediate entries
unmaterialized. Both newly read slots preserve the measured native
allocation and retain all supplied entries by identity. The process
then reads the exact two-byte producer link through that same member
map and verifies the feature and atom ID spans against native scalar
words. This confirms the linked field with the relevant original
owner. Complete Config and Resolved stream admission remain separate.

## Independently authored contrasts

A two-row frame reuses the actual earlier atom class. It allocates two
distinct atoms, keeps signed atom and producer words, and verifies the
unsigned state projection. With conditions `0x80` and `0x400080`,
independent inputs retain the high unsigned state, contrasting
omitted and present stamp words. These establish typed wire
behavior. Valid body, feature and kernel semantics for authored
negative values have their own acceptance requirements.

Invalid cases include partial and trailing data, a detached parent,
wrong versions and schema, null and borrowed atom owners, duplicate
IDs, invalid counts, populated concept and resolved links, and each
unqualified discriminator. Every queue case denies external file,
process and network access after loading the source evidence.

```sh
python -I -B re/tooling/sw2026/CheckCfgAtoms.py ladder
python -I -B re/tooling/sw2026/CheckCfgAtoms.py concave
```

[Guarded queue cases](../../../tests/Convert/Solidworks/Configuration/CfgAtomTests.py)

The new queue checks await execution. Named atoms, nonempty lists,
inline bodies, handle modes, other model roles, full Config and
Resolved bodies, kernel publication and native writing remain
separately scoped. The optional disclosed multistock packet was
not used for this slice.

[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
