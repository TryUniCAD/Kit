# Core sketch imports

## Expectation

A focused SOLIDWORKS sketch-projection helper can import geometry models from `convert`, just as the larger adapter module does.

## Actual behavior

On module initialization, `convert` starts adapter discovery before the shared model exports are fully initialized. A core helper that imports `GeometryKind`, `LineGeometry`, or other model symbols from `convert` can therefore fail with `ImportError: cannot import name ... from partially initialized module 'convert'`.

The error occurs while importing `convert.adapters.solidworks`, not while decoding any particular part. It is a dependency-boundary failure, not a malformed native stream.

## Workaround

Import shared `interchange` models directly in focused adapter-core modules instead of importing them through `convert`.

`src/convert/adapters/solidworks/core/PolylineSketch.py` follows that dependency direction and exposes only polyline projection. `Adapter.py` owns composition, profile-marker deduplication, and closed-wire identity, so no import cycle is needed for hashing or neutral model construction.

The public `ReadNativePart` path confirms five owned line entities and a five-edge closed wire in both vendor-authored and freshly written native parts. `ReadSldprt` and `OpenDoc` can instead preserve an embedded Kit source document when one exists; that separate source-preserving path is not evidence for the native projection.

See [the native five-line histories change](../../Changes/Solidworks/SolidworksFiveLineNativeHistories.md).
