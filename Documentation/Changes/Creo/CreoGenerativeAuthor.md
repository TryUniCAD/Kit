# Creo generative author

## Change

Adds `src/convert/adapters/creo/Author.py`, the first generative Creo PSB writer. It authors a part
from format knowledge only: no captured section bytes, no templates, and no donor file.

## Current status

Read side: complete for the retained control. It decodes `7` features, `8` parameters, `6` faces, `12` edges,
one solid and volume `18482541.490319017`, and a no-op container rebuild of the `81539`-byte control is
byte-identical.

Write side: **partial, and not vendor-loadable for anything with geometry.** What Creo has accepted:

| Candidate | What is authored | Creo |
| --- | --- | --- |
| `auth4` / `fullgen` | 41 of 54 directory rows, including a fully generated four-record `AllFeatur` (zero vendor bytes) | loads, 2 of 2 |
| `featdefs` | 42 rows, plus a generated `FeatDefs` carrying one dimension, read back as `Creo dimension 0 = 100.0` | loads, 2 of 2 |
| `fd_two` | 42 rows, `FeatDefs` with **two** dimensions, read back as `100.0` and `42.5` | loads, 2 of 2 |

Everything else fails. The authored part reads back as `4 features, 1 param, 0 bodies`, so there is **no
body count, volume, centre of mass or dimension rebuild measured in Creo** and these acceptance criteria are
not met. `Writer.py` therefore reports `mode=exact_native_roundtrip`, `vendor_loadable=False` and
`application_usable=False`.

The measured blocks, each with its evidence further down:

- **body geometry.** A class-`917` record declares 37 fields of revision/reference bookkeeping
  (`comp_hist`, `coll_refs_info`, `rev_info_arr`, `mdl_geom_rev`, `aggr_rev_info`), not a parametric
  description. A structurally correct `917` with those fields nulled is refused, twice, as is a `917` replay
  carrying datum values and a `923` replay carrying the csys id. Authored `VisibGeom` is refused as well, so
  surfaces cannot precede the solid that owns them.
- **13 required vendor rows.** Three `ND:*` token tables, `SolidPersistTable`, `SolidPrimdata`,
  `DispDataTable`, `THMB_IMG_MAIN`, `CGFPersistTable`, two kind-`b` rows and two free-space extents. Dropping
  them gives `cannot be retrieved`; the `ND:*` tables are also not derivable from our field enumeration and
  not replaceable. `SolidPersistTable` and `SolidPrimdata` are display-pipeline state, not B-rep.
- **`DispDataTable` does not decompress**, and it is the only compressed row whose directory kind is `c`
  (`a` and `12` decode; `maxbits`/block-mode flags are identical for all of them, and the width-growth
  threshold was tested at four offsets). Its third code is `302` against a table of `258`, which cannot follow
  its first literal, so `kind c` most likely uses a different codec. Latent, because display data is never
  consumed.

The ground-truth corpus the playbook asks for does not exist: `re/creo/oracle/` holds two documents, and four
`-uitrail` invocation shapes failed to make Creo replay a trail, so a corpus cannot be generated headlessly
here.

## Behaviour

`BuildContainer` writes the ASCII `#UGC:2` header, the `#- CMNM`/host lines, the product banner, the
`#UGC_TOC` directory, and each `#<name>\n` section body. The header base is computed from the real
byte offset of `#-END_OF_UGC_HEADER`.

`AuthorFeaturePayload` writes the `AllFeatur` tagged stream: `Sld_Features`, `first_feat_ptr`, each
feature's `id`/`type` pair, `next_feat_ptr` links, and a zero terminator.

`AuthorGeometryPayload` writes `VisibGeom` with six plane prototypes of a box. The first prototype
defines the schema (`geom_id`, `geom_type`, `feat_id`, `envlp`, `outline`, `local_sys`); the other
five replay positionally after `e3 <id> 34 74` boundaries. `local_sys` is emitted as the twelve
compact-lane slots that `DecodeLocalSystem` reads back.

The surface record itself is byte-identical to the ladder control's first element (`409` bytes), but a part
carrying authored `VisibGeom` is **not** accepted by Creo — every such candidate exits with no `End` line.
The prototypes reference topology that a datum-only part does not have.

`AuthorPart` and `AuthorBox` return the complete file bytes.

## Verification

Authored and read back through the production adapter:

```text
AuthorBox((0,0,0), (100,60,40))
features 5  bodies 1
faces 6  vertices 8  volume 240000.0
centroid (50.0, 30.0, 20.0)

AuthorBox((-10,0,-5), (10,20,5))
faces 6  vertices 8  volume 4000.0000000000005
centroid (0.0, 9.999999999999998, 0.0)
```

Both volumes equal the analytic box `dx*dy*dz`. The authored bytes are 2050 for the 100x60x40 box,
and the file comes solely from the emitters in `Author.py`.

`TestAuthoredBox` asserts the 100x60x40 case: 5 features, one body, 6 faces, 8 vertices, volume
240000.0, centroid (50,30,20).

The retained ladder control still reads `volume=18482541.490319017`,
`centroid=(15.038745265314674, -135.165, 14.792732911858081)`, `valid=True`.

Creo 2027.2 in Parallels was launched on the authored file with `-g:no_graphics`. The trail file
records that it was rejected:

```text
!15-Nov-26 00:44:09  Start C:\Mac\Home\Documents\creo-authored\box.prt
!%CE00:44:09 The file C:\Mac\Home\Documents\creo-authored\box.prt is not a valid PART file.
!%CE00:44:09 'C:\Mac\Home\Documents\creo-authored\box.prt' cannot be retrieved.
```

So the authored bytes round-trip through this reader but are **not** vendor-loadable. No Creo body
count, volume, or centre of mass exists for authored output.

Two container bisection steps were measured, and both still fail:

1. Replaced the short header with the vendor-shaped 70-byte header lines (`#- VERS`, `#- HOST`,
   `#- UOBJ_ID`, `#- CMNM <len><name>`, `#-END_OF_UGC_HEADER`). The computed base became `0x2cc`,
   the same value a vendor part reports. Creo still rejects with "not a valid PART file".
2. Changed the table row's numeric column from `-1` to `1` and relaunched. Same rejection.

3. Computed the table checksum column. The first checksum is `sum(stored section body) & 0xffff`;
   this was verified against five vendor sections (`BasicData f9f2`, `MdlStatus 96df`,
   `SolidPersistTable d31f`, `VisibGeom 0d36`, `AllFeatur e3e0`). Creo still rejects.
4. Added generated empty `BasicData`, `MdlStatus`, `SolidPersistTable`, `FeatDefs`, and
   `FeatDefsDtm` sections alongside `VisibGeom` and `AllFeatur`. Same rejection.

The remaining differences are the second checksum column, the first-line numeric tokens, and the
real bodies of the core sections. An empty struct is not a valid `BasicData` or `MdlStatus`.

