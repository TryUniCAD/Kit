# Material-folder name changes after native save

## Expectation

A generated part's native feature names remain identical after a successful depth edit, native save and saved-copy reopening.

## Actual behavior

The [controlled polygon measurements](../../../../../re/solidworks/measurements/2026/PolygonCurrent/README.md) record three generated parts on SOLIDWORKS 2026 SP05.2, build `34.5.2.0604`.
Each baseline and edited live tree reports 20 entries, with `authored material` at zero-based index 12 and type `MaterialFolder`.
Each fresh saved-copy reopening still reports 20 entries in the same type order, but that label becomes `Material <not specified>`.
All other reported names remain unchanged.

| Case         | Original and edited live label | Reopened saved-copy label  | Index and type         |
| ------------ | ------------------------------ | -------------------------- | ---------------------- |
| H3_scalene   | `authored material`            | `Material <not specified>` | `12`, `MaterialFolder` |
| H5_irregular | `authored material`            | `Material <not specified>` | `12`, `MaterialFolder` |
| H7_irregular | `authored material`            | `Material <not specified>` | `12`, `MaterialFolder` |

Both controls are healthy.
All nine candidate baseline/edit/reopen snapshots have one body, zero load and feature errors/warnings, successful rebuilds and matching predicted mass properties.
Original candidate files remain unchanged.
The [native edit report](../../../../../re/solidworks/measurements/2026/PolygonCurrent/EditReport.json) preserves every node.
The original report SHA-256 is `136484f02e546679352db915731e99e0947f7b1801034ee982e639f756586f82`.
The [derived analysis](../../../../../re/solidworks/measurements/2026/PolygonCurrent/EditAnalysis.json) retains each difference by case, phase and index.

This is a measured system-folder label normalization.
The observation alone does not identify the native setter, serialization field or save-time cause.
It does not establish a rule for assigned materials, other languages or other document types.

The later [canonical-flag measurements](../../../../../re/solidworks/measurements/2026/PolygonCanonical/README.md)
repeat the same name change on all three flag-corrected outputs.
All 20 feature names remain equal through live editing; fresh reopening changes
only index 12, while all 20 feature types and their order remain equal.
Geometry and depth-edit/save/reopen checks still pass with healthy controls.
Correcting the current-format archive flag therefore does not repair this label difference.

## Workaround

Compare native trees node by node after save and reopen, including names and types.
Keep bounded geometry/edit success separate from full feature-name preservation.
Record this label difference explicitly rather than treating identical body counts or type order as complete tree parity.
Recover and implement the material-folder ownership and naming rule before claiming full preservation.

The [change entry](../../../../Changes/Solidworks/Inspection/SolidworksCurrentPolygonMeasurements.md) links the bounded result and its limits.
