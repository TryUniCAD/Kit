# NX SPLMSSTR header and footer seals

## Expectation

Editing header fields or changing a stream size should leave the part loadable
because the directory and payloads remain internally consistent.

## Observed behavior

NX 2506 rejects an unsealed edit with:

```text
Checksum of data read does not match stored Checksum
```

The modern container has two xxh32 seals:

- the header seal is stored little-endian at `trailer_start + 0x21E`, where
  `trailer_start = 0x19 + header_directory_length`
- the header seal covers bytes `0x19` through the seal field, so it includes
  the complete header directory and every trailer byte before the seal
- the footer fingerprint is the final four bytes and covers the footer
  directory from the footer offset to the fingerprint

Rebuilding a directory with different sizes, offsets, or paths changes both
the covered bytes and the footer directory. The stored seals then fail.

## Workaround

Recompute both seals when the container is rebuilt. The adapter does this in
`SplmBuild`:

1. Write the header directory and the preserved trailer.
2. Compute `xxh32(header[0x19:seal])` and store it at the seal offset.
3. Compute `xxh32(footer_directory)` and append it as the terminal
   fingerprint.

The writer verifies both seals after rebuilding and refuses an inconsistent
container.

## Evidence

NX 2506 saved seven variants of the same part with different geometry and
directory layouts. The computed xxh32 digest matched the stored header seal
and footer fingerprint in all seven files. A Kit rewrite that grew
`/Root/FastLoad/ExternalReferences` by four bytes shifted the directory and
payload offsets, resealed both regions, and loaded in NX with one body, the
original feature tree, six expressions, volume `23999.999999999996`, area
`5200`, and unchanged mass. See
[the NX adapter guide](../../Reference/Adapters/Nx.md) and
[the NX data model](../../../re/nx/notes/DataModel.md).