## Loader evidence

`ugc_read_toc_from_file` (`coreutils_sh.dll` RVA `0x10d860`) routes version 1934 files through
`FUN_1800ede70`, which reads table lines and calls `FUN_1800efb40` per row. The row parser is:

```c
pcVar5 = "%ws %llx %llx %d %d %d %d %04x %04x";
/* newer tables: */
pcVar5 = "%ws %Lx %Lx %Lx %d %x %d %x %x";
pro_sscanf(param_1, pcVar5, lVar3, lVar3 + 0x88, lVar3 + 0x90,
           puVar6, ..., lVar3 + 0xb0, lVar3 + 0xb4);
```

So both checksum columns are parsed into fields and are **not computed or validated** by
`coreutils_sh.dll` at table-read time. That makes the second checksum unlikely to be the reason
Creo rejects the authored file.

`FUN_1800fbda0` then reads a binary tag section. The Ghidra data at `DAT_180205de0` is the UTF-16
string `AppendTOC`, so that path is an optional appended table, not the model payload. The
rejection "not a valid PART file" is a model-layer check after the container parses.

## Creo harness control

The same launch path was run on the retained vendor empty control (research oracle, not shipped):

```text
!15-Nov-26 00:54:44  Start C:\Mac\Home\Documents\creo-authored\control.prt
!LIGHT_FIX_MODEL_RMODE is 51
!15-Nov-26 00:54:45  End   C:\Mac\Home\Documents\creo-authored\control.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

No "not a valid PART file" line. So the harness and licensing work, and the rejection is specific to
the authored content, not to the headless launch.

## Container layout facts

Rebuilding the vendor control with byte-identical section bodies still fails, which exposed three
layout rules the author did not yet model:

- sections are separated by a literal `#\n` line that is **not** counted in the stored length
  (`Model_L05_PX` ends at `0xd8c+1252`, the next section starts at `+2`);
- the directory contains a `NEXT_TOC_ENTRY` row pointing at a continuation table
  (`105a7 747 0 1934 1 -1 0000 0000` in the control), so a part has two tables;
- the seventh column is `-1` for plain `kind 9` sections and `1` for compressed `kind a` sections.

`Author.py` now emits `-1` for plain sections.

## Geometry isolation experiments

`VisibGeom` body zeroed in place, same length and directory (vendor model otherwise untouched):

```text
!%CE01:02:15 Could not retrieve part "...corrupt.prt".
```

So the vendor model validates `VisibGeom`; zeroing it fails the load.

Authored `VisibGeom` appended to the vendor control and the directory row repointed to it, so no
other byte or offset changes:

```text
!15-Nov-26 01:03:19  Start C:\Mac\Home\Documents\creo-authored\vg2.prt
!%CI01:03:23  dbg_err_crash() - continuing from serious error (ORDER_DEBUG).
```

No "not a valid PART file" and no "cannot be retrieved", but also no "End" and no
`MT Part Solid`, so the open did not complete. The authored geometry is therefore not proven
valid, but the failure is now model-level rather than container-level.

## Byte-identical layout model

A no-op reconstruction of the vendor control now reproduces all `81539` bytes exactly:

```text
header + banner
TOC 1 head + rows                     @0x31b, 32 rows
sections 1                            @0xd8c..0x10871, 52 sections, exact gaps
TOC 2 head + rows                     @0x10873, 22 rows
sections 2                            @0x10fba..0x115a6, 2 sections
TOC 3 head + rows                     @0x115a6, 128 rows
trailing bytes                        @0x13e77..end, 12 bytes
```

The rule that made it work: sections are physically sorted by offset and each carries its own
follow-on gap bytes (`#\n` internally), so the stream must be copied by physical order rather than
by table row order. `EMPTY_SPACE_FOR_REUSE` is a free-space extent, not a zero-length row.

The regenerating emitter now reproduces the control byte-for-byte (`81539` bytes) with all three
tables rewritten. Rules found while matching the directory text:

- column 7 is `-1` for kinds `9`, `11`, `b`; `2` for kind `12`; `1` otherwise;
- `TOC 3` declares 128 rows but holds only 2 real rows; the other 126 are 80 `#` bytes plus newline;
- the file ends with `#END_OF_UGC`.

## Geometry isolation result

With the emitter proven byte-identical, only `VisibGeom` was replaced by the authored payload and
the sections after it shifted by the length delta. That candidate parses further than every earlier
attempt:

```text
!15-Nov-26 01:11:39  Start C:\Mac\Home\Documents\creo-authored\swap.prt
!%CI01:11:43  dbg_err_crash() - continuing from serious error (ORDER_DEBUG).
```

No `not a valid PART file`, no `cannot be retrieved`, but also no `End` line and no
`MT Part Solid`. So the container and directory are now valid, and the failure has moved to model
load. The authored `VisibGeom` payload is therefore rejected.

Reverse swap: the authored container carrying the vendor `VisibGeom` body is rejected again:

```text
!%CE01:13:51 The file ...rev.prt is not a valid PART file.
```

So the authored container is *also* not a valid model: a two-section part with only `AllFeatur`
and `VisibGeom` is missing the model payload Creo requires. The isolation matrix is:

| Container | Geometry | Creo result |
| --- | --- | --- |
| vendor (byte-identical rebuild) | vendor | loads (`End`, `MT Part Solid`) |
| vendor (byte-identical rebuild) | authored | model-load crash |
| authored (`Author.BuildContainer`) | vendor | not a valid PART file |
| authored (`Author.BuildContainer`) | authored | not a valid PART file |

Both halves still fail. Vendor loadability needs the real model sections, not just a valid
directory.

## Section-requirement bisection

`re/creo/tools/Subset.py` was added to rebuild the vendor control from its own directory, rewriting
every row, every `NEXT_TOC_ENTRY` link, and every section offset. Its no-op rebuild is byte-identical
to the control (`81539` bytes), so the container is settled and the bisection is about section
content, not layout.

Each row below is one Creo 2027.2 launch on a rebuilt control:

| Change | Creo result |
| --- | --- |
| none | loads: `End`, `MT Part Solid` |
| drop `IndentTag`, `FeatRefData` | loads: `End`, `MT Part Solid` |
| drop `Notes` | `'dropn.prt' cannot be retrieved` |
| drop `PipeInfos` | `'droppipe.prt' cannot be retrieved` |
| drop 21 display/view/thumbnail sections | `'dropdisp.prt' cannot be retrieved` |
| drop `Notes` row, keep its extent and every offset | `'resnote.prt' cannot be retrieved` |
| keep all rows, blank 8 text/display bodies | `Could not retrieve part` |
| vendor container, authored `AllFeatur` only | model-load crash, no `End` |

So the failure is not offset drift (the keep-space run preserves every absolute offset) and not one
display family (a single 21-byte section is enough). Creo validates the whole section set, and the
only proven-optional rows are the two trailing table-3 sections.

