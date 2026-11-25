# Compare native boss discovery records without admitting conversion

## Behavior

The [comparison command](../../../../re/solidworks/NativeBossProof/CompareSource.py) binds a native source to its exact recorded authoring definition and SDK JSON.
It can invoke the existing deterministic research command in a fresh process or inspect an immutable capture.
It also accepts an explicitly selected trusted SDK's external JSON snapshot.

The command records every typed collection, native type, retained-span digest and relevant ownership link.
It preserves the distinction between kernel topology and the public body summary.
It compares API metre depths with the typed driver and extrusion length.
An optional second JSON document receives an exact comparison with no ignored fields or inferred identity mapping.
The command does not project a writer request or change the SDK.

## Usage

Supply a source, its successful native authoring record and an unused research output directory.
The definition must bind the exact source digest.

```powershell
python re/solidworks/NativeBossProof/CompareSource.py --root . --source /absolute/Prism.SLDPRT --definition /absolute/Author/Record.json --definition-case NoOpBefore --run-directory .rescratch/FreshNativeBoss --output .rescratch/FreshNativeBossEvidence.json
```

Use `--capture` for an existing capture or `--document` for an external SDK snapshot.
Use `--compare-document` to include another complete typed JSON document.
Source and settled capture hashes are checked before evidence publication.
An existing evidence output refuses replacement.

## Verification and limits

The [findings](../../../../re/solidworks/NativeBossProof/Findings.md) bind nine c4 discovery captures to their independent authoring records.
All nine decode to JSON but refuse preparation before encoder entry.
A fresh child records incomplete exit `3`, with the capture unchanged.
The source identity is `c4e8a34186bdd173dad37d843b79bc8a3a59ebb9`.
Python 3.14.6 and zlib-ng were used.

The evidence retains 26 SDK rows, 19 API top-level rows, opaque closing geometry, unsupported properties and incomplete body ownership.
Recursive API observations retain occurrence counts, distinct IDs and parent relationships separately.
Five discovery controls also expose rounded driving-depth values on this c4 reader.
The [tree-view gotcha](../../../Gotchas/Research/Readers/NativeBossTreeCountsNeedOwnership.md) and [precision gotcha](../../../Gotchas/Research/Readers/NativeBossDepthPrecision.md) describe these boundaries.

The fresh nested process initially encountered a Windows staging-rename denial in the managed execution context.
A scoped approved run into another unused directory completed.
The [execution observation](../../../Gotchas/Research/Workers/Windows/NestedResearchStageRename.md) records this limit without attributing an unproved cause.

No CAD application was launched, no native measurement was added and no source fixture was copied into the SDK.
No new test roster entry duplicates the existing c4 refusals.
Admission, independent heldout validation and complete native acceptance remain unfinished.
