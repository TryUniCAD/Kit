# Creo feature record

## Scope

`AllFeatur` (`Sld_Features`) is a singly linked list of feature records. The empty control holds four:
the three datum planes `FRONT` 7, `TOP` 5, `RIGHT` 3 (all class `923`) and the coordinate system
`DEFAULT_CSYS` 11 (class `979`). The ladder control holds seven more, including a protrusion
(class `917`).

The list is `first_feat_ptr` then `next_feat_ptr`. Record one declares the schema inline; later records
replay it positionally, so two rules hold and both have been measured:

- never re-declare a field mid-array, because a redefinition appends to the shared global field table
  and everything after the array then reads through a shifted index;
- a record that must declare a new field can only be last in its array.

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

## The field that dominates the record

`cr_flags_xar` is `402` of those `1620` bytes. Its lane is a repeat-compressed array of signed 32-bit
values, and its encoding is now fully decoded (below). The values are the remaining unknown.

## The lane encoding is decoded

The lane is `f1` ``f8`` ``count`` then run-compressed signed integers:

| form | meaning |
| --- | --- |
| `00`–`7f` | value `0`–`127` |
| `80`–`bf` + 1 byte | value up to `0x3fff` |
| `c0`–`df` + 2 bytes | value up to `0x1fffff` |
| `e8`–`eb` + 1–4 bytes | payload of that width, smallest chosen |
| `f5` + int | negation |
| `f6` | `-1` |
| `e4`/`e5`/`e6` | the previous value repeats 1/2/3 more times |
| `e7` + int | the previous value repeats `n` more times |

`Author.CompactInt`, `Author.SignedInt`, `Author.SignedIntArray`, `Author.SignedIntElements` and
`Author.FlagValue` implement it. They reproduce **every** lane in both retained controls, definition and
replay form, exactly:

```text
empty  rec0 252 slots 402 bytes  identical True
empty  rec1 252 slots 398 bytes  identical True
empty  rec2 252 slots 398 bytes  identical True
empty  rec3 252 slots 392 bytes  identical True
ladder rec0 311 slots 462 bytes  identical True
ladder rec1 311 slots 458 bytes  identical True
ladder rec2 311 slots 458 bytes  identical True
ladder rec3 311 slots 452 bytes  identical True
ladder rec4 311 slots 484 bytes  identical True
ladder rec5 278 slots 385 bytes  identical True
ladder rec6 278 slots 385 bytes  identical True
ladder rec7   0 slots   0 bytes  identical True
ladder rec8 311 slots 484 bytes  identical True
```

Record one's lane is `f1` plus `f8 count` plus the elements; replay lanes are the elements only, with no
header and no count. That is why record one is 4 bytes longer than the others for the same values.

### Retraction

An earlier version of this page claimed the lane's *token shape* was load-bearing, on the strength of a
`+57`-byte explicit expansion and a `+68`-byte canonical re-encode both being rejected. Both of those
candidates were malformed by my own encoder — the expansion reused the wrong token bytes and the
canonical form emitted `eb` where the control uses `ea` for three-byte payloads. With the encoder above,
a value-preserving re-encode at `471` bytes is accepted:

```text
lane_1a0: lane 471 bytes, AllFeatur payload -> 3547
!15-Nov-26 02:57:04  End   C:\\Mac\\Home\\Documents\\creo-authored\\lane_1a0.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

So the lane is not size-constrained and not token-shape-constrained. A `0x1a0`-byte cap was hypothesized
from the accessor family's `size(kind)` values and is **disproved** by that same launch.

## The values are not a per-class constant

An earlier version of this page also claimed the vector is a per-feature-class constant. That is only
true of the datum features, and even then only of the leading slots:

| Control | Feature | Class | Slots |
| --- | --- | --- | ---: |
| empty | 7, 5, 3 | `923` | 252 |
| empty | 11 | `979` | 252 |
| ladder | 7, 5, 3, 11, 67, and one more | `923`/`979`/`917` | 311 |
| ladder | 75, 74 | — | 278 |
| ladder | one feature | — | 0 |

The same class `923` carries `252` slots in one document and `311` in the other, and within the ladder
the count varies from feature to feature. The leading `252` values of the ladder's datum features are
identical to the empty control's, so the lane behaves like an append-only per-field table that grows as
the document's schema grows — but the *length* is per feature and per document, and the ladder's
protrusion differs from its datums at `195` of `252` slots.

So the vector is state derived from the document and from the feature, not a constant that can be read
off a class. That is the remaining gap.

## The values are immaterial

This is the important result. `re/creo/tools/SlotBisect.py` rewrites the lane in **every** record with a
generated all-clean vector, using the shipped encoder, so each candidate is a well formed stream:

| Candidate | AllFeatur bytes | Creo |
| --- | ---: | --- |
| no-op rewrite from the shipped encoder | 3478 | loads |
| slots 126..251 all `-1` | 2853 | loads |
| slots 64..251 all `-1` | — | loads |
| slots 32..251 all `-1` | — | loads |
| slots 16..251 all `-1` | — | loads |
| slots 8..251 all `-1` | — | loads |
| slots 4..251 all `-1` | — | loads |
| slot 3 set to `-1` | 3478 | loads |
| every slot `-1`, count 252 | 1908 | loads |
| every slot `-1`, count 4 | 1899 | loads |
| every slot `-1`, count 2 | — | loads |
| every slot `-1`, count 1 | — | loads |
| single slot with value `0` | 1895 | loads |
| every slot `-1`, count 0 | 1891 | fails (twice) |

So neither the values nor the count carry meaning. Only one rule survives: the array must be
**non-empty**. `Author.CleanFlagValue()` emits `f1 f8 01 f6` and `Author.CleanFlagElements()` emits
`f6`, and a control whose four lanes are replaced by exactly those, `AllFeatur` `3478` → `1895` bytes,
loads with `End` and `MT Part Solid`.

### Two earlier claims withdrawn

The retracted table said every value `-1` fails and every value `0` fails. Both were **flaky launches**.
Creo in `-g:no_graphics` mode sometimes exits with no `End` line and no `dbg_err_crash`, which reads
exactly like a rejection. The all-clean candidate failed on its first run and loaded on retry, and the
count-0 candidate is the only one that failed twice. Every other candidate in the table above was
confirmed by a launch that reported `End`.

The field is still required, and that part is reproducible: `re/creo/tools/OmitMask.py` removes it from
all four records (`AllFeatur` `3478` → `1873`, no occurrence of the name left) and the process exits.

## What this means for the emitter

The dominant field is solved. Record one writes `Author.CleanFlagValue()` and the replay records write
`Author.CleanFlagElements()`, which is a rule rather than a captured table: one clean slot, no vendor
values, no document specific length.

## What is needed

`cr_flags_xar` no longer blocks anything. The remaining work on `AllFeatur` is the other seventy-seven
nodes of the feature record: `id`, `indep_attributes_arr`, `feat_type_ptr`, the choice scalars,
`sect_name`, `idtab_ptr`, `body_geom_hdr`, the transform, and the trailing pointers. Most are `-1`, `0`
or null, and the inventory above gives the value and span of every one, so they can be emitted field by
field the way `BasBasData` and `FeatDefsDtm` now are.

Until that lands, `AllFeatur` stays unauthored, and with it the whole authored part: it is the one
section that both our document validator and the vendor loader reject when absent.
