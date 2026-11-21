# Project disclosed SOLIDWORKS import geometry

`decode_import(raw)` requests a strict SOLIDWORKS SDK read with analytic
B-rep geometry. `project_import(document)` checks the sole design body's
final feature against its typed `moBaseBody_c` owner and the feature
name recorded there. The sole active configuration must agree with the
name, identity and both selection flags of its `moPartConfiguration_c`
manager record. [Projector](../../tooling/sw2026/imported_body_source/ProjectDisclosedImport.py)
· [Native authoring evidence](../measurements/2026/ImportedBaseBodySourcesNative01.json)

The input must contain one axis-aligned, closed, planar rectangular solid
in millimetres. The projector checks the eight exact SDK corner coordinates,
all twelve adjacent endpoint pairs, the six outward planes and their six
ordered four-edge outer loops. Every edge must have two opposite trim uses.
Line trim endpoints and plane origins use a residual limit of 10⁻⁹ mm
for floating-point evaluation. The generated neutral prism must have the
same corner set, undirected edges and oriented face boundaries. The local
BODY builder allocates a fresh graph from that prism.
[Local BODY builder](GeneratedLocalBodyKernel2026.md)

## Disclosed checks

| Source | Import feature | Configuration | Volume (mm³) | Area (mm²) | Centroid (mm) |
| --- | --- | --- | ---: | ---: | --- |
| Disclosed import | Imported1 | Default | 6669 | 2222 | (7, −11, 10.5) |
| Other shape | Imported1 | Default | 8190 | 2838 | (−18, 21, 2.5) |
| Renamed feature | Transfer Δ17 | Default | 6669 | 2222 | (7, −11, 10.5) |
| Renamed body | Transfer Δ17 | Default | 6669 | 2222 | (7, −11, 10.5) |

Two offline processes produced identical receipts. All four projections
retained identical geometry after removing source archive bytes, payloads,
attributes and provenance. Each generated BODY has 87 resident nodes,
matches the source corner-derived volume, area, centroid and bounds, and
round-trips through the typed codec and its compression frame. The two
renames keep the original kernel bytes. The other shape changes those bytes.
The parametric extrude control and 16 malformed variants were refused.
The audit observed zero runtime access during projection and construction.
[Numeric receipt](../measurements/2026/ImportedBodySourceGeometry01.json)

The result carries the verified feature and configuration names alongside
the B-rep. Its `body_name` is `None`. The strict neutral SDK exposes the
fallback `Body 1` even for the separate `Casting Ω72` rename. The geometry
projection omits the source part and body labels, datum and system tree,
remaining configuration data, material, appearance, properties, application
settings, identifiers, provenance, analytic carrier parameterization,
native payloads and tessellation.
[Native naming contrast](../measurements/2026/ImportedBodyNamesContrast01.json)
· [Separate body label ownership](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/ImportedBodyNamesUseSeparateOwners.md)

## Reproduce the offline receipt

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  uv run --offline --no-project --python 3.13 python -B \
  re/tooling/sw2026/imported_body_source/VerifyDisclosedImport.py \
  "$DISCLOSED_PACKET_PARENT"
```

Use the parent directory of the two disclosed packets
`ImportedBodySourceDisclosed03` and `ImportedBodyContrast02`. The verifier
requires the five recorded source digests and prints only the receipt.
These measurements cover offline source projection and generated local BODY
geometry. Native load and rebuild, held-out acceptance and SDK writing
remain separate milestones.