A generative author therefore has to emit all 52 section extents with readable bodies. There is no
minimal-part shortcut, and the two-section authored container is not a valid model regardless of how
clean its directory is.

## Authored section bodies

Eleven section bodies are now emitted from the tagged-stream grammar rather than the container
alone. Each builder is a small set of grammar operations: a named struct header
(`e0 00 <name> 00`), a compound begin (`e2`/`e3`), a close (`f1`-`f4`), a null struct
(`e0 00 <name> 00 e1`), a typed field (`e0 <type> <name> 00 <value>`), and an integer array
(`e0 01 <name> 00 f8 <count> <ints>`).

`Author.AuthoredSections(FeatureClasses)` returns:

```text
AssMrgPrt      BasFullData   DispDataColor   FamilyInf      FeatDefsIndex
Hatching       NeuAsmSld     Notes           NovisGeom      PipeInfos
Xsections
```

Every builder reproduces the retained control byte-for-byte, so the grammar is confirmed rather
than approximated:

```text
sections: 11  mismatches: []
```

The one model-dependent value is `FeatDefsIndex`, which carries the feature classes present. It is
emitted from the caller's feature list, not from the file.

Creo 2027.2 was then launched on the control container with all eleven bodies replaced by these
builders, and `FeatDefsIndex` widened from two classes to three (`923, 979, 917`) so the candidate
differs from the control by content, not only by layout:

```text
wrote 81541  delta +2  sections 11
!15-Nov-26 01:31:22  Start C:\Mac\Home\Documents\creo-authored\auth11.prt
!15-Nov-26 01:31:22  End   C:\Mac\Home\Documents\creo-authored\auth11.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

So eleven authored section bodies are accepted by the vendor loader, including one whose content
differs from the control.

Two caveats are measured, not assumed. Truncating the authored `Notes` body to
`e0 00 Sld_Notes 00 e3` still loads, so the loader tolerates a short stream there and byte equality
is not the only acceptance path. And an earlier drop experiment proved `Notes` presence matters, so
the authored set is load-bearing rather than ignored.

The remaining 41 sections are not authored. The cheapest next targets, by measured body size:

| Section | Body bytes | Status |
| --- | ---: | --- |
| `ActDatums` | 463 | datum planes; needs the repeat-encoded `local_sys` lane |
| `BasicText` | 573 | mass properties plus the unit-system block |
| `GeomDepen` | 434 | topology state; carries generated timestamps |
| `Geomlists` | 640 | body table; carries generated timestamps |
| `NeuPrtSld` | 918 | neutral part outline and layer/item names |
| `FeatDefsDtm` | 1784 | datum placement records; decoded by the reader |
| `AllFeatur` | 3489 | authored, but rejected on its own |
| `VisibGeom` | 42 | authored, but rejected on its own |
| `LargeText` | 5051 | names table |
| `FullMData` | 6977 | properties and view data |
| `BasicData` | 8232 | basic model data |
| `MdlStatus` | 10301 | model status |
| `SolidPersistTable` | 1148 stored | persistence table; Unix-compress payload |

## Minimal state sections

The large state sections accept an empty struct. `Author.MinimalSections()` emits
`e0 00 <struct> 00 e3 f1` for 27 sections, and `Author.EmptyPartSections(FeatureClasses)` combines
them with the eleven grammar-authored bodies.

Each addition was measured with one Creo 2027.2 launch on the rebuilt control:

| Minimal bodies added | Result |
| --- | --- |
| `BasicData`, `MdlStatus`, `FullMData`, `LargeText` | loads (`End`, `MT Part Solid`) |
| + 10 `ModelView#*`, `ColorSchemeInfo`, `ColorSchemeInfoNew`, `THMB_IMG_INDX`, `CGFMappingTable` | loads |
| + `BasicText`, `Geomlists` | loads |
| + `GeomDepen`, `DispCntrl`, `ActEntity`, `NeuPrtSld` | loads |
| + `DwgData`, `IdsGenInfoDb` | loads |
| + `ActDatums` | loads |
| + `FeatDefsDtm` | model-load crash, no `End` |
| + `BasBasData` | model-load crash, no `End` |

## Model-defining scalars

`BasBasData` is the one state section whose body cannot be empty. `Author.BasBasDataPayload` emits it
field by field:

```text
tab_key, tab_key_struct(type 72), revnum_ptr(geom_revnum, cosm_revnum, insert_layer_id),
layer_count, rel_part_eps, model_eps, fixed_model_eps, part_type, first_ent_id,
outline, attrib_array, max_part_size, ref_part_tabs
```

It reproduces the control byte for byte except the 21-entry `attrib_array`, which is emitted as
zeros rather than copied flag words. `first_ent_id` is a three-byte compact integer (`c7 e1 19` =
`516377`) in the control, so the field consumes those bytes rather than ending before them.

`EmptyPartSections((923, 979, 917))` now returns 39 bodies, including `BasBasData`. Applied to the
control container:

```text
39 sections  31271 bytes (control 81539)
!15-Nov-26 01:50:26  End   C:\Mac\Home\Documents\creo-authored\bb.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

So 39 of the 54 directory rows are authored and Creo accepts the result. Only one plain section
remains load-bearing: `FeatDefsDtm` (datum placement records). The other unauthored rows are the
three compressed `ND:` sections, `SolidPersistTable`, `SolidPrimdata`, `DispDataTable`,
`THMB_IMG_MAIN`, `CGFPersistTable`, the two `kind b` sections, and the two free-space extents.

## Datum placement record

`FeatDefsDtm` is the last plain section that rejects an empty body. Its first record is now emitted
from the grammar: `Author.DatumPlaneRecord(DatumId, Orient, Geometry2Id, Columns, Extent)`.

```text
datum record: ref 775 mine 775 byte-identical True
```

The record carries `id`, `symbol_key`, `model_type`, `place_rec_ptr` (`local_sys`, `own_ref_id`,
`orient`, `place_instruction_ptrs` with one instruction and two `plin_info` entries, `trf_arr` with
one transform), the revision and state scalars, and `feat_outl_info` with `ent_outl` and
`parchild_table`. The schema is recorded in
[the datum placement page](../../../re/creo/data-model/DatumPlacement.md).

Three reduced bodies were measured and all fail with a model-load crash and no `End`:

| Body | Result |
| --- | --- |
| `Sld_FeatDefsDtm e3 f1` | crash |
| `feat_defs_923` empty array | crash |
| `feat_defs_923` and `feat_defs_979` empty arrays | crash |
| three definition-form plane records, no `feat_defs_979` | crash |

The record grammar is settled and `DatumPlaneRecord` parameterises `Columns`, `Outline` and
`InstructionType`, because the three planes differ in all three: the outline slot order rotates per
plane and the second plane's instruction type is `514`, not `515`.

Non-first array elements are positional replays introduced by `f7 02 e3`. Five further candidates
were measured, and all crash: authored records with the vendor csys field, with `f7 02`
introductions, with per-plane frames, and with per-plane frames and outlines. The first three of
those were also malformed, because the byte range used as the csys tail was really element two, so
they declared three elements and carried five.

The remaining difference was structural. A second array element written in definition form re-declares
every field, which appends those names to the shared global field table; everything after the array
then reads through a shifted index, so the `feat_defs_979` record resolves to the wrong fields and the
load crashes.

`Author.DatumPlaneReplay` emits the replay form instead: no field headers, `f7 02` lead for element
two, no lead for element three, and the control's field selectors. Both elements are byte-identical:

```text
element 2: ref 139 mine 139 equal True
element 3: ref 123 mine 123 equal True
```

With the three authored elements and a datum extent of `200.0` rather than the control's
`254.33012701892218`, 56 bytes differ and Creo loads the part:

```text
payload len 1428  control 1428  bytes that differ: 56
authored 923 array: 1037  csys tail still vendor-sourced: 351 bytes
!15-Nov-26 02:04:32  End   C:\Mac\Home\Documents\creo-authored\dtm11.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

