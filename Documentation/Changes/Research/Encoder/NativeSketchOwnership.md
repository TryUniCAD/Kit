# Saved SOLIDWORKS sketch ownership in comparison

## Behavior

A detailed comparison report can identify an existing native feature as the owner of its typed SOLIDWORKS sketch.
The feature must declare one unique sketch and have matching native identity, adapter, and nonempty source span.
The observation includes the ordered constraints and the references reported for each constraint.
The original native feature and its unresolved records remain in the report.

## Usage

Run the existing [decoded document comparison](../../../Tasks/CompareDecodedDocuments.md) over the neutral JSON.
Find the `reader_reported_native_sketch_owner` classification under the source side's `observations`.
Use its feature and sketch IDs to locate the inputs and dependent features in the same report.
Use the [saved sketch span gotcha](../../../Gotchas/Research/Readers/SolidWorksSketchEvidenceStartsInsideEntry.md) to interpret the cited byte range.

## Evidence and limits

Eight pinned P01 and P03 SOLIDWORKS discovery variants show matching native identity and nonempty source spans for the owner and sketch.
The separate Origin feature lacks that binding. The P03 Boss retains its own dependency on the profile owner.
The [principal-readback verifier](../../../../re/automation/PrincipalReadbackEvidence.py) checks the saved profile against the separately collected source inventory.

The installed comparison command processed the same strict P03 SOLIDWORKS and Fusion JSON before and after the change.
It reported `different` and exit 3 in both runs. The comparison and both source issue inventories matched exactly.
The new source observation reported 11 ordered constraints and the 6,437-byte common span at byte 5,578.
All 191 SOLIDWORKS issues remained, including 25 native-only records.
Two focused process cases changed the sketch's reported native identity or source span in a copy of the JSON.
The source span case kept the original native identity. Both mismatches preserved the same issue inventory and withheld the ownership observation.
The [process cases](../../../../tests/Research/Archives/Comparison/NativeSketchOwnership/NativeSketchOwnerTests.py) passed locally in 15.95 seconds on Python 3.14.6.

The detailed comparison reports reader evidence. It leaves independent qualification, native acceptance, and the production writer guard in place.
