# Trace the continuation after origin solving

The full native observation profile now records three additional function entry and return boundaries.
They cover model finalization, modified-state propagation, and body collection.
Each event retains the object pointer, raw argument words, caller, and raw return register.
Raw register values do not establish semantic results.

The previous controlled trace showed a successful origin solve before the generated candidate crashed.
The [selected control and candidate evidence](../../../re/solidworks/v2026/evidence/TupniOriginSolved.json) retains the observations and source identities.
The final observed return continues into model modified-state propagation, followed by body collection.
The new boundaries follow that actual continuation.
They do not infer an error from the absence of an ordinary-sketch solve.

The selected addresses belong to the locked 2026 `sldmodu.dll` image.
Its SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The retained observation runner verifies module hashes before arming hooks.
Use its existing `full` profile with a healthy native control before the generated candidate.
The [controlled observation](../../../re/solidworks/v2026/evidence/TupniFinalizationReturned.json) showed that modified-state propagation and model finalization returned in the candidate.
All 25 observed body-collection calls also returned.
The process still terminated before native open completed.
The paired training control remained healthy with zero capture drops or script errors.
These observations move the next question past finalization.
They do not establish a body count from a raw return register.
This instrumentation does not enable the production writer or establish native output acceptance.
