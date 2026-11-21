# Generated rectangular child partition

The default SDK read resolved a validated exact solid in all three generated assembly pairs. The initial sketch reader added one false circle and reclassified the height relation as radius in both read modes. The controlled native comparison rejected the cache-bearing variant at open with warning 32.

The [typed rectangle ownership check](RectangleSketchOwners2026.md) subsequently
corrected the sketch geometry, driving constraints and bounds for all three
SDK reads. The experiment's generated files and independent B-rep measurements
are pinned in both receipts.

## Generation and provenance

The [isolated process](../../tooling/sw2026/AssemblyPartitionProcess.py) constructs the existing indexed assembly and an ordinary dimensioned child. It reads the four edges from the actual local `sgLine` endpoints, the placement from the sketch frame, and the depth from the actual forward blind boss parameter. It converts metres to millimetres, constructs the exact prism from the four lines, and sends it to `EncodeBrep(partition=True)` and `EncodePartition`. Its temporary neutral body identifier names the extrusion's actual `f08`. The SDK derives a separate design-body-to-feature link from the independent archive history. The payload carries its own topology record indices and none of the SOLIDWORKS-specific feature attributes. [Prism geometry](../../../src/convert/Geometry/Extrude/Polygon/PolygonExtrude.py), [partition API](../../../src/convert/adapters/solidworks/Container/Parasolid.py), and [history read](../../../src/convert/adapters/solidworks/Core/Adapter.py).

`BuildAudit` protects the emitter after grammar and code imports. Every run had zero runtime input reads. The process makes exactly one `EncodeBrepModel`, `EncodeBrepBody`, `EmitBodiesMut` and `EncodePartData` call. `EmitVendorMut` finds no feature attribute bases, so it writes none. The process denies any call to `EncodeBlankApi`, `EncodeBlankPart`, `WriteSolidAttrs` or `WriteBodySuffix`. The blank path reads `KBlankPartBody` and `KBlankDeltaBody`. The feature-attribute path would otherwise write the typed `LAST_BODY_MODIFYING_FEATURE_ID` assignment alongside unqualified values in `DOWNSTREAM_FACE_ID`, `SDL/TYSA_COLOUR`, `ENT_TIME_STAMP_2001`, `BODY_MATCH`, `SDL/TYSA_DENSITY`, `BODY_IN_LIGHTWEIGHT_PERM` and `ATOM_ID_2001`. The generated stream uses neither path. [Encoder source](../../../src/convert/Geometry/Parasolid.py).

The process emits one 3434-byte Parasolid payload under `SCH_1200000_12006`, and one length-framed compressed partition stream. The outer SOLIDWORKS history stays in archive version `19000` and retains the existing target Parasolid version metadata. The SDK's older-schema reconstruction derives its single region and shell from the decoded face adjacency. This experiment has SDK evidence for the older transmit schema inside the 2026 container. It does not establish that the SOLIDWORKS loader will hydrate cached bodies from it, bind the body to a live feature, or preserve it after save. The research entrypoint adds only `Contents/Config-0-Partition` to the child. The original streams and parent bytes are identical in each comparison. Existing composition defaults stay cache-free. [Independent SDK and geometry probe](../../tooling/sw2026/AssemblyPartitionProbe.py).

## Frozen probe

Run `python re/tooling/sw2026/AssemblyPartitionProbe.py <unused external directory>`. It creates three neutral requests and stages sibling pairs with and without the named cache. Their SDK-opened B-reps have 8 vertices, 12 line edges, 24 oppositely paired coedges, 6 planar faces with four-edge outer loops, one closed shell, one solid region and one body. The probe checks exact corner membership, endpoint trim consistency, loop connectivity, face planarity and outward orientation. A separate signed-tetrahedron integral obtains volume and centroid directly from the boundary and compares them to independent box formulas. The linked child equals the standalone read, and the repeated assembly has one shared definition, a rigid quarter turn and a translated placement. The missing-cache control raises `SLDPRT contains no readable Parasolid payload` for each default SDK open.

