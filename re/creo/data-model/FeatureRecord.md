# Creo feature record

## Scope

`AllFeatur` (`Sld_Features`) is a singly linked list of feature records. The empty control holds four:
the three datum planes `FRONT` 7, `TOP` 5, `RIGHT` 3 (all class `923`) and the coordinate system
`DEFAULT_CSYS` 11 (class `979`).

The list is `first_feat_ptr` followed by `next_feat_ptr` links. The first record declares the schema
inline; later records replay it positionally. That is the same mechanism as the datum placements, so
the two rules already proven apply:

- never re-declare a field mid-array, because a redefinition appends to the shared global field table
  and everything after the array then reads through a shifted index;
- a record that must declare a new field can only be last.

## Field inventory

Measured from the empty control. `bytes` is the span the record occupies in feature one, so the table
also shows where the size sits.

| # | field | type | bytes | value |
| ---: | --- | ---: | ---: | --- |
| 1 | `Sld_Features` | 0 | 1 | `'record'` |
| 2 | `first_feat_ptr` | 0 | 1 | `'record'` |
| 3 | `id` | 1 | 1 | `7` |
| 4 | `indep_attributes_arr` | 1 | 6 | `[4097, 0, 0, 0]` |
| 5 | `feat_type_ptr` | 0 | 1 | `'record'` |
| 6 | `table_id` | 1 | 1 | `-1` |
| 7 | `type` | 1 | 2 | `923` |
| 8 | `feattype_key` | 10 | 1 | `None` |
| 9 | `form` | 1 | 1 | `0` |
| 10 | `attributes` | 1 | 8 | `[0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 0]` |
| 11 | `placement` | 1 | 1 | `0` |
| 12 | `intersection` | 1 | 1 | `-1` |
| 13 | `internal_udf_type` | 1 | 1 | `-1` |
| 14 | `param_choice_ptr` | 0 | 1 | `'record'` |
| 15 | `blend_choice` | 1 | 1 | `0` |
| 16 | `depth_choice` | 1 | 1 | `0` |
| 17 | `angle_choice` | 1 | 1 | `0` |
| 18 | `pat_choice` | 1 | 1 | `-1` |
| 19 | `round_choice` | 1 | 1 | `-1` |
| 20 | `subsec_choice` | 1 | 1 | `-1` |
| 21 | `sweep_choice` | 1 | 1 | `0` |
| 22 | `dome_choice` | 1 | 1 | `0` |
| 23 | `draft_choice` | 1 | 1 | `0` |
| 24 | `misc_choice` | 1 | 5 | `[0, 0, 0, 0, 0, 0]` |
| 25 | `assoc_type` | 1 | 2 | `0` |
| 26 | `comp_like_type` | 1 | 1 | `-1` |
| 27 | `sect_name` | 10 | 7 | `'FRONT'` |
| 28 | `idtab_ptr` | 0 | 1 | `'record'` |
| 29 | `srf_id_tab_ptr` | 0 | 5 | `[29]` |
| 30 | `fc_hist` | 1 | 0 | `[]` |
| 31 | `save_geoms` | 0 | 1 | `'record'` |
| 32 | `fc_hist` | 1 | 5 | `[8, 0, 0, 0]` |
| 33 | `save_geoms` | 0 | 2 | `'record'` |
| 34 | `transform` | 2 | 12 | `[0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0,...` |
| 35 | `cr_flags_xar` | 1 | 402 | `[-1, -1, -1, -2049, -1, -1, -167772...` |
| 36 | `cvt_feat_dat` | 0 | 1 | `None` |
| 37 | `feat_dates_ptr` | 0 | 1 | `'record'` |
| 38 | `creat_date` | 1 | 3 | `260040` |
| 39 | `regen_date` | 1 | 3 | `280036` |
| 40 | `intrs_pairs_ptr` | 0 | 2 | `'record'` |
| 41 | `first_geom_id` | 1 | 2 | `8` |
| 42 | `topology_increment` | 0 | 1 | `'record'` |
| 43 | `body_geom_hdr` | 0 | 1 | `'record'` |
| 44 | `h_body_geom` | 0 | 5 | `[42]` |
| 45 | `p_body` | 1 | 1 | `'record'` |
| 46 | `p_body` | 1 | 3 | `-5778` |
| 47 | `first_geom` | 1 | 1 | `0` |
| 48 | `body_id` | 1 | 3 | `-5778` |
| 49 | `first_geom_id` | 1 | 1 | `-1` |
| 50 | `ids_null_goem` | 1 | 6 | `[-5778]` |
| 51 | `first_quilt` | 1 | 2 | `0` |
| 52 | `first_lo` | 1 | 1 | `0` |
| 53 | `first_hybrid_body` | 1 | 1 | `0` |
| 54 | `outline` | 2 | 6 | `[1.0, 1.0, 1.0, 1.0, 1.0, 1.0]` |
| 55 | `max_part_size` | 2 | 1 | `1.0` |
| 56 | `cur_max_size` | 2 | 1 | `1.0` |
| 57 | `xform_increment` | 0 | 1 | `None` |
| 58 | `roll_back_id` | 1 | 1 | `-1` |
| 59 | `time_stamp` | 0 | 1 | `'record'` |
| 60 | `time` | 1 | 5 | `1268265181` |
| 61 | `random_num` | 1 | 5 | `608905122` |
| 62 | `hostid` | 1 | 6 | `-443373664` |
| 63 | `quilt_diff` | 0 | 2 | `None` |
| 64 | `body_diff` | 0 | 1 | `None` |
| 65 | `hybrid_body_diff` | 0 | 1 | `None` |
| 66 | `lo_diff` | 0 | 1 | `None` |
| 67 | `attributes` | 1 | 3 | `32769` |
| 68 | `objs_affected` | 0 | 1 | `None` |
| 69 | `SpecTopolRefs` | 0 | 1 | `None` |
| 70 | `ActiveTopolRefs` | 0 | 1 | `None` |
| 71 | `revnum` | 1 | 2 | `3` |
| 72 | `rev_rec` | 0 | 1 | `'record'` |
| 73 | `extnd_rev_tab` | 0 | 1 | `None` |
| 74 | `num_plins` | 1 | 1 | `1` |
| 75 | `largest_prev_rev` | 1 | 1 | `3` |
| 76 | `largest_prev_rev_delta` | 1 | 1 | `0` |
| 77 | `revnum_cache_data` | 0 | 1 | `None` |
| 78 | `rev_flags` | 1 | 1 | `0` |

