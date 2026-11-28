# Hopper saved databases need a native reopen

REA opened the pinned modelling PE image, but the first function request timed
out after 900 seconds waiting for Hopper's initial analysis and bridge startup.
Hopper completed its analysis in about 21 minutes. The completed database could
be saved and reopened directly in Hopper. The tested REA macOS provider
rejected the `.hop` target because its launcher cannot start the analysis bridge
for that saved database kind.

Save a completed analysis under a new path outside the repository. Resolve the
timed-out REA session on its original connection and verify that no cleanup
remains pending. Open the new database in Hopper itself, select the document by
its database path, and use the native scripting API for a bounded procedure.
Keep the original executable hash alongside the database and result hashes.
Do not assume that the direct native result was returned by REA.

The [constructor receipt](../../../../../../re/solidworks/measurements/2026/MarkupHopperAnalysis01.json)
records the timeout, cleanup, unsupported target response and successful native
procedure query separately.
