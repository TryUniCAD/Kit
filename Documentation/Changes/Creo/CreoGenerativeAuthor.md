# Creo generative author

## Change

Adds `src/convert/adapters/creo/Author.py`, the first generative Creo PSB writer. It authors a part
from format knowledge only: no captured section bytes, no templates, and no donor file.

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

`AllFeatur` is the last structural blocker. Its record schema is inventoried in
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

The lane is neither value-driven nor size-driven. Six edits, one launch each:

| edit | byte delta | result |
| --- | ---: | --- |
| control | 0 | loads |
| first value `-1` → `-2` | +1 | loads |
| repeats expanded explicitly, each copy reusing the previous value's token bytes | +57 | process exits, no `End` |
| all `252` values re-encoded canonically | +68 | process exits, no `End` |
| every value `-1` | −162 | `dbg_err_crash` |
| every value `0` | −162 | `dbg_err_crash` |

So replacing the repeats with explicit copies of the same values fails, and so does re-encoding those
values, while a one-byte length change succeeds. The accepted form is the control's token shape with
limited freedom inside it.

Consequently the `252` slot count is a property of our reader's repeat expansion rather than a measured
file fact, and the `.ddt` index comparison is not evidence: the "one slot per registered field" idea is
withdrawn.

Three further measurements narrow the table without yielding the bit assignment:

| Control | Features | Slots per `cr_flags_xar` |
| --- | ---: | --- |
| empty | 4 | `252` for all four |
| ladder | 7 | `311` for the datum features and the protrusion, `278` twice, `0` once |

Within a file the four datum features carry identical masks, so the table is per-file schema state
rather than per-feature content. Its length is not the field-definition count (empty: `32` definitions
before the field, `252` slots; ladder: `33` and `311`), though both files start with the same four
values.

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

That record carries only `{name pointer, 1}` and nothing else, so it is a name registry rather than a
layout descriptor: it does not give the struct offsets, and it does not give the mask semantics. It does
put `cr_flags_xar` at index `250` against `252` slots in the empty control, which is a testable
hypothesis, recorded in [the feature struct page](../../../re/creo/loader/FeatureStruct.md).

So `AllFeatur` remains unauthored, and with it the part, because it is the one section both our
validator and the vendor loader reject when absent.

## Limits

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
- [Required section set gotcha](../../Gotchas/Conversion/CreoRequiredSectionSet.md)
- [Reader change entries](../../Changes/Index.md)
