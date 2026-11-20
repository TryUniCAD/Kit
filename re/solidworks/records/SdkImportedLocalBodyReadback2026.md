# SDK readback for generated SOLIDWORKS 2026 local solids

Task `B04-SW2026-IMPORTED-BODY`, PR #121. This result covers SDK readback of the
disclosed part candidates already measured on SOLIDWORKS 2026 SP05.2 build
`34.5.2.0604`. The native measurements retain their own job and process
identity in [GeneratedLocalBodyPartNative01.json](../measurements/2026/GeneratedLocalBodyPartNative01.json).

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
