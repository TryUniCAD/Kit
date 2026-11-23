# Compile an intact FreeCAD baked source to a local imported body

Two disclosed FreeCAD 1.1.4 files contain a literal standalone
`Part::Feature` with an authored Shape and no parametric dependencies.
The trial verifies the actual feature, final design body, Shape member
and active configuration through the intact neutral document. It
validates the retained FCStd archive and shape digests and compares a
fresh re-decode of the original in-memory archive with the supplied
neutral view. The original path and byte-stream entry points yield the
same plan. [Baked source locks](BakedFcstdSourceEligibility2026.md)

The plan derives six outward face rings, twelve edge incidences and the
signed corner geometry. All 26 typed boundary tolerances are `1e-7` mm.
The existing shared local-body composer generates the new Parasolid
nodes, partition and ordinary part archive at the original measured
locators and epoch. The guarded construction reads zero files after
intake. Both distinct processes reproduce the same receipt and match
both previously native-tested complete files exactly.
[Exact receipt](../measurements/2026/IntactBakedImport01.json) ·
[Earlier SOLIDWORKS 2026 results](BakedLocalToleranceNative2026.md)

| Case | Generated part bytes | SHA-256 |
| --- | ---: | --- |
| Baked01 | 9,910 | `5b4100d6c7f9b2e172337ced9c6c1d882dcac505ee8577414e8258c6028c9e83` |
| Baked02 | 9,895 | `448f35575f79d58e3154eba0f54d2eb151a2c6c2b0b23d1feb1126c6fffa8efc` |

The plan accounts for geometry, the active configuration and the
generated body linked to its actual import feature. It reports the
original FreeCAD parameter records, native payloads, provenance and
round-trip metadata as untransferred. Both ElementMap and StringHasher
collections are empty. A same-topology live `Part::Box` with actual
length drivers, a cross-format relabel and a stale neutral tolerance
under genuine retained bytes all refuse.

The normal registry still enforces its existing lossless transaction.
Public conversion, independent held-out compilation and native
verification of the effective reopened edge and vertex tolerances
remain open. This experiment publishes no CAD file and counts zero
benchmark conversions.

Run the [method](../../tooling/sw2026/imported_body_source/CompileBakedInput.py)
with the source tree from `660100bffe19eb22795c34006516feb369286674`,
the disclosed source directory and a new report path.

```sh
python3.14 -E -B re/tooling/sw2026/imported_body_source/CompileBakedInput.py \
  /absolute/path/to/DisclosedSources01 /tmp/IntactBakedImport.json
```
