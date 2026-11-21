# Part configuration label definitions in SOLIDWORKS 2026

This tranche reads the complete seven-layout ordinary label group under
`moPart_c.fae0`. Its supported contexts keep the conditional layer
field absent. Whole configuration admission, neutral style transfer,
and native write acceptance require their own evidence.

Task `B04-SW2026-CONFIG-LABEL-FIELDS` belongs to the PR #121 takeover team.
Delivery branch `codex/solidworks-config-label-fields` uses accepted main
`f3d8760f214d65fbe71aa4b8bf81a17f553dbb60` and its merged font and width reader.
The original standalone label delta is `bdb35d3fa3243f6576a9d168b64f36cbd6373805`.
Its exit includes guarded integration and exact revision queue and review.

## Native owners

The exact `sldmfcu.dll` 34.5.2.0604 image, SHA-256
`af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`,
provides the serializer dispatch and field order. The native owner record
binds each class to its RTTI and complete function range.
[Exact-build annotation record](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/AnnotationArchive2026.md)
[Dispatch and field rows](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/AnnotationArchive2026.json)

| Native layout | Serializer entry | Direct member or suffix |
| --- | --- | --- |
| `moLabelDefs_c` | `0x3c85eae0` | Two i32 words, five concrete labels and the `f458` character format |
| `moDrViewLabelData_c` | `0x3c86dd80` | Eleven i32 fields, signed `f48`, conditional `f50`, two CStrings, three numeric fields, six character formats, two width records |
| `moDetailLabelData_c` | `0x3c86dca0` | Shared base, `u32 fcc`, `i32 fc8` |
| `moSectionLabelData_c` | `0x3c86e2c0` | Shared base, three f64 and five i32 fields |
| `moAuxLabelData_c` | `0x3c86dc20` | Shared base, `i32 fc8` |
| `moOrthoLabelData_c` | `0x3c86e210` | Shared base, `i32 fc8`, `i32 fcc` |
| `moMiscLabelData_c` | `0x3c86e210` | Shared base, `i32 fc8`, `i32 fcc` |

The two last rows have distinct RTTI identities and share the same
serializer entry. The direct calls add no tag or map slot. The base class
has no observed exported concrete runtime descriptor in the pinned
inventory. This tranche defines embedded grammar and keeps tagged
class admission unchanged.
[Runtime descriptor inventory](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/ConfigRuntimeDescriptors2026.json)

Each base reads two `utLineWidth_c.Serialize0` values between its
second and third character formats. The spelling preserves this caller
separately from the dimension line-font width `Serialize.2.0`.
These current-format spans can carry identical width fields. Raw field
values remain separate from the loader's runtime repairs.
[Width and character evidence](ConfigFontSlice2026.md)

## Physical source comparison

The pinned reader at `9f0ccb5389c121e750ca3b73f8e5d248b34d2e15` traversed
complete Config-0 in both tracked native parts. It observed the label
calls at `moModel_c.FUN_4c234150/fae0/f2750`. The table gives half-open
physical offsets. Each group contains five shared bases, 31 character
formats and ten label widths.

| Layout | L1 span | Concave span |
| --- | --- | --- |
| Complete label definitions | `[12607,16177)` | `[11056,14626)` |
| Detail | `[12615,13301)` | `[11064,11750)` |
| Section | `[13301,14023)` | `[11750,12472)` |
| Auxiliary | `[14023,14705)` | `[12472,13154)` |
| Orthographic | `[14805,15491)` | `[13254,13940)` |
| Miscellaneous | `[15491,16177)` | `[13940,14626)` |

The incoming and outgoing map base is four. The next slot is 69 in L1
and 54 in Concave throughout these calls, with no change of map
membership or entry identity. Each bounded replay establishes the live
`moPart_c` schema-one root with `ReadPartStart` and retains the three
initial class, part, and ModelHeader alias entries. The alias in slot
three retains original index 69 in L1 and 15 in Concave. The measured
later counter is applied to the bounded proof. The current layouts
need no intermediate slots.
[Source and span receipt](../measurements/2026/ConfigLabelSource01.json)

The native cases matched the independently decoded fields and exact child
and base stops through the ordinary shared body executor. The authored
cases vary signed and unsigned longs, doubles, width values, UTF-16
and Latin-1 CStrings, and selectors from `-32768` through positive
values. Three cases distinguished a clear condition, an unrelated bit,
and the exact `-1` sentinel with the layer condition set.
[Reader measurement and manifest](../measurements/2026/ConfigLabelReader01.json)

## Layer boundary and remaining work

The native base requests an `f50` object when archive condition bit
`0x40000000` is set and signed i16 `f48` differs from `-1`.
The recorded receiver type is `moLayerData_c`. Its current
serializer is at `0x3c85ebf0` and its vtable is at `0x3cc6b7a0`.
These locations establish the intended class. A concrete descriptor,
body grammar and real populated owner trace remain required.
[Current serializer table](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/data/Serialization/SerializeMap2026.json)

Both sources have clear conditions and five selectors equal to `-1`.
The supported reader runs the proved predicates and refuses the
unqualified active layer at the first tag. An authored active group can
present slot three as a tag. That slot belongs to a ModelHeader alias.
The decoder refuses at byte 54, immediately after the signed selector,
before resolving the alias. Zero and truncated active cases stop at
the same byte. Version, selector, text, concrete suffix and trailing
data refusals are also measured. The probes use no CAD process and
reject external access during decoding.

Full detail admission still requires the `moDimDefs_c`,
`moAnnotationDefs_c`, `moTableDefs_c`, and annotation helper families.
The separately measured frame belongs to `moGTolDataHelper_c`. It needs
`su_CStringArray`, the native signed count modes, and concrete owner
proof for populated datum, indicator and tolerance children. Keep the
`moLabelDefs_c` direct grammar in the same part cursor and shared map
when composing the complete `moDetailDefs_c` owner.
[Remaining detail dependencies](ConfigFontSlice2026.md#composed-detail-dependencies)

## Reproduce

Run the source trace with the pinned Git object present. Run the bounded
decoder with this checkout and its two tracked controls. The commands
emit the receipts and preserve all inputs.

```sh
python3.14 -I -B re/tooling/sw2026/TraceCfgLabels.py
python3.14 -I -B re/tooling/sw2026/CheckCfgLabels.py measure
```

The guarded host run is the current measurement. The two queue test
modules use the same process cases on the candidate revision.
