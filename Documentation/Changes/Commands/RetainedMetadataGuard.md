# Refuse retained source bytes in CLI metadata

`kit convert` checks document metadata before invoking a writer, including metadata on embedded assembly documents.
The retained-source key `solidworks_source_bytes` is refused whenever present, including with empty or nonbinary values.
Raw `bytes`, `bytearray`, and `memoryview` values are refused through nested mappings, lists, tuples, sets, and frozen sets.
The scan protects against container cycles and does not trust aliases or wrapper names.

This closes a source-retention route that can exist even when a document has typed feature history and linked geometry.
Public SDK source-retention behavior and developer inspection remain unchanged.
Ordinary provenance text, hashes, and paths remain eligible, and the existing strict Fusion round trips remain required.
Metadata eligibility does not establish native or parametric acceptance.

Process cases start with a real typed Fusion cylinder and retain the actual committed SOLIDWORKS fixture archive in metadata.
They cover the original key, an alias, nested mappings and JSON-supported collection forms, plus empty or null retained-source markers.
Root and nested cases validate source documents and verify source preservation, missing or existing destination preservation, and successful `kit decode` inspection.
Positive cases preserve digest and text provenance metadata.
The existing Fusion compatibility job executes this test subdirectory.

The JSON wire serializer supports binary `bytes` records but rejects `bytearray` and `memoryview`; cycles are not serializable.
Those broader scan branches have source-inspection evidence, not JSON process-fixture evidence.
No tests, SDK decoding, or CAD applications ran locally.
Pinned Black and Prettier formatting passed.
Pyright reported zero errors, mypy reported no issues, and steering compliance passed for the three new Python files.
Pyright also reported three unsupported settings already present in the repository configuration.
Tracked-tree path policy and staged whitespace checks passed; remote process evidence remains required.

See [command usage](../../Tasks/CommandLine.md) and [the retained-source metadata gotcha](../../Gotchas/Conversion/Commands/RetainedSourceMetadata.md).
