<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Independently verify the offline pilot

## Scope and source

The A15a verification agent inspected PR #158 source `9fc3c9a238f3128691e6b6a90e7769fffdb82a65` on 17 November 2026.
The comparison base was `5299eb2ffa5c287c93008bd221df6af2c2f9eb5b`.
The agent used a separate worktree and did not change the live controller or its store.
SOLIDWORKS and Fusion implementation and native sessions remain with their existing owners.

The [automation plan](../../../../Reference/Research/AutomationPlan.md) permits an independent offline pilot.
Models remain disabled, and optional model prerequisites do not apply.
The [step register](../../../../Reference/Research/AutomationSteps.md) keeps A07, A08b, and A14 as A15a dependencies.
Historical process evidence and current PR checks support preparation; they do not establish the operating window.

## Prerequisites and evidence limits

The retained [commissioning evidence](../OfflinePilotCommissioning.md) records two separate Windows batches.
The first processed 26 jobs during a 210.125-second window.
The second records a controlled interruption and recovery during 56.174 seconds.
Neither batch establishes a two-week operating window.
Their elapsed time cannot be added to a new source-bound pilot.

An inference-only registry must contain the reviewed inference entry points and no application installation.
`Runners.Registry` rejects job kinds with the `model.` prefix.
That name check alone does not constrain arbitrary commands registered under another name.
The pilot must therefore retain and verify its exact registry, argument lists, configuration, source files, and input pins.

The [private evidence reporter](../PrivatePilotEvidence.md) verifies source digests and attestation structure.
Independent acceptance requires the underlying baseline and candidate receipts under their applicable gates.
A completed inference job or archive rescan is not an independently verified document gain.
Missing acceptance, agent-activity, and operator-intervention evidence must stay explicitly unmeasured.
An empty intervention attestation requires an actual operator observation of its stated period.

Measure observation continuity separately from controller activity.
A quiet event ledger can mean parked work and cannot establish supervisor uptime.
Retain watchdog observations, process identities, recovery dispositions, and gaps for the full window.
Report unique completed jobs, completed attempts, retries, and zero-attempt dependent waits separately.
Final completion requires the actual two-week window and all required evidence.

The retained private host observation has SHA-256 `f9937161f5b7b040a5a631a4dc638d356638212e4d26294f6b20cf8e53b153e6`.
The verifier independently checked that digest and all 20 recorded package versions against `uv.lock`.
No recorded version differed, and the base interpreter digest agreed with the observed executable.
The recorded AC and DC automatic sleep and hibernate timeouts were zero.
These are observations of the preparation environment, not guarantees against reboot, manual sleep, power loss, or later changes.
No power setting was changed by the verifier.

## Independent setup and recovery verification

The verifier ran the real disposable setup process scenario with CPython 3.14.6:

```powershell
rtk run python -B -m pytest -q tests/Research/Supervisor/Pilot/Setup
```

The scenario passed in 250.23 seconds.
Its retained manifest and smoke result identify tested source `e3bac0f67677b526a2dcc09082d3711dcb2b4cc6`.
The result has SHA-256 `2b975bf3bfa78c0f2437e0a4a96c55bf1fda8b9301cbe3e704bd037a586ebaa6`.
The retained run manifest has SHA-256 `d3b0fdb13a71434cc3d4ce28e52c24da94e9887a9634530e332bea54728a979d`.
The complete disposable store and logs were retained privately as `OfflinePilotIndependentSetupEvidence`.
This rehearsal is separate from the live two-week pilot.

The driver observed a real running inference worker before its first deliberate supervisor interruption.
That job completed on attempt two after recovery.
The verifier independently read the final ledger: 23 jobs completed and three remained waiting for evidence.
The recorded worker birth no longer matched a live worker.
The scenario also exercised an idle supervisor interruption, operator stop and relaunch, fixed-window preservation, and changed-configuration refusal.
Six healthy supervisor heartbeat samples were retained, including the observation beyond the 60-second stale threshold.
The rehearsal journal records four supervisor launches and two operator stops.
The driver deliberately caused two supervisor exits; these actions do not describe live-pilot intervention counts.

Review identified a Windows virtual-environment launcher identity defect before live launch.
The capacity publisher runs in the child interpreter, whose PID differs from the launcher PID.
The corrected check verifies the actual publisher's process birth and membership in the owned Windows Job Object.
It retains both container and publisher identities in the heartbeat.
The scenario verifies this boundary through the actual virtual-environment launcher.

Final setup commit `e3446a9b356d7d9c2933481c98f7fb358e4f9437` contains one formatting change after the tested revision.
The verifier inspected that exact diff: only `OwnerProcess.py` argument wrapping changed.
Python AST comparison found no behavioral syntax difference.
No further full process run was needed for that formatting change.

