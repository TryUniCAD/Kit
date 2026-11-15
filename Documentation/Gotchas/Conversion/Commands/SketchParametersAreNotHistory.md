# Parameters do not supply sketch feature history

SDK document validation accepts a parameter-bearing document with sketches and
an empty feature timeline. JSON serialization preserves it but does not establish
an editable sketch history. A timeline referencing another sketch leaves the
unreferenced sketch equally unqualified.

The CLI requires a reference feature for each sketch before conversion. Keep
incomplete records available through `kit decode` while recovering their history.
Parameter-only documents with no sketches and complete reference histories remain
supported. See [the change entry](../../../Changes/Commands/SketchHistoryGuard.md).
