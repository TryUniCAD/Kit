# Native verification queue repairs

PR 209 queue acceptance exposed independent defects that the earlier PR reuse checks did not execute.
The [Linux comparison failures](https://github.com/TryUniCAD/Kit/actions/runs/44909982746/job/136863760372) came from treating numeric face and edge counts as unordered collections.
Numeric topology counts now use the existing numeric comparison and tolerances; geometric lists retain unordered matching.
CLI comparison assertions include the emitted report when a comparison fails.

Windows uses native handle metadata snapshots consistently across the path and open descriptor.
This avoids comparing CPython path creation times with descriptor metadata change times while retaining identity, size, timestamp, regular-file, reparse-point and link-count checks.
The path handle denies concurrent writes and deletion during the read.
Installed CLI integration coverage includes a rewritten stable document, historical measurement modification time, hard-linked inputs, directory inputs and oversized measurements.
See the [Windows snapshot gotcha](../../../Gotchas/Research/Workers/Verification/WindowsStatSnapshotTimes.md) and [topology comparison gotcha](../../../Gotchas/Research/Workers/Verification/TopologyCountsAreNotCollections.md).

Catalogue finalization again runs native verification for completed scope rescans after the supervisor settles.
Paused runs and active workers do not start verification.
Completed scopes can produce their application report while later scopes wait for evidence; this never promotes the overall incomplete result to completed.
A completed catalogue additionally requires nonempty passing live verification reports.
The source-file coverage guard remains in force.
Unavailable APIs retain actionable setup instructions.

The memory-reserve process case now checks the sequential contract: the first scope is queued, later scopes wait for predecessor evidence, and every job has zero attempts.
Checkout validation and reader argument preparation now have focused CLI modules, retaining existing forwarding and legacy outcomes while meeting the declaration limit.

## Verification

The failures above were observed on merge-group candidate `9ebb322451b9dd286b10b00678647b7cb997bb33`.
Black, Prettier, Python syntax parsing and Git whitespace checks are the only local verification performed.
No local tests, reproductions, collection or licensed application runs were executed.
Remote checks and a new merge-group acceptance run are required for the repaired revision.
These fixes do not establish licensed SOLIDWORKS or Fusion acceptance or writer qualification.