## Independent reporting verification

The reporting implementation was delivered as `f43d686050dbc9d0785fc5f2c3d6fc8371f17907`.
The verifier independently ran its six process scenarios with CPython 3.14.6:

```powershell
rtk run python -B -m pytest -q tests/Research/Supervisor/Pilot/Metrics
```

All six scenarios passed in 9.43 seconds.
The 18 tested Python files have a content-roster SHA-256 of `ea147b63702d35280bb62b265a4a71b077eec4a3621465fbc94d70624f983a28`.
The commit changed only the verification prose after this run.
The reporter and process-scenario source bytes stayed unchanged.

The scenarios exercise the real controller and reporting command boundaries.
They cover frozen replay after later ledger activity, dependent jobs with zero attempts, and copied private-source evidence.
They also refuse future windows, enabled models, changed reporting-source pins, changed launch evidence, changed journals, and escaping member paths.
The verifier identified a Windows drive-relative path gap during review.
The implementation now rejects rooted paths and enforces resolved containment within the snapshot bundle.

Reports retain healthy, unhealthy, and unmeasured supervisor heartbeat counts.
They measure maximum gaps between observations and between healthy samples, including the requested window boundaries.
These sampled gaps do not prove uninterrupted availability.
The [reporting change](OfflinePilotMetrics.md) describes freeze and replay commands.

## Vendor software audit

The repository filename guard passed for the complete current index and incoming history:

```powershell
rtk run "C:/Program Files/Git/bin/bash.exe" .github/scripts/CheckBinaries.sh . 5299eb2ffa5c287c93008bd221df6af2c2f9eb5b 9fc3c9a238f3128691e6b6a90e7769fffdb82a65
```

The first sandboxed Bash invocation failed during Windows IPC initialization.
The identical read-only command passed with that IPC access permitted.
No index or source change was made for the audit.

A separate content inspection used CPython 3.14.6 and Git object reads.
It combined all current-tree blobs with objects reachable only through the incoming commit range.
Git replacement objects, grafts, inherited Git overrides, global configuration, and lazy fetching were disabled.
The inspection checked executable headers even when file extensions did not identify software.
It inspected nested ZIP, ZIP Zstandard, gzip, bzip2, xz, and tar contents.

| Observation                                     |      Result |
| ----------------------------------------------- | ----------: |
| Current-tree paths                              |      13,248 |
| Current-tree unique blobs                       |      12,861 |
| Combined inspected blobs                        |      12,995 |
| Inspected Git blob bytes                        | 695,636,057 |
| Inspected archives, including nested archives   |       3,706 |
| Inspected archive members                       |      75,910 |
| Executable-header or prohibited-member findings |           0 |
| Archive read errors                             |           0 |
| Size or nesting limits reached                  |           0 |

The sorted Git object roster has SHA-256 `04b6c024ad4518cd2e95ff59fd1f071e5e6673d833748e9529d5d07e3b055d69`.
The content inspection checked PE, ELF, and Mach-O headers.
Archive member checks covered DLL, DMG, EXE, MSI, PDB, SO, DYLIB, LIB, OCX, and SYS extensions without case sensitivity.
It imposed a 512 MiB content limit and eight nested archive levels; neither bound was reached.
No vendor DLL was identified in this inspected source and history.
This bounded inspection does not identify every proprietary source listing or unknown container format.
The [research artifact policy](../../../../Reference/Research/ResearchArtifacts.md) continues to apply.

The final integration source was `5b0608d91f3dcd2e9a73d56207168a50aab54fff`.
The complete index and incoming-history filename guard passed again for this source.
A differential content inspection added every previously uninspected blob from the current tree and incoming history.
It inspected 39 additional blobs, totaling 274,244 bytes, with no executable or prohibited-member finding.
These additional blobs contained no archives, and the inspection reported no errors.
The combined source-and-history object roster has SHA-256 `e33c3cd9287c7cf06c5d20591105b37ffedb9ff3b9df11493d8a3bfc8cb6be17`.
The added object roster has SHA-256 `d2c63d5e09f54bc2f5d04f200ee16053e5ba3d82f8a0970b2e18c6a258f65b15`.
This extends the original content inspection to the integrated setup and reporting implementation.

## Remote evidence boundary

GitHub reported ten successful PR workflow runs for the inspected starting head.
Examples are [path policies](https://github.com/TryUniCAD/Kit/actions/runs/44184982965) and [Python quality](https://github.com/TryUniCAD/Kit/actions/runs/44184982812).
These results apply to the starting head, not later pilot changes.
The workflow named Merge queue on a PR does not establish native merge-group acceptance.
Configured review statuses remained failed at inspection.
No queue enrollment, merge, native CAD execution, model call, or capability promotion was performed by this verifier.
