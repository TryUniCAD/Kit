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

## Earlier generated cohort in PR #121

The following measurements use their own exact build and source hashes.
[Original native receipt](../measurements/2026/GeneratedLocalBodyPartNative01.json)

## Decoder discrimination

`ScanPartRecords` calls `ParseBridge` with null ownership allowed only under
the legacy v12 prefix. For the current local transmit, the field read as the
bridge owner is `FACE.attributes_features`. Its typed value is zero and
its wire reference is one in every generated face. At the exact sequential FACE
offsets the legacy parser accepted zero of 6 rectangular faces and zero of 8
concave faces. Allowing the null attribute pointer accepted them all. Allowing
direct tolerance alone admitted none. All faces carry the existing tolerance
sentinel.

Keeping the remaining scan results then failed with `missing vertex point`.
The scan keeps the first accepted record for an encoded index. An incidental
record at body-payload offset 718 supplied point 4096 for rectangular encoded
vertex 65. The typed vertex record at 2115 supplies point 66. The concave scan
similarly used point 5120 at offset 810 for encoded vertex 95. The typed record
at 2965 supplies point 96. These are sample offsets. The local repair uses the
declared node lengths and links to find each record.

## Bounded repair and observations

The normal SOLIDWORKS part reader preserves its original result when it has
one. The local route selects exactly one configuration-zero LocalBodies
payload and its current body-free active partition and history. It reuses
the current typed kernel decoder, checks the complete one-solid owner graph,
and projects the line, plane, vertex and oriented fin records through the
shared neutral B-rep builder. [Reader](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/ReadLocalBodyBrep.py)

The host observations call `convert.open_document` on each exact SHA-256,
verify the returned model, and integrate its oriented boundary rings in SI
units. The reported figure of merit is the geometry from the SDK, compared
with the independent native cold measurements. Each generated case also
retained all three payload records and returned no B-rep with geometry
disabled. The native import control returned the same neutral B-rep as the
original decoder.

| Input | SHA-256 | Bodies / faces / edges / vertices | Volume, m³ | Area, m² | Centre of mass, m |
| --- | --- | --- | ---: | ---: | --- |
| RectangularBare | `370af2e50469c911a5655f9b84a64d3ffc6a26789248fd7a4f0268ec362018b5` | 1 / 6 / 12 / 8 | 0.000002574 | 0.00115 | (-0.0025, 0.014, 0.0085) |
| RectangularOwned | `e2f7f1c721986c8cf7d1f1c5368588dbebafd55222e4d2ed75d5652ace725408` | 1 / 6 / 12 / 8 | 0.000002574 | 0.00115 | (-0.0025, 0.014, 0.0085) |
| ConcaveBare | `e0c79c5d6c02f61e7a808a4e88a006e0f982d0c15adb70c7c81460375ff26e9e` | 1 / 8 / 18 / 12 | 0.000005160 | 0.002068 | (0.01744186046511628, -0.00430232558139535, 0.0035) |
| ConcaveOwned | `921a155cb67a721e4988032835d6a4d41e17b7f7f2e9e4bac2858210d7fdd05b` | 1 / 8 / 18 / 12 | 0.000005160 | 0.002068 | (0.01744186046511628, -0.00430232558139535, 0.0035) |

The native control input SHA-256 is
`13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325`.
The control-phase hash in the native summary identifies the observer record.
These observations cover the four disclosed candidate files and this control.
Held-out readback and public imported-body writing still require their own
qualification.

The completed-update cohort independently passes four native saves and fresh
reopens. The strict SDK reads one valid solid, the expected face, edge and
vertex inventories, and the actual `Imported geometry` feature from all four
generated files and all four native saves. It re-emits Config-0, CMgr,
ResolvedFeatures and both model header streams byte-for-byte in all eight.
The shared map advances 94→157 on generated input and 115→183 on native
saves. [Accepted native lifecycle](../measurements/2026/GeneratedLocalBodyPartCompleted01.json)
· [Eight SDK readbacks](../measurements/2026/ImportedLocalBodySdkSavedRead01.json)

## Aggregate integration after PR #172

The combined reader retains the strict source-backed import selection
and the existing cache-free parametric branch. Typed reference planes
and the origin can have public aliases while their binary classes remain
the actual datum owners. The same-path comparison decodes and reconstructs
three disclosed imports before and after integration. Each generated
16-stream container and its property manager compare byte for byte. An
independent renamed source retains its authored name and design-body link.
[Aggregate receipt](../measurements/2026/AggregateLocalImportReadback01.json)

## Bound topology for ordinary local payloads

The subsequent six original and native-saved snapshots select the
ordinary decoder's LocalBodies payload. The actual import and shared
atom prove one closed local solid for each selected design body. The
projection now derives the topology summary after that ownership
check. The B-rep, raw payloads, design IDs and bounds match the prior
reader. The revised summary has one solid, one shell, six faces,
twelve edges and eight vertices in all six cases.

The removal control alters only the actual resolved output-atom row.
Its ordinary geometry still decodes, and the local count binding
refuses because the reference no longer agrees with the atom manager.
[Typed topology receipt](../measurements/2026/ImportedNativeKeywordTopology01.json)