So `FeatDefsDtm`'s datum array is authored and accepted.

The `feat_defs_979` csys record is now authored too. `Author.CsysReplay` reproduces its 351 bytes
exactly, including the wider `place_instruction_ptrs` array (`f8 07`), the several instructions with
distinct `geometry1_id` values, the inline `data(plin_info_ref_uv)`/`uv_val` declaration, and a
transform of type `10` rather than `11`:

```text
ref 351 mine 351 equal True
```

`Author.DefaultFeatDefsDtm(Extent)` emits the whole section, and it is byte-identical to the control
when given the control extent (`control-equal: True 1441 1441`). `EmptyPartSections` now includes it,
so 40 bodies are authored:

```text
sections 40  bytes 31271  delta -50268
!15-Nov-26 02:07:15  End   C:\Mac\Home\Documents\creo-authored\auth40.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

`FeatDefsDtm` therefore has no vendor-sourced content.

## The datum feature record

`Author.DatumFeatureRecord` emits the first `AllFeatur` record field by field, and it is byte-identical
to the control (`1601` bytes). The record is a flat run of `e0 <type> <name> 00` headers whose values
carry the structural tokens, so four details mattered:

- `feattype_key` uses a `e0 0a` header, not `e0 00`
- `sect_name` is `f1` plus raw text plus NUL, with no length prefix
- close tokens ride at the front of a later field's value (`assoc_type` is `f1 00`), and one reference
  array opens its element with a bare `e3`
- `outline`, `max_part_size` and `cur_max_size` use the lane where `18` means `1.0`

`creat_date`, `regen_date`, `time`, `random_num` and `hostid` are save-time stamps, so we generate ours.

Four launches replaced record one with the emitter:

| Candidate | Result |
| --- | --- |
| control dates, all-clean 252 slot mask | `End` + `MT Part Solid` |
| our dates, control mask | `End` + `MT Part Solid` |
| our dates, all-clean 252 slot mask | `End` + `MT Part Solid` |
| our dates, one slot mask | silent exit twice |

So the record body and its generated datetime and host fields are accepted. The rejection is the mask
*length*: the defining record's slot count must match the replay records, which carry elements only. The
earlier all-one-slot control loaded because it changed all four records together.

## The replay record

`Author.DatumFeatureReplay` emits the replay form and reproduces both control replay records exactly:

```text
record1 definition identical: True 1601
record2 replay     identical: True 537
record3 replay     identical: True 537
```

The replay is not a strip of the definition. It drops field headers, leading close tokens, plain array
counts and typed array intros; it keeps reference arrays verbatim; it adds `f7 03` at the head of the
first replay and `f7 1e` / `f7 2b` before the duplicate names `fc_hist` and `p_body`; and `fc_hist`
carries `first_geom_id` rather than a constant.

Replacing all three plane records with our own generated values is still rejected, and six candidates
separate why:

| Candidate | Differs in | Result |
| --- | --- | --- |
| record one only, all-clean 252 mask | mask in record one | loads |
| records one to three, control scalars, all-clean 252 | mask in three | silent exit twice |
| records one to three, 252 plain `f6` masks | mask encoding | silent exit twice |
| records one to three, one slot everywhere | mask length | silent exit twice |
| records one to four, all-clean 252 | mask in all four | silent exit twice |
| records one to three, revisions `3/2/1` | revisions | silent exit twice |

Generated scalars, mask encoding and mask length are all ruled out. Only the mask *content across
records* remains: record one alone may be all-clean, all four may not. The plane and csys classes differ
at exactly two slots (`28`, `236`), so the closest reading is that the mask is validated per class.

A per-record bisect with `re/creo/tools/MaskRecord.py` then located the constraint exactly:

| Record swapped to all-clean | Result |
| --- | --- |
| one (definition) | loads |
| two (first replay) | silent exit twice |
| three (second replay) | silent exit twice |
| four (csys) | silent exit twice |
| all four | silent exit twice |

The definition record's mask is exempt; every replay's mask is validated against a per-class expectation.
That is why cleaning record one alone loads and every other swap fails, and it makes the csys mask a real
blocker: the csys class differs from the plane class at exactly two slots (`28`, `236`), and those two
values are the only vendor-sourced mask content still needed.

Replacing the csys lane with the **plane** lane outright loads (`3` of `3`), so slots `28` and `236` are
not class-specific and the requirement is one **per-schema** vector shared by every replay record. That
reconciles all five observations at once and leaves exactly one vendor-derived value in the section.

The harness was calibrated before these probes: the byte-identical control loaded `3` of `3`, the
authored record one `2` of `2`, and `csysasplane` `3` of `3`, so silent exits are real rejections. False
*successes* remain a risk, which is why the earlier single-load result for a one-slot mask was withdrawn.

Two candidates (`allclean4`, `allclean4b`) were malformed and their launches carry no information:
record four's lane is elements-only, so substituting `Author.FlagValue` injected a stray close and count.
`allclean4c`, which uses `Author.SignedIntElements`, is the valid test.

`StreamParser` is not an oracle for replay records: it parses the control cleanly (`334` nodes,
`pos 0xd96`) but explodes on a rebuilt section (`37456` nodes at `pos 0x597`) because it does not
understand the `f7` selectors. Byte comparison against the control remains the reliable check.

## A one-feature AllFeatur loads

The definition record's mask is exempt, so a section holding a single feature record needs no replay
records and no schema mask vector. `Author.AllFeaturPayload` emits `Sld_Features`, `first_feat_ptr`, our
record, a `next_feat_ptr` terminator of `e1`, and the layer tail. With the control's tail it loads, three
times out of three:

```text
onefeat: head 34 record 1199 terminator 17 tail 129 total 1379
!15-Nov-26 04:00:40  End   C:\Mac\Home\Documents\creo-authored\onefeat.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

