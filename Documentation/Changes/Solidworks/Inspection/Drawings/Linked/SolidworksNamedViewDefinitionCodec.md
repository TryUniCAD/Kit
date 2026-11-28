# Typed named drawing Definition profiles

The internal SDK Definition codec now admits one ordinary Front, Top, Right or Isometric view at a finite positive explicit scale. It reuses the existing linked field layouts and adds explicit per-family selector, canonical-basis, scale and eligibility guards. The original unit-scale Front entry points keep their prior behavior.

Use `NamedGraph`, `WriteNamedDef` and `ReadNamedDef` under `Drawing.Definition.Named`. The complete owner graph must retain archive version 19000, one active unformatted ANSI A landscape sheet and actual support/child-reference aliases. Unsupported orientations, conflicting modes, invalid ratios, annotations and optional display/preview payloads reject. The public adapter remains read-only and semantic graph construction remains in research.

Eight new neutral designs each pass two isolated processes with exact full Definition/map parity, SDK read/write, independent readback and real linked-child identity. Independent trigonometric rotations and eight projected corners check geometry. Thirty additional shared/scale rejections and twelve per-family selector/basis/eligibility rejections pass. All 58 processes retain zero runtime input reads and unchanged predecessor sources. Steering, Black, Mypy, Pyright and the donor scan pass. This tranche performs no vendor-runtime or held-out run.

See the [usage guide](../../../../../Reference/Research/Solidworks/DrawingNamedDefinition.md), [source ledger](../../../../../../re/solidworks/records/DrawingNamedDefinition2026.md), [process receipt](../../../../../../re/solidworks/measurements/2026/SdkDrawingNamedDefinition01.json) and [scale gotcha](../../../../../Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingNearUnityScalePreservesRatio.md).
