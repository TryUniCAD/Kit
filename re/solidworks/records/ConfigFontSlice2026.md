# Part configuration font and format fields in SOLIDWORKS 2026

This reader tranche covers four version-19000 layouts inside `moPart_c.fae0`.
Its scope is raw field decoding. Full physical part configuration admission,
portable style semantics, editable conversion and native writer acceptance
remain open.

Task `B04-SW2026-CONFIG-FONT-FIELDS` belongs to the PR #121 takeover team.
Delivery branch `codex/solidworks-config-annotation-font` starts from
`b7206312cbdd4ef7b0966263e08ec84bb52ea0df`. It reuses the accepted body
executor and ModelHeader handoff. The exit includes the bounded process
evidence and exact-head review and queue acceptance.

## Field ownership

The confirmed raw orders below come from `sldmfcu.dll` 34.5.2.0604, SHA-256
`af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`.
The prior native findings bind complete function extents and content hashes.
[Font and width dispatch](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/DrawingLineFontArchive2026.json)
[Character and print width dispatch](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/AnnotationArchive2026.json)

| Layout | Native entry | Confirmed raw fields in wire order |
| --- | --- | --- |
| `uiLFConfig_c` | `0x3c7a7760` | CString `f08`, embedded width `f10`, signed `i16 f18` |
| `utLineWidth_c.Serialize.2.0` | `0x3c84a9e0` | `i16 f06`, `f32 f00` |
| `utCharFormat_c` | `0x3c7bfa50` | CString `f08`, `f64 f10`, `i32 f18`, `f64 f20`, `u32 f30`, `f64 f28/f38/f40/f48/f50`, `u32 f58` |
| `utLineWidthPrintData_c` | `0x3c84afb0` | Eight `f32` fields `f8/fc/f10/f14/f18/f1c/f20/f24` |

The native line-font reader sign-extends its final word. The width loader
stores a separate runtime cache. Character layout can use native font
preferences after reading its wire fields. Runtime substitutions, font
mapping, numeric domains and older versions require separate evidence.
The exact-build records distinguish raw values from these runtime decisions.

## Linked source intervals

The pinned reader at `9f0ccb5389c121e750ca3b73f8e5d248b34d2e15` traversed
the complete typed `Config-0` stream of each tracked version-19000 part.
Each source exposed twenty line fonts, twenty embedded widths, 81 character
formats and one print width layout. The selected character format is the
first view-label format. All offsets below are half-open offsets in the
physical Config-0 bytes. All selected spans leave the live map base at four.

| Bounded lane through `fae0` | L1 interval | L1 next slot before and after | Concave interval | Concave next slot before and after |
| --- | --- | --- | --- | --- |
| `f13b0/fe0/moBaseDimDef_c/fd0` line font | `[4647,4679)` | 62 | `[3558,3590)` | 54 |
| Line font `f10` width | `[4671,4677)` | 62 | `[3582,3588)` | 54 |
| `f2750/f18/moDrViewLabelData_c/f98` character format | `[12681,12781)` | 69 | `[11130,11230)` | 54 |
| `fb0` print widths | `[19734,19766)` | 69 | `[18375,18407)` | 54 |

The source trace checks the identity of every incoming map entry before and
after those reads. In each bounded replay, `ReadPartStart` supplies the
concrete `moPart_c` schema-one descriptor and its object in slots one
and two. The ModelHeader self object is at slot three and retains original
index 69 in L1 and index 15 in Concave. The bounded replay retains those
three identities and the measured later counter. The selected layouts
have no archived object tags or lookups.

The native font name is `CONTINUOUS` in L1 and `Continuous` in Concave.
The view-label font is `Century Gothic` in both. Its stored height is
0.003175 in L1 and 0.0035 in Concave. The independent field decoders agree
on every field, its value and its end offset.
[Native custody and exact intervals](../measurements/2026/ConfigFontSource01.json)
[Current reader results and source hashes](../measurements/2026/ConfigFontReader01.json)

The separately authored records vary widths, signed and unsigned words,
Latin-1 text, UTF-16 text with a supplementary character, and all print
widths. The guarded processes reject truncated text, a noncanonical string
length, missing width and character fields, extra bounded bytes, an older
archive version and an unregistered width layout. External access during
decoding fails the worker. These host records contain no native launches.

## Composed detail dependencies

The next label record is `moDetailDefs_c.f2750`, measured at
`[12607,16177)` in L1 and `[11056,14626)` in Concave. The seven layouts
in `LabelAnnotationFields.py` depend on the character format, the
distinct `utLineWidth_c.Serialize0` call site, and the shared condition
and signed selector branches. Its optional `f50` layer object appears
when condition `0x40000000` is set and `f48` differs from `-1`.
Require a typed owner and shared-map proof for that state before widening
the label profile. The first stored label widths occupy `[12881,12887)`
and `[11330,11336)` and match the respective font width bytes. Keep the
two call identities when composing their owners.

The pinned static `Base` and `Embed` walk under `moDetailDefs_c` names
62 layouts. The four layouts here, three accepted user-unit layouts,
and the accepted vector layout cover eight of those. The rest include:

- `DimAnnotationFields.py` (11), `BaseAnnotationFields.py` (11), and
  `AnnotationTablesFields.py` (10). They use branch comparisons and the
  accepted unit and vector rules where their owners require them.
- `LabelAnnotationFields.py` (7), `HelperAnnotationFields.py` (8), and
  `AnnotationFrameFields.py` (1). The frame needs `su_CStringArray` and
  signed count branches. Populated frame datum and indicator records name
  `moGtolItemDatum2022_c` and `moGtolItemIndicator_c`, which require their
  own layouts and native controls. Tagged tolerance and layer references
  also require concrete dispatch.
- `AnnotationDetailFields.py` (1), `CommonFields.py` (the
  `moSwiftGtsOptions_c` leaf), `ContainerFields.py` (`su_CStringArray`)
  and `MaterialFields.py` (`utLineWidth_c.Serialize0`). The two latter
  leaves have a separate bounded field-mode extraction.

The aggregate graph also executes the surrounding section, shared map and
part-body owners. After those dependencies arrive, qualify complete
`moDetailDefs_c` spans `[3234,20732)` and `[2287,18859)` with the
continuous part cursor and actual native graph. Annotation views have
a separate model lane. A read of individual font fields cannot establish
physical Config-0 ownership for optional property transfer.

## Reproduce

The source trace requires the pinned aggregate Git object. The reader replay
uses the active SDK and two committed sources. The command prints the
receipts without writing to the sources.

```sh
python3.14 -I -B re/tooling/sw2026/TraceCfgFont.py
python3.14 -I -B re/tooling/sw2026/CheckCfgFonts.py measure
```

The test planner includes the two queue integration modules under
`tests/Convert/Solidworks/Configuration`. The local evidence is the
guarded research command. Queue results remain revision-bound.
