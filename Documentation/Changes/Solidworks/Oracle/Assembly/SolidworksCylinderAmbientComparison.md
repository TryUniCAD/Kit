# Generated cylinder authored-ambient comparison

PR #121 adds a bounded source-only cylinder ambient comparison and its read-only native diagnostic. It reuses the existing actual PartCandidate, output atom and ambient constructor, preserves the default writer bytes, and changes only the five independently classified lighting/bookkeeping streams at one common file locator.

Use [the construction and diagnostic record](../../../../../re/solidworks/records/ConcentricCylinderAmbient2026.md), [generator](../../../../../re/tooling/sw2026/PrepareConcentricAmbient01.py) and [observer](../../../../../re/tooling/sw2026/InspectConcentricAmbient01.py). Run each tool with `--help`; the frozen external recipe binds exact source, input, predicted geometry, artifact and observer hashes. Commit the source before root's exclusive native execution.

The [host proof](../../../../../re/solidworks/measurements/2026/ConcentricAmbientHost01.json) records exact reproduction of the old parent/child and two separate guarded same-locator build processes. Both ambient variants retain identical geometry owners, flags, partition and all unchanged streams. Host verification, static syntax and undefined-name checks pass. The first pre-CAD metric-container mismatch is preserved separately from its observer-only correction.

No native run, save/reopen, parent mate/name acceptance, hidden-input access or public writer support is added by this tranche. The native job reports warning effect as a diagnostic and keeps target-application acceptance false.

The same-locator native comparison passed all four controlled phases. Empty environment opens with warning 32. A generated ambient light clears that warning and the first-open save flag while retaining the exact cylinder and both dimensions. The standalone test ends after rebuild. [Native result](../../../../../re/solidworks/measurements/2026/ConcentricAmbientNative01.json)
