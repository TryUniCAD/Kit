# Internal named-view Definition codec

The internal SDK can write and completely read one ordinary Front, Top, Right or Isometric drawing view at a finite positive explicit scale. This extends the typed codec. Public SOLIDWORKS writing remains disabled, and the complete neutral graph factory remains separate work.

Use `NamedGraph`, `WriteNamedDef` and `ReadNamedDef` under `convert.adapters.solidworks.Drawing.Definition.Named`. Supply the complete UI drawing owner, archive version 19000 and the exact orientation name. The reader also requires that explicit orientation. It returns the typed graph, actual archive map and grammar evidence.

Preserve the single active unformatted ANSI A landscape sheet and the actual support/reference aliases required by the [linked Front boundary](DrawingLinkedDefinition.md). Named profiles use the same field layouts. The guard checks the selected name, native selector, source-derived canonical rotation, explicit ratio, transform scale and separate dimension-eligibility cache. Unsupported families or conflicting state raise before output is returned.

The original Front-only codec keeps its unit-scale admission. Use the named overlay for rotated or nonunit views. Annotations, additional sheets or views, preview/detail maps, populated display caches and alternate reference modes remain excluded. Abort the enclosing construction on any codec error.

Eight independently authored designs each pass two isolated processes. Complete stream bytes, final maps, full SDK read/write, independent readback and real linked-child identity match. An independent trigonometric/eight-corner predictor verifies orientation and bounds. Thirty shared/scale rejection jobs and twelve per-family rejection jobs also pass. All 58 workers retain zero runtime input-file access, and all predecessor files remain unchanged.

These are offline codec measurements. They do not add native save/reopen acceptance or enable public export. See the [source ledger](../../../../re/solidworks/records/DrawingNamedDefinition2026.md), [receipt](../../../../re/solidworks/measurements/2026/SdkDrawingNamedDefinition01.json), [retained native scale/support evidence](../../../../re/solidworks/records/DrawingScaledSupports2026.md) and [near-unity scale gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingNearUnityScalePreservesRatio.md).
