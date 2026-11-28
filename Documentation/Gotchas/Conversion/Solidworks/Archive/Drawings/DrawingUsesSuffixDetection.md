# SOLIDWORKS drawing inspection uses suffix detection

An `.SLDDRW` path lets the conversion SDK select its SOLIDWORKS adapter and dispatch the drawing CLSID to `open_document(path, strict=False)`. An explicit `source_format="slddrw"` selects a registry identifier. That identifier has no registered reader in the current checkout and raises `AdapterNotFoundError`. For the current bounded inspection use the drawing file path and the adapter's suffix detection. [Generated drawing inspection evidence](../../../../../../re/solidworks/records/GeneratedBlankDrawing2026.md)
