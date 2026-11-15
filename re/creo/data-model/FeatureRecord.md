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

## The definition record is authored

`Author.DatumFeatureRecord(...)` emits record one from the inventory above, field by field, and it is
byte-identical to the control:

```text
definition record: 1601 bytes, byte-identical: True
```

The record is a flat run of `e0 <type> <name> 00` headers whose *values* carry the structural tokens, so
the emitter is a straight sequence rather than a nested builder. Three details had to match exactly:

| Detail | Actual bytes | Consequence |
| --- | --- | --- |
| `feattype_key` | `e0 0a` header, value `e1` | the header carries the field type, not always `e0 00` |
| `sect_name` | `f1` then raw text plus NUL, no length prefix | `NameValue` is wrong here |
| close tokens | ride at the front of a later field's value, e.g. `assoc_type` is `f1 00` | structural tokens belong to value spans |
| `outline`, `max_part_size`, `cur_max_size` | `18` means `1.0` in this lane | the one byte double lane is context dependent |
| `srf_id_tab_ptr` | `f8 01 f7 1d fb` then a bare `e3` | a reference array opens its element without a field name |

Two values are generated rather than modelled: `creat_date`, `regen_date`, `time`, `random_num` and
`hostid` are stamped by the vendor at save time, and we emit our own.

### Verified in Creo

Replacing record one with our emitter, using **our own** dates, stamp time, random number and host id,
and an all-clean generated mask, is accepted:

```text
dtmrec4  control dates, all-clean 252 slot mask   End + MT Part Solid
dtmrec3  our dates, control mask                  End + MT Part Solid
dtmrec2  our dates, all-clean 252 slot mask       End + MT Part Solid
dtmrec   our dates, one slot mask                 silent exit twice
```

So the record body, including its generated datetime and host fields, is authored and loadable. The one
rejection is the mask **length**: the defining record's mask must have the same slot count as the replay
records, because the replays carry elements only and inherit the shape. Length has to agree across the
records of one section; the earlier all-one-slot control loaded because it changed all four together.

## The replay record is authored too

`Author.DatumFeatureReplay(...)` emits the replay form, and it reproduces both control replay records
exactly:

```text
record1 definition identical: True 1601
record2 replay     identical: True 537
record3 replay     identical: True 537
```

The replay form is not a simple strip. Against the definition record it changes five things:

| Change | Example |
| --- | --- |
| field headers dropped | `e0 01 id 00 07` becomes `07` |
| leading close tokens dropped | `assoc_type` `f1 00` becomes `00`; `save_geoms` `f2 e3` becomes `e3` |
| plain array counts dropped | `indep_attributes_arr` `f8 04 90 01 00 e5` becomes `90 01 00 e5` |
| typed array intros dropped | `transform` `f9 04 03 0f 18 e5 ...` becomes `0f 18 e5 ...` |
| field selectors added | `f7 03` leads record two; `f7 1e` and `f7 2b` sit before the duplicate names `fc_hist` and `p_body` |

Two exceptions must be kept verbatim: reference arrays keep their count (`f8 01 f7 1d fb`,
`f8 01 f7 2a fb`), and only the first replay carries the leading selector, which matches the datum
plane array where element two has a lead and element three does not.

`fc_hist` is `(FirstGeomId, 0, 0, 0)` rather than a constant: the control has `8` in the FRONT record and
`6` in the TOP record, tracking `first_geom_id`.

## Open: the fully authored section is still rejected

What the earlier section could not separate is now separated. Every candidate below uses our emitters for
records one to three, which are byte-identical to the control when given its values, and one Creo launch
each after the retry rule (a single silent exit is inconclusive):

| Candidate | Differs from the control in | Result |
| --- | --- | --- |
| record one authored, our dates, all-clean 252 mask | mask in record one | loads |
| records one to three authored, control scalars, all-clean 252 mask | mask in records one to three | silent exit twice |
| records one to three authored, 252 plain `f6` masks | mask encoding only | silent exit twice |
| records one to three authored, one slot everywhere | mask length | silent exit twice |
| records one to four authored, all-clean 252 everywhere | mask in all four | silent exit twice |
| records one to three authored, descending revisions | revisions | silent exit twice |

So the rejection is **not** the generated scalars, **not** the mask encoding, and **not** the mask
length. It survives every one of those. What it tracks is the mask *content across records*: record one
alone may be all-clean, but all four may not.

The closest reading is that the mask is validated per class rather than per record. The plane class and
the csys class differ at exactly two slots (`28` and `236`), and making every record clean removes that
distinction.

## Per record bisect: the definition mask is exempt

`re/creo/tools/MaskRecord.py` replaces exactly one record's lane with an all-clean 252 slot vector and
leaves the other three at their control values. The all-clean lane is `f6` plus `e7 7f` plus `e7 7c`, so
every repeat count fits in one byte and the stream reads the same whether a reader takes `e7` as a byte
count or as a compact count.

| Record swapped | Class | Result |
| --- | --- | --- |
| one (definition, FRONT) | `923` | loads |
| two (first replay, TOP) | `923` | silent exit twice |
| three (second replay, RIGHT) | `923` | silent exit twice |
| four (csys) | `979` | silent exit twice |
| all four | mixed | silent exit twice |

So the definition record's mask is **exempt**, and every replay record's mask is **validated**. The
reading that fits every measurement is that the loader recomputes or ignores the schema-defining mask,
then checks each replay against a per-class expectation. It explains why record one alone may be cleaned
while any replay may not, and why cleaning all four also fails.

### The csys does not need its own values

The next probe replaces record four's lane with the **plane** mask outright. It loads:

```text
slots differing plane->csys: [(28, -536871041, -129), (236, 131072, 0)]
csysasplane: record4 mask -> 252 slots, AllFeatur 3478 -> 3484
!15-Nov-26 03:57:45  End   C:\Mac\Home\Documents\creo-authored\csysasplane.prt
```

Three loads out of three. So slots `28` and `236` are **not** class-specific: class `979` accepts the
plane vector. The required content is therefore **one per-schema vector shared by every replay record**,
not a per-class table.

That reconciles every measurement:

| Observation | Explanation |
| --- | --- |
| record one's mask may be all-clean | the definition record is exempt |
| record two, three or four cleaned alone fails | each replay must carry the schema vector |
| all four cleaned fails | records two to four lose the vector |
| csys replaced by the plane vector loads | the vector is per schema, not per class |

So `AllFeatur` needs exactly one 252-value schema vector, and it is the only vendor-derived content left
in the section. It is not derivable from a record's own fields, because record one may carry anything
while the replays must carry it.

### A one-feature section is authored and loads

Because the definition record's mask is exempt, a section with a **single** feature record needs no replay
records and therefore no schema mask vector. `Author.AllFeaturPayload` emits it: `Sld_Features`,
`first_feat_ptr`, our record, a `next_feat_ptr` terminator of `e1`, and the layer tail.

The first version kept the control's 129-byte tail and it loads:

```text
onefeat: head 34 record 1199 terminator 17 tail 129 total 1379
!15-Nov-26 04:00:40  End   C:\Mac\Home\Documents\creo-authored\onefeat.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

Three loads out of three. That is the first authored `AllFeatur` the vendor has accepted, and everything
in it is generated: the record fields, the dates and host id, the all-clean mask, the list skeleton and
the terminator. Only the tail was vendor-sourced in that candidate.

Two useful facts fell out of it. The `next_feat_ptr` terminator is a single `e1`, and the layer tail is
**not** checked against the feature list: the control's tail declares four layer entries for features
`7`, `5`, `3` and `11`, and the loader accepted it beside a one-feature list.

### The tail rule: four entries, content free

`re/creo/tools/TailRule.py` varies one property at a time. The rule is the **entry count**, not the
content:

| Variant | Result |
| --- | --- |
| one entry, our own feature id | silent exit twice |
| four entries, all carrying our own feature id `7` | **loads** |

So the loader wants four layer entries, and it does not check them against the feature list — the control
declares ids `7`, `5`, `3` and `11` beside a one-feature list, and repeating `7` four times is equally
accepted. `Author.LayerListTail` now emits `KLayerEntries = 4` entries with the caller's feature id, and
`Author.DefaultAllFeatur()` composes the whole section.

The section is therefore fully generated and accepted:

```text
genall2: fully generated AllFeatur 1394 bytes, control section 3489
genall2 identical to the accepted t4_same: yes
End + MT Part Solid, 3 loads out of 3
```

The tail, for the record, is:

```text
e0 00 layer_list 00 f8 04 f7 51 fb
e2 e0 01 feat_id 00 07 e0 01 layer_id 00 00 e0 01 back_layer_id 00 00 f1
f7 51 e2 07 00 00  f7 51 e2 07 00 00  f7 51 e2 07 00 00
e0 00 footer 00 f2 e3  e0 00 foot_first_feat_ptr 00 e1  e0 01 foot_layer_count 00 00  f2
```

### A container with 41 authored sections loads

`Author.EmptyPartSections` now includes `DefaultAllFeatur`, so 41 of the 54 rows are generated, and a
rebuilt control with all 41 replaced loads three times out of three:

```text
auth42 prt 29176 bytes, from control 81539
!15-Nov-26 04:10:12  End   C:\Mac\Home\Documents\creo-authored\auth42.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

