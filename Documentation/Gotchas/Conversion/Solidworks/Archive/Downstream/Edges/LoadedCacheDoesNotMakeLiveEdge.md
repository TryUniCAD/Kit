# A loaded downstream row is not a live edge cache

Expected: loading a populated part downstream stream, retaining reference flags `0x300` and finding f380/f60 would establish a reusable selected edge.

Actual: f380 lookup returns a reference wrapper in the actual selected model. Normal live resolution separately checks the real component/body context, entity class, runtime pointers and stamps. Failed reuse clears runtime state and cache bits `0x700`; it can then reconstruct the edge from actual surface identities. Successful reconstruction publishes a live edge handle in f70. The separate construction-only global used for a f340 shortcut is not established merely by loading model.f1348. A drawing also has its own f1570 lookup route and real-body/node fallbacks.

Keep construction, raw archive replay, standalone load and actual edge resolution as distinct proofs. Observe the intended actual child/config/body/edge and linked edit/save/fresh reopen; preserve unqualified paths when the route was not measured. This is exact-build static evidence, not a native failure report or universal flag default.

[Source rules](../../../../../../../re/solidworks/records/DownstreamLinkedEdgeResolution2026.md) · [Source-only receipt](../../../../../../../re/solidworks/measurements/2026/DownstreamLinkedEdgeSource01.json)
