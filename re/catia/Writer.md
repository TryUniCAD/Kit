# CATIA native B-rep writer

## Scope

`src/convert/adapters/catia/NativeWriter.py` emits a `V5_CFV2` CATPart from a neutral `BrepModel`.
It supports plane faces with one loop per face. It refuses other surfaces and multi-loop faces.

## Emitted structure

| Layer | Content |
| --- | --- |
| outer container | `Format`, `Data`, eight declared streams, `CATSummaryInformation` |
| nested container | `MAIN`, `Describe`, `MainDataStream`, `Header`, `SceneGraph`, `SurfacicReps` |
| `MainDataStream` | fan trim packets, FBB rows, edge table, vertex table |
| `SurfacicReps` | plane records, line curve rows, vertex roster |

Every count, length, offset, and directory entry is computed from the neutral model. The writer
does not read a vendor file.

## Verification

The writer round-trips a six-face box through the production reader:

```text
mode=native_brep faces=6 edges=12 vertices=8 validation=()
```

The writer sets `vendor_loadable=False` and `application_usable=False` because CATIA acceptance is
not measured. The Parallels CATIA install has no license, so the oracle cannot open the candidate.

## Limits

- Plane faces only.
- One loop per face.
- No feature history, sketches, dimensions, or constraints.
- No compressed cylinder, cone, sphere, or torus carriers.
- No CATProduct or CATDrawing output.

## Evidence

- `src/convert/adapters/catia/NativeWriter.py`.
- `tests/convert/catia/CatiaNativeTests.py`.
- `re/catia/Brep.md`.