The rows still vendor-sourced are the three `ND:*` token tables, `SolidPersistTable`, `SolidPrimdata`,
`DispDataTable`, `THMB_IMG_MAIN`, `CGFPersistTable`, the two `kind b` rows and the two free-space extents.

### Oracle reliability

Every verdict in this page depends on the launch harness, so it was calibrated before the last probes:

| File | Loads observed |
| --- | --- |
| byte-identical no-op rebuild of the control | `3` of `3` |
| record one authored with our dates, all-clean mask | `2` of `2` |
| csys lane replaced by the plane lane | `3` of `3` |

No false failures were observed, so a silent exit is treated as a real rejection once it repeats. False
*successes* remain a risk, which is why the earlier single-load result for a one-slot mask was withdrawn.

### Correction to the earlier mask section

The earlier section reported that `cleanlane` — all four lanes replaced by a single slot — loaded. Under
the model above it should not have, and the per-record bisect contradicts it with four independent
failures. That single success is now treated as **unreliable**, most likely a launch that reported `End`
from a session that had not yet reached the model. It should not be used as evidence that mask length is
free.

### Two void candidates

`allclean4` and `allclean4b` were malformed and their launches carry no information. Record four's lane
is **elements only** — `392` bytes with no `f1` and no array count — so substituting `Author.FlagValue`,
which emits `f1` plus `f8 01`, injected a stray close and count. Only `allclean4c`, which uses
`Author.SignedIntElements` for record four, is a valid test.

### The parser is not an oracle here

`StreamParser` reaches the end of the control section cleanly (`334` nodes, `pos 0xd96`, `len 0xd96`) but
explodes on a rebuilt section (`37456` nodes at `pos 0x597`). It does not understand the `f7` field
selectors that replay records use, so it cannot confirm or deny a replay stream. Byte comparison against
the control is the only reliable check, and it passes.

Records one and two are structurally exact and load individually, but replacing all three plane records
with our own generated values was rejected twice:

| Candidate | Result |
| --- | --- |
| record one authored, our dates, all-clean mask | loads |
| records one to three authored, our dates, descending revisions | silent exit twice |

Six candidates now separate the cause: generated scalars, mask encoding and mask length are all ruled
out, and only the mask *content across records* remains. See the table above.

## The solid feature in the ladder

Authoring a protrusion is the remaining geometry blocker, so the ladder's feature list was inventoried:

| Feature id | Class | Note |
| ---: | ---: | --- |
| `7`, `5` | `923` | datum planes, definition then replay |
| `3` | `923` | third plane, replay |
| `11` | `979` | coordinate system, a definition with its own field set |
| `67`, `75`, `74` | `917` | the solid-producing features |

The ladder's `AllFeatur` is `7838` bytes against the empty control's `3478`, and the datum definition alone
is `1648` bytes with `72` field headers, while the two datum replays carry none.

### The feature list declares its schema once

Searching the ladder's `7838`-byte section for the literal `next_feat_ptr` returns **one** occurrence, at
`0x684`. Every other record boundary is a replay, and `id` and `type` are likewise declared once in the
first record and replayed afterwards.

So the linked list follows the same rule as every array in this format: the first record declares the
schema, later records carry values only. That has a direct consequence for authoring a solid feature:

> a `917` protrusion cannot be appended to our authored part, because its fields are not in the schema
> that our first record declares.

**The delta is only three fields.** Comparing the ladder's first record against ours field by field:

