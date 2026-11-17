# A drawing save event returns an aggregate listener result

A passive `FileSaveAsNotify` listener returning zero establishes only
that listener's response. The native dispatcher combines the results
of all listeners. The save routine can return before storage when the
combined result is nonzero, even after the listener observed event 7.

Use the combined result or an independently observed downstream
storage entry when localizing the generated blank's failure.
[Native branch map](../../../../../re/solidworks/records/DrawingSavePostEventBranches2026.md)
