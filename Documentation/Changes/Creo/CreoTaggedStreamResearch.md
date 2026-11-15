# Creo tagged-stream research parser

## Change

Adds `re/creo/tools/TaggedStream.py`, a research-only parser for the self-describing tagged
streams inside Creo PSB sections.

The parser decodes the `AllFeatur` feature chain of the vendor empty-part control and the
one-feature ladder. It is not production code and is not imported by `src/`.

## Grammar

The confirmed grammar is recorded in
[the loader notes](../../../re/creo/loader/Loader.md#tagged-stream-parser-status):

- `e0 <type> <name> 00` defines a field and appends it to the global field table;
- `f1`-`f4` close tokens may precede a value and pop structure levels first;
- `f7 <id>` selects the id-th field of the global field table;
- `f8 <count>` and `f9 <rows> <cols>` are part of the first definition of an array field, and
  later records reuse the stored count; a fresh `f8`/`f9` header at the same field replaces the
  stored count;
- `next_feat_ptr` restarts the field index at the feature schema's first field;
- `e1` is null, `e2`/`e3` begin a structure, `e4`-`e7` repeat, `f5` negates, `f6` is -1, `fb`
  closes an array;
- array-element names such as `ref_geom[0]` and `ref_geom[1]` are distinct global-table
  entries, so dropping them shifts every later index.

## Use

```bash
python3 re/creo/tools/TaggedStream.py re/creo/oracle/ladder/ladder1.prt.2 --features
```

The tool accepts an extracted section body and skips a leading `#<name>\n` header when present.

## Result

| File | Feature chain |
| --- | --- |
| `re/creo/oracle/empty/solid_start_part_mmks.prt` | `FRONT` (7), `TOP` (5), `RIGHT` (3), `DEFAULT_CSYS` (11, type 979) |
| `re/creo/oracle/ladder/ladder1.prt.2` | the same four, plus `id 67` (923), `id 75` (923), `id 74` (917) |

The chain matches the model tree Creo shows for both files.

Both controls' `AllFeatur` now decode end-to-end: 330 nodes for the empty control and 1015 for the
ladder, including the footer (`foot_first_feat_ptr`, `foot_layer_count`) and the recursive
`layer_list` (`feat_id` 7, 5, 3, 11 for the empty control). The parser wraps the field index to the
enclosing structure's start when it runs past the end of the field table, which is what lets the
recursive `layer_list` decode.

The rule that unblocked the ladder was that a stored array count must not override a fresh
`f8`/`f9` header at the same field. The ladder's later rows then expose `id 75` (923) and `id 74`
(917; cadmpeg's additive section-sweep / extrude class). Array counts are also pre-scanned from
every definition site, because the first use of a field can precede the definition that carries
its `f8`/`f9` header.

End-to-end section coverage:

| Section | Empty control | Ladder |
| --- | --- | --- |
| `AllFeatur` | 334 nodes, complete | 987 nodes, complete |
| `FeatDefsDtm` | 292 nodes, complete | 432 nodes, complete |
| `NovisGeom` | 3 nodes, complete | 39 nodes, complete |
| `BasicData` | 838 nodes, complete | 915 nodes, complete |
| `SolidPrimdata` | 40 nodes, complete | 143 nodes, complete |
| `FeatDefs` | section absent | 830 nodes, stops at `0x1158` |
| `VisibGeom` | 2 nodes, complete | 117 nodes, stops at `0x2f7` |

`FeatDefsDtm` (`Sld_FeatDefsDtm`) also decodes the datum placement records. The first record is the
`FRONT` datum with `id = 7`, `type = 515`, `offset = 1.0`, `geometry2_id = 8`, and
`attr = [32768, 0, 0, 0, 0]`. That is the parametric placement of the datum plane, not just a name.

The `ent_outl`, `envlp`, and `outline` bounding boxes use the world-coordinate token lane, and the
decode is resolved. In the positional-outline/world lane, `46 <tail7>` reconstructs `40 <tail7>`
(positive) and `2d <tail7>` reconstructs `C0 <tail7>` (negative). The seven-byte sub-unit forms
`4f <tail6>` and `d5 <tail6>` reconstruct `3F <tail6> 00` and `BF <tail6> 00`. The `0x18` byte is
the one-byte 1.0 constant. The empty control's `ent_outl` decodes to
`[254.33012701892218, 254.33012701892218, 1.0, -254.33012701892218, -254.33012701892218, 1.0]`,
a square in homogeneous coordinates. The ladder's `ent_outl` decodes to
`[186.8986780200836, -0.000125701882057086, 1.0, -156.82118748945425, -272.72085742045164, 1.0]`,
a rectangle in the sketch plane.

`FeatDefs` (`Sld_FeatDefs`) now reaches `0xd91` and 753 nodes. It begins at `Sld_FeatDefs`,
counter `feat_defs_949`, and the first definition record (`id = 66`). The stop is an `0xfc` byte
that sits inside a `46 <tail7>` world double, so the field index is out of step there rather than
meeting an unknown token.

`VisibGeom` (`Sld_VisGeom`) decodes the first geometry prototype, a plane surface:
`geom_id = 77`, `geom_type = 34`, `feat_id = 74`, `orient = -1`, `boundary_type = 0`,
`next_geom_ptr = 82`, `srf_prim_ptr(plane) = 48865`, `frst_cntr_ptr = 108`,
`frst_cntr_crv_hdr_ptr = 105`, `trv = 110`, and `next_cntr_ptr = 0`. `geom_type = 34` is a plane
surface and `feat_id = 74` is the owning feature. Its `envlp` decodes to
`[184.50782059963194, 86.06680966899467, -154.4303300690026, -115.65227549271083]` and its
`outline` to
`[184.50782059963194, 1.0, 115.65227549271083, -154.4303300690026, 1.0, -86.06680966899467]`.
The parser now reaches `0x2f7` and 117 nodes through the plane and curve prototypes. The
`local_sys` frame is a 4x3 matrix; the `0x10` byte is the one-byte 1.0 constant in that lane.

## Limits

- `FeatDefs` stops at `0x1158` and `VisibGeom` at `0x2f7`. In both, the parser lands on an `0xfc`
  byte inside a `46 <tail7>` world double, which means the field index is one or more fields out of
  step at that record, not that the token is unknown.
- `AllFeatur`, `FeatDefsDtm`, `NovisGeom`, `BasicData`, and `SolidPrimdata` decode end-to-end on
  both controls.
- The parser is research code; it does not change the production adapter, which remains
  container-only.

## Trace mode

`python3 re/creo/tools/TaggedStream.py <section.bin> --trace` prints the last 24 field reads as
`<offset> field <index> <name> type <type>`.

## Row mode

`python3 re/creo/tools/TaggedStream.py <section.bin> --rows` prints the cadmpeg row spans as
`<start>-<end> id=<id> root=<class> bytes=<n>`. A row starts at offset 0 or immediately after
`0xe3` and carries `e3 f6 <compact-class> e1` within the first 16 bytes after its identifier.

Measured: empty `AllFeatur` yields 2 spans, ladder `AllFeatur` 8 spans (including class `949` and
the extrude class `917`), while `FeatDefs` and `VisibGeom` yield 0 because they use bare `e3`
boundaries without the `e3 f6 <class> e1` anchor. The row finder is additive and does not change
the field parser.

## Element mode

`python3 re/creo/tools/TaggedStream.py <section.bin> --elements` adds the anchor-free splitter for
geometry arrays. A boundary is a bare `e3` followed by a compact identifier, one byte, and the
element `feat_id` byte (`0x4a`). It prints each span and then runs the parser with per-element
schema resets.

Measured on ladder `VisibGeom`: `srf_array` declares 6 elements and the splitter recovers 6
(`82, 87, 89, 91, 93` plus the inline `77`); `crv_array` declares 12 and recovers 12 (`79, 80, 81,
83, 84, 85, 86, 88, 90, 92, 94` plus the inline `78`). Feeding the 16 boundaries to the parser
advances the boundary parse from `0x2f7` (117 nodes) to `0x928` (393 nodes). `FeatDefs` has no such
boundaries; its `e3` bytes precede `e0`/`f7` definitions, so it needs a definition-tree parser.

Field-level `e4`/`e5`/`e6` repeats resolve to the preceding logical value, `e1` terminates a numeric
array, `0xfb` and `0xf0` act as value terminators, and a fresh `f8`/`f9` header overrides a stored
array count. Each rule is additive: the empty control keeps its 330 `AllFeatur` nodes and the
ladder grows from 389 to 1015.

A direct experiment that swapped `e2`/`e3` to cadmpeg's reading (`e2` open, `e3` close) produced
byte-identical node counts and stop offsets on both controls. The `e3` question is therefore not
what blocks the current rows; it stays recorded as an open question.

`VisibGeom` also shows that `e3` is context dependent at array-element boundaries. `srf_array` is
six elements of class 3; element 1 defines the schema inline, element 2 is introduced by
`f2 f7 03 e3`, and element 3 follows a bare `e3` with `57 22 4a` (`geom_id 87`, `geom_type 34`,
`feat_id 74`). Three local boundary rules were measured against both controls and all regress at
least one section, so none was adopted. The measurements and the required level-tracking direction
are recorded in
[the compound-boundary gotcha](../../Gotchas/Conversion/CreoTaggedCompoundBoundary.md).

## Verification

- The empty control decodes four features and the ladder decodes seven.
- The empty control's `AllFeatur` node count is unchanged at 330; the ladder advances from 389 to
  1015 nodes and the five previously seen features keep their ids and types.
- `FeatDefsDtm`, `NovisGeom`, `BasicData`, and `SolidPrimdata` are `complete` on both controls.
- The CLI accepts the extracted section body including its `#<name>\n` header.
- The feature ids and types match the model tree that Creo 2027.2 shows for both files.
- The world-coordinate decode produces finite, ordered bounding boxes for both controls:
  the empty `ent_outl` is a symmetric square and the ladder `ent_outl` is a rectangle in the
  sketch plane. The `VisibGeom` plane `envlp` and `outline` decode to the same coordinate family.
- The parser is exercised only on the retained research controls under `re/creo/oracle/`.
- No vendor file, vendor block, or captured table is stored under `src/`.

## Documentation

- [Creo PSB container reader](CreoPsbContainer.md)
- [Creo loader analysis](../../../re/creo/loader/Loader.md)
- [Creo data model](../../../re/creo/data-model/DataModel.md)
- [Creo writer gap](../../../re/creo/open-items/WriterGap.md)
