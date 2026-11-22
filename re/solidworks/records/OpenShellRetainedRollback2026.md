# SOLIDWORKS 2026 retained open-shell rollback

Task `B04-SW2026-OPEN-SHELL-ROLLBACK` is a read-only #121 research slice on
`codex/solidworks-open-shell-rollback`. It depends on the [saved shell reader](SavedOpenShellReader2026.md)
at `31254df08b173d8cd218cf6b0b81b9703ae23fea` and the shared retained
transaction and scalar codecs at `0167c3e33a045b82fb9ac17a5aa10560b2070ba8`.
The [native source protocol](https://github.com/TryUniCAD/Kit/blob/84d925a36c79c2b3124aba3ac06830c95297bca1/re/solidworks/records/OpenShellSourceLock2026.md)
binds both intact disclosed sources, the edit and reopen, and the surrounding
controls to SOLIDWORKS 2026 SP05.2, build `34.5.2.0604`. This evidence is
specific to the same one-cap inward shell before and after its driving
thickness edit.

## Physical replay and chronology

Both complete `Contents/Config-0-Partition` streams replay exactly, including
the compression wrappers in the recorded host run. Each active transmit is
10,633 bytes and each delta transmit is 4,085 bytes after decompression. The
codec computes both native payload headers, schema descriptors, field extents,
qualified references, and terminators from typed state. It takes the
observed logical IDs, wire slot assignments, row order, and qualifier values
as replay inputs. The existing delete-only reader still refuses both
histories at the start of the first restored list.

| Scope | Original | Edited save |
| --- | --- | --- |
| Configuration activation, stock and shell controllers | 3, 12, 15 | 3, 17, 20 |
| Physical PMARK order | 15, 1, 3, 12 | 20, 1, 3, 17 |
| Nodes in selected, stock, activated and initial states | 292, 169, 27, 27 | 292, 169, 27, 27 |
| Active / restored last modifying feature | 34 / 32 | 34 / 32 |
| Active / restored body name | OpenShell / ShellStockBoss | OpenShell / ShellStockBoss |
| Retained BODY slot / atom ID | 2 / 101 | 2 / 101 |
| Active / restored BODY_MATCH | 1855 / 1855 | 2579 / 2579 |
| Active / restored ENT_TIME_STAMP_2001 | 111 / 109 | 115 / 113 |

The selected mark comes from the PARTITION and the reciprocal predecessor
chain. The mark controllers in the linked archive are Config-0 `fe38` and
both features' `f3d0`. The active WORLD corroborates the selected PMARK.
The previous WORLD copies have `current_id=highest_id=0` in both saves.
The prior states therefore get their mark identity from the chain.

The selected undo occupies [144, 3262) in both decompressed delta payloads.
It restores 12 rows, removes 135 and supplies 38 previous copies with
capacity 41. The first restore is the stock body name and the copies include
the prior BODY at its original slot. The selected mark header counters are
149, 15, and 11. These counters and the physical row counts occupy separate
fields. The stock undo removes the actual earlier BODY. The next two states
are body-free. Current builds and format origins are traced in the
[pinned kernel framing study](https://github.com/TryUniCAD/Kit/blob/ce0ff08fe0f20b2ac242e8aed26b0632e76b1d7b/re/solidworks/records/ThroughAllMultiStockHistory2026.md)
and the [prior retained fillet proof](https://github.com/TryUniCAD/Kit/blob/ce0ff08fe0f20b2ac242e8aed26b0632e76b1d7b/re/solidworks/records/EdgeFilletRollback2026.md).

## Historical cap and sidecars

The restored stock graph owns six faces, twelve edges and eight vertices.
The eight point coordinates match the box computed from the actual sketch,
support datum and live boss depth. Its real `FACE_ID_2001` attributes bind
all four side identities plus both caps. The `f828` selection's EndFace
role 1, actual stock feature ID and creation event join to the four top
vertices of the prior body's cap in slot 300. The active body also has
the same producer and ordinal key in slot 41. That active face has two
trim loops and is the rim. This overlap makes the controller and historical
state part of the physical selection identity.
[Face key gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/History/OpenShellCapSharesFaceKey.md)

| Field or stream | Status | Observation |
| --- | --- | --- |
| Qualified restores, removals and copies | Confirmed wire order | Existing build-pinned kernel framing consumes both exact saved payloads and re-emits them without unowned bytes. Native allocation and copy filtering for newly generated geometry remain open. |
| Active body stamp | Confirmed header and kernel relation in this scope | Header2 `f44`, the third ModelStamps word, and BODY-owned `ENT_TIME_STAMP_2001` agree. The earlier body retains its own earlier count, while BODY_MATCH is the shared atom's separate result stamp. |
| Native Definition | Confirmed existing typed boundaries | Both saves use the same 3,816-byte Definition and the same 60 next-map index. Its shared parser and store reproduce every byte. |
| History and Biography | Confirmed existing typed boundaries | The document-level History is identical at 101 bytes. Biography changes from 1,455 to 1,467 bytes. Both streams replay exactly, separately from the kernel marks. |
| CnfgObjs, ModelStamps and DLUpdateStamp | Confirmed existing sidecar rules | Header2 `f70`, `f40`, and `f44` supply the three modeled stamps and reproduce all three typed streams in both saves. The empty configuration objects have an unchanged 12-byte representation. |
| `moEndSpec_c.f150/f154` | Not found | Both typed words remain equal across the disclosed thickness edit. Their semantic owners remain unresolved. |
| Config-0-LWDATA and DisplayLists | Not found at field level | The saved streams change digests but keep lengths 1,437 and 17,966 bytes. A same-model save control or build-pinned field trace is needed to separate edit effects from save effects. Earlier cache omission evidence applies to its own measured families. |

The [sanitized receipt](../measurements/2026/OpenShellRetainedRollback01.json)
records the two source hashes, two complete partition digests, four individual
kernel replay digests, twelve other exact stream replays, and the independent
header and topology observations. The [replay tool](../../tooling/sw2026/shell_source/AuditShellRollback.py)
reads the disclosed sources once per case and retests their custody afterward.
It extracts the pinned kernel source into a temporary directory and runs two
fresh guarded workers per document. Neither worker opens data after imports.
The general tracked-asset research runner cannot enroll these external
disclosures without fixture custody. This probe keeps the existing source
lock and emits numeric evidence only.

```sh
python3.14 -I -B re/tooling/sw2026/shell_source/AuditShellRollback.py \
  --disclosure /absolute/path/to/Disclosure --output /absolute/new/OpenShellRetainedRollback.json
```

This is an exact saved-state reconstruction. Fresh rollback generation
still needs independent rules for the kernel's internal allocation
threshold, qualifier map, filtered row inventory, and historical mutation.
The proof adds no production wiring, protected input credit, or native
writer acceptance. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
· [Reverse-engineering playbook](../../Playbook/README.md)
