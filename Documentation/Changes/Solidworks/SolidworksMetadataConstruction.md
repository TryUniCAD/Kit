# SOLIDWORKS metadata construction

The research-only
[`Metadata.py`](../../../re/tooling/sw2026/builders/Metadata.py) module constructs
2026 Header2, ModelHeader, Biography, History and KeyWords archive records from
explicit semantic inputs and shared `Core.Obj` schemas. It returns objects or
stream bytes without reading saved files or launching a vendor runtime.

Callers supply persistent-id allocator output, owning-model context, names,
revision logs, counters, timestamps, actual configuration/feature graphs and
truthful provenance. The builder supplies no stock feature graph, recorded
field table, captured default or donor fallback. The
[construction reference](../../../re/solidworks/records/MetadataConstruction2026.md)
documents the exact keyword-only interfaces, binary ownership and each emitted
field's formula or constructor-derived seed.

An empty persisted biography follows a recovered native loader branch. History
requires nonempty version and date-code arrays with explicit provenance.
Unsupported native-save flags, nonzero header license state, component references,
unrecovered feature tags and multiple dissectable children fail closed.
The [history cardinality gotcha](../../Gotchas/Solidworks/EmptyHistoryNeedsState.md)
explains why these streams cannot share one empty-collection policy.
The [active-content counter gotcha](../../Gotchas/Solidworks/HeaderActiveContentCounts.md)
records that macro-content categories must not be derived from ordinary feature
counts.

This is a construction candidate, not a complete part/assembly writer or an
accepted native document. Constructor seeds are distinct from final model state.
Header enum/flag domains, active-content and reference summaries, cached bounds,
final counters and save normalization remain incomplete. No generated file has
passed the target application for this component.

The PR adds remote process-boundary integration checks for construction under a
runtime file-access guard, input-dependent stream sets and lengths, byte-complete
schema decoding/re-encoding, semantic graph values, Unicode XML and provenance
rejections. No local tests, reproductions, collection or builder imports were
run; local checks are static parsing and formatting only. Current-head remote
results are reported in the PR. The
[initial remote smoke run](https://github.com/TryUniCAD/Kit/actions/runs/43673584432/job/132688748536)
selected all three new process checks and finished with 126 passed and 158
unrelated unavailable-corpus skips. Later heads require fresh checks.
Merge-queue acceptance and held-out vendor acceptance are separate obligations.

## Class schema correction

The native class audit found that `su_CStringArray` requires schema zero,
although `suObList` and the concrete metadata `mo*` classes use wire schema one.
Header user/company arrays now emit the binary-proven zero schema explicitly.
The [construction record](../../../re/solidworks/records/MetadataConstruction2026.md)
records exact getter/descriptor addresses and the image digest. Native
acceptance of the combined corrected part remains pending.
