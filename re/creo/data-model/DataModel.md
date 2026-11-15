# Creo PSB data model

## Scope and confidence

This page describes the data layers found in Creo PSB part files.
The `confirmed` label means the layer is present in multiple unrelated files and its framing is validated.
The `partial` label means the layer exists but the field map is incomplete.
The `not found` label means the field was not located.

The production adapter currently reads the container and source replay path only.
This page records the model needed for the next implementation phase.

## Layer map

| Layer | Container | Contents | Status |
| --- | --- | --- | --- |
| Envelope | Text header and `#UGC_TOC` | Identity, version, section directory | Confirmed |
| Storage | Named sections | Plain, Unix-compress, binary | Confirmed |
| Record grammar | Tagged stream | Self-describing fields and arrays | Confirmed grammar, partial field map |
| Geometry | `VisibGeom`, `NovisGeom` | Surfaces, curves, contours, topology | Partial |
| Design | `AllFeatur`, `FeatDefs`, `FeatDefsDtm` | Features, dimensions, sketches, datums | Partial |
| Units | `UnitSystemDef` | Length, mass, angle systems | Partial |
| Display | `SolidPrimdata`, `ModelView#*`, `THMB_IMG_MAIN` | Annotation strips, views, JPEG | Partial |
| Bookkeeping | Header, `MdlStatus`, checksums | Session identity, counts, version | Partial |

## Tagged stream grammar

A section is a stream of typed values.
A field is introduced by a named-record header.

```text
e0 <type> <name> 00
```

The first use of a field stores its type and name.
Later uses refer to the field number and the remembered transition.
The field number is carried by `f7 <id>`.

| Token | Meaning |
| --- | --- |
| `e0 <type> <name> 00` | Field definition |
| `f1` to `f4 <n>` | Close one or more structures |
| `f7 <id>` | Select the next field |
| `e1` | Null |
| `e2`, `e3` | Structure begin or end |
| `f8 <n>` | Array of `n` elements |
| `f9 <rows> <cols>` | Count-bounded scalar body |
| `fa <rank> <dims>` | Array rank and extents |
| `fb` | Array close |
| `e4` to `e6` | Repeat the previous element once to three times |
| `e7 <n>` | Repeat the previous element `n` times |

The field transition cache is the reason a field can be absent from the byte stream and still exist in the model.
The cache is reset at document or section boundaries.

## Scalars

| Type | Meaning |
| --- | --- |
| `00` | Structure |
| `01`, `05`, `07`, `08`, `09`, `0b` | Integer |
| `02` | Double |
| `03`, `0a` | String or byte string |
| `04` | Byte |
| `06` | Float-precision number |

Compact integers use:

| Bytes | Value |
| --- | --- |
| `00` to `7f` | One-byte value |
| `80` to `bf XX` | Two-byte big-endian value |
| `c0` to `df XX YY` | Three-byte big-endian value |
| `e8` to `eb` | One to four explicit bytes |
| `f5 <int>` | Negated value |
| `f6` | Minus one |

Doubles are IEEE-754 big-endian values with a compressed high byte.
One-byte constants cover common values such as zero, one, minus one, pi, and pi fractions.
Group tokens and class tokens supply the high bytes, then the stream supplies the mantissa tail.
Escapes supply explicit bytes.

## Geometry section

`VisibGeom` carries the visible B-rep.
The section root is `Sld_VisGeom`, then `active_geom`.
The principal arrays are:

```text
srf_array[]
  geom_id
  geom_type
  feat_id
  boundary_type
  next_geom_ptr
  orient
  srf_prim_ptr
  frst_cntr_ptr
  next_cntr_ptr
  topol_ref_data

crv_array[]
  crv_id
  type
  crv_pnt_dir[2]
  crv_pnt_arr[n][4]
  crv_hdr_geom_ptr[2]
  next_crv_hdr_ptr[2]

body_array[]
  body_id
  outline
  first_geom_ptr
  material pointer
```

Observed `geom_type` families include plane (`0x22`), cylinder (`0x24`), cone (`0x25`), torus or sphere (`0x26`), spline (`0x28`), fillet (`0x29`), and linear extrusion (`0x2a` or `0x2c`).
The type selects the prototype field body.

A prototype carries a `local_sys` frame.
The frame is a `[4][3]` array in row-major order.
Columns zero to two are the two radial directions and the normal or axis.
Row three is the origin.

| Surface | Placement and parameters |
| --- | --- |
| Plane | `O + u X + v Y` |
| Cylinder | `O + r(cos u X + sin u Y) + v Z` |
| Cone | `O + v tan(half-angle) (cos u X + sin u Y) + v Z` |
| Torus | `O + (R1 + r cos v)(cos u X + sin u Y) + r sin v Z` |
| Sphere | `R1 = 0` torus with radius `r` |
| Spline | Interpolating bicubic grid with end tangents and corner twists |
| Fillet | Rolling-ball blend with a centre curve, radius vector, and tangent |
| Ruled | Linear interpolation between two curves |

`orient` is `1` or `-1`.
A face with `topol_ref_data.list_type = 98` belongs to the solid body whose id is `list_id`.
A face with `list_id = -1` is loose or cosmetic.

The contour table stores an outer or inner flag, a first curve pointer, and traversal data.
`crv_pnt_arr` stores the same edge sample in both neighbouring faces' parameter spaces.
The sample order and direction resolve trimming.

## Design section

`AllFeatur` carries feature rows, generated-entity tables, affected-geometry identifiers, and references.
`FeatDefs` carries feature definitions, placement records, outlines, dimensions, and saved section entities.
`FeatDefsDtm` carries datum feature definitions.

### Geometry prototypes

`VisibGeom` (`Sld_VisGeom`) carries the geometry prototype records. The ladder's first record is a
plane surface:

