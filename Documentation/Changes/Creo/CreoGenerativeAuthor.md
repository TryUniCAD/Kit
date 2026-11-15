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

The `#\n` separators and the three-table `NEXT_TOC_ENTRY` chain (`0x31b` 32 rows, `0x10873` 22
rows, `0x115a6` 128 rows in the control) are still not authored by `Author.py`.

## Limits

- The authored part contains only `AllFeatur` and `VisibGeom`. Creo rejects it as "not a valid PART
  file", so the header, table-of-contents fields, section set, or section bodies are still
  incomplete for the vendor. It has no `FeatDefs`, `BasicData`, or other sections a vendor part
  normally carries.
- Authored geometry has no curves, so shell closure is not proven and `solid_count` stays zero.
  Volume comes from the six plane half-spaces.
- No Creo-measured acceptance exists for authored output.
- Existing documents still write through exact source replay; this module is a separate generative
  path.

## Documentation

- [Creo adapter](../../Reference/Adapters/Creo.md)
- [Mass properties change entry](CreoNeutralMassProperties.md)
- [Reader change entries](../../Changes/Index.md)
