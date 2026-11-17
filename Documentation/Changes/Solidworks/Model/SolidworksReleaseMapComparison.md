# SOLIDWORKS serializer release comparison

The research workflow can compare the checked-in SOLIDWORKS serializer maps offline. It reports observed membership, target address and vtable changes for modules present in both inventories, with separate counts for DLLs covered by one inventory. The comparison receipt includes both map hashes and distinguishes primary and alternate entries.

Run `CompareSerializeMaps.py` with two local map files and either `--check` for a byte-for-byte comparison to a receipt or `--output` to generate one. Provide the known module explicitly when a legacy map omits it. [Commands and verified 2025–2026 observations](../../../../re/solidworks/v2026/SerializeMapDiff.md)

The checked-in receipt was regenerated and checked byte for byte using the two repository maps. Inventory differences do not qualify a new reader or writer version. The adjacent-release procedure identifies the wire, construction and native acceptance evidence required to extend support. [Qualification procedure](../../../../re/solidworks/records/AdjacentReleaseQualification.md)
