# Ordinary SOLIDWORKS configuration section emission

Task `B04-SW2026-CONFIG-SECTION-EMISSION` belongs to the PR #121 takeover
team. The isolated branch `codex/solidworks-config-section-emission` starts
from accepted main `e3b75f8860497fd92583e5397b7d0c4ac40528cf`.
The source precedent is the shared field writer in the published aggregate
`d00e45fbc24b8da87c02999c914aa45dbfaa2f62`. The standalone delivery uses
the accepted #193 section and ghost reader and the #188 header handoff.

## Format authority

[Configuration section framing](ConfigSectionSlice2026.md) binds the
ordinary SOLIDWORKS 2026 SP05.2 `34.5.2.0604` version-19000 section,
zero-wire header alias and empty ghost owner to serializer addresses and
two independently saved parts. The shared writer has three new operations.

| Action | Emitted rule and ownership |
| --- | --- |
| Section | Write the child fields to a temporary buffer using the enclosing writer's same graph and scope. Prefix the result with its little-endian unsigned 32-bit byte length. Reject alternate archive versions and skip-condition bits `0x80000` and `0x100000`. |
| Direct | Take the selected standalone header objects from the caller's `HeaderRefNodes` result. On a mapped schema-one part root, allocate them in supplied self-then-directory order and peg the base at the resulting counter. Emit zero bytes. |
| GhostCount | Require an empty modeled row set for the admitted profile. Derive the low 28 bits from its size and use the authored signed flag in the high four bits. Require an integer flag from -8 through 7. The adjacent `f80` field remains owned by the typed scalar and comes from modeled inputs. |

With a failed child, the writer restores the caller's buffer and publishes
no bytes from the failed section. A containing archive operation still
owns its error boundary and discards any partially built graph. The
standalone header and both positive cases have distinct object aliases in
the normal shared map. A missing, duplicated, already mapped, or wrong-class
alias is refused before allocation.
The shared graph writer also refuses a section with a nested part
requesting the outer header aliases. A parentless field scope can belong
to an embedded object, so the emitter checks the actual object writing
depth before reserving any direct slots.

## Guarded results

The writer creates its model and header in memory after source-file access
is disabled. The reader runs in a separate guarded process. It compares
the emitted frame to the ordinary tag and size formulas, resolves its
actual aliases and consumes every byte. The reader independently loads
the two pinned native controls for the ghost comparison before starting
its guard. No native bytes enter construction.

| Authored graph | Outer sections | Final cursor | Config reference slot / next slot |
| --- | --- | ---: | --- |
| Single self reference | `[18,22)`, `[26,32)` | 32 | 3 / 4 |
| Self and two directory references, nested signed ghost | `[18,22)`, `[26,44)` | 44 | 5 / 6 |

The first frame reproduces the independent #193 sibling bytes. Removing
its header context makes the second sibling fail without advancing the
outer cursor beyond 22. The second frame increases the emitted length by
12 bytes and preserves directory order as well as header slot identities.
The framed empty ghost rejects populated rows and signed flag overflow.

The author supplies `f80=10000` and flags 1 and 0 for the two independent
ghost comparisons. Their eight-byte payloads match L1 `[3174,3182)` and
Concave `[2227,2235)` exactly. An independent `f80=25`, flag -8 case
round-trips against the signed packing formula. Twelve malformed writer
inputs refuse and leave the failed section unpublished. The two guarded
workers report zero runtime external accesses and zero CAD launches.

The existing ordinary Definition proof reproduced both authored and both
native stream digests, lengths, and map counters. The two guarded atom
encoder reports were byte-identical against the accepted main tree.
[Definition regression authority](../measurements/2026/SdkOrdinaryPartDefinition01.json)
· [Atom regression authority](../measurements/2026/ConfigAtomEmission01.json)

```sh
python3.14 -I -B re/tooling/sw2026/CheckCfgSectionWrite.py measure
```

[Native control custody](../measurements/2026/ConfigSectionSource01.json)
· [Sibling reference](../measurements/2026/ConfigSectionSiblings01.json)
· [Source-bound process evidence](../measurements/2026/ConfigSectionEmission01.json)

The remaining model-body layouts and ordinary stream composition require
separate evidence. These bytes measure two bounded archive graphs and
three ghost records. Native application acceptance, generated files and
FCStd conversion credit remain absent from this stage.
