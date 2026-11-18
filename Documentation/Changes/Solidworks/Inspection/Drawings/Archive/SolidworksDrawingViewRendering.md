# SOLIDWORKS drawing view rendering state

The typed ordinary 2026 drawing Definition path now distinguishes an absent sketch cache from a present cache with zero saved records. It retains native occurrence-colour map keys and unsigned colour words, rather than rejecting every nonempty map.

`NamedRead.Rendering` and `FrontRead.Rendering` expose the actual owned view, cache presence, saved cache count and native colour rows. Nonempty rows add `drawing.occurrence_colours` to `Unprojected`. The native occurrence-to-child join and portable appearance interpretation remain unqualified. Existing detailing-index metadata is preserved.

Only the two explained view-state guards change. Other view, graph, annotation and context guards remain. Populated caches, noncanonical pointer flags, malformed counts/rows, unknown row fields and duplicate occurrence keys fail closed. No class schema or wire layout changes, saved defaults, research runtime imports or public writer registration are added.

Root's exact-source verification passed 43 prior workers, both original raw byte/map/alias comparisons, 60 malformed full-store cases and three complete generated-control variants. Both original normal Definition reads still reject at `blank drawing Definition excludes sheet annotations`. Native acceptance, full source equivalence and the original held-out verdict remain unchanged.

See the [native rules and source bindings](../../../../../../re/solidworks/records/DrawingViewRendering2026.md), [sanitized receipt](../../../../../../re/solidworks/measurements/2026/DrawingViewRenderingRead01.json), [empty-cache gotcha](../../../../../Gotchas/Conversion/Solidworks/Drawings/Qualification/PresentSketchCachesCanHaveNoSavedRecords.md) and [unprojected colour gotcha](../../../../../Gotchas/Conversion/Solidworks/Drawings/Qualification/NativeOccurrenceColoursNeedAComponentJoin.md).