```text
geom_id = 77
geom_type = 34
feat_id = 74
orient = -1
boundary_type = 0
next_geom_ptr = 82
srf_prim_ptr(plane) = 48865
frst_cntr_ptr = 108
frst_cntr_crv_hdr_ptr = 105
trv = 110
next_cntr_ptr = 0
```

`geom_type = 34` is a plane surface, `feat_id = 74` is the owning feature, and `srf_prim_ptr(plane)`
is the surface primitive pointer. `frst_cntr_ptr` and `frst_cntr_crv_hdr_ptr` are the first contour
and curve header pointers. The prototype's `envlp` decodes to
`[184.50782059963194, 86.06680966899467, -154.4303300690026, -115.65227549271083]` and its
`outline` to
`[184.50782059963194, 1.0, 115.65227549271083, -154.4303300690026, 1.0, -86.06680966899467]`.
The parser then decodes the second plane prototype (`geom_id = 82`, `orient = 1`) and the first
curve prototype (`crv_id = 87`, `type = 34`), and stops at `0x272` in the curve point array. The
`local_sys` frame is a 4x3 matrix; the `0x10` byte is the one-byte 1.0 constant in that lane.

Feature identity is split across a native id, a user-visible name, a type, a parent feature, and references.
The data model needs all of these to rebuild a live tree.
Copying a feature row without its references is not a feature.

### Ladder field additions

The one-feature ladder at `re/creo/oracle/ladder/ladder1.prt.2` adds these `AllFeatur` field names
that are absent from the empty control:

```text
flags
first_hybrid_body_id
topo_parents
avail_feat_parents
dtm_id_tab
dtm_id
dim_id
comp_hist
owner_id
component_ids
sorted
revnums
owner_type
owner_ind
ref_id
hist_ref_info
coll_refs_info
ref_revnum
ref_plcm_revnum
ref_status
dma_update_revnum
flags_arr
upd_ctrl_data
upd_ref_revnum
upd_coll_refs_info
upd_aggr_rev_info
rev_info_arr
info(basic_geom_rev_info)
mdl_geom_rev
revision(mdl_g_rev_dtl_t_ft_regen)
rev_cnt
tstamp
version
versions
aggr_rev_info
aux_rev_data
edg_id_tab_ptr
ed_hist
lo_id_tab_ptr
lo_hist
```

The names confirm that the ladder carries feature-parent links, dimension ids, component ids, and
revision records.
They are the fields a writer must populate for a live tree, not just a shape.

### First feature record

The first `AllFeatur` record in both the empty control and the ladder decodes as the same datum
feature. The ladder's record is:

```text
id = 7
indep_attributes_arr = [4097, 0, 0, 0, 0, 0]
feat_type_ptr = empty
table_id = -1
type = 923
feattype_key = null
form = 0
attributes = [0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 0, 0, 0, 0]
placement = 0
intersection = -1
internal_udf_type = -1
param_choice_ptr = empty
blend_choice = 0
depth_choice = 0
angle_choice = 0
pat_choice = -1
round_choice = -1
subsec_choice = -1
sweep_choice = 0
dome_choice = 0
draft_choice = 0
misc_choice = [0, 0, 0, 0, 0, 0]
sect_name = "FRONT"
```

The `sect_name` and the empty `feat_type_ptr` identify the default `FRONT` datum plane.
The record is a useful anchor because it is present in both files and its field order is stable.
The empty control's record has the same `id`, `type`, and `sect_name`, but its
`indep_attributes_arr` has four elements and its `attributes` array has eleven; the ladder's arrays
are longer. The array lengths are therefore document-dependent, not fixed.
The ladder's extrude and sketch records follow it, but their field boundaries are not yet closed.

### Datum placement

`FeatDefsDtm` stores one placement record per datum. The record grammar is decoded and emitted by
`Author.DatumPlaneRecord`; the field table is in [the datum placement page](DatumPlacement.md).

**A `FeatDefs` row must describe every feature, and a definition needs its placement record.**

Four measurements settle this. First, replacing the ladder's row (`5977` bytes, seven definitions) with our
generated one-definition row reads back through our adapter as `7 features, 2 params` with the body intact
(`6` faces, volume `18482541.49`) but Creo answers `dbg_err_crash()`. Second, emitting **one definition per
feature** (`(7, 5, 3, 11, 67, 75, 74)`, `2319` bytes) still crashes, so the definition count is necessary but not
sufficient. Third, editing a single dimension value **in place** in the ladder's own row — same length, one
`value` field rewritten from `-201.7190851617055` to `-123.5` — loads twice with the body intact:

```text
ladder_same_len: 110065 bytes (unchanged length)
readback params: [-123.5, -338.93815066863453, -86.06680966899467, -154.4303300690026]
!15-Nov-26 07:27:07  End   C:\Mac\Home\Documents\creo-authored\ladder_same_len.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid        (2 of 2)
```

Fourth, a definition built with a real `place_rec_ptr` — `local_sys` identity frame, `own_ref_id`, `orient`,
`trf_arr` with one `type`/`key`/`idx` element, `transf`, `plcm_revnum`, `next_prop`, `cond_tbl_idx`, `comment`,
`merge_info_ptr`, `state_ind`, `alumni_info` — loads on the datum control twice (`place_ctrl`, then
`fd_place` from the landed emitter), so placement records are accepted and are now what
`Author.PlacementRecord` emits.

The ladder is still refused with placements present (`place_ladder`, silent exit twice). Comparing the two field
sets shows what a solid feature needs beyond placement:

| Field | Ladder definitions | Ours |
| --- | --- | --- |
| `place_rec_ptr` with `local_sys` / `trf_arr` / `transf` | present | present |
| `sub_feat_arr` | 1 element: `id`, `type`, `sub_type`, `data(subft_indexnumber)`, `index`, `tool_type`, `sep_index` | absent |
| `feat_outl_info` | `ent_outl` (6 doubles), `max_text_len` | absent |
| `gsec_ptr` | `type`, `is_ref_gsec`, `name` (`Sketch 1`), `gsec2d_ptr` | absent |
| `segtab_ptr` | `f8 06 f7 2f fb` with per-segment tables | absent |

So a solid feature's definition carries its **sketch and segment tables**, which describe the geometry the
feature was built from. That is the same boundary the `917` record reaches from the other side, and it is why a
parameter can be edited into a part that has a body but not synthesised into one.

### Where a Creo parameter lives: `FeatDefs` dimension records

Parameters come from the `FeatDefs` row (`Sld_FeatDefs`), which the datum-only control **does not have** — only
the ladder does. Its shape, decoded from the ladder's `5977`-byte payload (`1492` nodes):

```text
Sld_FeatDefs
  feat_defs_949            list[1]
    id, symbol_key, model_type, group_info_ptr, place_rec_ptr, own_ref_id, orient,
    trf_arr, type, key, idx, transf, plcm_revnum, next_prop, cond_tbl_idx, comment,
    merge_info_ptr, state_ind, alumni_info, sub_feat_arr
```

and inside a feature definition, the dimension table:

```text
dimtab_ptr        t00, count 2
  type            1
  value           t02 double      <- the dimension value
  direct          -1
  aux_value       t02 double
  ext_id          -1
  dispdimattr     0
  dimattr         list[7]
  dim_ref         t00, count 7
    item_id, sense, point[2], relat_ptr
      id 32770, used -1, a[4], b[4], c[3], sign, idim 32770, type 0, formula_ptr -1
```

The `value` nodes decode cleanly, and they match what the reader reports:

| Dimension offsets | Values |
| --- | --- |
| `1045`, `4728` | `-201.7190851617055` |
| `1186`, `4776` | `-338.93815066863453` |
| `1234`, `4824` | `-86.06680966899467` |
| `1282`, `4872` | `-154.4303300690026` |

which is exactly the reader's eight parameters (four values, each appearing twice), so the dimension path is
understood end to end on the read side.

**Both pieces are now solved for one dimension.** `re/creo/tools/AddRow.py` renames the control's reserved
`157`-byte `EMPTY_SPACE_FOR_REUSE` row and writes a body into its region, so a section the part never had can be
added without touching the directory tables (the rebuild is byte-identical run to run), and
`Author.DefaultFeatDefs()` emits a `Sld_FeatDefs` row with one `dimtab_ptr` dimension. The part loads twice
(`End` plus `MT Part Solid`) and the dimension reads back as `Creo dimension 0 = 100.0`.

The earlier note about the two blockers is kept below because it explains why insertion looked impossible:

Generating one is blocked on two separate pieces, not one:

1. **the row has to exist first.** `Subset.Build` can only `Drop`, `Replace`, `KeepSpace` or `Blank` rows it
   already has; there is no insert path, and the datum-only control has no `FeatDefs` row to replace. Adding a
   row means extending the directory tables, which the subset tool does not do.
2. **the skeleton has no generator.** A `Sld_FeatDefs` row is `1492` nodes of feature-definition structure, of
   which the dimension table is a small part; nothing in `Author.py` emits any of it.

### `SolidPersistTable` and `SolidPrimdata` are display tables, not B-rep

Both rows are Unix-compress streams (`1f 9d`) and both are ordinary token format once decompressed —
`1125` bytes to `1788`, and `235` to `301`. Their contents:

| Row | Root | Fields |
| --- | --- | --- |
| `SolidPersistTable` | `pgl_persist_table` | `table_id`, `srf_prim_data_refs`, `appdatakeysH`, `fontsH`, `linestylesH`, `colorrefsH`, `imagesH`, `texturesH`, `mrshadersH`, `appearancesH`, `surfpropsH`, `symbolsH`, `segmentsH`, `gpurefsH`, `segmentrefsH` |
| `SolidPrimdata` | `pgl_primdata_group_table` | `pgl_primdata_groups_arr` → `pgl_primdata_group` → `segref_array` → `pgl_segref` → `p_seg_persistref` → `primdata_container` → `pgl_primdata` |

So they are the **display pipeline's persistence state** — hash tables of style objects, GPU references,
segments and LOD primdata groups — not the boundary representation. The B-rep is in `VisibGeom` and the
feature records, both of which are already authored.

The entries carry save-time state: object ids, `change_count` values (`29`, `26`, `14`, `13`), appdata rows
named `COLOR_INDEX` and `__pgl_segment_id__`, and LOD values. In the datum-only control they still hold two
segments and two primdata groups.

**Both rows are required.** Dropping them is refused with an explicit message, as is dropping the display
rows:

```text
nosolidtbl: 28275 bytes; rows 50; dropped SolidPersistTable, SolidPrimdata
!%CE06:23:43  'nosolidtbl.prt' cannot be retrieved.

nodisp: 28154 bytes; rows 49; dropped CGFPersistTable, DispDataTable, THMB_IMG_MAIN
!%CE06:24:49  'nodisp.prt' cannot be retrieved.
```

That fits the earlier finding that only trailing rows (`IndentTag`, `FeatRefData`) may be dropped: the
container's row set is otherwise fixed.

**They parse once the double lane is decoded.** The divergence was at offset `94` of the decompressed
`SolidPrimdata`, on `lod_value`: the value there is `2f 30 00`, which is the prefix `2f` followed by an ASCII
decimal string and a `00` terminator, so `lod_value` is `0.0`. `ReadDouble` did not know that lane, so its
fallback advanced eight bytes and returned `None`, swallowing the next field's header.

With the lane decoded, `SolidPrimdata` parses coherently — `30` nodes, consuming exactly `301` bytes:

```text
pgl_primdata_group_table   t00 record
pgl_primdata_groups_arr    t00 [2]
pgl_primdata_group         t00 record
lod_value                  t02 0.0
segref_array               t00 [5]
pgl_segref                 t00 record
p_seg_persistref           t00 record
```

and the earlier mis-assignments are gone: `segref_array` is an array of `5`, not the scalar `114`, and
`pgl_segref` / `p_seg_persistref` are records, not single bytes.

