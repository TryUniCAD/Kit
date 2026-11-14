# CATIA V5 research

This directory records the CATIA V5 container, native B-rep, and loader findings used by
`src/convert/adapters/catia/`.

## Current state

| Layer | State | Evidence |
| --- | --- | --- |
| `V5_CFV2` outer and nested containers | Confirmed on 27 parts and 3 products | `Container.md`, `src/convert/adapters/catia/Container.py` |
| Standard nested B-rep spine | Confirmed on 22 of 27 parts | `Brep.md`, `src/convert/adapters/catia/NativeBrep.py` |
| Plane and cylinder surfaces | Confirmed from bounds and trim vectors | `Brep.md` |
| Native B-rep writer | Implemented for plane faces with one loop | `Writer.md`, `src/convert/adapters/catia/NativeWriter.py` |
| OSMX feature graph | Symbol table decoded; object records unresolved | `FeatureGraph.md` |
| CATProduct occurrences | Names and references decoded; transforms and constraints unresolved | `Assembly.md` |
| CATDrawing, CGR, 3DXML | Not decoded | `OpenItems.md` |
| Vendor acceptance | Not measured; the Parallels CATIA install has no license | `Measurements.md` |

## Corpus

`examples/.CATPart` contains 27 vendor-authored parts. `examples/.CATProduct` contains 3
vendor-authored products. The two directories stay siblings because product references resolve
through the sibling part directory.

## Reproduce

```bash
uv run python re/catia/tooling/ListStreams.py
uv run python re/catia/tooling/ParseBrep.py
uv run python re/catia/tooling/BuildModel.py
```

`ParseBrep.py` prints the decoded face, trim, edge, and vertex counts for every part.
`BuildModel.py` validates the neutral B-rep model for every decoded part.

## Confidence

The confidence vocabulary is the repository one: confirmed, partial, not found, refuted.
A field is confirmed only when loader evidence and a corpus record agree. The B-rep spine and
surface bounds meet that bar. The compressed carrier parameters and the OSMX object graph do not.
