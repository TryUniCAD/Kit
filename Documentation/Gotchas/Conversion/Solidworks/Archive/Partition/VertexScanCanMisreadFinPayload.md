# Vertex scanning can accept bytes inside a fin record

The current-schema typed partition reader and the general geometry byte scanner
can disagree on the same payload. A successful typed structural replay does
not imply that `ScanPartRecords` selected the same record boundaries.

For the disclosed generated five-line part, the scan accepts a kind-18 pattern
at body-relative offset 988, inside the actual kind-17 fin 18 at `[978, 1001)`.
Its apparent attribute is 83 and its point reference is 5120, which is absent.
`ScanTopoMut` uses `setdefault`, so the earlier incidental match wins over the
real kind-18 vertex at 2809. That vertex has typed index 82 and points to the
real point at 2837, typed index 83. Their scanner attributes are 83 and 84.

The unchanged public reader returns a document with no B-rep for this input;
the payload reader records `invalid partition topology (missing vertex point)`.
The four-line generated control and independent vendor control retain their
public B-reps. This observation does not establish malformed generated data.

For diagnosis, validate the complete current-schema graph with existing
`ReadActiveNodes` and `CheckXmtGraph`. Obtain every vertex boundary through
`XmtCursor` and `ReadXmtNodeMut`, validate its index and point identities, and
construct a separate transient vertex table. Do not patch one numerical offset
or silently modify the public scanner. The next qualified integration belongs
to the existing #121/B08 reader owners.

[Reproducible diagnostic and limits](../../../../../../re/solidworks/records/PartitionRecordBoundary.md)
are separate from [fin orientation](CurrentParasolidFinsStoreTerminalVertices.md).
