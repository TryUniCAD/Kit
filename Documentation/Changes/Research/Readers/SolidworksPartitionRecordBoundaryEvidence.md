# Diagnose a partition record-boundary collision

The new read-only research command compares the unchanged #121 geometry scan
with existing complete typed partition readers on two exact generated parts
and one locked vendor control. It binds input hashes, origin receipts,
dependency revision and method source. It writes only a diagnostic JSON report.

The five-line scanner accepts bytes inside a fin as an earlier vertex-use
record. The later correct record cannot replace it. All three complete typed
graphs pass the existing ownership check. Rebuilding a separate transient
vertex table from every typed vertex produces validated topology for all
three inputs while the unchanged public five-line read still lacks a B-rep.
There is no SDK, serializer or public heuristic change.

Use [the scoped command and selective checkout procedure](../../../../re/solidworks/records/PartitionRecordBoundary.md).
The [record-boundary gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Partition/VertexScanCanMisreadFinPayload.md)
records the actual earlier-match behavior and the next owner handoff.

## Actual verification

Two fresh CPython 3.14.6 processes emitted byte-identical report SHA-256
`b37f3d6abd4eedeac6df0eb2a6b453d42d87deaf723b821184dfb7984ebb3247`.
The executed method SHA-256 was
`aaf199c8fb15315c8c493eedfa40650ab950d7fd35281c30d05fc082b65028a2`.
The wrong SDK revision exited 1 before writing output. Inputs and SDK source
remained unchanged. No CAD process was launched.

This is a measured reader diagnosis on three disclosed inputs. It does not
qualify native acceptance, complete source admission or a general scanner fix.
