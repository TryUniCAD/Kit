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

## Raw extraction and curved imports

The missing-history control also exercises public raw extraction. It
checks both readable payloads by hash and retains the strict document
refusal. A separate control checks refusal of a truncated Parasolid frame.
The read mode travels in a typed option so strict adapters keep their
format-specific option validation. A [Fusion integration](../../../tests/Convert/Api/Fusion/RawBrepTests.py)
checks extraction from a supported parameter archive through a
non-seekable stream and expects an empty payload tuple.

Read-only strict SDK comparisons used the disclosed native cylinder
sources from the [topology receipt](https://github.com/TryUniCAD/Kit/blob/12d8ba0381af7504f4680088c93ee64642a8be6b/re/solidworks/measurements/2026/ImportedBodyTopologyNative01.json).
The native `Result.json` has SHA-256
`bbaa59c9661882912fdc0f140feb864824a9ddc36609e902e359d8c50ffd1105`
and records healthy controls on `34.5.2.0604`.

| Native source | Source SHA-256 | LocalBodies payload SHA-256 |
| --- | --- | --- |
| CylinderZ | `ef72c75f230331903726a4e48ca61682736289dba78261d654071f2fe2a54166` | `d6e924671f7e65f9d985f9043cb0c03ac5ecd258eae08d732c0b038f3363e09d` |
| CylinderReverseY | `91a3a675d932d0f14c886446885980d484beb66a4f821d5ecfe9908e41182179` | `81b3209741cffe06e5332b552d82743554eb9ce3415688b82e3c32f78cda623f` |

Revisions `c34686b1b448485ae78e00ceff89ee9536094473`,
`ba5285916f31294b457fd5ca410567e3e48895c7`, and
`bf91cbe27e4b33df2d903bd4d8ad4b1769ef4eda` each returned a valid B-rep
with one body, one shell, three faces, two edges, and two vertices for
both inputs. Each boundary has one analytic cylinder and two planes.
The ordinary decoder accepts each LocalBodies payload directly. That
result keeps priority over planar reconstruction and its refusal policy.
