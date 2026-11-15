# SOLIDWORKS authored creation-log names

The research metadata builder now accepts the optional `name` in each
`revision_logs` mapping and preserves it in `moLogs_c.f50`. A named document's
creation log takes its explicit authored document name. Omitting `name` retains
the log constructor's empty seed. This does not fabricate vendor save history,
license state, identity, or timestamps.

The previous rejection treated the empty log-constructor seed as the only
supported final state. Static analysis closes the missing caller: active
filed-concept construction at `sldmodu.dll!0x4bda5a20` assigns the document name
after attaching the creation log. `sldarchiveu.dll!0x31a04830` serializes the
member as a CString without an emptiness branch. The
[construction reference](../../../re/solidworks/records/MetadataConstruction2026.md)
and [constructor-seed gotcha](../../Gotchas/Conversion/Solidworks/Archive/CreationLogDocumentNames.md)
record the field ownership, module digests and instruction evidence.

Remote process coverage constructs metadata under the shared import and runtime
file-access guard, encodes and independently decodes every archive stream, then
requires exact re-encoding. The named-document case checks Unicode log names in
Header2 and ModelHeader, corresponding KeyWords names, input-dependent stream
lengths and unchanged Biography/History streams. Separate process construction,
codec and reporting modules each own one responsibility; all load under the
import-phase audit before strict construction denies file access. The runner
also rejects a constructor that catches and hides a denied read. No local tests, reproductions,
collection or builder imports are run. Current-head remote results belong in the
PR; static parsing and formatting do not establish process success.

This change closes one semantic input. It does not establish native loadability,
rebuild behavior or acceptance of the complete generated document. Later log
roles, final save normalization and other documented metadata restrictions
remain separate work.
