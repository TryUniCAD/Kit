# SOLIDWORKS edited drawing view positions

The opt-in drawing reader reports the authored view position from the native Definition record. The independent Header2 bounds still corroborate the view outline. Asymmetric outlines can have a different centre after a view move or linked model edit.

Use `open_document(source, strict=False)` or `kit decode SOURCE --partial` for a supported single-view drawing. The reported position and outline are in metres. The reader still rejects a nonplanar position or inconsistent outline. Strict drawing reading remains unavailable.

The [2026 readback receipt](../../../../../../re/solidworks/measurements/2026/DrawingEditedViewPosition01.json) records 63 fresh SDK processes. Six edited states now match the native position and outline. The other 24 disclosed states produce identical neutral documents across the change. Twenty-four states had a live or saved native observation and all matched. Separate malformed position and outline probes and the strict-mode probe were rejected.
