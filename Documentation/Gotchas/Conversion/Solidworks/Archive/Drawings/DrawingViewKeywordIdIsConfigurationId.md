# Drawing view keyword IDs identify the referenced configuration

The drawing's `View` keyword rows use `id` for the selected model configuration. In the two disclosed SOLIDWORKS 2026 drawings that ID is `0` and the `moAbsoluteView` feature ID is `11`. The resolved branch of `moDrView::SerializeXmlData` reads the linked configuration before formatting the keyword row at `0x4c98ad4e`.

Build the two keyword `View` rows from the actual linked configuration and retain the same ID in `SW-Config-Model-View-Sheet-List`. The view's own persistent ID belongs to its typed Definition object. [Native routine and stream rules](../../../../../../re/solidworks/records/GeneratedFrontDrawing2026.md) · [Disclosed measurements](../../../../../../re/solidworks/measurements/2026/GeneratedFrontDrawingCandidate01.json)
