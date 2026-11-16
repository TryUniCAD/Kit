# Provisional schemas do not prove archive closure

## Expectation

A byte-identical round trip proves that the exercised archive schema is complete.
The registry's provisional inventory identifies exactly which provisional schemas the input used.

## Actual behavior

The registry inventory includes every provisional declaration, including declarations that the selected input never executes.
Schemas also execute through base, embedded and custom-framing calls, beyond the concrete class names in object headers.
A raw byte field can preserve bytes without classifying its contents or proving how a fresh writer computes them.
Byte identity therefore does not establish the complete data model, derived-field rules or native acceptance.

The round-trip report now records actual load and store schema usage separately.
It preserves linked-map seed usage as a distinct dependency record.
Custom prerequisite reads identify their source candidates without receiving standalone byte-comparison credit.
Fresh contexts prevent an earlier file's coverage from appearing in another file's result.

## Workaround

Use `--require-proven` in the authorized remote process-boundary check.
Inspect each stream's `schema_usage.load`, `.store` and `.dependencies` records.
Require empty `provisional_schemas` and `missing_schemas` lists for the exercised phases.
Also require completed load, store and dependency phases, no errors and no unread tails.
An error before named registry dispatch can leave the missing-schema inventory empty.
Empty inventories from incomplete operations do not establish admission.
Keep byte identity, unread tails and schema admission as separate observations.

Inspect `raw_operations` for the owning schema, field, length rule, operation path and observed byte count.
A callable length rule with unavailable source records that gap explicitly.
A nonprovisional schema or length-bounded byte array still requires independent semantic and construction evidence.
Do not promote preserved bytes, recorded field values or tentative declarations into writer defaults.

The [change entry](../../../../Changes/Solidworks/Model/SolidworksArchiveSchemaUsage.md) describes the report contract and verification limits.
See the [schema guide](../../../../../re/tooling/sw2026/serial/README.md),
[wire-value gotcha](../ArchiveWireValues.md)
and [CAD success criteria](../../../../Reference/Operations/CadSuccessCriteria.md).
