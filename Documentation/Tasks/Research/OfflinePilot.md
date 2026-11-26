<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Run the unattended offline research pilot

## Purpose

Use this procedure to run A15a with models and native application dispatch disabled.
It measures the actual two-week operating window and retains reproducible evidence.
The pilot uses the existing controller, inference runner, and supervisor.
It does not qualify native conversion routes.

## Before you start

Read the [automation plan](../../Reference/Research/AutomationPlan.md) and [commissioning evidence](../../Changes/Research/Supervisor/OfflinePilotCommissioning.md).
Read the [step register](../../Reference/Research/AutomationSteps.md) for current prerequisites and acceptance gaps.
Assign one owner for the live controller and store.
Coordinate source and evidence ownership in the PR conversation before edits.

Use a clean, isolated checkout at the exact committed source revision.
Keep that checkout unchanged throughout the run.
Keep later documentation and concurrent integration work in another worktree.
Use an unused evidence directory outside the frozen source checkout.
Preserve any existing controller stores and their owners.

Windows requires CPython 3.14 and the locked pywin32 dependency.
The research environment also requires NumPy and the retained historical capture Git objects.
Verify installed dependency consistency with `uv pip check --python` and the selected interpreter path.
Use task-owned uv caches when the default cache is unavailable.

The commands below use example Windows paths.
Replace them together with the selected host paths.
The interpreter and historical inputs must satisfy the preparation checks.

## Prepare the run

1. Select the frozen checkout and private evidence directory.

   ```powershell
   $PilotSource = 'C:\Research\KitOfflineRun'
   $PilotState = 'C:\Research\OfflinePilotObservation'
   $PilotPython = 'C:\Research\PythonEnvironment\Scripts\python.exe'
   Set-Location -LiteralPath $PilotSource
   ```

2. Read the exact frozen revision.

   ```powershell
   $PilotRevision = rtk git rev-parse HEAD
   rtk git status --short
   ```

3. Prepare the unused directory without starting the live supervisor.

   ```powershell
   rtk run $PilotPython re/automation/Pilot/PreparePilot.py `
     --directory $PilotState --source-revision $PilotRevision --sessions 1
   ```

Expected result: preparation reports `prepared_not_started` and 26 planned jobs.
`RunManifest.json` pins the source revision, runtime, configuration, registry, schema, schedule, and input files.
Both model and application enablement flags are false.
P03 and P04 remain discovery inputs.
P05 remains reserved.
Preparation time does not count toward the operating window.

## Start and observe the pilot

The assigned controller owner performs this step once.
Keep the host available for the observation window.
Record sleep, reboot, shutdown, and recovery gaps instead of treating them as continuous supervision.

```powershell
Start-Process -FilePath $PilotPython -WindowStyle Hidden `
  -WorkingDirectory $PilotSource `
  -ArgumentList @('re/automation/Pilot/RunPilot.py', '--directory', $PilotState) `
  -RedirectStandardOutput (Join-Path $PilotState 'Owner.stdout.log') `
  -RedirectStandardError (Join-Path $PilotState 'Owner.stderr.log') `
  -PassThru
```

`Observation.json` records the actual start time and the fixed end 1,209,600 seconds later.
`Events.jsonl` records heartbeat and recovery observations.
Keep launcher and supervisor process identities distinct.
The Windows virtual-environment launcher can have a separate process identifier.

The watchdog retains one inference session with this configuration.
It restarts a failed supervisor within its persistent retry limit.
The window remains unchanged when the owner restarts.
Exhausted retries open the recovery circuit and require an intervention record.
Parked jobs remain parked until their declared evidence changes.
Do not resubmit equivalent work to inflate throughput.

## Report the observed window

Use the [pilot metrics procedure](../../Changes/Research/Supervisor/Pilot/OfflinePilotMetrics.md) to freeze and replay an observed cutoff.
Retain the report, manifest, journal prefix, controller event cutoff, and independent evidence pins together.
Repeat the frozen report and compare its bytes.
Later controller activity must not change that report.

```powershell
$PilotSnapshot = Join-Path $PilotState 'Snapshots\Initial'
rtk run $PilotPython re/automation/PilotMetrics/ReportPilot.py freeze `
  --run $PilotState --output $PilotSnapshot
$PilotSnapshotHash = (Get-FileHash -LiteralPath `
  (Join-Path $PilotSnapshot 'Snapshot.json') -Algorithm SHA256).Hash.ToLowerInvariant()
rtk run $PilotPython re/automation/PilotMetrics/ReportPilot.py replay `
  --snapshot $PilotSnapshot --snapshot-sha256 $PilotSnapshotHash
```

Choose a new snapshot directory for each observation.
The freeze command refuses an existing output directory.
Retain the frozen reporting checkout because replay also verifies reporter source bytes.

Report elapsed time, active attempt time, throughput, recovery, parked jobs, interventions, and independently verified gains separately.
Missing agent-time and independent acceptance evidence remains unmeasured.
Completed discovery and rescan jobs do not establish new accepted documents.
Use the actual observed cutoff while the two-week window remains open.

## If the task fails

| Symptom                                     | Action and stop condition                                                                                                      |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Preparation refuses an input or runtime pin | Preserve the refusal. Resolve the prerequisite before starting a new run.                                                      |
| Another controller owner holds the store    | Leave that owner and store unchanged. Use the assigned unused directory.                                                       |
| Supervisor exits                            | Inspect the retained recovery journal and owned process identities. Let bounded automatic recovery act first.                  |
| Watchdog exits or the host restarts         | Preserve logs and the observation manifest. The assigned owner reruns the same `RunPilot.py` command after checking ownership. |
| Recovery circuit opens                      | Record the cause and operator action. Preserve the original window and all failed attempts.                                    |
| Source or configuration pin changes         | Stop the affected run. Preserve evidence and report the changed prerequisite.                                                  |
| Work waits for native evidence              | Keep the job parked. Coordinate with its existing native owner.                                                                |

To request an intentional stop, create `Stop.request` in the private evidence directory.
Record the action and its reason as an operator intervention.
Stopping early leaves A15a incomplete.
Never terminate an unrelated process or modify another owner's store.

## Related information

- [Actual A15a observations](../../Changes/Research/Supervisor/Pilot/OfflinePilotObservation.md)
- [Independent verification](../../Changes/Research/Supervisor/Pilot/OfflinePilotVerification.md)
- [Supervisor configuration and recovery](../../Reference/Research/ResearchSupervisor.md)
- [Pinned private evidence sources](../../Changes/Research/Supervisor/PrivatePilotEvidence.md)
- [Readiness-to-acceptance timing](../../Changes/Research/Supervisor/PilotAcceptanceTiming.md)
