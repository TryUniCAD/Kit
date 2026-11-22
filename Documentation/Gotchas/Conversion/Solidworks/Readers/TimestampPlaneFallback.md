# A sampled timestamp can hide the selected sketch plane

## Expectation

The selected native plane reference should determine the sketch attachment.
A strict decode alone should not establish that its placement matches the native model.

## Actual behavior

Five sampled native records carry a timestamp that differs from the legacy sampler's fixed `KSketchPlaneRefTag` bytes.
The typed `PrincipalRef` layout identifies those bytes as `TimeValue`.
The sampler rejects that reference and falls back to the first framed plane, even though the correct top or right frame is present.
The typed rectangular-part reader separately rejects the captured scene-state branch and leaves the fallback model in use.

The recovered corpus records fifteen correct front-plane centroids and 96 incorrect top/right centroids.
All 111 files still return strict neutral documents.
The [source-bound finding](../../../../../re/solidworks/FeatureLadderRecovery/SolidWorksPlacementRootCause.json) records sample hashes, fields and code locations.

## Required follow-up

Qualify owned timestamp-bearing references and the typed scene-state branch from their recorded structure.
Keep malformed ownership, axis and matrix refusals.
Do not remove guards or accept a timestamp pattern as a complete format rule.
Replay all planes and directions and add independent controls before claiming a production placement repair.
