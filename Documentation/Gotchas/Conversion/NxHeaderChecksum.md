# NX SPLMSSTR header checksum

## Expectation

Editing one byte in an NX SPLMSSTR header or its reserved trailer should leave
the part loadable because the directory layout does not change.

## Observed behavior

NX 2506 rejects the part with:

```text
Checksum of data read does not match stored Checksum
```

The header directory is followed by a reserved trailer before the first file
payload. NX validates a checksum over the header and the trailer. A byte change
in the reserved trailer produces the checksum failure. A same-length byte
change in `/Root/part/attrs` loads successfully.

## Workaround

Preserve the complete header directory, reserved trailer, and file byte
lengths when rewriting a native part. Replace only payload bytes of the same
length. Refuse header-changing edits until the checksum coverage and algorithm
are recovered.

The writer enforces this boundary and raises a clear error for a header-changing
edit. See [the NX adapter guide](../../Reference/Adapters/Nx.md) and
[the NX data model](../../../re/nx/notes/DataModel.md).

## Evidence

The control part and a byte-flipped control were opened in NX 2506. The
attribute-only change loaded with zero unloaded parts. The header-padding
change failed with the checksum status above. The change entry records the
oracle measurements.
