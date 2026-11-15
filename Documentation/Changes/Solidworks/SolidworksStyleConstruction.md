# SOLIDWORKS 2026 style and unit construction

The research model builder can construct a fresh standard-1 `moDetailDefs_c`
graph and counted native unit tables from authored semantic settings. The graph
includes typed dimension defaults, annotations, tables, drawing labels, helper
records and Swift tolerances. It uses documented 2026 constructor rules and
constructor-referenced language vocabulary; it reads no source save or template.

The subprocess entry point delegates construction, codec round trips and result
projection to focused helper modules. Those helpers accept the already loaded
runtime contracts; importing them does not load a source save or start another
process.

The [construction record](../../../re/solidworks/records/StyleConstruction2026.md)
documents exact keyword-only interfaces, native DLL owners, addresses, field
classification and limits. Fonts, localized labels, print widths, unit choices
and precision are explicit caller settings. Unsupported standards, unknown unit
codes and malformed inputs fail closed. The two unit tables belong to separate
document/user and analysis slots; default model length and angle use the user
table.

The new process checks start the shared construction audit before builder
imports. Importlib code reads and loader directory discovery are recorded;
direct module data reads are rejected. Construction then blocks every file
read, directory scan and subprocess. The checks build independent candidates
from JSON, then serialize and read the entire style and unit
graphs through the existing native record codecs. They vary text, language,
counted exclusions, unit enums and unit-table shape. These are process-boundary
checks, not vendor acceptance. Local verification is limited to static parsing,
formatting, type and naming checks.

[Remote job 132707460142](https://github.com/TryUniCAD/Kit/actions/runs/43679709295/job/132707460142)
passed all three style process cases on PR 126 head `9adead2e1`, using synthetic
merge `e700702` with parent `53c79e739`. The complete typed style and variable
unit tables encoded/decoded/re-encoded exactly under the audit guard. The whole
step still had six inherited part/polygon failures, alongside 132 passes and
158 skips. Parent and full PR acceptance were not green; subsequent current-head
CI remains required.

GTol helper `f80=0` is derived from the native GTol-data constructor and the
actual data-to-helper projection, including its absent-data branch. Its
user-facing mode name and nonzero modes remain unresolved. Vendor loadability,
rebuild behavior and editing remain unproven. No source serializer, production adapter,
CAD application automation or existing builder was changed. The parent native
writer's full held-out acceptance criteria remain in force.

New findings are recorded in [folded style setters](../../Gotchas/Conversion/Solidworks/FoldedStyleSetters.md),
[PE import budgets](../../Gotchas/Conversion/Solidworks/PeImportBudgetHidesUnits.md)
and [GTol constructor initialization](../../Gotchas/Conversion/Solidworks/GtolUninitializedConstructorField.md).
The [style offset-key finding](../../Gotchas/Conversion/Solidworks/StyleSchemaOffsetKeys.md)
records the exact schema-interface repair discovered by the first remote run.
