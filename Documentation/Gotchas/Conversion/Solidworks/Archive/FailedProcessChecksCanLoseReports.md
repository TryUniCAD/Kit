# Failed process checks can lose their full reports

## Expectation

A process check writes its JSON receipt before failing, so the receipt will be
available in the workflow artifact.

## Actual behavior

The strict curve check on `7228c20e09ca7f6f862b01683316afe06e2809df` wrote its
report and then failed schema admission. The following upload step had no
failure-aware condition and was skipped.
The [job metadata](https://github.com/TryUniCAD/Kit/actions/runs/43787058896/job/133036949541)
records that skipped step; the run's artifact inventory was empty.
The fetched failure-log response was truncated, so its observed schema names
are candidates rather than a complete report inventory.

## Workaround

Keep the process failure intact and give the upload step an explicit status
condition. Upload after actual success or failure of the native-format step,
while excluding cancellation and skipped execution.
Retain complete JSON, stdout, stderr and scope receipts in the existing artifact.
Treat partial reports and unsuccessful schema admission as failed evidence.

The [workflow change](../../../../Changes/Solidworks/Model/SolidworksParserFailureArtifacts.md)
preserves the check commands, action pin and failure gates.
Remote verification of the new retention condition remains pending.
