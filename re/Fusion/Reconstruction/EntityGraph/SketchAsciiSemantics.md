# Sketch attribute ASCII semantics

The version-three kernel `sketch_attrib_def` string stores six real fields:

```text
primaryId secondaryId direction topologyRoleFlags splitSequenceId splitTotalNumber
```

For `102 0 0 0 1 1`, the fourth zero is the value of the stored topology-role mask. It is not an inserted delimiter or reserved constant. The final ones mean fragment one of one; they are not independent enumerations.

## Direct native evidence

[SketchAsciiSemantics.json](SketchAsciiSemantics.json) contains symbol-resolved ARM64 disassembly, binary provenance, import-stub identities and corpus observations. [SketchAsciiSemantics.py](SketchAsciiSemantics.py) reproduces the static disassembly and read-only corpus inspection without executing product code or calling Fusion.

`Ns::ASMInterface::sketch_attrib_def::save(save_context const&)` at `0xdb9a0` writes its own version, then passes its embedded `sketch_tag_id` at attribute object `+0x18` to `sketch_tag_id::save` at `0xdc8d8`. That serializer writes the sketch tag's version from `+0`, creates an ASCII stream, writes the six members below separated by spaces, and calls `save_context::write_string` at `0xdc9b8`.

| ASCII position | Member offset in `sketch_tag_id` | Width / signedness | Save load / output | Restore target / input |
| --- | --- | --- | --- | --- |
| 1, primary ID | `+0x08` | unsigned 64-bit | `0xdc908` / `0xdc910` | `0xdcc8c` / `0xdcc90` |
| 2, secondary ID | `+0x10` | unsigned 64-bit | `0xdc924` / `0xdc928` | `0xdcc94` / `0xdcc98` |
| 3, direction | `+0x18` | unsigned 32-bit | `0xdc93c` / `0xdc940` | `0xdcc9c` / `0xdcca0` |
| 4, topology-role flags | `+0x20` | unsigned 64-bit | `0xdc954` / `0xdc958` | `0xdcca4` / `0xdcca8` |
| 5, split sequence | `+0x28` | unsigned 32-bit | `0xdc96c` / `0xdc970` | `0xdccac` / `0xdccb0` |
| 6, split total | `+0x2c` | unsigned 32-bit | `0xdc984` / `0xdc988` | `0xdccb4` / `0xdccb8` |

The final two values are read into temporary unsigned integers and stored to `+0x28/+0x2c` at `0xdccc0`. The import table resolves output stub `0x107890` to `operator<<(unsigned long long)` and `0x107878` to `operator<<(unsigned int)`. Input stubs `0x1077ac` and `0x1077a0` likewise resolve to the unsigned 64- and 32-bit reference overloads. This establishes signedness independently of observed small values.

The six-field attribute string must not be confused with the separate `saveToString` diagnostic/recipe form, which includes its own textual header and version. Nor does it share the field order of `ISketchTag_Streamer`: the fixed binary Design callback writes `version, primary, secondary, direction, sequence, total, flags`. The ASCII kernel form places flags before sequence and total.

## Semantic domains

Primary and secondary IDs form a source-curve key. Both have unsigned 64-bit storage in the current string form. The secondary component is zero for ordinary authored sketch curves in the qualified writer. Corpus kernel attributes also contain nonzero secondary IDs, including generated text-outline identifiers; storage width alone does not establish the allocation policy of every source kind.

Direction has semantic values zero, one and `4294967295`; the last is the native direction wildcard. The [split evidence](SketchSplitSemantics.md) establishes the joint producer invariant `1 <= sequence <= total <= UINT32_MAX` and the unsplit pair `(1,1)`. A fragment ordinal is distinct from the total fragment count.

Native `compareDirection` at `0xdc8bc` returns a match for equal values or a wildcard in either operand. `exactMatch` repeats that wildcard logic at `0xde768..0xde784`. Reversal should therefore preserve the wildcard while exchanging zero and one. That mapping is a semantic inference from the comparison contract, not a traced native reversal routine: no named sketch-tag reverse/flip method was found in the inspected `NsASMInterface10`, `NsASMEntityTracking10`, `NaFusion10` and `NaTagUtility10` symbol inventories. Inlined logic may exist. Arithmetic `1-direction` without the wildcard branch would produce an invalid result for `UINT32_MAX`.

`topologyRoleFlags` is the behavior-based name established in [SketchTagSemantics.md](SketchTagSemantics.md). Native sheet-metal/tagging routines set nonzero bit masks in this member. Its complete bit dictionary and exact source field name remain unresolved. A qualified ordinary-profile writer can require zero, but it should identify this as a restricted semantic mask value, not pretend the field is absent or structural padding.

Older kernel tag versions take a different restore branch. Versions at most two read primary and secondary through signed `read_int` and sign-extend them into their 64-bit member slots, followed by direction, sequence and total. Version two then reads flags as a trailing signed integer and sign-extends it. Earlier versions omit that trailing field. These historical paths do not change the unsigned domain of the current version-three ASCII serializer and should not be silently normalized into it.

## Corpus corroboration

The read-only inspection covered all 1,083 distinct `.smb`/`.smbh` blob digests in the frozen corpus inventory, including archived record revisions. Repeated blob members were counted once. It found 20,636 sketch attributes, all using version three:

| Observation | Count |
| --- | ---: |
| Direction zero / one / wildcard | 15,573 / 4,964 / 99 |
| Topology-role mask zero | 20,636 |
| Unsplit `(1,1)` | 20,180 |
| Split pair other than `(1,1)` | 456 |
| Values outside the stated unsigned domains or split invariant | 0 |

Examples and exact split-pair counts are retained in the JSON. These source observations substantiate field interpretation; they do not establish native acceptance of expanded product writer qualifications.

## Scoped product/documentation corrections

Rename the current sketch model's `EnumA/EnumB` or equivalent provisional fields to `SplitSequenceId/SplitTotalNumber`. Model the fourth member as `RoleFlags` or `TopologyRoleFlags`, with explicit zero qualification if broader bit semantics are not supported. Validate the ordinal/count jointly and use the current unsigned widths. Keep ASCII and binary callback member orders distinct.

The previously frozen cuboid research text inherited the wording `reservedZero` for the fourth ASCII member. That wording is superseded by this native evidence; its observed zero value remains correct. Existing accepted cylinder and cuboid-control bytes do not change merely because the semantic names are corrected.

No production files, frozen cuboid artifacts or native application state were modified by this investigation. No local tests were run.
