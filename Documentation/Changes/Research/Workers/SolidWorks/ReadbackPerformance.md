<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Reduce SOLIDWORKS readback overhead

## Behavior

The collector runs the initial healthy control with the normal startup settings.
It then enables `ISldWorks.CommandInProgress` for the capture and final control sequence.
The collector records the previous value and restores that value during cleanup.
Restoration failure marks the observation as failed and still permits the owned process exit attempt.

The measurements retain `readback_options` and the existing visibility observations at document close.
These records identify the applied settings.
The source-bound progress journal retains the configuration, restoration, control, rebuild, and process-exit stages.
The visibility override remains at the final control. Applying it earlier repeatedly stalled native shutdown on the measured build.
[Early visibility and shutdown findings](../../../../Gotchas/Research/Workers/SolidWorks/EarlyPartVisibilityShutdown.md)

## Optional combined discovery batch

Use `p01-p03-p04-readback` to observe the fixed P01, P03, and P04 discovery rosters in one owned process.
This operation observes six P01 files, eight P03 files, and eleven P04 files.
It retains one healthy control before the complete roster and another afterward.
Every file still receives independent before-rebuild and after-rebuild observations.
The collector closes each scratch document and verifies that the session is empty before opening the next file.

The plan uses recipe `P01-P03-P04`.
The receipt requires `observed_files` and `discovery_files_observed` to equal `25`.
All eleven P04 observations must retain verified supporting-face evidence.
The combined batch excludes P02 and the reserved P05 holdouts.
Use the [readback batch queue](QueuedReadbackBatches.md) to collect requests and release them together.

Start the listener with the explicit operation:

```powershell
python re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py --installation <installation.json> --readback-operation p01-p03-p04-readback listen --interop <SolidWorks.Interop.sldworks.dll>
```

Configure the same operation before `dispatch` in the registered runner:

```text
python re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py --installation <installation.json> --readback-operation p01-p03-p04-readback dispatch {session}
```

Use empty job inputs and these exact option keys:

```json
{
  "source_revision": "REVIEWED_PR_HEAD",
  "readback_operation": "p01-p03-p04-readback"
}
```

Replace `REVIEWED_PR_HEAD` with the accepted forty-character source SHA.
Use that same SHA in the installation configuration.
Retain the existing single-session runner and capacity-one application resource.
The selected operation and source revision bind the queued request and job fingerprint.
Callers cannot select additional native inputs.
The five-minute dispatch cap remains unchanged.
After verifying the source and scratch files against their pins, a successful queued combined run removes its temporary part copies to fit the existing spool limit.
The plan, measurements, progress journal and receipts remain available. Failed runs retain their files for diagnosis.

## Evidence and limits

The existing P04, P01/P03, and P02 operations remain available with their fixed rosters.
Use separate fresh-process operations when independent startup, exit, or restart evidence is required.
A combined run does not establish two independent native process observations.

The combined artifacts do not replace the separate inputs required by `StageEleven.py`.
Use the existing P01/P03 and P04 operations for that paired discovery replay.
The combined operation supplies routine supplemental observations and batch timing evidence.

Completion remains an unqualified application observation with `native_qualified` set to `false`.
Fresh native Fusion acceptance, broad feature qualification, and lossless conversion remain separate requirements.

## Private native comparison

The original collector and the edited collector each ran the same 25-file roster in the same serial order on SOLIDWORKS 34.4.1.1011.
Both runs used a fresh owned process, passed the two stock controls, retained all eleven cut-support checks and observed normal exit.
The edited run verified that the previous command state was restored.
The stock controls reported one solid and the expected volume in each run.

| Measurement           | Original | Command batching |
| --------------------- | -------: | ---------------: |
| Collector wall time   |  85.20 s |          73.08 s |
| Median capture        |  2.038 s |          1.876 s |
| Initial stock control |  10.64 s |          10.95 s |

These are single serial runs through the collector with the original fixtures and separately hashed local source.
The comparison does not measure queued settlement time or establish repeatability.
Committed-source native queue verification remains pending.

The retained original measurement digest is `eb3944e58972a8a9eebdb67647783b8ca20385121e037af93b7ff25877413f39`.
The command batching measurement digest is `0b0bf286df02803634b5f369af53e983eac1b60f0fd053613d84d92c6d0ef757`.

## Related information

- [Queued SOLIDWORKS readback](../SolidWorksQueuedReadback.md)
- [Native testing procedure](../../../../Tasks/Research/AutomationNativeTesting.md)
- [Paired discovery replay](../../Controller/PairedDiscoveryReplay.md)
- [Owned native process](OwnedReadback.md)