| Declared by the ladder, not by us | Type | Value |
| --- | ---: | --- |
| `flags` | `1` | `3`, placed between `transform` and `cr_flags_xar` |
| `first_hybrid_body_id` | `1` | `-1`, between `first_geom_id` and `ids_null_goem` |
| `topo_parents` | `0` | `f1 e1`, between `hostid` and `quilt_diff` |

We declare five fields the ladder does not (`p_body`, `first_geom`, `first_hybrid_body`, `body_diff`,
`hybrid_body_diff`), which is a schema-version difference rather than a gap.

`Author.DatumFeatureRecord(..., ExtraSchema=True)` emits the three extra fields, and the authored part with
that superset schema loads:

```text
extra3: superset schema (+flags, +first_hybrid_body_id, +topo_parents); record 1199 section 1394
!15-Nov-26 05:23:57  End   C:\Mac\Home\Documents\creo-authored\extra3.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

repeated, twice out of two. So the feature schema can be widened to the ladder's without losing
loadability, which is the prerequisite for adding a `917` record.

### A `917` replay is refused

A `917` record is a replay of that same schema with `type = 917`, so one can be emitted without inventing
fields. Emitting a datum definition plus a `917` replay in second position:

```text
solid917: datum + 917 replay; section 1537 record2 137
!15-Nov-26 05:26:06  Start C:\Mac\Home\Documents\creo-authored\solid917.prt
(no End line; second run identical)
```

Refused, silently, twice.

**That result is void as evidence about protrusions.** A control with a second *datum* replay in the same
position, class `923` instead of `917`, is refused in exactly the same way:

```text
twodatum: datum definition + datum replay; section 1525
!15-Nov-26 05:28:55  Start C:\Mac\Home\Documents\creo-authored\twodatum.prt
(no End line)
```

So our multi-record assembly is wrong on its own, independently of the feature class, and the earlier
conclusion about `917` does not follow. The likely cause is positional: `ExtraSchema` widens the definition
by three fields, and a replay must then carry three more values, which the hand-written replay does not.

`Author.ReplayOf(Definition)` was added to derive a replay from a definition instead of duplicating the
field list, so the two cannot desynchronise. Building a `TOP` definition and deriving its replay gives
`541` bytes against the control replay's `537`, with one structural difference left:

```text
ref : ... f8 01 f7 1d fb e3 f7 1e 06 00 e5 e3 0f 18 e5 ...
mine: ... f8 01 f7 1d fb e3 f7 1e 06 00 e5 f7 1f e3 0f 18 e5 ...
```

The array counts, the typed-array introductions and the `f7 1e` duplicate selector are now right. The
remaining error is that the selector is emitted for **every** repeated name, while the control emits it
only for some: the second `fc_hist` and the second `p_body` carry `f7 1e` and `f7 2b`, but the second
`save_geoms` carries none. The distinguishing property has not been identified yet, so `ReplayOf` is
close but not exact, and the two-record question stays open.

Progress made getting there is real: `fc_hist` was being written as a hardcoded `8` instead of
`first_geom_id`, and the array-strip test was scanning for the `f7` **byte** anywhere in a value rather
than for a real reference token, which wrongly kept the mask's `f8 80 fc` header.

To add one, the **first** record would have to declare the union of datum and protrusion fields, and every
later record would then have to carry values for that wider schema — including the replay-only sections
that currently carry datum values. In other words the authored feature section is not extensible by
adding a record; it has to be rebuilt around the widest feature in the list.

This is the point where the work stops being an emitter task. A `917` record does not exist in the
authored part at all, and its surfaces reference contours and topology that only a regenerated solid
provides. Authoring it means the solid feature, its topology tables, and the surface set together — a
different order of work from every section completed so far, none of which required the vendor to
regenerate anything.

## What is needed

The definition record is done and loadable. What remains is the **replay form**. A replay record is a
positional subsequence of the definition record: values only, with the field headers and the closing
tokens dropped. Record two of the control is `420` bytes against record one's `1601`, and it starts
`03 05 90 01 00 e5 e3 f6 83 9b e1 00 00 e7 07 10 00 e4 00 f6 f6 e3 ...`, which is exactly record one's
values in order with the headers removed.

Two more pieces follow from that: the replay emitter, and the `feat_defs_979` coordinate system record,
which is a different class with its own field set.

Until that lands, `AllFeatur` stays unauthored, and with it the whole authored part: it is the one
section that both our document validator and the vendor loader reject when absent.
