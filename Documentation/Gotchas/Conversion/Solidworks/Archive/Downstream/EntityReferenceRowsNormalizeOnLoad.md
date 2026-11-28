# Embedded entity-reference rows normalize on load

## Expectation

Reading and saving the embedded `moEntRefDownstreamIdData_c` map/vector retains every raw row and its order.

## Actual behavior

The exact 2026 native serializer writes signed-key map rows in tree order. Load clears and rebuilds that map. A duplicate key replaces its prior value. The following integer-vector loader consumes every declared wire row but skips zero values when reconstructing the runtime vector. The wire wrapper is embedded directly and has no additional class/object tag.

Consequently, the native reconstructed container is not a lossless representation of arbitrary original wire rows. The surrounding reference loader also repairs some sentinel identities, separately from the map/vector behavior.

## Workaround

A raw typed codec must preserve explicit counts, row order, duplicate keys and zero values. Model native fixups as a separate operation. Fresh construction needs independently established semantic inputs and canonical containers.

[The exact field/context record](../../../../../../re/solidworks/records/DownstreamEntityReferenceWire2026.md) binds duplicate assignment at `0x4b53b31c`, zero-value skipping at `0x4b53b3a5/0x4b53b3a7`, and the complete pinned Serialize body. [Verification](../../../../../../re/solidworks/measurements/2026/DownstreamEntityReferenceSource01.json) is metadata-only, with no SDK/native execution or malformed-file acceptance claim.