**The lane has to be scoped, not global.** Treating any `2f` as a decimal string drops the ladder from
`8` parameters to `0`, because the same byte appears in `FeatDefs` doubles in a different sense. The reader
therefore only takes the decimal form when the bytes up to a nearby `00` are all digits or signs, and falls
back to the previous behaviour otherwise. With that guard the control still reads `4` features and the ladder
still reads `7` features, `8` parameters, `6` faces, `12` edges, one solid and volume `18482541.490319017`.

**The silent fallback cannot yet be made loud.** Making it raise was tried, and the failures are wider than
the feature section:

```text
ladder1.prt.2: 33 rows parse, 25 raise
  VisibGeom   -> Creo double lane 0x59 at 612 is not decodable
  AllFeatur   -> Creo double lane 0x57 at 6347 is not decodable
  FeatDefs    -> Creo double lane 0x00 at 921 is not decodable
```

Those three are exactly the sections the adapter reads, and with the raise enabled the ladder reads `0`
features instead of `7`. Across the whole empty control `20` of `56` rows raise.

The lanes themselves are not the obstacle. Inspecting the survivors shows the parser has already slipped
before the raise fires: around offset `6347` the bytes are
`e3 52 80 cb 00 e4 e3 57 80 c8 07 00 e3 59 80 c8 06 00 …`, where `52` was taken as a full 9-byte double and
swallowed `e3 57 80 c8`, and the values `52`, `57`, `59`, `5b`, `5d` are object ids in an id-table, not
doubles. So the raise is pointing at an alignment error upstream, not at a missing double lane.

The selector convention was also checked, because the csys record showed a selector naming the field *before*
the resumed value. The reader's convention is `Index = selector - 1`, and the alternative
(`Index = selector`) is **wrong**: it drops the control from `4` features to `1` and the ladder from `7`
features to `1`. So selectors are handled correctly and are not the alignment fault either.

Instrumenting the selector branch (offset, selector, resolved field name, type) answers part of this. The
ladder's `AllFeatur` resolves **56** selectors and every one names a sensible field — `extnd_rev_tab`,
`fc_hist`, `srf_id_tab_ptr`, `edg_id_tab_ptr`, `parent_table`, `bnd_type`, `crv_type`, `list_id`,
`layer_list` — so the selector mechanism itself is sound and the resolved indices are not garbage.

The field table is sound too, and an earlier guess of mine is wrong: the section contains exactly **149**
`e0 <type> <name> 00` headers and the parser learns exactly `149` fields. It is not inventing headers from
data. The ladder's records genuinely append fields — record one declares 71, and the solid records (`67`,
`75`, `74`) add more — which is why the count is far above 71.

### Two parser changes tried, neither moves the short mask

The 71 schema jumps in record `74` looked like a selector-driven table, so the selector branch was logged: only
**17** of the `311` field reads in that record are preceded by a selector, and each resolved name appears
exactly once. So the repetition is *not* selector-driven.

