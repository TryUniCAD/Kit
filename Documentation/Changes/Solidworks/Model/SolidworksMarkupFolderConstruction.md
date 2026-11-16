# Explicit markup folder construction

## Behavior

The shared research folder factory now admits `moInkMarkupFolder_c` through the
existing `moFolder_c` object model and serializer. It derives `f360=1` and
`f370=0` from the 2026 constructor/store rules. It does not add notes-area fields,
copy a native node or write a captured stream.

The part graph accepts two explicit complete class/name maps: the historical
notes-area set and the ordinary markup set. The ordinary set replaces the extra
top-level notes-area class with the concrete markup class. Unknown, incomplete
or combined sets still fail closed. All persistent IDs, feature counts, object
tags and stream lengths continue to follow from the graph.

`MakeTreeInput.py` supplies an independently authored neutral request for the
ordinary English presentation: standard system-folder labels, the concrete
markup role and the annotations cabinet. The markup and empty-material labels
also have independently verified 2026 resource identities. This is research
composition, not a new public adapter option.

## Evidence and verification

The [constructor and class-lookup record](../../../../re/solidworks/records/MarkupFolderConstruction2026.md)
documents native method identities, field rules and the separate notes/markup
classes. The [independent source lock](../../../../re/solidworks/v2026/heldout/TreeSourceLock.json)
was published at `7e3b294e3` before this writer change. It covers two new native
sources, four phases and 192 checks; private trees, geometry and poses remain
sealed until this writer is frozen and remote predictions pass.

The new discovery integration runs the existing guarded camera/part producer
in a fresh interpreter, requires eight complete archive comparisons, checks
concrete feature classes and unresolved references, and exercises rejection of
an unsupported combined folder set. Existing historical/current regressions
still require all eight previously measured output hashes unchanged.
Remote execution is pending. Only static source/AST inspection and formatting
ran locally; no local tests or writer/codec executions ran.

No generated native tree-parity acceptance is claimed. The source failure for
the earlier mixed-end pair remains failed and ineligible. General locale
selection, arbitrary folder edits, full feature coverage and production writing
remain unfinished. The public adapter is read-only.