That is the first authored `AllFeatur` the vendor has accepted, with generated record fields, generated
dates and host id, a generated mask, and a generated list skeleton.

Two incidental facts: the list terminator is a single `e1`, and the layer tail is not validated against
the feature list — the control's tail declares four layer entries and the loader accepted it beside a
one-feature list.

The tail's rule is the **entry count**. `re/creo/tools/TailRule.py` varies one property at a time: a
one-entry list is rejected twice, while four entries all carrying our own feature id `7` load. So the
loader wants four layer entries and does not check their content against the feature list.

`Author.LayerListTail` now emits `KLayerEntries = 4` entries and `Author.DefaultAllFeatur()` composes the
whole section, which is fully generated:

```text
genall2: fully generated AllFeatur 1394 bytes, control section 3489
genall2 identical to the accepted t4_same
End + MT Part Solid, 3 loads out of 3
```

`Author.EmptyPartSections` now includes it, so 41 of the 54 rows are generated, and a rebuilt control with
all 41 replaced loads three times out of three (`auth42.prt`, `29176` bytes against the control's
`81539`). The rows still vendor-sourced are the three `ND:*` tables, `SolidPersistTable`,
`SolidPrimdata`, `DispDataTable`, `THMB_IMG_MAIN`, `CGFPersistTable`, the two `kind b` rows and the two
free-space extents.

## The list length is load-bearing, and three of four records are authored

The feature list cannot be truncated. That is what blocked every two-record candidate:

| Candidate | Records | Creo |
| --- | --- | --- |
| `fullgen` | control's four, generated tail | loads |
| `twocontrol`, `twocontrol2`, `twocontrol3` | control's own first two, three different boundaries | silent exit twice each |
| `csyspair` | FRONT + csys, control bytes | silent exit twice |
| `inplace1` | **our** record one, control records 2-4 | loads |
| `inplace2` | **our** records 1-3, control csys | loads |
| `inplace3` | **our** records 1-3 with all-clean masks and our dates, control csys | loads, 2 of 2 |

So a part must declare the same four features the rest of the container describes; the one-feature section
loaded only because it never opens a second element. Authoring therefore replaces records **in place**
instead of appending them.

`Author.ReplayOf` derives each replay from its own definition, and the three authored records compose with
the boundary the control uses: `next_feat_ptr` declared once, `f2 e3` opening element two, bare `e3` for the
later elements.

### Retraction: the mask vector is not needed

`inplace3` carries all-clean 252-slot masks in the definition **and** in both replays, and loads twice. That
overturns the earlier per-record bisect, which reported every replay mask validated. That bisect predates
three emitter fixes (`fc_hist` hardcoded instead of `first_geom_id`; the array-strip test matching the `f7`
byte inside a value; replays hand-written rather than derived), so its candidates were malformed in ways
unrelated to their masks. No per-schema mask payload is required.

#### A class-979 record cannot be faked

Two attempts to avoid decoding the csys failed twice each: a `979` replay carrying datum fields
(`inplace4`) and a `923` replay carrying `id 11` (`inplace5`). The class is validated against the record's own
fields, so the fourth feature must be a real csys.

Parsing that record against the shared schema shows why it is not a positional replay: it carries only `43`
bytes of datum-shaped values and then **declares** its own fields at three points — `misc_id_tab_ptr` and
`misc_hist` after `idtab_ptr`, `parent_table` after `first_geom_id`, `avail_feat_parents` after `hostid` —
skipping the datum fields it does not carry with `f7` selectors. Three values also differ from a plane:
`intersection` is `991`, `misc_choice` starts with `301989889`, and `sect_name` is null.

### The csys is generated, and AllFeatur has no vendor bytes

`Author.CsysFeatureRecord` generates the `619`-byte coordinate system record, byte-identical to the
control's. It is not a positional replay: `26` fields of datum-shaped values, then four fields declared in
place, with `f7` selectors that skip the datum fields the record does not carry. The selectors are 1-based
schema field indices — `31` `save_geoms`, `40` `topology_increment`, `43` `p_body`, and `60` `hostid`, the
last naming the field *before* the resumed range. The record is assembled from `ReplayPieces` slices, so it
cannot desync from `DatumFeatureRecord`.

With that, every byte of `AllFeatur` is generated — four records, list skeleton, terminator and tail:

```text
allfeat4: records 1199 135 135 223, payload 1880 vs control 3478
!15-Nov-26 06:19:17  End   C:\Mac\Home\Documents\creo-authored\allfeat4.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

two loads out of two, and `Author.DefaultAllFeatur` now emits exactly that section (`1880` bytes,
byte-identical to the probe). The container with 41 authored sections loads with it:

```text
auth4 part 29673 bytes from control 81539
!15-Nov-26 06:21:17  End   C:\Mac\Home\Documents\creo-authored\auth4.prt
```

Two shortcuts were refused twice each first: a `979` replay carrying datum fields (`inplace4`) and a `923`
replay carrying `id 11` (`inplace5`). The feature class is validated against the record's own fields.

### The two "solid" rows are display tables

`SolidPersistTable` and `SolidPrimdata` were the next candidates for decoding, on the assumption that they
describe a body. They do not. Both are Unix-compress rows (`1f 9d`) that decompress to ordinary token format
(`1125` to `1788`, `235` to `301`) and then read as the display pipeline's persistence state:

- `pgl_persist_table` — hash tables of `fontsH`, `linestylesH`, `colorrefsH`, `imagesH`, `texturesH`,
  `mrshadersH`, `appearancesH`, `surfpropsH`, `symbolsH`, `segmentsH`, `gpurefsH`, `segmentrefsH`
- `pgl_primdata_group_table` — LOD groups of segment references and primdata containers

So the boundary representation is in `VisibGeom` and the feature records, both already authored, and not in
these rows. Both are still **required**: dropping them, or dropping `DispDataTable`, `CGFPersistTable` and
`THMB_IMG_MAIN`, is refused with `cannot be retrieved`. That matches the earlier finding that only trailing
rows (`IndentTag`, `FeatRefData`) may be dropped.

They parse once one double lane is decoded. The divergence was at offset `94` of the decompressed
`SolidPrimdata`: `lod_value` is encoded `2f 30 00` — the prefix `2f`, an ASCII decimal string, and a `00`
terminator — so it is `0.0`. `ReadDouble` did not know that lane and its fallback advanced eight bytes,
swallowing the next field's header, which is why `segref_array` read as the scalar `114` and
`pgl_segref`/`p_seg_persistref` as single bytes.

With the lane decoded, `SolidPrimdata` parses coherently: `30` nodes, consuming exactly `301` bytes,
`lod_value` `0.0`, `segref_array` `[5]`, and records for the rest.

Two limits were measured and are worth keeping:

- **The lane must be scoped.** Treating any `2f` as a decimal string drops the ladder from `8` parameters to
  `0`, because the byte recurs in `FeatDefs` doubles with a different sense. The reader now takes the decimal
  form only when the bytes up to a nearby `00` are digits or signs, and the control and ladder reads are
  unchanged (`4` features; `7` features, `8` parameters, `6` faces, `12` edges, one solid, volume
  `18482541.490319017`).
- **The silent fallback stays, and the reason is broader than the feature section.** Making it raise was
  tried: `25` of `58` ladder rows raise, including the three the adapter reads — `VisibGeom`
  (`0x59` at `612`), `AllFeatur` (`0x57` at `6347`) and `FeatDefs` (`0x00` at `921`) — and with the raise
  enabled the ladder reads `0` features instead of `7`.
  The lanes are a symptom, not the cause: near `6347` the bytes are
  `e3 52 80 cb 00 e4 e3 57 80 c8 07 00 e3 59 …`, so `52` was taken as a 9-byte double and swallowed
  `e3 57 80 c8`, while `52`/`57`/`59`/`5b`/`5d` are object ids in an id-table. Enabling the raise needs the
  upstream alignment fixed first.
- **Two sentinel lanes were tried and dropped.** `0xf6` (null) and `0xf5` (negated integer) inside a double
  lane changed no measurement: with or without them the ladder's `AllFeatur` is `1007` nodes at
  `7838/7838`, and `SolidPersistTable`/`SolidPrimdata`/`VisibGeom` parse to `357`/`30`/`2` nodes. Only the
  `2f` decimal string mattered, so only it stayed.

Re-emitting these rows byte-identically is not the goal either — a parsed vendor row re-emitted is a recorded
payload replay, which the no-donor standard forbids in `src/`.

### What the authored container reads back as

The container built from the 41 authored sections reads back through our own adapter as:

```text
authored container reads back: 4 features, 0 params, 0 bodies
  features: ['Creo datum_plane 7', 'Creo datum_plane 5', 'Creo datum_plane 3', 'Creo coordinate_system 11']