Feature one occupies `1620` bytes and the whole section `3478`.

## The blocker

One field is `402` of those bytes: `cr_flags_xar`. It is a compact-int array of 32-bit dirty masks,
each word being `0xffffffff` with one or two bits cleared:

```text
-1, -1, -1, -2049, -1, -1, -16777217, -1, -1048577, -1, -536870913, ...
```

`0xfffff7ff` clears bit 11, `0xfeffffff` clears bit 24, `0xffefffff` clears bit 20, and
`0xdfffffff` clears bit 29. The array is one mask per feature field, but which bit belongs to which
field, and why those particular bits are dirty in a fresh part, is not decoded.

Reproducing that array byte for byte from the control would be copying a captured table rather than
generating it, so it is not implemented.

The array is `f1 f8 80 fc ...`: a close token, then a compact count of `252`, then the values. The
values use the whole compact-integer vocabulary (`f6` 27 times, `eb` 23, `e4` 14, `ea` 11, `e5` 8), so
`252` logical elements come from far fewer bytes than `417`.

## The masks are load-critical

Three substitutions were measured on the control, each with one Creo 2027.2 launch. The field spans
`0x21c..0x3bd` and the splice was first checked to be an identity (`splice is identity: True`).

| Substitution | Result |
| --- | --- |
| every one of the 252 masks set to `-1` | model-load crash, no `End` |
| every mask set to `0` | model-load crash, no `End` |
| identity (control bytes) | loads |

So the mask set is validated content, not a redundant cache. Both natural generated defaults fail:
all-clean (`-1`) and all-dirty (`0`). The bit-to-field assignment therefore has to be decoded, or a
mask layout that the loader accepts has to be found, before `AllFeatur` can be generated.

## What the mask table is not

Three measurements narrow it, and none of them match the obvious guesses.

Slot count per file, and per feature within a file:

| Control | Features | Slots per `cr_flags_xar` |
| --- | ---: | --- |
| empty | 4 | `252` for all four |
| ladder | 7 | `311` for the datum features and the protrusion, `278` for two, `0` for one |

Within a file the values are identical for the four datum features (`173` slots differ from `-1` in
the empty control), so the table is per-file schema state, not per-feature content.

Slot count is not the number of field definitions: the empty control defines `32` fields before its
first `cr_flags_xar` and has `252` slots; the ladder defines `33` and has `311`. Both files begin with
the same four values (`-1, -1, -1, -2049`), so the leading slots are stable while the length is not.

## Why name-based RE does not reach it

`cr_flags_xar` is not in the binaries we hold. `strings` finds `Sld_Features` and `first_feat_ptr` in
`coreutils_sh.dll`, `metatoolsapi.dll` and `diagexport.dll`, which is why the container and the linked
list were tractable: those names are in the loader. `cr_flags_xar` appears in none of the four local
binaries, so the loader reads the feature struct **positionally through a compiled layout** and the
name only ever existed inside the stream.

Decoding which bit gates which field therefore cannot be done in the container modules. The name does
exist in the model module, and the field sits inside an ordered feature-field name pool there; the
location, the neighbouring names (`more_cr_flags`, `save_geoms`, `-dummy_*`) and the next step are in
[the feature struct page](../loader/FeatureStruct.md).

## What is needed

1. Decode `cr_flags_xar` bit-to-field assignment, or prove that an all-dirty or all-clean array is
   accepted.
2. Emit the remaining 72 fields, which are mostly constants (`-1`, `0`, null) plus three small
   nested records (`feat_type_ptr`, `idtab_ptr`, `body_geom_hdr`) and one 12-slot transform.
3. Replay records two to four from the first record's schema.

Until step 1 lands, `AllFeatur` stays unauthored, and with it the whole authored part: it is the one
section that both our document validator and the vendor loader reject when absent.
