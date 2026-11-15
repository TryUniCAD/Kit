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

## The lane's token shape is load-bearing

Six edits were measured on the same field, one Creo launch each. Two load, four do not:

| Edit | Byte delta | Result |
| --- | ---: | --- |
| control | 0 | loads |
| first value `-1` → `-2` (`f6` → `f5 02`) | +1 | loads |
| explicit expansion of every `e4`/`e5`/`e6`/`e7` repeat, each copy reusing the previous value's own token bytes | +57 | process exits, no `End` |
| all 252 decoded values re-encoded canonically | +68 | process exits, no `End` |
| every value set to `-1` | −162 | `dbg_err_crash`, no `End` |
| every value set to `0` | −162 | `dbg_err_crash`, no `End` |

A further attempt changed a byte inside a `f5` negation token and is **void**: it edited the token
structure rather than a value, so its result carries no information and is not listed above.

Two conclusions follow, and both matter:

- the lane is **not** governed by values alone — replacing the twelve repeats with explicit copies of
  the same values, or re-encoding those same values, both fail;
- it is **not** governed by byte length alone either — a one-byte length change is accepted.

So the accepted form is the control's token shape with limited freedom inside it, and neither "generate
by value" nor "generate by size" reproduces it.

## The field cannot be omitted

The obvious bypass — drop the field and let the loader default it — was measured and fails. The whole
field was removed from all four records: record 0's header `e0 01 cr_flags_xar 00`, its `f1 f8 80 fc`
array introduction, and its 398 element bytes, plus the 398-element runs in records 1, 2 and 3. The
`AllFeatur` payload went from `3478` to `1873` bytes and contained no occurrence of the name.

```text
omit_a: AllFeatur 3478 -> 1873
no cr_flags_xar name left: True
!15-Nov-26 02:40:09  Start C:\Mac\Home\Documents\creo-authored\omit_a.prt
(no End line, no dbg_err_crash, process exits)
```

So the field is required, and the loader is not filling a default for it.

## Replay records store only the element bytes

The four records do not carry the field the same way, and the difference is exact:

| Record | Bytes | Contents |
| --- | ---: | --- |
| 0 | `402` | `f1 f8 80 fc` then 398 bytes of elements, preceded by `e0 01 cr_flags_xar 00` |
| 1 | `398` | elements only — no header, no array introduction |
| 2 | `398` | elements only |
| 3 | `392` | elements only |

Record 1 begins `f6 e5 f5 88 01 ...`, which is exactly record 0's element run; the only difference is
the missing four-byte introduction. So a replay record replays the *elements* of an array without
re-declaring the array, and record 0 is the only one that carries the count.

## The vector is a per-class constant

The masks are not per-document state. Measured across the two retained controls:

| Comparison | Result |
| --- | --- |
| empty control, features 7 / 5 / 3 (classes `923`) | identical to each other |
| ladder, features 7 / 5 / 3 | identical to the empty control's |
| empty control, four-feature vector vs ladder's first 252 entries | **identical** |
| empty control feature 11 (csys, class `979`) vs a plane | differs at exactly 2 slots: `28` and `236` |
| empty control feature 11 vs ladder feature 11 | the same two slots, same two values |
| ladder protrusion (class `917`) vs a plane | differs at 195 of 252 slots |

Two unrelated documents — a datum-only empty part and a part with three datums, a csys and solid
geometry — produce byte-identical datum masks, including the csys's two deviations. The ladder's
vector is the empty control's 252 values followed by 59 more.

So the vector is a function of the feature class, not of the model. For the class set `{923, 979}` it is
a fixed 252-entry vector with one variant for the planes and one for the csys.

That is precisely the shape of a **captured table**: the values are ordered schema data read back from
vendor saves, not something a generator can compute. Emitting them from `src/` would be transcribing
vendor bytes, which the repository standard forbids.

## The lane is not a plain value array

Two further launches contradict the assumption that `cr_flags_xar` is a list of 252 integers whose
values are the only thing that matters.

| Candidate | Result |
| --- | --- |
| control bytes | loads |
| first value `-1` → `-2`, one extra cleared bit, same token count | **loads** |
| all `252` decoded values re-encoded canonically (`f6`, `f5 <n>`, `eb <4 bytes>`) | process exits, no `End`, no `dbg_err_crash` |

So a single value change is tolerated, but re-encoding the *same* values with different tokens is not.
The lane therefore carries meaning in its token stream, not only in the decoded integers. The most
likely reading is that the `e4`/`e5`/`e6`/`e7` tokens are structural in this field — possibly
terminators or run markers the loader interprets directly — and that our reader's repeat expansion is
its own convention.

That matters beyond this field: the "`252` slots" figure, and with it the comparison against the
`.ddt` registry index `250`, are properties of our reader, not measured facts about the file. The
hypothesis that the mask array is one slot per registered field is therefore **not supported**, and
should not be used to size a generated array.

What is established: the control's exact token stream loads, a one-value deviation with the same token
count loads, and wholesale substitution does not.

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

The remaining question is a policy one, because the technical options are exhausted:

| Route | Status |
| --- | --- |
| omit the field | measured, fails |
| all-clean (`-1`) or all-dirty (`0`) generated default | measured, both fail |
| re-encode the same values with different tokens | measured, fails |
| decode the bit semantics from the loader | no accessor exists (210 accessors cover only parenthesised union members); the consumer is at a compile-time struct offset in a 219 MB `.text` |
| emit the per-class vector | would transcribe vendor saves, which the standard forbids |

The per-class vector is stable across two documents, so it is *format-shaped* data rather than
document-shaped data. But it is still copied, not computed. Until that distinction is resolved,
`AllFeatur` stays unauthored, and with it the whole authored part: it is the one section that both our
document validator and the vendor loader reject when absent.
