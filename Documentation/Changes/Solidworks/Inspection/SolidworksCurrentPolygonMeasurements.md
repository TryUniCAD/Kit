# Publish current polygon geometry, views and editable-depth measurements

Full CAD acceptance remains unfinished.
Three generated polygon parts now have completed controlled geometry, canonical-view and depth-edit/save/reopen measurements at their recorded source revision.
The [measurement bundle](../../../../re/solidworks/measurements/2026/PolygonCurrent/README.md) contains original report fingerprints, redacted native results, neutral inputs, standalone quantitative analysis and ten unchanged PNGs.
The production SOLIDWORKS adapter remains read-only.

## Evidence and usage

The measured generator and inspectors are source `b23e72c609caca0d0ca4acf871e9680a325f0548`.
The oracle owner independently verified full byte equality between the three measured candidate files and the corresponding files in artifact `14180956560` from head `033b97679263fe31d7c4fb46899470be6c2923c5`.
The [artifact record](../../../../re/solidworks/measurements/2026/PolygonCurrent/ArtifactIdentity.json) binds that narrow equivalence to GitHub metadata, verified synthetic parents and tree.
No other output or later revision inherits these measurements.

The fresh heptagon repeat passes with healthy controls before and after.
The visible five-row batch opens and rebuilds three candidates plus two controls with one body each, zero load or feature errors/warnings and unchanged inputs.
All 90 standard rotation arrays are finite length-nine arrays.
All nine named views match both controls before and after selection, with maximum coefficient discrepancy `7.888609052210118e-31` against tolerance `1e-12`.
The oracle owner inspected all ten PNGs: all three selected isometric views show extrusion depth and side faces.
Initial active-camera parity remains unestablished.

The separate depth batch uses 11 distinct native process lifetimes, including two healthy controls.
All three candidates pass baseline, depth multiplication by `1.25`, rebuild, clean save and fresh saved-copy reopening.
Body counts remain one, volume changes by `1.25`, and volume, surface area and center of mass match both independent expected metrics and neutral polygon derivations.
Original candidate hashes remain unchanged.

Read the [view analysis](../../../../re/solidworks/measurements/2026/PolygonCurrent/Analysis.json), [fresh geometry analysis](../../../../re/solidworks/measurements/2026/PolygonCurrent/GeometryAnalysis.json) and [edit analysis](../../../../re/solidworks/measurements/2026/PolygonCurrent/EditAnalysis.json) together.
The bundle README gives the standalone reanalysis commands.
Those commands read measurements and neutral inputs; they do not drive CAD or run tests.

## Limits and verification

Feature type order and the count of 20 reported entries survive editing and reopening.
The material-folder label changes on saved-copy reopening in all three cases: `authored material` becomes `Material <not specified>` at index 12.
All other reported names remain unchanged.
The [specific gotcha](../../../Gotchas/Conversion/Solidworks/Model/MaterialFolderNameChangesOnSave.md) records the observation.
Full feature-name preservation is not established.

The [earlier interruption](SolidworksControlledPolygonInterruption.md) remains historical evidence with no attributed format crash.
The controlled repeats do not reproduce its disconnect and do not identify its cause.
Depth edits do not prove sketch-dimension edits, broader feature families, assembly writing or full source conversion.
The full CAD goal and curve-family acceptance remain unfinished.

Original native report hashes, tool hashes, process creation identities, every private-path replacement and image conversion hashes are retained.
Published PNG bytes match the oracle owner's staged PNGs.
Original BMPs remain external; decoded-pixel equality was not independently measured.
The publication used JSON/hash/link inspection, standalone measurement arithmetic, syntax and formatting checks.
No local product tests, native source-stream inspection or oracle access occurred in the publication agent.

Repository CI on source `033b97679263fe31d7c4fb46899470be6c2923c5` completed successfully.
The [large-diff gotcha](../../../Gotchas/Ci/Audits/LargePullRequestDiffLimit.md)
records successful analysis jobs whose pull-request diff retrieval was incomplete.
Their results do not prove exhaustive per-file coverage or full CAD acceptance.
Configured review reports failed, and an actual current-head approval is absent.
Those gates remain separate from repository CI.
