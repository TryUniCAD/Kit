# An empty biography does not imply an empty history

It is tempting to emit every optional metadata collection with count zero to
avoid inventing session provenance. The 2026 biography loader explicitly handles
a zero persisted record count and then appends a newly initialized current
record. The version-history and date-code-history loaders instead dereference
their final saved entries. Zero history counts do not follow the biography's
loader branch.

The evidence belongs to `sldmodu.dll`: biography serializer `0x4c71ec40`,
version-history serializer `0x4c71fb70`, date-code-history serializer `0x4c71f5b0`.
Binary identity, field rules and remaining uncertainties are recorded in
[HistoryConstruction2026.md](../../../re/solidworks/records/HistoryConstruction2026.md).

Construct nonempty history only from explicit truthful build provenance and
authored stamps. If that provenance is unavailable, fail rather than substituting
an empty history, a guessed native build or a captured control value. The
zero-record biography remains a research construction candidate until a complete
generated document passes held-out target acceptance.