| Neutral profile width × height × depth (mm) | Occurrences | Boundary volume (mm³) | Area (mm²) | Local centroid (mm) | Compressed partition bytes |
| --- | ---: | ---: | ---: | --- | ---: |
| `OffsetRepeated` 18.5 × 24.8 × 16.7 | 2 | 7661.96 | 2363.82 | (12.05, 6.3, 8.35) | 1426 |
| `CenteredSingle` 37.6 × 21.4 × 10.9 | 1 | 8770.576 | 2895.48 | (0, 0, 5.45) | 1407 |
| `L1Single` 40 × 20 × 10 | 1 | 8000 | 2800 | (0, 0, 5) | 1387 |

The two novel rectangles and the disclosed L1 dimensions are discovery inputs. The tested writer base was `3c17262762ed465e4a29125dee46dfd38b696528` with tree `495a774e45ca6507d6208c9fb8bc93fa2331773a`, plus these two research scripts. `Index.json` SHA-256 `2ba14f2f3fd8185c2011bd9243566185fe3f309a9d8835be67581c3e3426b1eb` binds every neutral request and probe receipt. `SourceInventory.json` SHA-256 `c9c461db8a2c02eb7b3807aea53afbb4f717de0835581513102f498f82f07a54` binds the source imports, harnesses and Python version. The encoder digest is `539d7a62018e956df488b4cc49271bf4f8073ef521c702181d7979dd463a7353`. These artifacts are in the external `GeneratedPrismPartition-6c31` stage. The [repository receipt](../measurements/2026/GeneratedPrismPartitionSdk01.json) preserves the SDK results and artifact hashes. A15 and A16 remain sealed.

## Native intervention

Copy `L1Single/WithoutPartition` and `L1Single/WithPartition` one at a time into the exact encoded location `C:\Users\Public\Documents\KitOracle\GeneratedPrismPartition-6c31\Active\L1Single`. The two parent files share SHA-256 `75a62061ffee94dce7aa32607ee7aa39d73e1fcb044777d7317964bcc2daec7e`. The corresponding children hash to `2f9a7bc4ac421f5d18a60bd7c9fc38c9a73453173a5624ad7dadb1778120a331` and `024faf5e879743a6ad002a1bc4b9d748647b5d0044446a69c9c56f102ed5dd7e`.

The [native comparison](../measurements/2026/GeneratedPrismPartitionNative02.json)
used those exact byte pairs at the same encoded location. Without the partition,
the child exposed one body immediately on open and kept its 50 mm width through
the synchronized save and clean fresh reopen. With the partition, the same
parent opened with zero errors and warning 32, failing the initial gate. The
probe stopped that lane before rebuild or edit. Both controls passed across
five processes and all staged inputs remained immutable. The experiment
qualifies the archive construction and SDK geometry evidence only for the
cache-bearing variant. The native source of warning 32 remains unassigned.

## SDK history discrepancy

All three public reads retain the real `sldprt:plane:14`, `sldprt:sketch:18`, `sldprt:feature:21` blind join and all three driving values. The decoded sketch also contains a false circle tagged as the D2 radius. In `OffsetRepeated`, the `CircleSet` fallback pairs marker offsets 5493 and 5655 at the two ends of the same vertical edge. It reads a radius of 24.8 mm at `(21.3, -6.1)` and the correct rectangle independently from line offsets 5983, 6075, 6167 and 6259. Public `closed_profile_entity_ids` therefore reports loops of sizes 1 and 4. `BoundingBoxA` uses that profile list and reports `[-3.5,-30.9,0]` to `[46.1,18.7,16.7]`, while the decoded boundary has `[2.8,-6.1,0]` to `[21.3,18.7,16.7]`. The probe records both exact geometry and failed strict history semantics. [Sketch detection](../../../src/convert/adapters/solidworks/Core/Native.py) and [body summary](../../../src/convert/adapters/solidworks/Core/Adapter.py).
