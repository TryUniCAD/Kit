# Record an incomplete polygon measurement batch

The controlled viewport batch for source `b23e72c609caca0d0ca4acf871e9680a325f0548` is incomplete.
It does not establish generated-output acceptance.
The [measurement record](../../../../re/solidworks/measurements/2026/PolygonCurrentInterruption.json)
retains the native results, raw hashes, cleanup identity and subsequent refused retry.

The original control, triangle and pentagon opened with zero errors and warnings and returned one body.
The heptagon opened and returned rebuild success, then its COM connection was lost during grouped body, mass and feature extraction.
The recorded boundary does not identify which grouped call failed.
The process remained after graceful cleanup, preventing the trailing control from launching.
The exact owned process was subsequently terminated through its verified creation identity.

A fresh three-row retry refused before activation because a different preexisting session was present.
That retry measured no control or candidate.
The origin of the new session remains unverified.
The heptagon observation is not counted as a format crash because no passing trailing control brackets it.

Read this record separately from the successful earlier canonical-view batch.
Later configuration and profile changes still require valid native measurements, dimension edits and saved-copy reopening.
The production adapter remains read-only.