```

which is exactly what it is: four datum features, no parameters and no solid. It is a correct round trip and
it is not acceptance evidence — there is no body to measure.

## What is left

One vendor record: the csys (`619` bytes, class `979`). It is a replay of the first record's schema opened
with `id 11`, `type 979`, `sect_name DEFAULT_CSYS`, and then it declares four fields of its own —
`misc_id_tab_ptr` (`24` bytes), `misc_hist` (`436`), `parent_table` (`70`) and `avail_feat_parents` (`46`),
the last two listing feature ids `3`, `5` and `7`. Declaring fields is legal for this record because a record
that declares a new field must be last in its array, and it is.

## The list wrapper is proven, the list boundary is not

Two results this round, one positive and one negative.

**Positive.** The control's four feature records, taken verbatim and paired with a *generated* tail
(`Author.LayerListTail`), load:

```text
fullgen: control's four records verbatim, generated tail; payload 3482 vs control 3478
!15-Nov-26 05:50:04  End   C:\Mac\Home\Documents\creo-authored\fullgen.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

So the wrapper — `Sld_Features`, `first_feat_ptr`, the record list, its terminator and the four-entry tail —
composes with a real multi-record list. Only the record bytes in that candidate are vendor.

**Negative.** Truncating the same list to two records is refused, whatever the record bytes are: the
control's first two with an `f2 e1` terminator (`twocontrol`), the same two with the control's own
end-of-list bytes (`twocontrol2`), and our definition plus a byte-exact derived replay (`twodatum5`) all
exit without `End`, twice each. The record encoding is therefore no longer implicated.

The ladder explains why the boundary is subtle: only the **first** boundary declares `next_feat_ptr` and it
carries `f2 e3`, while record three opens with a bare `e3` and no header at all. Every two-record candidate
re-declares `next_feat_ptr` before the terminator, which violates the "never re-declare a field mid-array"
rule this format follows everywhere else.

### A retraction about the widened schema

An earlier revision of this entry recorded that the feature schema could be widened to the ladder's
superset (`flags`, `first_hybrid_body_id`, `topo_parents`) and that the widened part loaded twice out of
two. That result is **void**: `ExtraSchema` was a silent no-op, so the file tested was byte-identical to
the plain datum part.

Implemented properly the widened record is genuinely different (`1249` bytes, `76` declared fields against
`1199` and `73`) and it is **refused**, twice. Our `73`-field schema is the one this build accepts; the
ladder's `71`-field schema is a different schema version, and an ordered diff shows the lists diverge at
index `30` (`flags` against `cr_flags_xar`), so they cannot be reconciled by adding fields.

## Authored geometry is still rejected

With `AllFeatur` now generated, the control rebuilt with 42 authored sections and an authored
`VisibGeom` box (`AuthorGeometryPayload`, `100 x 60 x 40`) is rejected twice. The same container without
the authored `VisibGeom` row loads three times out of three, so the geometry payload is the cause and not
the surrounding part. Its six plane prototypes with the `local_sys` lane have never been accepted.

## VisibGeom and the authored container

`Author.EmptyVisibGeom()` emits the empty geometry form, `Sld_VisGeom` with an opened `active_geom` and
no surfaces. It is byte-identical to the control (`control-equal: True 42 42`) and loads:

