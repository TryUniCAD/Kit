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
The sole modeling feature in each source is the XML `Feature` of type
`Imported`, id 18, named `Imported geometry`. The resolved name record and
`moBaseBody_c` class match the Unicode key of the local storage group. The
neutral timeline retains the import and its source provenance. The solid
and design body share an identifier and topology counts. The face loops
retain winding through the forward fin links and terminal vertices of the
current schema.

These observations qualify inspection of the native feature and its stored
solid. Parametric conversion acceptance follows the
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).

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
centroid from the returned face rings. It also checks the retained import
and design body ownership. The absent-history control retains the active
partition and local payload in an in-memory input. A separate control
keeps all three payloads and selects the actual first rollback mark, id 1,
while the active world retains id 3. A mismatched Unicode group key tests
the storage owner check. Each control checks strict refusal of the
required local solid and a warning with the same reason on explicit
non-strict reads. The metadata control sets `include_brep=False`.
Current revision acceptance is the integration result from the
repository merge queue.
