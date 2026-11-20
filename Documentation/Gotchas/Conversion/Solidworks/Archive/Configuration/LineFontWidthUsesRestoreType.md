# Line font width uses restore type two

A line-font width and a view-label width can have the same six bytes in
version 19000. The line-font loader passes restore type two and force
zero to the width serializer. The older width grammar uses these
arguments to select which fields are present.

Keep `utLineWidth_c.Serialize.2.0` for `uiLFConfig_c.f10`. View labels
select `utLineWidth_c.Serialize0`. Record the caller's layout identifier
and preserve the stored width value separately from the runtime cache.
[Observed wire contrast](../../../../../../re/solidworks/measurements/2026/ConfigFontSource01.json)
[Exact-build line-font evidence](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/solidworks/records/DrawingLineFontArchive2026.md)