```text
sections 41  bytes 31271
!15-Nov-26 02:08:44  End   C:\Mac\Home\Documents\creo-authored\vgempty.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

`Author.EmptyPartContainer()` assembles those 41 bodies through `BuildContainer`, so the result is a
generated container rather than a rebuilt one:

```text
bytes 7956  base 0x2cc  rows 41  notes ()
tail "#\n#END_OF_UGC\n"
```

The table parses cleanly with no notes. Our own reader refuses the file, correctly: with `AllFeatur`
absent there are no features, parameters, or bodies, so the document validator reports "document has
neither parameters, feature history, B-rep, mesh, nor assembly data". That is the same gap Creo shows
as a rejection.

The 13 rows still missing are the three `ND:*` token tables (each a `PSB_Tokens` root with a
run-length `type_har` string), `SolidPersistTable`, `SolidPrimdata`, `DispDataTable`,
`THMB_IMG_MAIN`, `CGFPersistTable`, the two `kind b` rows (`IndentTag`, `FeatRefData`), the two
free-space extents, and `AllFeatur`.

## AllFeatur

`AllFeatur` is the last structural blocker, but its hardest field is now solved: `cr_flags_xar` accepts
any non-empty generated lane. The record schema is inventoried in
[the feature record page](../../../re/creo/data-model/FeatureRecord.md): 78 nodes for the first
feature, `1620` bytes, of which `cr_flags_xar` alone is `402`.

`cr_flags_xar` is `f1 f8 80 fc ...`: a close token, a compact count of `252`, then 32-bit masks, each
`0xffffffff` with one or two bits cleared (`0xfffff7ff`, `0xfeffffff`, `0xffefffff`, `0xdfffffff`).
Which bit maps to which field is not decoded. Copying the control's array would be donor data, so it is
not emitted.

The masks are load-critical, measured with three launches on the control (the splice first verified as
an identity):

| substitution | result |
| --- | --- |
| all 252 masks `-1` | crash, no `End` |
| all masks `0` | crash, no `End` |
| identity | loads |

So neither natural generated default works: all-clean and all-dirty both fail.

The field also cannot be dropped. `re/creo/tools/OmitMask.py` removes record 0's field header, its
`f1 f8 80 fc` array introduction and its elements, plus the element runs in the three replay records:

```text
omit_a: AllFeatur 3478 -> 1873   no cr_flags_xar name left: True
!15-Nov-26 02:40:09  Start C:\Mac\Home\Documents\creo-authored\omit_a.prt
(no End line, no dbg_err_crash, process exits)
```

So the loader has no default for the field.

That probe also pinned the replay form exactly: replay records carry the **elements only** — record 0 is
`402` bytes (`f1 f8 80 fc` plus 398 element bytes, behind `e0 01 cr_flags_xar 00`) and records 1 to 3 are
`398`, `398` and `392` bytes with no header and no array introduction.

The masks are per class, not per document. Across the two unrelated controls the three datum planes have
identical vectors, the empty control's 252 entries are identical to the ladder's first 252, and the csys
differs from a plane at exactly two slots (`28`, `236`) in both files, while the ladder's protrusion
differs at 195. See
[the mask lane gotcha](../../Gotchas/Conversion/CreoMaskLaneRequired.md).

## The mask lane is decoded

`cr_flags_xar` is a repeat-compressed array of signed 32-bit values. The encoding is fully decoded:
`f1` then `f8 <count>` then run-compressed integers, with `00`–`7f` as-is, `80`–`bf`, `c0`–`df` and
`e8`–`eb` for wider payloads, `f5` for negation, `f6` for `-1`, and `e4`/`e5`/`e6`/`e7` for repeats.

`Author.CompactInt`, `Author.SignedInt`, `Author.SignedIntArray`, `Author.SignedIntElements` and
`Author.FlagValue` implement it, and they reproduce **every** lane in both retained controls exactly —
thirteen lanes, definition and replay form:

```text
empty  rec0 252 slots 402 bytes identical True    ladder rec0 311 slots 462 bytes identical True
empty  rec1 252 slots 398 bytes identical True    ladder rec4 311 slots 484 bytes identical True
empty  rec2 252 slots 398 bytes identical True    ladder rec5 278 slots 385 bytes identical True
empty  rec3 252 slots 392 bytes identical True    ladder rec7   0 slots   0 bytes identical True
```

Record one is `f1` plus `f8 count` plus elements; replay records are the elements only, which is exactly
why they are four bytes shorter.

### Correction

An earlier revision of this entry recorded that the lane's token shape was load-bearing, because a
`+57`-byte explicit expansion and a `+68`-byte canonical re-encode were both rejected. **Both candidates
were malformed by my own encoder**: the expansion reused the wrong previous-token bytes, and the
canonical form emitted `eb` where the control uses `ea` for a three-byte payload. With the encoder above,
a value-preserving re-encode at `471` bytes loads:

```text
lane_1a0: lane 471 bytes, AllFeatur payload -> 3547
!15-Nov-26 02:57:04  End   C:\Mac\Home\Documents\creo-authored\lane_1a0.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

A hypothesised `0x1a0`-byte cap, inferred from the accessor family's `size(kind)` values, is disproved
by the same launch.

The **values are immaterial**. `re/creo/tools/SlotBisect.py` rewrites the lane in every feature record
with a generated all-clean vector through the shipped encoder, so each candidate is a well formed
stream, and every one loads:

| Candidate | AllFeatur bytes | Creo |
| --- | ---: | --- |
| no-op rewrite from the shipped encoder | 3478 | loads |
| slots 126..251 cleaned, then 64, 32, 16, 8, 4 | 2853 → — | loads |
| every slot `-1`, count 252 | 1908 | loads |
| every slot `-1`, count 1 | — | loads |
| single slot with value `0` | 1895 | loads |
| every slot `-1`, count 0 | 1891 | fails |

Neither the values nor the count carry meaning; the array only has to be non-empty. `Author.CleanFlagValue`
(`f1 f8 01 f6`) and `Author.CleanFlagElements` (`f6`) emit that, and a control whose four lanes are
replaced by exactly those loads with `End` and `MT Part Solid` (`AllFeatur` `3478` → `1895`).

The field is still required — `re/creo/tools/OmitMask.py` removes it from all four records and the
process exits.

### Second correction

Two earlier measurements in this entry — "every value `-1` fails" and "every value `0` fails" — were
**flaky launches**. Creo in `-g:no_graphics` mode sometimes exits with no `End` line and no
`dbg_err_crash`, which reads exactly like a rejection; the all-clean candidate failed once and loaded on
retry. Silent exits are now treated as inconclusive. See
[the mask lane gotcha](../../Gotchas/Conversion/CreoMaskLaneRequired.md).

Three further measurements narrow the table without yielding the bit assignment:

| Control | Features | Slots per `cr_flags_xar` |
| --- | ---: | --- |
| empty | 4 | `252` for all four |
| ladder | 7 | `311` for the datum features and the protrusion, `278` twice, `0` once |

The four datum features within a file carry identical vectors, but the length is neither per-file nor a
function of the class alone: class `923` has `252` slots in the empty control and `311` in the ladder,
and the ladder's own count varies per feature. Its length is also not the field-definition count (empty:
`32` definitions before the field, `252` slots). Only the leading values coincide across the two
documents.

Name-based RE cannot reach it from the container modules: `strings` finds `Sld_Features` and
`first_feat_ptr` in `coreutils_sh.dll`, `metatoolsapi.dll` and `diagexport.dll`, which is why the
container and the linked-list skeleton were tractable, but `cr_flags_xar` appears in none of them.

It does appear in the model module. `xtop.exe` (326,650,848 bytes, at
`Common Files\x86e_win64\obj\xtop.exe`) contains `cr_flags_xar` exactly once, at file offset
`0xe7c2220`, inside an ordered pool of about 423 feature-field names that also contains
`more_cr_flags`, `save_geoms`, `cvt_feat_dat`, and `-dummy_*` placeholders. `more_cr_flags` being a
separate field means the mask state is split across at least two members.

The module was copied outside every checkout (`~/Documents/creo-re-bin/xtop.exe`) and is researched
only.

The name pool is referenced from a table in the `.ddt` section: `cr_flags_xar` at file
`0x133db880`, records of stride `0xd0`, table extent `0x133ced60..0x133f40f0` with **734 entries**
over **514 unique names**. `cr_flags_xar` is entry `250` and `more_cr_flags` entry `246`.

