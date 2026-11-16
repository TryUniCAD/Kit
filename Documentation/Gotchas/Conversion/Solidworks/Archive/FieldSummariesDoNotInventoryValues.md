# Field summaries do not inventory every value

## Expectation

The `FieldScan.py --json` output contains every decoded field value and reference needed for corpus correlation.

## Observed behavior

The existing summary keeps only the first six `repr` values in each field group.
It combines repeated list-item paths and labels repeated object references by class alone.
Byte fields report their length without an identifying hash.
The JSON switch changes the display format, not those limits.

Source inspection established these behaviors before the inventory addition.
No native input, schema or tool execution was needed to observe the summary code.

## Workaround

Use the separate `--inventory-json` mode in authorized remote CI.
It records every retained decoded list/dictionary value and explicit graph identities.
Byte fields carry lengths and hashes without raw payloads.
Integer decimal text preserves exact values for consumers with limited numeric precision.

Keep the legacy summary interface for compatible human inspection.
Do not use its six-value prefix to infer a complete count, constant, field domain or identity map.
For linked resolved streams, preserve the configuration seed and its distinct source ownership.
Treat absent, discarded or semantically unclassified data as open work rather than inventing a value.

See the [inventory change and remote process contract](../../../../Changes/Solidworks/Model/SolidworksCurveFieldInventory.md),
[wire-value distinction](../ArchiveWireValues.md),
and [CAD success criteria](../../../../Reference/Operations/CadSuccessCriteria.md).
