# SOLIDWORKS blind-pocket edit measurement

The research observer opens the generated all-bodies pocket, edits its driving depth and saves a separate part. A fresh process reopens the edited file. The observer checks feature ownership, sketch geometry, solid count, volume, area and centre of mass at each rebuild.

Use the pinned candidate from the [native scope comparison](../../../../../../re/solidworks/measurements/2026/GeneratedBlindPocketNative02.json). Provide the authored geometry, feature names, candidate hash and bracketing control in the job. The observer uses the established SOLIDWORKS COM authoring and measurement helpers. All native inputs and outputs stay outside the repository checkout. [Protocol and target geometry](../../../../../../re/solidworks/records/OrdinaryBlindPocketSynthesis2026.md)

The first native trial opened and rebuilt the part, then stopped at the source observer's fixed feature names. The observer now requires the generated part's authored names. Native edit and fresh reopen results are pending. The measurement covers a generated discovery part.
