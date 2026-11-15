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

## Array elements and per-plane values

`feat_defs_923` is `f8 03 f7 02 fb`. The first element defines the schema; elements two and three
are introduced by `f7 02 e3` and then replay the schema positionally, selecting only the fields whose
width changes (`f7 0c`, `f7 16`, `f7 17`, `f7 1b`, `f7 20`, ...). A definition-form element after the
first is therefore not equivalent, and the author must be able to emit replay form.

Each of the three planes differs in more than its identifier:

| Element | `id` | `local_sys` twelve slots | `ent_outl` six slots | instruction `type` |
| --- | ---: | --- | --- | ---: |
| 1 `FRONT` | 7 | `[1,0,0,0, 1,0,0,0, 1,0,0,0]` | `(+E, +E, 0, -E, -E, 0)` | 515 |
| 2 `TOP` | 5 | `[0,1,0,0, 0,1,1,0, 0,0,0,0]` | `(+E, 0, +E, -E, 0, -E)` | 514 |
| 3 `RIGHT` | 3 | `[0,0,1,1, 0,0,0,1, 0,0,0,0]` | `(0, +E, +E, 0, -E, -E)` | not yet confirmed |

with `E = 254.33012701892218`. The outline slot order rotates per plane, so it is a parameter rather
than a value derived from the extent. `Author.DatumPlaneRecord` therefore takes `Columns`, `Outline`
and `InstructionType`.

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
| authored records 1-3 plus the vendor `feat_defs_979` field | crash, no `End` |
| same, with `f7 02` element introductions | crash, no `End` |
| same, with per-plane frames | crash, no `End` |
| same, with per-plane frames and outlines | crash, no `End` |

The first three attempts were also invalid on their own account: the byte range chosen as the
"`feat_defs_979` tail" was really the start of element two, so those candidates carried five
elements under an `f8 03` count. Only the last two attempts spliced correctly.

## Elements two and three must be replays

The remaining difference was structural, not a value. A second element written in definition form
re-declares every field with `e0 <type> <name> 00`, which **appends those names to the shared global
field table**. Everything after the array is then read through a shifted index, so the `feat_defs_979`
record resolves to the wrong fields and the model load crashes.

`Author.DatumPlaneReplay` emits the replay form: no field headers, a `f7 02` lead for element two, no
lead for element three, and the field selectors the control uses (`f7 0c` type, `f7 16`, `f7 17`,
`f7 1b`, `f7 20`). Both elements are now byte-identical to the control:

```text
element 2: ref 139 mine 139 equal True
element 3: ref 123 mine 123 equal True
```

## Accepted by Creo

With all three `feat_defs_923` elements authored and the datum extent set to `200.0` instead of the
control's `254.33012701892218`, 56 bytes of the section differ and Creo still loads:

```text
payload len 1428  control 1428  bytes that differ from control: 56
authored 923 array: 1037  csys tail still vendor-sourced: 351 bytes

!15-Nov-26 02:04:32  End   C:\Mac\Home\Documents\creo-authored\dtm11.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

So the authored datum array is accepted with our own values. The `feat_defs_979` csys field is still
351 vendor-sourced bytes, and it is the last content in the section that is not generated.

## Next

Emit the `feat_defs_979` record and give records two and three their own frames. The counts are
known (`feat_defs_923` has three elements of class 2, `feat_defs_979` has one element of class 53),
and the control's positional replay for both shows the field order above.
