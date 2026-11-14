# Reject opaque records in CLI conversion

## Behavior and usage

`kit convert SOURCE DESTINATION` now checks the document returned by its selected
SDK reader before invoking the writer. It refuses `NativeFeature` definitions
and `NativeGeometry` sketch entities in the root or any nested assembly document.
It also refuses PR #94's `kit.research_read_status: unqualified` metadata, including on nested components, even when the installed SDK predates that safeguard.
These records preserve vendor payloads whose portable semantics are still unknown.
Serializing them as interchange JSON does not make them conversion-ready.

Use `kit decode SOURCE` or the deterministic `kit research` commands to inspect
these files and continue reverse-engineering work. Inspection output and the
research document/receipt contract remain available. The guard changes only the
user-facing conversion command; public SDK read and write behavior is unchanged.

The CLI selects and reads the source once, checks it, then uses the public SDK
writer. Strict reading, configuration selection, explicit format selection,
carrier refusal, source protection, and overwrite behavior remain enforced.
Reports retain the selected reader's source identity and the actual writer's
destination identity, including JSON inputs carrying original vendor provenance.
Refusal exits with status 1 and leaves missing or existing destinations untouched.

This guard addresses explicit opaque records. A passing conversion still requires
all applicable native-loadability, editable-history, lossless-conversion, and
target-application acceptance evidence; it establishes none of those by itself.
See [the CLI procedure](../../Tasks/CommandLine.md) and
[the opaque JSON gotcha](../../Gotchas/Conversion/Commands/InterchangePreservesOpaqueRecords.md).

## Verification

No local tests, decoding runs, or CAD applications were executed.
Pinned Black, Pyright, and Mypy checks and the repository steering/path checks
cover the changed source and process cases. Execution evidence belongs to remote
CI on the accepted PR head; no new native acceptance result is claimed here.

Actual subprocess coverage exercises native SOLIDWORKS refusal, root and nested
JSON native-feature/native-geometry and unqualified research-marker refusal, missing and existing destinations,
source preservation, and continued developer decoding. Genuine typed Fusion
cases retain successful JSON conversion, overwrite handling, native round trips,
and selected-adapter report identities. Typed-source cases retain the unsupported
writer and CATPart output-usability policy checks. This is a CLI follow-up repair
for the conversion guard, separate from deterministic research automation.
