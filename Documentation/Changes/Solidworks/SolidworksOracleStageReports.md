# Preserve each native measurement stage

Clean and instrumented SOLIDWORKS measurements now retain partial results before each native call can fail.
The stage sequence separates open, rebuild, status, bodies, mass properties, feature enumeration, and document close.
Each stage has a start and return marker.
The original failing stage remains in `failure_stage` when later cleanup also runs.

`InspectFresh.py` writes the current measurement record after each stage.
`ExerciseSolidworks.py` retains the same partial record in tracing preparation and marks the active native trace phase.
Stage-marker transport errors remain recorded separately from the original measurement failure.
The existing entry points require no new command options.
`Swapp.measure` accepts an optional progress callback and an explicit read-only open selection for research callers.

Previously, an exception after native open could discard the successful open result.
A missing `opened` field therefore did not identify `OpenDoc6` as the failed call.
The [stage attribution gotcha](../../Gotchas/Conversion/Solidworks/Tracing/MeasurementFailuresNeedStageEvidence.md) describes this evidence limit.
Clean health checks also require a nonempty feature tree and successful feature error-status queries.
Unknown status is not treated as zero errors.

Static Python syntax inspection passed.
The [controlled stage sequence](../../../re/solidworks/measurements/2026/FreshPartStages.json) completed between two healthy original controls.
The candidate returned no document with native open error `4194304` and zero warnings.
No rebuild or later query ran for that candidate.
Both controls completed all fourteen start/return markers and rebuilt one solid with zero errors or warnings.
No local repository tests were run.
