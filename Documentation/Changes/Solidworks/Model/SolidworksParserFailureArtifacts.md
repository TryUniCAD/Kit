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
Remote verification of failed-run artifact retention remains pending.
No local tests or native CAD calls ran.

See the [failure-report gotcha](../../../Gotchas/Conversion/Solidworks/Archive/FailedProcessChecksCanLoseReports.md)
and [research serializer guide](../../../../re/tooling/sw2026/serial/README.md).
