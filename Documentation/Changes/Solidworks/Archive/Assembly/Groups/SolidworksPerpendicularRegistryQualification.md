# Qualified perpendicular assembly writing

The public SOLIDWORKS 2026 writer now accepts one initially satisfied perpendicular between principal planes of two direct occurrences of one owned dimensioned rectangular part. It writes the native `.SLDASM` and its generated sibling `.SLDPRT` through `convert.write_document`, with native usability and loadability reported on the result. Use an unused filesystem destination and provide the corresponding Windows path when writing from another host.

The profile has one fixed occurrence and unknown neutral alignment. Initially invalid angles, extra or mixed mates, custom datums, and nested components are excluded.

Both pre-writer locked pairs passed 484 checks, twelve paired native comparisons and six strict SDK readbacks across twelve fresh processes with four healthy controls. Independent child depth edits, valid reorientation, synchronized saves and fresh reopens preserved the native owners. Strict writer processes reproduced the two disclosed native-tested files on the matching interpreter. The [process integration](../../../../../../tests/Convert/Solidworks/AssemblyWriting/PerpendicularPairTests.py) verifies both selection routes and rejection of invalid starting geometry.

[Writer usage](../../../../../Reference/Adapters/SolidworksAssemblyWriting.md) · [Exact result and limitations](../../../../../../re/solidworks/records/PerpendicularRegistryAccepted2026.md) · [Native receipt](../../../../../../re/solidworks/measurements/2026/SdkPerpendicularRegistryHeldout01.json)
