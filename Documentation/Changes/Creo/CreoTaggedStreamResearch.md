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
The parser now records an undecodable packed double as `RawDouble(<8 bytes>)` and continues, so
`FeatDefsDtm` decodes through `ent_outl` to the next field.

`FeatDefs` (`Sld_FeatDefs`) decodes the first feature definition, the ladder's extrude:
`id = 66`, `type = 160`, `sub_type = -1`, `tool_type = 60001`, `index = 1`, and
`max_text_len = 85`. `type = 160` is the feature definition type and `tool_type = 60001` is the
extrude tool type. The parser stops at `0x3be` because the flat field-index approach does not
handle the nested structures in `FeatDefs`.

## Limits

- The empty control's `AllFeatur` decodes end-to-end. The ladder's `AllFeatur` decodes the five
  features and the footer prefix, then stops in the sketch/extrude payload at `0x1061`.
- The `ent_outl` bounding-box matrix in `FeatDefsDtm` and `FeatDefs` uses a packed encoding that is
  not yet decoded. The parser records each undecodable double as `RawDouble(<8 bytes>)` and
  continues, so the rest of the section decodes.
- `FeatDefs` decodes the first feature definition, then stops at `0x3be` because the flat
  field-index approach does not handle the nested structures.
- `VisibGeom` geometry records are not decoded.
- The parser is research code; it does not change the production adapter, which remains
  container-only.

## Verification

- The empty control decodes four features and the ladder decodes five.
- The feature ids and types match the model tree that Creo 2027.2 shows for both files.
- The parser is exercised only on the retained research controls under `re/creo/oracle/`.
- No vendor file, vendor block, or captured table is stored under `src/`.

## Documentation

- [Creo PSB container reader](CreoPsbContainer.md)
- [Creo loader analysis](../../../re/creo/loader/Loader.md)
- [Creo data model](../../../re/creo/data-model/DataModel.md)
- [Creo writer gap](../../../re/creo/open-items/WriterGap.md)
