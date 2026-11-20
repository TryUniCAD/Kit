# Locked SOLIDWORKS through-all cut evaluation

The [research evaluator](../../../../../re/solidworks/records/SdkLockedThroughAllEvaluation2026.md)
freezes the SDK, an independently authored rectangular stock and free
circle intent, and the selected-stock comparator. The current native
construction emits the actual cut and its selected stock object. It
edits the stock depth and checks that the cut remains through the body
without acquiring a cut-depth driver.

Pass `--revision` with an exact SDK commit when freezing a later
candidate. Each packet pins its source tree, observer and epoch.

Disclosed guarded builds matched across ten streams. Disclosed native
records also passed the comparison for the full tree and owned driver.
The first locked candidate passed native edit, save and reopen with
two healthy controls in SOLIDWORKS 2026 SP05.2. Its secondary stock
depth differed from the source. The repaired SDK matches the second
pre-writer locked source in all six scoped observations. Both controls
passed, and the native-saved candidate retains the actual selected
stock in the strict reader. Continuous automatic scope, complete
original-source transfer and public writer admission remain open.
[H01 native comparison](../../../../../re/solidworks/measurements/2026/SdkLockedThroughAllNativeComparison01.json)
· [H02 scoped comparison](../../../../../re/solidworks/measurements/2026/SdkLockedThroughAllScopedParity01.json)
