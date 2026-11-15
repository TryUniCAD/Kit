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
