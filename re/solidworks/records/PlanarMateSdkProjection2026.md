# Typed SDK projection for ordinary planar mates

The shared SDK graph now has a projection for a version-19000 coincident, parallel, or positive distance mate with two direct part selections in one assembly configuration. The projection receives decoded `ArchiveNode` objects. It uses the same object identities that the archive tag reader binds. The mate and selected objects require concrete runtime class descriptors. [Projection](../../../src/convert/adapters/solidworks/Assembly/PlanarMates/ReadPlanarMate.py) · [Process receipt](../measurements/2026/PlanarMateSdkBoundary01.json)

For each ordered slot in the mate's `f410`, the wrapper's `f74`, `f78`, and `f7c` fields identify the mate and endpoint ordinal. The actual wrapper plane leads to a one-hop occurrence chain owned by the assembly. Its inherited `moExtFeature_c` must match both the occurrence's `f4f8` member and the chain's backlink. The occurrence must belong to the assembly list by object identity. The model index maps its persistent feature ID to the occurrence object ID in `ComponentsTree`. [Wrapper and chain rules](AssemblyPlanarEndpointConstruction2026.md)

The selected child matches its configuration ID and name, its file definition and creation time, and its update stamp. The SDK header graph supplies its file identity from `Config-*-ModelHeader`. The projection resolves the child datum ID to the actual named `moRefPlane_c` in the child's resolved feature graph. Its output retains the ordered occurrence and datum identities, stored frame, and alignment code. A distance reads the finite positive length from the live parameter beneath the display handle. [Shared header reader](../../../src/convert/adapters/solidworks/Archive/Header/ReadNativeHeader.py) · [Driving length](PlanarDistanceMateConstruction2026.md)

The direct caller is `ProjectPlanarMates.py`. The CLI consumes real parent and child archives and still checks the complete mate-list byte round trip. Six hash-bound pairs produced byte-identical JSON compared with the original CLI in fresh processes. This covered twelve endpoints across three disclosed vendor pairs and their three generated counterparts. A18 paired with the A17 child failed at the part identity join. [Projection command](../../tooling/sw2026/serial/ProjectPlanarMates.py) · [Process receipt](../measurements/2026/PlanarMateSdkBoundary01.json)

## Linked map dependencies

The census uses the disclosed A17–A19 pairs and generated coincident, parallel, and distance pairs with the schemas at `5fb3445359690ac08620c4d9ae9cf60a63a753ab`. It counts distinct reached schemas across each operation, including base, embedded and context reads. New runtime classes count distinct descriptors added between each stream's starting and terminal map. Context reads have separate maps.

| Read operation | Reached schemas | New runtime classes |
| --- | ---: | ---: |
| Parent Config-0 | 141 | 35 |
| Parent ResolvedFeatures | 99 | 19 |
| Parent MatesList | 69 | 13 |
| Child Config-0 | 148 | 40 |
| Child ResolvedFeatures | 150 | 47 |

Each coincident or parallel mate reached 44 schemas and added six runtime classes and 22 objects. Each distance mate reached 67 schemas and added 11 runtime classes and 28 objects. The native parent map next index advanced from 107 after Config-0 to 168 after ResolvedFeatures. The generated parents use 76 and 133, respectively. MatesList begins at that terminal counter and consumes tag references to actual earlier objects. A18's occurrence chain refers to an existing external-feature object at slot 11 and an occurrence at slot 8. The stream prefix checks the counter. It cannot supply this table. [MatesList wire rule](AssemblyMatesList2026.md) · [Separate mate stream](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/MateGroupChildrenLoadFromSeparateStream.md)

Automatic public SLDASM admission requires a complete linked graph producer. Config-0 binds the self file and external directory objects from its ModelHeader. ResolvedFeatures inherits the resulting map and reads its branch context from CMgr. Both the parent and the child use those dependencies. The current process uses the research graph loader for Config-0, ResolvedFeatures and MatesList, and the production shared header reader for the selected child header. At the measured revision, four distinct provisional schemas were reached in the parent dependency reads, while the MatesList read itself reached none. The receipt records those exact names. It also records the production projection source hashes and the independent file identities.

The public adapter's preexisting selection-string path is separate from this entry point. The native toolchain and held-out pairs are outside this source-only integration result.
