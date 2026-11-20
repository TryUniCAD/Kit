# Header aliases retain their standalone index

At the start of a part's lightweight section, the configuration archive
registers the exact objects from its ModelHeader. L1's self-file object
has standalone index 69 and configuration slot 3. The ConcaveOwned part
uses standalone index 15 for its object in the same configuration slot.
The binding consumes zero bytes and advances the configuration archive's
base and counter to 4 in both cases.

Use the configuration map to resolve an inherited reference. Keep the
header object's original index and fields so the standalone header can
still be read or serialized independently.
[Native field order and process evidence](../../../../../../re/solidworks/records/ConfigHeaderLinkSlice2026.md)
