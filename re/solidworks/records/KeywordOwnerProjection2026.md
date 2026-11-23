# Binary owners and presentation order in SOLIDWORKS 2026 Keywords

Task `B03-SW2026-KEYWORDS-MODEL/owners`, owner `/root`, delivery
[PR #121](https://github.com/TryUniCAD/Kit/pull/121). The disclosed
comparison starts from `9dca0bd65a4762962b0d71b896cdd354eb405a98` and
the same manifest-pinned recovered cuboids as the typed keyword audit.
The pinned native analysis binds SOLIDWORKS 2026 SP05.2 build
`34.5.2.0604`, the model DLL, and its XML extractor DLL.
[Typed source framing](KeywordTypedCorpus2026.md) ·
[Native instruction and slot evidence](../measurements/2026/KeywordNativeOrder01.json)

| Field or record | Classification | Binary owner and construction rule |
| --- | --- | --- |
| Assembly document title and event | Authored title, event input | The model node owns its name. Its header `f38` self-file owns the shared epoch `f28`. |
| Assembly configuration row | Derived selection | The selected CMgr `f360` provides the actual configuration name and identity. Its ID agrees with the saved Config-0 model. |
| Environment, annotated items, exploded manager | Derived containment | Resolve the environment through Config-0 `f1e0` and its unique resolved alias. Resolve its lights and the cabinet's notes through each `f60` list. The empty exploded manager is the direct `f1590` owner and enters once. Decoded graphs prove containment through their scoped wire lanes. Generated graphs also validate their construction back-pointers. |
| Assembly occurrence | Authored name and allocated identity | Use the actual `f68` occurrence. The saved cohort writes the leaf of its target's logical `h10` name. The generated assembly already binds the physical leaf of the actual linked child. Both projections use the same typed occurrence, row vocabulary, framing, and lexical role and ID order. |
| Displayed sketch parameters | Derived display selection | The sketch's display list `f118` selects its local dimension handle and actual value-array slot `ff8` under the matching `ff0` sketch. The radial shape word `f80=3` or `15` selects the respective radius or diameter glyph. |
| Displayed extrusion and revolve parameters | Derived display selection | The active depth or angle lane selects a display, local handle, dimension, and parameter. The extrusion's retained direction and end words control whether a stored secondary depth is visible. A dormant depth stays in the history and is absent from the keyword index. |
| Dimension text and name | Input value and derived display | Follow the real parameter name and binary64 SI value at `f58`. The Model Config-0 user units supply `f0c` precision. Multiply metres by 1,000 for millimetres or convert radians to degrees. Round to the document's places, with positive ties rounded upward, then trim insignificant fractional zeros. In the disclosed density probe 8.625 and 17.125 display as 8.63 and 17.13. The scoped fixed formatter supports decimal millimetres and degrees. |
| Dimension sibling order | Volatile native ordering; computed generated order | Independently allocated dimensions can own a parameter whose node ID remains `-1`. SOLIDWORKS uses the lower 32 bits of the live display object's address in the XML discriminator for an unregistered parameter. Generated rows use the modeled presentation sequence. The typed source decoder retains the observed semantic row sequence for exact source replay. |

At `0x4bb2aaa4`, the common feature serializer asks vtable slot
`+0x1398` for the feature's live displays. The profile resolves
`sgSketch::GetDims`; its copy uses `su_CObList::AddTail` on `+0x118`.
The extrusion and cut share `0x4bae0010` and gate the second direction
under the actual end fields. Slot `+0x498` at `0x4bb2aac9` dispatches
the distance, radial, and angle shapes to the same `0x4c837780`
keyword serializer.

That serializer saves the display pointer at `0x4c8377a8` and queries
the actual parameter's ID through `+0x188`. The length and angle
parameter tables both resolve that slot to `0x4b283ba0`, which reads
the signed node word at `+8`. The code substitutes the ID only when
it is different from `-1`. At `0x4c8379f1` it passes the retained low
32-bit word to the signed decimal discriminator formatter. The name
and value updates use this same XML extractor key. The pinned
extractor materializes its map before the document is returned. This
explains why the authored display sequence can differ from the
saved sibling order even when the display set and all values agree.

The [source owner audit](../measurements/2026/KeywordOwnerProjection01.json)
independently generates the complete keyword stream for all eight saved
assemblies. The saved keyword payload enters only for the equality
comparison. The binary projection accounts for 184 feature rows and nine
occurrence rows. Four invalid owner contrasts per file are refused.

Across all 203 disclosed parts the real display selection reproduces all
309 named values, units and glyphs. All 309 parameters have node ID `-1`.
196 files follow the modeled sibling order. The seven remaining files
have precisely the same display membership and values, with a different
sibling order. The receipt records those differences without using the
saved order to seed any generated output.

The separate [recovered cuboid comparison](../measurements/2026/RecoveredKeywordOwners01.json)
rebuilds the complete stream for all 111 recovered cuboids using their
binary owners. The single active CMgr configuration supplies its identity
and name. Its unassigned material label comes from the actual material
folder. The header supplies the epoch. One atomic boss and its
type-less dissectable sketch are emitted alongside the concrete system
rows and configuration-owned helpers. The 2,886 feature rows and the
complete framed streams all match. The saved keyword is read after
the model has generated its stream.

Two independently chosen document precisions change the byte length of
a fresh generated index and retain the expected half-tie and angular
representations. These workers record zero runtime input-file reads.
A separate before/after guarded run reproduces 43 ordinary and nested
assembly and child files, including every stream, using 40 workers.
The audit adds no native launches or held-out qualifications.
Scope is the witnessed archive fields. New component target presentations,
other part feature row roles and unmeasured display policies still require
their own evidence.

```sh
python3.14 -I -B re/tooling/sw2026/key_index/PinKeywordOrder.py /path/to/native/modules /tmp/UnusedOrder.json
python3.14 -I -B re/tooling/sw2026/key_index/AuditKeywordOwners.py /path/to/frozen/worktree /path/to/disclosures /tmp/UnusedOrder.json /tmp/UnusedOwners.json
python3.14 -I -B re/tooling/sw2026/key_index/AuditRecoveredPartKeywords.py /tmp/UnusedCuboidOwners.json
```