Records vary in how much they carry: many hold offset-like words at `+0x50` and `+0x80`, but
`cr_flags_xar`'s record holds only `{name pointer, 1}` and nothing else. For this field the registry is
therefore a name registry rather than a layout descriptor: it does not give the struct offset, and it
does not give the mask semantics. It does
put `cr_flags_xar` at index `250` against `252` slots in the empty control, which is a testable
hypothesis, recorded in [the feature struct page](../../../re/creo/loader/FeatureStruct.md).

So `AllFeatur` remains unauthored, and with it the part, because it is the one section both our
validator and the vendor loader reject when absent.

## The record-74 parse drift is measured, not explained

Logging every field read inside the ladder's record `74` shows the drift concretely. Around offset `6341` the
bytes are a table of records — ids `57`, `59`, `5b`, `5d` with a counter `7, 6, 5, 4`, each opened by `e3` —
but the parser labels them `fc_hist`, `save_geoms`, `transform` and `flags`, then reads `cr_flags_xar` with
`0` slots where every other record has `311` or `278`.

The obvious suspect was the reference-array form `f8 <count> f7 <field> fb` with records following inline, and
it was implemented and measured:

| Measure | Before | After |
| --- | --- | --- |
| record `74` mask slots | `0` | `3` |
| `AllFeatur` nodes | `1007` | `882` |
| ladder surfaces / edges / solid / volume | `6` / `12` / `1` / `18482541.4903…` | **`5` / `6` / `0` / `None`** |

The change broke `VisibGeom`, which uses the same form for `srf_array` (`f8 06 f7 03 fb` followed by six
surface records) and relies on the records being read positionally as fields. **The form is normal; the
diagnosis was wrong**, and the change was reverted.

So the drift is localised but not explained: record `74` mislabels its table bytes and parses a short mask,
while records `7`, `5`, `3`, `11`, `67`, `75` and the trailing one parse `311` or `278` slots. Distinguishing a
vendor schema difference in the `917` records from a reader bug needs a second saved document.

## A generated dimension loads

The empty control reserves space it calls `EMPTY_SPACE_FOR_REUSE`, including a `157`-byte row. Renaming that
row and writing a body into its region adds a section the part never had, without extending the directory
tables — `re/creo/tools/AddRow.py`, and the rebuild is byte-identical run to run.

With that, `Author.DefaultFeatDefs()` emits a `Sld_FeatDefs` row carrying one `dimtab_ptr` dimension, and the
part loads:

```text
featdefs.prt: 81661 bytes, FeatDefs body 279 (reserved 157)
  rows before 53, after 54
  new rows: ['FeatDefs']
!15-Nov-26 06:43:50  End   C:\Mac\Home\Documents\creo-authored\featdefs.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

twice, and the dimension reads back through our own adapter:

```text
readback: 4 features 1 params [('Creo dimension 0', 100.0)]
```

So this is the first loadable authored part that carries a **parameter**: a generated dimension record, no
donor bytes, accepted by Creo. It moves the parametric criterion from "no evidence" to "a dimension authored
and read back" — while the part still has **no body**, so body count, volume and centre of mass remain
unmeasured, and the 13 vendor rows are unchanged.

## A `917` record is a revision graph, and authored surfaces are still refused

Diffing record `67` — the ladder's first solid feature — against the learned schema shows it declares **37**
new fields, all revision and reference bookkeeping: `comp_hist`, `owner_id`, `component_ids`, `revnums`,
`hist_ref_info`, `coll_refs_info`, `ref_revnum`, `ref_status`, `rev_info_arr`, `mdl_geom_rev`,
`revision(mdl_g_rev_dtl_t_ft_regen)`, `aggr_rev_info`, `aux_rev_data` and so on. Nothing there is a parametric
description of a solid; it is a graph over geometry the vendor kernel produced. That matches every earlier
attempt: a `917` replay carrying datum values is refused, and so is a `923` replay wearing the csys id.

Retesting authored `VisibGeom` against the now-working assembly also fails — six generated surface records
pointing at feature `7` (`geomfeat2`) exit with no `End` line, twice. So surfaces cannot be authored ahead of
the solid that owns them.

### A real bug found while testing this

`PlaneDefine` ended with `return Payload + b"\xf2" if TrailingClose else Payload`, a name that only exists on
`DatumFeatureRecord` — a bad patch that had landed in the wrong function and would raise `NameError` for any
caller, including `AuthorBox`. It is repaired, and the surface record is still byte-identical to the ladder's
first element (`409` bytes).

### Dimensions are authored, counted and chosen

`Author.DefaultFeatDefs` takes a tuple of dimension values and emits one `dimtab_ptr` entry per value, with the
array count in the `f8 <count> f7 03 fb` introduction. Three facts are measured:

| Part | Dimensions emitted | Read back | Creo |
| --- | --- | --- | --- |
| `featdefs` | `(100.0,)` | `Creo dimension 0 = 100.0` | loads, 2 of 2 |
| `featdefs425` | `(42.5,)` | `Creo dimension 0 = 42.5` | loads, 2 of 2 |
| `fd_two` | `(100.0, 42.5)` | `100.0`, `42.5` | loads, 2 of 2 |

So the dimension value is the one we choose rather than a constant, and the count is honoured rather than
ignored — the parametric path is generative, not a single hardcoded record.

### A 917 emitter with nulled fields is refused

`re/creo/tools/Protrusion.py` composes the proven four-record section plus a `917` record built from record
67's `37` declared fields in order, each null or `-1`, alongside the generated dimension:

```text
solid917b: AllFeatur 2574
(no End line; second run identical)
```

The assembly and the field order are therefore not the gap — the content is. Those fields are
`comp_hist`, `coll_refs_info`, `rev_info_arr`, `mdl_geom_rev`, `aggr_rev_info` and friends: references and
revision state over geometry that only a regenerated solid has.

## Limits## Limits

- The authored part contains only `AllFeatur` and `VisibGeom`. Creo rejects it as "not a valid PART
  file". The section set is the cause: Creo validates every model section, and the authored part
  carries 2 of 52 extents.
- Authored `AllFeatur` and authored `VisibGeom` are each rejected on their own when swapped into an
  otherwise byte-identical vendor container, so both section bodies still need work.
- Authored geometry has no curves, so shell closure is not proven and `solid_count` stays zero.
  Volume comes from the six plane half-spaces.
- No Creo-measured acceptance exists for authored output.
- Existing documents still write through exact source replay; this module is a separate generative
  path.

## Documentation

- [Creo adapter](../../Reference/Adapters/Creo.md)
- [Mass properties change entry](CreoNeutralMassProperties.md)
- [Section subset tool change entry](CreoSectionSubsetTool.md)
- [Mask lane gotcha](../../Gotchas/Conversion/CreoMaskLaneRequired.md)
- [Required section set gotcha](../../Gotchas/Conversion/CreoRequiredSectionSet.md)
- [Reader change entries](../../Changes/Index.md)
