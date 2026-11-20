# Strict SDK readback for SOLIDWORKS 2026 local solids

Task `B04-SW2026-LOCAL-IMPORT-READBACK` extracts the typed read path from
[PR #121](https://github.com/TryUniCAD/Kit/pull/121). The local body transmit
stores the closed solid outside the configuration-zero active partition.
The ordinary scanner expects a non-null attribute reference when detecting
current faces. The generated local faces supply a null reference and keep
their shell links. Permitting the null pointer in a scan also admits
incidental vertex-shaped data. The typed path follows the declared records
and verifies the exact topology references.

## Scope and selection

The strict SDK reader considers the local path after the ordinary partition
decoder completes without usable or ambiguous geometry. It requires sole
configuration zero and exactly three payloads: the local body, the
body-free current active partition, and its validated rollback history.
It reads one closed solid with straight edges and planar one-loop faces.
The returned neutral B-rep retains winding through the forward fin links
and terminal vertices of the current schema.

## Disclosed measurements

Both fixtures are generated from separate neutral prism models. Their
exact hashes identify the cold SOLIDWORKS input in the completed-update
Probe03 retry. SOLIDWORKS `34.5.2.0604` completed open, rebuild, save, and
fresh reopen for these inputs with successful controls and zero load
diagnostics. An earlier strict SDK read on the research branch reported
the same body and boundary counts. The source revision, raw job and receipt
digests, fixture digests, and native measurements are in the
[compact receipt](../measurements/2026/LocalImportReadbackFixtures01.json).

| Fixture | Bodies / faces / edges / vertices | Volume (mm³) | Area (mm²) | Centroid (mm) |
| --- | ---: | ---: | ---: | --- |
| RectangularBare | 1 / 6 / 12 / 8 | 2574 | 1150 | (−2.5, 14, 8.5) |
| ConcaveOwned | 1 / 8 / 18 / 12 | 5160 | 2068 | (17.441860465, −4.302325581, 3.5) |

The [public SDK integration](../../../tests/Convert/Solidworks/Core/SolidworksLocalBodyTests.py)
checks both exact input hashes and computes signed volume, area, and
centroid from the returned face rings. The missing-history control retains
the active partition and local payload in an in-memory input. The
metadata control sets `include_brep=False`. Current revision acceptance is
the integration result from the repository merge queue.
