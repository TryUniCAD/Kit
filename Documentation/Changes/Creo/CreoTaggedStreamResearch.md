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
  later records reuse the stored count;
- `next_feat_ptr` restarts the field index at the feature schema's first field;
- `e1` is null, `e2`/`e3` begin a structure, `e4`-`e7` repeat, `f5` negates, `f6` is -1, `fb`
  closes an array.

## Use

```bash
python3 re/creo/tools/TaggedStream.py re/creo/oracle/ladder/ladder1.prt.2 --features
```

The tool expects an extracted section body, not a whole `.prt` file. The extraction helper is the
`ReadSection` call in the research notes.

## Result

| File | Feature chain |
| --- | --- |
| `re/creo/oracle/empty/solid_start_part_mmks.prt` | `FRONT` (7), `TOP` (5), `RIGHT` (3), `DEFAULT_CSYS` (11, type 979) |
| `re/creo/oracle/ladder/ladder1.prt.2` | the same four, plus `id 67` (type 923) |

The chain matches the model tree Creo shows for both files.

The empty control's `AllFeatur` now decodes end-to-end, including the footer
(`foot_first_feat_ptr = None`, `foot_layer_count = 0`) and the recursive `layer_list`
(`feat_id` 7, 5, 3, 11). The parser wraps the field index to the enclosing structure's start when
it runs past the end of the field table, which is what lets the recursive `layer_list` decode.

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

`FeatDefs` (`Sld_FeatDefs`) decodes the first feature definition, the ladder's extrude:
`id = 66`, `type = 160`, `sub_type = -1`, `tool_type = 60001`, `index = 1`, and
`max_text_len = 85`. `type = 160` is the feature definition type and `tool_type = 60001` is the
extrude tool type. The parser stops at `0x3be` because the flat field-index approach does not
handle the nested structures in `FeatDefs`.

`VisibGeom` (`Sld_VisGeom`) decodes the first geometry prototype, a plane surface:
`geom_id = 77`, `geom_type = 34`, `feat_id = 74`, `orient = -1`, `boundary_type = 0`,
`next_geom_ptr = 82`, `srf_prim_ptr(plane) = 48865`, `frst_cntr_ptr = 108`,
`frst_cntr_crv_hdr_ptr = 105`, `trv = 110`, and `next_cntr_ptr = 0`. `geom_type = 34` is a plane
surface and `feat_id = 74` is the owning feature. Its `envlp` decodes to
`[184.50782059963194, 86.06680966899467, -154.4303300690026, -115.65227549271083]` and its
`outline` to
`[184.50782059963194, 1.0, 115.65227549271083, -154.4303300690026, 1.0, -86.06680966899467]`.
The parser then decodes the second plane prototype (`geom_id = 82`, `orient = 1`) and the first
curve prototype (`crv_id = 87`, `type = 34`), and stops at `0x272` in the curve point array. The
`local_sys` frame is a 4x3 matrix; the `0x10` byte is the one-byte 1.0 constant in that lane.

## Limits

- The empty control's `AllFeatur` decodes end-to-end. The ladder's `AllFeatur` decodes the five
  features and the footer prefix, then stops in the sketch/extrude payload at `0x1065`.
- `FeatDefs` decodes the first feature definition, then stops at `0x3be` because the flat
  field-index approach does not handle the nested structures.
- `VisibGeom` decodes two plane prototypes and the first curve prototype, then stops at `0x272` in
  the curve point array.
- The parser is research code; it does not change the production adapter, which remains
  container-only.

## Trace mode

`python3 re/creo/tools/TaggedStream.py <section.bin> --trace` prints the last 24 field reads as
`<offset> field <index> <name> type <type>`. The trace shows that the ladder's `AllFeatur` stops at
field 88 `owner_ind` (type `0x01`) at `0x1064`, where the byte is `0xe5`. The preceding fields are
`sorted = 7`, `revnums = 16`, and `owner_type = 0`. The first occurrence of the same fields, in the
field definitions at `0x1336`, has `sorted = 1`, `revnums = [ref 86, ref 86]`, `owner_type = 4`,
and `owner_ind = 0`. The second occurrence's `revnums = 16` is a structure pointer, not a scalar,
so the flat field-index approach misaligns before `owner_ind`. The trace makes that visible without
guessing.

## Verification

- The empty control decodes four features and the ladder decodes five.
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
