# SOLIDWORKS part configuration and system construction

The SDK can construct the ordinary version-19000 part configuration and system
subgraph from explicit neutral inputs. It creates fresh style, unit, visual and
standard-view graphs, an independent configuration manager, twelve authored
system folders, the annotation cabinet, registered principal planes and the
origin with its fixed-point relation.

Use `MakePartRefs` with `StyleInput` and separate document/analysis `UnitInput`
values, then pass those references and the explicit root, manager, system and
target inputs to `MakePartSysMut`. Retain its actual `PartSystem` objects for
shared Config and Resolved map composition. `MakePartHeader` creates typed
fresh provenance headers with the allocator's real final counter.

Configuration IDs remain separate from global feature IDs. The manager stays
in its independent CMgr stream, and the environment folder keeps the same
actual object identity in Config and resolved roots. Folder order and names,
plane names, origin support, localized style vocabulary and epochs come from
the caller. Counts, references, creation counters and FILETIME words derive
from the constructed graph. No saved input, template, private data, CAD runtime
or research import is used by these SDK factories.

The [construction ledger](../../../../re/solidworks/records/SdkPartSystemConstruction2026.md)
classifies the fields and links the exact 2026 constructor evidence. Existing
[system-folder](../../../Gotchas/Conversion/Solidworks/SystemFoldersHaveModelBindings.md),
[configuration update-state](../../../Gotchas/Conversion/Solidworks/Model/ConfigurationConstructionClearsUpdateState.md),
[raw sketch backlink](../../../Gotchas/Conversion/Solidworks/Archive/Construction/SketchBacklinksDependOnArchiveContext.md)
and [compact index](../../../Gotchas/Conversion/Solidworks/Archive/Construction/CompactSketchIndicesOmitExtendedFields.md)
boundaries remain enforced.

The frozen source contains 75 SDK modules, four permanent process-test modules
and two guarded transport scripts. Static AST, Black, Ruff, strict Mypy,
Pyright, steering and donor scanning pass. No local product/test execution was
performed by the worker. The parent independently froze 4,393 source files and passed the permanent
`TestPartSystem` process check. Two SDK-only builds and their separate
preparations pass ten complete stream comparisons, twenty-eight malformed
request rejections and zero runtime input reads. Actual manager/configuration
identity, the shared environment and Config/Resolved prefix, native folder time
encoding, origin constraint and compact index remain checked. The
[sanitized receipt](../../../../re/solidworks/measurements/2026/SdkPartSystemConstruction01.json)
binds the exact source and retained result. Detailed child reports were not
retained, so no exact stream size, hash, map counter or class count is invented.
The six view modules remain separately landed shared dependencies.

This component leaves root/origin update scheduling and solver state at their
native constructor values. It does not construct a full part file, body
operation, container or external identity, and it does not enable public SDK
writing. Native open/rebuild/edit/save/reopen and held-out qualification remain
required. The known material-folder caption normalization remains unresolved.
