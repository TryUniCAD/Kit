# History needs its final states

Fresh Biography can store an empty record list. The ordinary
version-history and date-code-history loaders each read their
last state. Their lists therefore need at least one stored state.

Build both histories from the actual target version and explicit
build provenance. Check the count and the concrete date-code
object before treating a stream as a complete graph.
[Loader and disclosed stream evidence](../../../../../../re/solidworks/records/HistoryStreamSlice2026.md)
