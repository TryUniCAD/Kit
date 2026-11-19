# Drawing edge-cache lookup can precede save notification

Expected: a save observer can begin at FileSaveAsNotify event 7 and determine whether the drawing used its linked child's downstream edge cache.

Actual: the exact 2026 drawing save preparation can call the detailing bucket postprocessor and f380/f60 lookup before shared DoSave reaches event 7. Normal save events and a correct outline therefore do not identify this route. The preparation also waits for background work while pumping window messages, so the whole save need not retain one uninterrupted frame.

Arm the exact owned-process source-site observer before the normal COM SaveAs call. Match each individual wrapper call/return and its actual cache/model/downstream ID. Keep null returns, absent stops, demonstrated fallback and cleanup failure separate. For storage, retain actual SaveModelData and the forced externalization result of copy1; do not reuse a part-local EdgeRef graph or silently turn an authored false option into true.

[Source evidence](../../../../../../../re/solidworks/records/DownstreamLinkedDrawingSave2026.md) · [Unexecuted protocol](../../../../../../../re/solidworks/records/DownstreamEdgeAnnotationProtocol2026.json)
