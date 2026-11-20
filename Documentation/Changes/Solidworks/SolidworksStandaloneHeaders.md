# Typed SOLIDWORKS 2026 standalone headers

The internal archive codec reconstructs the standalone `Header2` and
`Contents/Config-0-ModelHeader` graphs for ordinary version 19000.
Each stream starts a new map and stores one `moHeader_c` root of schema
one. Typed fields preserve file and text handles, list order, logs,
scalar widths and bounding sphere data. The codec requires complete
input consumption and rejects unknown classes and a nonnull
configuration object.

The [process regression](../../../tests/Convert/Solidworks/ArchiveHeader/HeaderReplayTests.py)
uses the existing native L1 part to check exact re-emission and source
immutability for both streams. It expects only a JSON receipt.
Results for the extraction are pending remote CI.
[Provenance and historical comparisons](../../../re/solidworks/records/StandaloneHeaderSlice2026.md)
