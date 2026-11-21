# Retain native parser evidence after failed process checks

The workflow-quality job now uploads its research output when the native-format
process step finishes with success or failure. This preserves complete parser
JSON and scope receipts when a strict archive check fails.

## Behavior and use

Download the existing `solidworks-construction-<candidate SHA>` artifact from
the workflow-quality run. Curve parser records live under `SourceParser/Curve/`.
Read each report's hashes, byte-identity result, schema-usage result and scope.
Source parsing evidence remains separate from generated candidate files.

Upload does not run for a canceled workflow or a skipped native-format step.
The pinned upload action, artifact name, error on missing files and 14-day
retention remain unchanged. The native process step keeps its original commands
and failure result; retaining evidence never makes a failed check pass.

## Observed failure and verification

The [first strict curve job](https://github.com/TryUniCAD/Kit/actions/runs/43787058896/job/133036949541)
on `7228c20e09ca7f6f862b01683316afe06e2809df` failed its new schema-admission checks.
The following artifact step was skipped and the run exposed zero artifacts.
The failure log response was truncated, preventing a complete schema inventory.
The new condition addresses that evidence-retention gap.

GitHub's [status-check expression reference](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions)
documents the implicit success predicate and the cancellation status function.
The change received source and YAML inspection only.
The [subsequent failed job](https://github.com/TryUniCAD/Kit/actions/runs/43788378770/job/133041020665)
on `1f4c335b85eee2989c754348d6a8dc47eeb69f35` retained artifact `14191736051`.
The native-format step remained failed and the upload step passed.
The artifact contains complete primary and linked reports of 20,890,994 and
14,866,232 bytes. The [admission record](../../../../re/solidworks/measurements/2026/CurveArchiveAdmission01.json)
retains their exact hashes and unsuccessful schema-admission results.
No local tests or native CAD calls ran.

See the [failure-report gotcha](../../../Gotchas/Conversion/Solidworks/Archive/FailedProcessChecksCanLoseReports.md)
and [research serializer guide](../../../../re/tooling/sw2026/serial/README.md).