The repetition comes from the reader's positional rewind — `if Index >= len(Fields) and StructureStart:
Index = StructureStart[-1]` — which re-enters the field range when structure tracking drifts. Disabling it
changes the node count but nothing else:

| Measure | Baseline | Rewind disabled |
| --- | --- | --- |
| `AllFeatur` nodes | `1007` | `941` |
| bytes consumed | `7838` | `7838` |
| record `74` mask slots (offset `6393`) | `0` | `0` |
| ladder features / params / faces / edges / solid / volume | `7 / 8 / 6 / 12 / 1 / 18482541.4903…` | identical |

Together with the earlier inline-record attempt (mask `0` → `3`, but `VisibGeom` broke: `6` faces → `5`,
volume → `None`), the position is:

- the mask count is *alignment-sensitive* — the inline change moved it — so `0` is probably an artifact;
- no change tried so far makes it correct without breaking something else;
- the reader's headline results are unaffected by all of this, because they come from feature markers,
  `FeatDefs` and `VisibGeom`, not from record `74`'s node labels.

A single document cannot distinguish "the `917` records carry a table here" from "the reader is one field off".
That is now the only open question in the feature section, and it is not answerable from the two oracle files.

### Record-by-record diff against the learned schema

Counting, per record, how many fields the parser reads and how often the schema index jumps:

| Record | Class | Fields read | Index jumps | Last index |
| ---: | ---: | ---: | ---: | ---: |
| `7` | `923` | `75` | `2` | `73` |
| `5` | `923` | `75` | `2` | `73` |
| `3` | `923` | `75` | `2` | `73` |
| `11` | `979` | `79` | `8` | `73` |
| `67` | `917` | **`315`** | `31` | `73` |
| `75` | `917` | `75` | `2` | `73` |
| `74` | `917` | **`311`** | **`71`** | **`148`** |

Three facts fall out. The datum records all read `75` fields with two jumps — clean. Records `67` and `74`
read `315` and `311` fields, numbers of the same size as a mask (`311` slots), and record `74`'s last index is
`148` against a schema of `149`. Its node list contains `transform`, `flags` and `cr_flags_xar` **repeated**
(`transform` twice, `flags` nine times, `cr_flags_xar` twice), which is what re-reading the same field range
again and again looks like.

So `67` and `74` carry long tables whose entries walk a *sub-range* of the schema repeatedly, and our parser
labels each entry with those fields' names.

The parse is nevertheless self-consistent about extent and identity: `AllFeatur` consumes `7838` of `7838`
bytes, all seven feature ids come out (`7`, `5`, `3`, `11`, `67`, `75`, `74`) and six of the nine masks read
`311` or `278` slots. So the record boundaries are right and the labels inside the `917` records are wrong.

That is the precise state of the question: **not** a lost or duplicated record, but a mislabelled table inside
the `917` records, with one mask (`record 74`, offset `6393`) short at `0` slots. Whether the vendor's `917`
records legitimately carry a table at that position — in which case our schema names are simply not applicable
there — or whether the reader enters it one field off cannot be decided from a single document.

### Retraction: that form is normal, and "fixing" it breaks VisibGeom

The form was implemented — after `f8 <count> f7 <field> fb`, consume `<count>` `e3`-opened structures instead
of reading them as fields — and measured:

| Measure | Before | After |
| --- | --- | --- |
| ladder `AllFeatur` mask slots for record `74` | `0` | `3` (still wrong; others are `311`/`278`) |
| ladder `AllFeatur` nodes | `1007` | `882` |
| ladder surfaces / edges / solid / volume | `6` / `12` / `1` / `18482541.4903…` | **`5` / `6` / `0` / `None`** |

The regression is decisive: `VisibGeom` uses exactly the same form for `srf_array` — `f8 06 f7 03 fb`
followed by six `e3`-opened surface records — and that is how the reader correctly finds `6` surfaces. So the
records after such an array are the array's elements and reading them positionally as fields is **correct**.
The change was reverted.

Which means the earlier claim on this page is wrong: this form is not a defect and does not explain the
record-`74` drift. What the measurement does confirm is narrower and still useful — the record-`74` region
genuinely mislabels table bytes as `fc_hist`/`transform`/`flags`, and its mask parses short, while every other
record parses `311` or `278` slots.

### The real defect: reference arrays carry their records inline

Logging every field the parser reads inside record `74` shows the divergence concretely. Around `6341`:

```text
6341..6346  fc_hist        52 80 cb 00 e4
6346..6347  save_geoms     e3
6347..6387  transform      57 80 c8 07 00 e3 59 80 c8 06 00 e3 5b 80 c8 05 00 e3 5d 80 c8 04 00
6388..6393  flags          f8 0c f7 74 fb
6393..6393  cr_flags_xar   (empty)
```

Those bytes are not a transform. They are a **table of records**: ids `57`, `59`, `5b`, `5d` with the counter `7, 6, 5, 4`, each opened by `e3`, and they end at the header
`e0 00 edg_id_tab_ptr 00` — a field the parser then reads *again* later, because it never consumed the table.

The form that causes it is a reference array:

```text
f8 06  f7 1d  fb     <- array of 6 elements, each is a record of field 0x1d, then close
e3 <id> ...          <- the six inline records follow here, opened by e3
```

`f8 <count> f7 <field> fb` declares the array and closes it immediately; the records themselves are written **inline after the array**, opened by `e3`. The same form appears in the control's csys record, where `misc_id_tab_ptr` is `f8 01 f7 4d fb` followed by a bare `e3`. Our reader treats those inline records as *subsequent fields*, so it drifts from that point on.

That single mechanism explains all three symptoms at once: the empty `cr_flags_xar` in record `74` (the parser is reading table bytes by then), the "unknown double lanes" (`0x57`, `0x59`, `0x00`) that block the loud raise, and why the earlier csys work needed a bare `e3` whose owner was never identified.

The fix is a parser change, not a data-model one: after reading a reference array whose elements name a field, read `count` inline records of that field's shape instead of continuing positionally. It is not implemented yet.

What remains is a *type* mismatch rather than an index mismatch. In record `74`, which begins at `6267`,
the field at `6347` is typed `t02` (double) but its bytes are an id table — `52 80 cb 00 e4 e3 57 80 c8
07 00 e3 59 80 c8 06 00 …`, where `52`, `57`, `59` are ids — and that record's `cr_flags_xar` comes out
with `0` slots while every other record has `311` or `278`. Reading those bytes as doubles is what makes the
loud raise fire at `0x57`.

So the defect is localised: the schema position reached in the solid records does not carry the type the
vendor wrote there. That is either a genuine schema difference between record one and the appended fields, or
a place where a selector resumes at the wrong field. Distinguishing those two needs a second saved document;
with one file it cannot be settled, and guessing has already produced two wrong answers on this page.

 Scanning the section for `0xf7` bytes is not a valid
measurement — the byte occurs inside ordinary values, and a naive scan reports "selectors" like `581633` —
so the selectors have to be observed through the parser, not by byte search.

Two sentinel lanes were tried and are **not** in the code because neither changed any measurement:
`0xf6` (null) and `0xf5` (negated integer) inside a double lane. With and without them, the ladder's
`AllFeatur` parses to `1007` nodes at `7838/7838`, and `SolidPersistTable`, `SolidPrimdata` and `VisibGeom`
parse identically (`357`, `30` and `2` nodes). The only lane that mattered was the `2f` decimal string.

**Re-emitting them byte-identically is not the goal anyway.** A parsed vendor row re-emitted is a recorded
payload replay, which the no-donor standard forbids in `src/`. These rows have to be generated, so the
useful output of parsing is field semantics.

### The `ND:*` token tables

The three `ND:*` rows are not display data and not simple shapes. Each decompresses to a `PSB_Tokens`
record with four parallel arrays:

| Field | Content |
| --- | --- |
| `format` | `0` |
| `type_har` | one type letter per token (`77`, `79`, `70`, `81`, `67`, `73` …) |
| `int_har` | one integer per token, including `-1` and `-2147483648` sentinels |
| `double_xar` | doubles for the tokens that need them, null otherwise |
| `string_xar` | identifiers such as `ndmoddeps_j03::ModelDescriptor_J03`, and in the model table the original part name |

So they are **per-schema streaming tables**: a token list describing how the model's fields were
serialised, with the vendor's own class identifiers in `string_xar`. Replacing one with a minimal
`PSB_Tokens` root is rejected (`dbg_err_crash`), and the unwrapped sizes are `1662`, `907` and `1490`
bytes.

### The model table is smaller than it looked

The `expanded` column overstates it. `ND:0:Model_L05_PX:1` decompresses to **142 bytes**, and it holds
only three things: the `PSB_Tokens` root, `format = 0`, and a single `type_har` array. There is no
`int_har`, no `double_xar` and no `string_xar` in this row — the richer rows are the unit-system and
PDM-trail tables.

The `type_har` array declares `317` entries and decodes to 317 letters over 13 distinct values:
`C F H I M N O P Q R S T U`.

```text
MOMOIOIOIOIOFCOFOMOFOMOFOFOFOFCCONOMOPQMOMOMOFOICOHONCOMOIOIOFONONOSTFTFTFUOMOFC
```

317 is close to the number of typed fields the model actually declares, so these letters may be one type
letter per serialised field rather than an opaque blob. If that holds, the table is **derivable** from the
field list our own reader already decodes, which would make it the first remaining row with a generative
path rather than a transcription.

That was a hypothesis, and it is now tested and rejected.

| Enumeration over the control's sections | Count |
| --- | --- |
| field definition sites (`e0 <type> <name> 00`) | `1855` |
| unique `(type, name)` pairs | `947` |
| nodes produced by `StreamParser` | `42145` |
| distinct type ids present | `8` |
| letters in `type_har` | **`317`** |

None of those enumerations yields `317`, and the parser over-produces badly on replay records, so the
letter list cannot be produced by walking the fields we can decode. `317` is therefore not a count of the
model's field declarations in any form we can enumerate; it is a token count for the vendor's own
serialised `Model_L05_PX` object, which our reader never reconstructs.

The same applies to the unit-system and PDM-trail tables, which carry `string_xar` entries naming vendor
classes such as `ndmoddeps_j03::ModelDescriptor_J03`.

So the `ND:*` rows are **not derivable** from what we can decode. They are one more instance of the same
pattern as the mask vector: per-schema payload that a generator cannot compute from a record's own
fields.

They are also **load-bearing**: dropping all three, together with the two trailing `IndentTag` and
`FeatRefData` rows and keeping the 41 authored sections, is rejected with an explicit message.

```text
nodrop: 41 authored sections, 5 rows dropped; 24852 bytes (control 81539)
!15-Nov-26 05:22:02  End   C:\Mac\Home\Documents\creo-authored\nodrop.prt
!%CE05:22:02 'nodrop.prt' cannot be retrieved.
```

So unlike `IndentTag` and `FeatRefData`, the `ND:*` rows cannot be dropped, and they cannot be replaced
with a minimal form either (`dbg_err_crash`, earlier), and their content is not derivable. They have to be
present, well formed, and carrying the vendor's own schema token data.

That places them in the same category as the mask vector: structured schema payload that a generator cannot
compute from a record's own fields. The remaining rows split as:

| Row | Kind | Assessment |
| --- | --- | --- |
| `ND:0:Model_L05_PX:1`, `ND:0:UnitSystemDef_L03:1`, `ND:0:PDMTrail_L03:1` | schema token tables | vendor schema payload |
| `SolidPersistTable`, `SolidPrimdata` | persistence tables | undecoded |
| `DispDataTable` | display data | compressed, no decoder |
| `THMB_IMG_MAIN` | JPEG thumbnail | image payload |
| `CGFPersistTable` | gzip blob | opaque |
| `IndentTag`, `FeatRefData` | trailing sections | proven droppable |
| two `EMPTY_SPACE_FOR_REUSE` | padding | filler |

### Authored geometry is still rejected

Retested now that `AllFeatur` is authored rather than vendor: the control rebuilt with 42 authored
sections, where `AllFeatur`, `BasBasData`, `FeatDefsDtm` and 39 others are generated and `VisibGeom`
carries `Author.AuthorGeometryPayload` for a `100 x 60 x 40` box, is rejected twice.

```text
geom42 sections 42 bytes 30506 VisibGeom 1372
(no End line, no dbg_err_crash, exits twice)
```

The same container without the authored `VisibGeom` row loads three times out of three (`auth42`), so the
rejection is the geometry payload itself, not the rest of the part. That payload is six plane prototypes
with a `local_sys` lane; it has never been accepted by the vendor in any candidate.

The most plausible cause was that the surface prototypes carry `feat_id = 74`, a feature the authored part
never contains. `AuthorGeometryPayload` now takes `FeatureId` and `FirstGeomId`, so the surfaces can be
pointed at the datum that exists. Aligning them (`feat_id = 7`, geometry ids `1..6`) is also rejected:

```text
geomfeat: feat_id 7, geom ids 1..6
!15-Nov-26 05:05:14  Start C:\Mac\Home\Documents\creo-authored\geomfeat.prt
(no End line; repeated, second run identical)
```

So the reference mismatch was not the cause. The vendor payload was then used as the reference for a
byte comparison, and it exposed three defects in our emitter that are now fixed:

| Defect | Vendor | Ours before |
| --- | --- | --- |
| missing fields | `orient`, `boundary_type`, `next_geom_ptr` after `feat_id` | absent |
| compact double lane | `46`/`2d` prefix plus 7 payload bytes, any low byte | only when the low byte was zero, and it dropped it |
| arrays | `18` for `0.0` and `0f` for `1.0` inside `envlp`, `outline`, `local_sys` | full 9-byte `52` doubles |

With those fixed the payload matches the vendor **byte for byte for the first `138` bytes**, which covers
`geom_id`, `geom_type`, `feat_id`, `orient`, `boundary_type`, `next_geom_ptr` and the `envlp` array
introduction.

That is a prefix match, not a structural match, and the difference matters. Parsing the ladder's first
surface element (`652` bytes; each of the five replays is `120`) gives the full field list:

| Field | Value in the ladder's first surface |
| --- | --- |
| `geom_id` | `77` |
| `geom_type` | `34` |
| `feat_id` | `74` |
| `orient` | `-1` |
| `boundary_type` | `0` |
| `next_geom_ptr` | `82` |
| `envlp` | four doubles, `184.5078`, `86.0668`, `-154.4303`, `-115.6523` |
| `outline` | six doubles |
| `srf_prim_ptr(plane)` | **nested plane record** |
| `local_sys` | twelve doubles |
| `frst_cntr_ptr` | record: `frst_cntr_crv_hdr_ptr` `78`, `trv` `1`, `envlp`, `next_cntr_ptr` |
| `topol_ref_data` | record: `owner_feat_revnum` `13`, `srf_flip_dat`, `list_id` `-5778`, `list_type` `98` |

So our emitter covers the first seven fields and stops; the vendor record also carries a nested plane
primitive, a first-contour reference with its own envelope, and topology reference data. That is why our
payload is `399` bytes against `2899`.

All three nested structures are now emitted, and the surface record is **byte-identical** to the
ladder's first element:

```text
record 409  element 1 409  byte-identical: True
```

The conventions, decoded from the ladder payload:

| Field | Convention |
| --- | --- |
| `envlp` | four doubles: `(u0, u1, v0, v1)`; the ladder's first surface is `184.5078, 86.0668, -154.4303, -115.6523` |
| `outline` | six doubles, the same envelope with the two zero crossings interleaved |
| `srf_prim_ptr(plane)` | opens with `e3` and contains `local_sys`; it is **not** a separate payload |
| `local_sys` | twelve doubles in run-compressed lanes, e.g. `[1,0,0,0,0, 1,0,-1,0,0,0,0]` |
| `frst_cntr_ptr` | opens with `f1 e3`, so the close of the plane record rides inside its value |
| `frst_cntr_crv_hdr_ptr` | the surface's own id plus one, not `next_geom_ptr` |
| `topol_ref_data` | `owner_feat_revnum`, `srf_flip_dat`, `list_id` `-5778`, `list_type` `98`, then `f2` |

With those values replaced by a box's own envelope (`±extent`) the payload is still rejected: `geomv3`,
six byte-faithful surface records with `feat_id 7` and geometry ids `1..6`, exits silently twice. So the
record *shape* is right and the *content* is still not accepted, which points at what the record refers to
rather than at how it is encoded: `frst_cntr_crv_hdr_ptr`, `topol_ref_data` and the `next_geom_ptr` chain
all describe topology that a datum-only part does not have.

Four details cost a byte comparison each: doubles inside these arrays use the compact scalar lanes and
run compression; the close of the plane record belongs inside `frst_cntr_ptr`'s value; the contour header
pointer is `geom_id + 1`; and `srf_prim_ptr(plane)` wraps `local_sys` rather than carrying its own data.

The corrected payload is still rejected (silent exit twice), so the values matter too, but the emitter is
now structurally faithful rather than guesswork.

The write side therefore has two independent blocks, not one:

| Block | What it needs |
| --- | --- |
| schema payload | mask vector, `ND:*` token tables, `SolidPersistTable` |
| geometry | a `VisibGeom` surface set and a solid feature that the loader accepts |

### Authored sections

Forty-one of the fifty-four directory rows can be emitted from format knowledge and accepted by the
vendor loader; `FeatDefsDtm`, `BasBasData`, and `VisibGeom` are among them. What remains is
`AllFeatur`, the three `ND:*` `PSB_Tokens` tables, the persistence/tessellation rows, and the two
free-space extents.

### Feature record

`AllFeatur` is a linked list of feature records. The field inventory, the linked-list rules, and the
one undecoded field that blocks authoring (`cr_flags_xar`, 402 of the first record's 1620 bytes) are
in [the feature record page](FeatureRecord.md).

### Decoded feature chain

`re/creo/tools/TaggedStream.py` now decodes the full `AllFeatur` feature chain of both controls.
The chain is a linked list: `first_feat_ptr` points at the first feature, and each feature's
`next_feat_ptr` points at the next one. A zero `next_feat_ptr` ends the list.

| File | Feature chain |
| --- | --- |
| `empty/solid_start_part_mmks.prt` | `FRONT` (id 7, type 923), `TOP` (5, 923), `RIGHT` (3, 923), `DEFAULT_CSYS` (11, 979) |
| `ladder/ladder1.prt.2` | the same four, plus `id 67` (923), `id 75` (923), `id 74` (917) |

The chain matches the model tree Creo shows for both files.
Type `923` is a datum plane and type `979` is a coordinate system.
Type `917` is the additive section-sweep class that cadmpeg calls the extrude definition.
The ladder's sketch and extrude definition still live in `FeatDefs` (`Sld_FeatDefs`), not in
`AllFeatur`.

The grammar that makes the chain decode is recorded in
[the loader notes](../loader/Loader.md#tagged-stream-parser-status):

- the field table is global, and `f7 <id>` selects the id-th field;
- `f1`-`f4` close tokens may precede a value and pop structure levels first;
- `f8`/`f9` array counts are part of the first definition and are reused by later records;
- a field-level `e4`/`e5`/`e6` repeats the preceding logical value once, twice, or three times,
  and `e1` terminates a numeric array;
- `next_feat_ptr` restarts the field index at the feature schema's first field.

### Datum placement records

`FeatDefsDtm` (`Sld_FeatDefsDtm`) carries the datum placement records. The first record is the
`FRONT` datum:

```text
id = 7
symbol_key = -1
model_type = 2
local_sys = [0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1]
own_ref_id = -1
orient = 1
place_instruction_ptrs = [ref 11]
type = 515
offset = 1.0
dim_id = -1
ref_id = -1
geometry1_id = -1
geometry2_id = 8
memb_num1 = 0
memb_num2 = 0
attr = [32768, 0, 0, 0, 0]
plin_info_arr = [ref 21]
```

`type = 515` is the placement type, `offset = 1.0` is the placement offset, and
`geometry2_id = 8` is the reference geometry. `attr` is the datum attribute array.
This is the parametric placement of the datum plane, not just a name.

The `ent_outl` bounding-box matrix uses the world-coordinate token lane, not the hex-string
encoding. The `ugc_ieee_unformat_double` function reads a hex string where each byte's low nibble
is a hex digit, and stores the bytes into the double buffer from the end backwards. The `0x0f`
(0.0) and `0x18` (1.0) one-byte constants are handled by the caller, not the function.

The hex-string hypothesis is disproved for `ent_outl`: `0x46` is a valid hex digit but `0x6f` is
not, so the reader consumes one digit and fails. The bytes are world-coordinate tokens. In the
positional-outline/world lane, `46 <tail7>` reconstructs `40 <tail7>` (positive) and `2d <tail7>`
reconstructs `C0 <tail7>` (negative). The seven-byte sub-unit forms `4f <tail6>` and `d5 <tail6>`
reconstruct `3F <tail6> 00` and `BF <tail6> 00`. The `0x18` byte is the one-byte 1.0 constant.

The empty control's `ent_outl` decodes to
`[254.33012701892218, 254.33012701892218, 1.0, -254.33012701892218, -254.33012701892218, 1.0]`,
a square in homogeneous coordinates. The ladder's `ent_outl` decodes to
`[186.8986780200836, -0.000125701882057086, 1.0, -156.82118748945425, -272.72085742045164, 1.0]`,
a rectangle in the sketch plane. The ladder's `outline` decodes to
`[186.8986780200836, 1.0, 118.04313291316248, -156.82118748945425, 1.0, -88.45766708944632]`.
The `VisibGeom` plane prototype's `envlp` decodes to
`[184.50782059963194, 86.06680966899467, -154.4303300690026, -115.65227549271083]` and its
`outline` to
`[184.50782059963194, 1.0, 115.65227549271083, -154.4303300690026, 1.0, -86.06680966899467]`.

### Feature definitions

`FeatDefs` (`Sld_FeatDefs`) carries the feature definitions. The ladder's first definition is the
extrude feature:

```text
id = 66
symbol_key = -1
model_type = 2
local_sys = [0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1]
own_ref_id = -1
orient = 0
trf_arr = [ref 11]
type = 1
key = -1
idx = 0
transf = [1.0, RawDouble(...)]
plcm_revnum = None
next_prop = None
cond_tbl_idx = -1
comment = None
merge_info_ptr = None
state_ind = -1
alumni_info = None
sub_feat_arr = [ref 23]
id = 0
type = 160
sub_type = -1
data(subft_indexnumber) = { index = 1, tool_type = 60001, sep_index = -1 }
expl_state_ref = None
feat_outl_info = { ent_outl = [...] }
max_text_len = 85
```

`type = 160` is the feature definition type and `tool_type = 60001` is the extrude tool type.
The parser stops at `0x3be` because the flat field-index approach does not handle the nested
structures in `FeatDefs`; the field table is global but each structure has its own schema.

### Loader-confirmed record schemas

The `metatoolsapi.dll` `CreoSerializer` exports give the authoritative field order and types for the
high-level records. The full field tables are in [the loader notes](../loader/Loader.md).

`CreoDesignatedItem` is the live feature-tree record:

```text
Id, Type, SubType, DsgnName, CreoName, OwnerId, OwnerType, ModelLikeAttr,
FeatureStatus, FeatureInStockAttr, Symbols, KeyPropsFlag
```

`Symbols` is a sequence of `CreoParameter`. `OwnerId` and `OwnerType` are the parent links.

`CreoParameter` is the dimension record:

```text
CreoParameterValue, CreoParameterDef, CreoModel, CreoName, IsReadOnlyInProE,
IsReadOnlyInDB, IsSystemParameter, DBName, ValueType, Default, Restriction,
AccessTbl, DefinitOwner, IsChanged, QuantType, Description, Class, Label
```

`CreoParameterValue` is the value record:

```text
Integer, Bool, Real, DoubleEpsilon, Unit, String, DateTime, Icon, Link, User,
CreoQuantType, Length, Time, Mass, Temperature, Current
```

`Real` is the numeric value, `Unit` is the unit token, and `CreoQuantType` selects the quantity
family. A writer that emits `Real` without `CreoParameter` identity and `CreoQuantType` would produce
a dumb number, not a driving dimension.

`CreoItem` is the model-level record. Its `CreoDesignatedItems` field is the feature sequence, its
`CreoModelParameters` field is the parameter table, and its `CreoDependencies` field is the
dependency table.

## Units

`UnitSystemDef` carries the active unit system.
Observed selectors include:

| Selector | System | Length scale |
| ---: | --- | --- |
| 50 | CGS | 10 mm per stored unit |
| 51 | mmNs | 1 mm per stored unit |
| 54 | inLbmS | 25.4 mm per stored unit |
| 55 | mmKs | 1 mm per stored unit |

The `string_xar` names can include `Offset` and a unit token.
The active selector is the authoritative value when present.

## Parameters and expressions

Dimensions are stored as parameter references.
A driving dimension needs:

- parameter identity;
- value and unit;
- expression or relation source;
- owner feature and sketch;
- referenced entities;
- configuration overrides.

The field map for relations and configurations is partial.
A writer that emits a number without its parameter identity would produce a dumb shape and fail the parametric criterion.

## Derived and bookkeeping data

B-rep caches, display strips, view state, timestamps, session ids, and checksums are derived or bookkeeping.
They must not be copied between documents.
The source-preserved replay path can keep them only because the output is the same document.

## Open questions

- The per-field transition cache is not fully mapped.
- The geometry prototype lanes have unresolved scalar prefixes.
- The feature definition schema is not closed for every family.
- The unit selector must be read from the section, not from a fixed default.
- The writer must reproduce every authored record and recompute every derived record from the neutral model.

## Sources

- [Cadmpeg Creo specification](https://github.com/cadmpeg/cadmpeg/blob/main/docs/formats/creo_prt.md), CC-BY-4.0
- [TeamCraft Creo research](https://github.com/rudalabs/TeamCraft/blob/main/docs/src/research/creo-brep-preview.md)
- [Container findings](Container.md)
- [Writer gap](../open-items/WriterGap.md)
