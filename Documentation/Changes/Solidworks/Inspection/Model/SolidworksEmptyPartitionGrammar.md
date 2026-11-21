# SOLIDWORKS empty Parasolid partition research

The research encoder can generate the paired Parasolid partition and
rollback stream for an empty geometry graph. Call
`builders.EmptyPartition.blank_partition_stream` from the 2026 research
tooling with an `EmptyHistory` carrying the current mark ID and delta
handle. The default transmit format is the SP05.2 kernel build. A separate
historical format reproduces the established blank-stream interface bytes.

The generated 2026 section pair matched the disclosed E0 part's complete
578-byte stream. The historical pair matched the existing 577-byte output.
Two independently chosen mark states changed the relevant fields and
compressed lengths. An emission audit recorded zero file opens. Native
acceptance of newly generated documents and nonempty geometry remain outside
this research result. [Wire rules and verification](../../../../../re/solidworks/records/EmptyPartitionGrammar2026.md)
