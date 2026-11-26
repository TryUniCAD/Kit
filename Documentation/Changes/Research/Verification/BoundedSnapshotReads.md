# Bound verification reads by the observed file size

Native verification reads request the observed regular-file size plus one byte, bounded by the configured limit.
On Windows, the native handle snapshot establishes the size and rejects oversized files before reading.
On other systems, the opened descriptor size bounds the read.
The extra byte detects growth; the existing file identity, size, timestamp, link, reparse-point and final-path checks still apply.
No limit, rejection assertion, receipt hash or verification requirement changes.

The earlier implementation requested the entire limit plus one byte for every file.
Source hashing uses a 256 MiB limit and reads 3,879 SDK files individually.
The large buffer request made Windows verification bookkeeping take minutes despite small actual files.

## Evidence and limits

The [Windows queue job](https://github.com/TryUniCAD/Kit/actions/runs/44962146215/job/137023195551) completed 45 cases but failed three installed reader commands at their unchanged 300-second subprocess limits.
All thirteen saved-prism decoding controls passed within the first two minutes of the test step.
The complete candidate acceptance workflow passed separately.
Parallel scheduling exposed the stalled commands; it did not remove their cause.

Profiling the existing Windows host found 2.339 of 2.427 seconds spent inside buffered reads for 50 source-file hashes.
For 100 real source-file reads, the original implementation took 4.6743715 seconds; the bounded implementation took 0.0250773 seconds and returned identical bytes.
The profile retained the native handle and metadata checks and did not launch CAD.
These timings describe that host and workload, not a guaranteed CI duration.

Existing public CLI coverage retains its per-command and job limits, stable/oversized/linked/nonregular input cases, and complete saved-file decoding assertions.
No local automated test suite ran.
Current-head CI, native verification and the next queue candidate remain the acceptance evidence after publication.

See the [acceptance guide](../../../Reference/Research/FusionAcceptanceEvidence.md) and [Windows read-size gotcha](../../../Gotchas/Research/WindowsSnapshotReadAllocation.md).
