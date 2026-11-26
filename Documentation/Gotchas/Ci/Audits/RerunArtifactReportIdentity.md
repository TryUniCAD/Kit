# Rerun artifacts can retain an earlier test summary

## Expectation

After a successful shard retry, the combined report appears to describe the latest accepted attempt.

## Actual behavior

The [decoding audit](https://github.com/TryUniCAD/Kit/actions/runs/44931832555) retained two artifacts named `TestReport-1`.
Artifact `14718695179` contains the initial calibration failure.
Artifact `14718629152` belongs to the successful retry.
The [retry job](https://github.com/TryUniCAD/Kit/actions/runs/44931832555/job/136935973155) reports 1,124 passes and 59 skips.
The [combined report](https://github.com/TryUniCAD/Kit/actions/runs/44931832555/job/136937834905) still prints one failure, 6,739 passes, and 358 skips.
All current workflow jobs report success.

The workflow downloads artifacts by the `TestReport-*` pattern.
Artifact names alone do not identify a test attempt.
This observation does not establish a general artifact selection order.

## Workaround

Record the workflow attempt, job ID, and artifact ID together.
Use the successful retry's own log and artifact when reporting that shard's result.
Preserve the failed attempt as separate evidence.
Inspect current job conclusions separately from the combined report's counts.
Do not claim that a successful retry erased the original failure.

See the [bounded decoding audit](../../../Changes/Research/Solidworks/BlindBossDecodeAudit.md) for the measured feature scope and its acceptance limits.
