# A saved selected revolve body can have zero remap fields

A saved two-member revolve-cut selection includes both consumed stock atoms and both cut-result atoms. In one disclosed case, the second selected wrapper keeps its consumed atom, stock producer ID and same five-row representative through an angle edit. Its `f100` and `f104` remain zero in both saves. The other case stores the observed live face remap and result atom for its second wrapper. [Saved selection comparison](../../../../../../re/solidworks/measurements/2026/SelectedRevolveCutSavedContrast01.json)

Verify membership against the actual `f548` list, the consumed and result atom lists, the representative's producer and the later geometry. The serializer clears both remap words before it consults the validity of its retained live face and body. [Store evidence](../../../../../../re/solidworks/records/DownstreamBodyRepresentative2026.md#final-ordinary-store-normalizes-both-identity-words)
