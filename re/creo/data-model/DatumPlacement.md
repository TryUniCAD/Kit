# Creo datum placement record

## Scope

`FeatDefsDtm` (`Sld_FeatDefsDtm`) stores one placement record per datum. In the empty control it
holds a `feat_defs_923` array of three records (planes `FRONT` 7, `TOP` 5, `RIGHT` 3) and a
`feat_defs_979` array of one record (the `DEFAULT_CSYS`).

`src/convert/adapters/creo/Author.py` now emits the plane record from the grammar. The record is
`775` bytes and is byte-identical to the first control record.

## Record grammar

The first array element defines every field; later elements replay it positionally (`f7 <id>` or a
bare value, with no field header).

| Field | Type | Value in the control |
| --- | --- | --- |
| `id` | 1 | `7` (then `5`, `3`) |
| `symbol_key` | 1 | `-1` |
| `model_type` | 1 | `2` |
| `group_info_ptr` | 0 | null |
| `place_rec_ptr` | 0 | record |
| `local_sys` | 2 | `f9 04 03` then twelve repeat-compressed slots |
| `own_ref_id` | 1 | `-1` |
| `orient` | 1 | `1` |
| `place_instruction_ptrs` | 0 | `f8 01 f7 0b fb` then one instruction |
| `type` | 1 | `515` |
| `offset` | 2 | `0.0` |
| `dim_id`, `ref_id`, `geometry1_id` | 1 | `-1` |
| `geometry2_id` | 1 | `8` (then `6`, `4`) |
| `memb_num1`, `memb_num2` | 1 | `0` |
| `attr` | 1 | `f8 03 c0 80 00 00 e4` |
| `plin_info_arr` | 0 | `f8 02 f7 15 fb` then two entries |
| entry 1 `type` | 1 | `1` |
| `data(plin_info_ref)` | 0 | `id_type1 = -4`, `id_type2 = 5`, `offset2 = 0.0` |
| entry 2 `type` | 1 | `6`, replayed positionally |
| `data(plin_info_ui_step)` | 0 | `step_ids = [-100]`, `attr = 0`, `uv = f3 f8 02 18 e4` |
| `trf_arr` | 0 | `f8 01 f7 1f fb` then one transform |
| `type` | 1 | `11` |
| `key` | 1 | `-1` |
| `idx` | 1 | `0` |
| `transf` | 2 | `f9 04 03` then twelve repeat-compressed slots |
| `plcm_revnum` | 0 | close |
| `next_prop` | 0 | null |
| `cond_tbl_idx` | 1 | `-1` |
| `comment` | 10 | null |
| `merge_info_ptr`, `alumni_info`, `expl_state_ref` | 0 | null |
| `state_ind` | 1 | `-1` |
| `feat_outl_info` | 0 | record |
| `ent_outl` | 2 | `f9 02 03` then `(+E, +E, 0, -E, -E, 0)` with `E = 254.33012701892218` |
| `pre_roll_back`, `post_roll_back`, `post_regen` | 0 | null |
| `parchild_table` | 0 | close, then `e3` |
| `Structure_Invalid` | 9 | `c0 ab cd` (`43981`) |
| `copy_info_ptr` | 0 | close |
| `embed_info_ptr` | 0 | null |

Two details matter for byte equality:

- `local_sys` and `transf` are twelve slots in the repeat lane. A slot run of four
  `[1, 0, 0, 0]` is `0f 18 e5`, so the compression is a literal, then `e5` for two extra copies of
  the following zero. The record's frame is *not* a rotation matrix.
- `ent_outl` reuses the same lane: `+E` then `e4`, `18`, `-E` then `e4`, `18`.

## Measured results

`Author.DatumPlaneRecord(7, 1, 8, ((1, 0, 0, 0),) * 3, 254.33012701892218)` reproduces the control's
first record byte for byte:

```text
datum record: ref 775 mine 775 byte-identical True
```

Reduced `FeatDefsDtm` bodies are rejected, each measured with one Creo 2027.2 launch:

| Body | Result |
| --- | --- |
| `Sld_FeatDefsDtm e3 f1` | crash, no `End` |
| `feat_defs_923` empty array, one field | crash, no `End` |
| `feat_defs_923` and `feat_defs_979` empty arrays | crash, no `End` |
| three definition-form plane records, no `feat_defs_979` | crash, no `End` |

So the section needs the records, and the last attempt shows the csys entry or the per-datum frames
still differ from what the loader wants.

## Next

Emit the `feat_defs_979` record and give records two and three their own frames. The counts are
known (`feat_defs_923` has three elements of class 2, `feat_defs_979` has one element of class 53),
and the control's positional replay for both shows the field order above.
