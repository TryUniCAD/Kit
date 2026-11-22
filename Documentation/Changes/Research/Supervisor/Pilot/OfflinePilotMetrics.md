<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Freeze and replay actual offline pilot evidence

A15a uses the existing controller activity and private evidence reporters.
The new [report command](../../../../../re/automation/PilotMetrics/ReportPilot.py) binds those reports to an actual launch.
It does not start, stop, recover, or refresh the live controller.
Root remains the sole live controller owner.

## Before you start

Use the pilot's pinned Python environment and source checkout.
Retain the original controller store and immutable artifact objects.
The run directory must contain `RunManifest.json`, `Observation.json`, and `Events.jsonl` from the pilot launcher.
Choose a new snapshot directory.
Keep its returned SHA-256 outside the snapshot directory.

## Procedure

Freeze a current observation from the run directory:

```powershell
python re/automation/PilotMetrics/ReportPilot.py freeze --run C:/Pilot/Run --output C:/Pilot/Snapshots/First
```

The returned object identifies the snapshot digest, report digest, controller event cutoff, and observed end time.
The output directory contains these files:

| File               | Retained evidence                                                                      |
| ------------------ | -------------------------------------------------------------------------------------- |
| `RunManifest.json` | Original source revision, configuration pins, input pins, and disabled dispatch policy |
| `Observation.json` | Original launch time, planned end, run identity, and manifest pin                      |
| `Events.jsonl`     | Complete watchdog records before the observed end                                      |
| `JobSnapshot.json` | Read-only transactional queue state at the selected current event cutoff               |
| `Snapshot.json`    | Evidence member digests, reporting source digests, time bound, and event cutoff        |
| `Report.json`      | Deterministic controller, queue, watchdog, and independent evidence report             |

Replay the snapshot with its returned digest:

```powershell
python re/automation/PilotMetrics/ReportPilot.py replay --snapshot C:/Pilot/Snapshots/First --snapshot-sha256 FULL_SNAPSHOT_SHA256
```

Use `--store` to select a relocated copy of the original store.
The reporting source bytes must match the snapshot.
A successful replay reports `byte_identical` and the same report digest.
Later controller and watchdog records do not change the frozen report.

For a historical cutoff, supply `--until-unix` and `--through` to `freeze`.
The end must be within the actual elapsed pilot window.
Historical cutoffs cannot reconstruct mutable queue state.
Such reports retain historical transitions and mark the queue snapshot unavailable.

## Independent evidence

Use the existing [private evidence manifest](../PrivatePilotEvidence.md) for intervention, agent interval, acceptance, and optional CI sources.
Its window must match the activity window exactly.
Pass its path with `--evidence-manifest` and its exact digest with `--evidence-sha256`.
The command copies the original manifest and supplied source files into the snapshot.
It checks their pins through the existing reporter.

An omitted intervention source is unmeasured.
An empty intervention source supplies an operator attestation of zero interventions.
An omitted or empty interval source does not establish active agent time.
Acceptance attestations remain attestations until the independent gate verifies their referenced receipts.
The command claims zero independently verified gains when acceptance evidence is absent.
Job completion never establishes a document gain.

## Measurement boundaries

Throughput uses the actual observed seconds, including idle time.
It distinguishes completed attempt settlements, provisional completions, and completed jobs at the queue observation.
The queue snapshot includes dependent parked jobs with zero attempts.
Historical settlement waits include immutable receipt reasons.
Controller attempt seconds remain separate from measured active agent seconds.

Watchdog summaries count recorded healthy, unhealthy, and unmeasured supervisor heartbeat samples.
They report trailing gaps and maximum gaps between observations.
They also report the maximum gap between healthy supervisor samples, including window boundaries.
Sparse observations do not establish uninterrupted availability.

Elapsed two-week time does not establish pilot acceptance.
The report keeps independent evidence review outstanding.
No result qualifies SOLIDWORKS, Fusion, native writing, or cross-format conversion.

## Verification

The command-boundary scenarios use actual controller subprocesses and disposable stores.
They cover completed work, dependency parking, unchanged ledger bytes, and replay after later activity.
They also cover private-source retention, future-window refusal, disabled-model policy, changed journal evidence, source pin drift, and launch pin mismatch.
The maintained observation report records actual run measurements and final source revisions separately.
These process fixtures do not supply a two-week operating witness.

On 17 November 2026, all six focused scenarios passed in 8.22 seconds on native Windows with CPython 3.14.6.
The pinned Black, Ruff, Prettier, changed-path, and focused rationale checks passed.
The first sandboxed controller submission failed with `PermissionError`.
The same real process boundary passed with normal Windows filesystem permissions.
No model provider or CAD application was invoked.
Local typing tools were unavailable in the retained environment.
Remote current-revision quality checks and merge-group acceptance remain separate requirements.

Run the focused process coverage with the pinned environment:

```powershell
python -m pytest tests/Research/Supervisor/Pilot/Metrics -q
```

## If the task fails

For a changed pin, preserve the failed bundle and inspect the original evidence.
Use the original reporting source and retained store for replay.
For a partial live journal line, freeze another snapshot after the next complete append.
Never relabel missing evidence as measured or restart the live controller from this command.
