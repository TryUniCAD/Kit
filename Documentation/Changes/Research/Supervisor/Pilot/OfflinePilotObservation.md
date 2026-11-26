<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Observe the A15a offline operating pilot

## Assignment and revision boundary

A15a owns the two-week unattended offline research pilot on PR #158.
The assignment starts from `9fc3c9a238f3128691e6b6a90e7769fffdb82a65` in isolated worktrees.
Models and native application dispatch remain disabled.
SOLIDWORKS and Fusion implementation and native sessions remain with their current owners.

The [ownership plan](https://github.com/TryUniCAD/Kit/pull/158#issuecomment-6962791556) preceded source edits.
Root owns the live controller, private store, launch, recovery actions, integration, and publication.
Three subagents independently own setup/recovery, metrics/evidence, and verification.
The [documentation refinement](https://github.com/TryUniCAD/Kit/pull/158#issuecomment-6962882203) preserves the supervisor directory limit.

The [step register](../../../../Reference/Research/AutomationSteps.md) remains with its existing integration owner.
The [automation plan](../../../../Reference/Research/AutomationPlan.md) defines A15a measurements and acceptance boundaries.
This note records actual observations without promoting the programme status.

## Prerequisite observations

| Prerequisite                     | Observed result                                                                                                    |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Original discovery inputs        | Both P03 scopes and both P04 gaps resolve through the retained archive readers.                                    |
| Research interpreter             | CPython 3.14.6, NumPy 2.4.6, pywin32, Black 26.10.1, and pytest 9.1.1 import successfully.                         |
| Installed dependency consistency | `uv pip check` reports all 20 installed packages compatible.                                                       |
| Earlier commissioning            | Scheduling and controlled interruption results exist, with separate source revisions and fixed controller cutoffs. |
| Vendor software                  | The independent starting-revision path, incoming-history, signature, and compressed-member audits passed.          |

These observations establish input and environment availability.
All 20 installed distribution versions also match the source `uv.lock`.
No version mismatch was observed.
The host uses High performance, with AC and DC sleep-after and hibernate-after values set to zero.
No power setting changed.
They do not qualify native routes or independently accepted document gains.
The [independent verification note](OfflinePilotVerification.md) records the audit scope and limits.

The operator retains the private `HostEnvironment.json` prerequisite record on the pilot host.
Its SHA-256 is `f9937161f5b7b040a5a631a4dc638d356638212e4d26294f6b20cf8e53b153e6`.
It retains interpreter identity, installed versions, the observed power policy, and host uptime.
The watchdog recovers supervisor exits while its owner runs.
Host reboot or logoff can interrupt that owner; gaps require recorded recovery and remain visible in sampled coverage.

## Historical evidence boundary

The [commissioning note](../OfflinePilotCommissioning.md) records 210.125 seconds of scheduling and 56.174 seconds of controlled recovery.
Neither duration establishes a two-week operating window.
The earlier 16 November observation checkpoints use source `1303a7543c95e37f2e7858aa607a16203d72c50e`.
Their private stores, source bindings, and controller owners remain preserved.
Their elapsed time does not contribute to this new current-head run.

A15a remains active while its actual observation window or required independent evidence is outstanding.
Controller completions measure research throughput.
Independently verified capability gains require separate acceptance evidence for the same document and route.
Missing intervention, agent-time, or acceptance evidence remains unmeasured.

## Actual live run

The live run ID is `a15a-b0387957524a4107a6f27b45ee2bd5a4`.
Its frozen source is published revision `5b0608d91f3dcd2e9a73d56207168a50aab54fff`.
The persisted start is 17 November 2026 at `22:56:28.503668 UTC`.
The fixed deadline is 1 December 2026 at `22:56:28.503668 UTC`.
The manifest SHA-256 is `16a9cf878f59b178f110f22d036965738657e9e65bb9568a636c6a2a2b7b20ae`.
The [live-start coordination record](https://github.com/TryUniCAD/Kit/pull/158#issuecomment-6963435313) identifies this same run and scope.

The registry contains only `inference.fields`, `inference.paired-gap`, and `inference.rescan`.
It permits one inference session and reserves two logical CPUs and 4 GiB of memory.
Model calls and native application dispatch remain disabled.
All 26 P03/P04 discovery jobs were submitted to a fresh store.
P05 remains reserved.

Root observed the actual supervisor publisher inside its owned Windows Job Object.
The virtual-environment launcher and actual publisher have different process identities.
The startup heartbeat preceded capacity publication; later heartbeat observations were healthy.
No restart was required in these initial observations.

## Reproducible initial operating report

The settled-queue checkpoint ends at Unix time `1794956348.7643335`, after 160.26066517829895 seconds of actual observation.
It selects controller events through ID `163`, with `after_event_id` set to `0`.
The selected event digest is `948c399014e2cb1adfaf753c784bff4a872bf2c456fe740a220b78e53eb67356`.
Its report SHA-256 is `59e7c1df55937bc85327e9f38fe97896e1829a8a545597080c5fbe3838bb2e20`.
Its snapshot SHA-256 is `c0d82e9d3431dd61a028d81b202c5318580ee5819f8c2e48c17294784a96c32e`.
The operator retains the complete private bundle as `Settled`, with the original store and frozen reporting source.

| Measurement                                      | Actual checkpoint result                                           |
| ------------------------------------------------ | ------------------------------------------------------------------ |
| Completed jobs and completed attempt settlements | 23; none provisional                                               |
| Claims                                           | 24                                                                 |
| Parked jobs                                      | 3                                                                  |
| Queued, running, failed, or rejected jobs        | 0                                                                  |
| Completed attempts per observed hour             | 516.6582823544403                                                  |
| Closed controller attempt wall time              | 124.64545130729675 seconds                                         |
| Recorded live retries or expired claims          | 0                                                                  |
| Live supervisor launches and restarts            | 1 launch; 0 restarts                                               |
| Healthy supervisor samples                       | 5                                                                  |
| Startup sample before capacity publication       | 1 unhealthy sample                                                 |
| Maximum healthy-sample gap, including boundaries | 32.27200174331665 seconds                                          |
| Operator-intervention attestation                | Unmeasured; no stop or recovery event in the retained live journal |
| Independently measured agent activity            | Unmeasured                                                         |
| Independently verified capability gains          | 0 claimed; independent acceptance evidence unmeasured              |

The parked assessment needs the pinned distinguishing application grid.
Its receipt SHA-256 is `2603a1a932ac7f3e96c069c2d6199ab54307a2eeaa17d83cc55bc19c7eaf2631`.
Both dependent rescans remain parked with zero attempts.
The pilot does not claim their missing evidence or dispatch native applications to obtain it.

The rate describes this short initial observation, not sustained two-week throughput or a forecast.
Later idle time belongs in subsequent denominators.
The watchdog continues observing the parked queue until its fixed deadline.
Actual active and idle recovery were verified in separate disposable rehearsals; no such recovery was needed in this live checkpoint.

The earlier `Initial` checkpoint covered 118.95551204681396 seconds and selected events through ID `160`.
It recorded 21 completed jobs, one queued job, one running job, and three parked jobs.
Its snapshot SHA-256 is `e4f57bdc6bb7e82948744a69dc2a777d699e81ef0ab8a188a6236644666605b5`.
Its report SHA-256 is `040a7df450e8fe30d727a592cad6f943beeb33b80af4fdc72411f958483c65e3`.
Both checkpoints replayed byte-for-byte against the store at the later cutoff.

Use the [task procedure](../../../../Tasks/Research/OfflinePilot.md) with the original frozen source and private bundle.
Supply the bundle's snapshot digest to the replay command.
Retain later observations as new bundles, without replacing these reports.
The full operating window, independent evidence review, and final report remain outstanding.

## Verification and publication

Metrics and setup were published in two substantial commits, preserving the concurrent native-owner source.
The combined metrics process suite passed all six cases in 15.64 seconds on the integrated source.
The 33 changed destinations passed path policy, and the committed code diff passed whitespace checks.
Independent setup and reporting evidence is recorded in the [verification note](OfflinePilotVerification.md).
The vendor audit covers the complete starting tree and incoming history, plus all added integration blobs.
It identified no vendor DLL or executable payload within its documented inspection bounds.

On the frozen source, [CI Agg](https://github.com/TryUniCAD/Kit/actions/runs/44194379047/job/134431801129) and [path policies](https://github.com/TryUniCAD/Kit/actions/runs/44194382871/job/134431999550) passed.
Ruff, Black, rationale, explicit-import, workflow-pin, and workflow-quality checks also passed.
Typing, full-suite, platform, and heavy security checks remain governed by the merge-group phase.
The separate managed code-quality Python analysis was still running at this observation.
Existing configured review failures and native merge-group acceptance remain separate requirements.
No review approval, queue enrollment, merge, or native capability qualification is inferred.

Automatic approval review rejected a proposed public comment containing private host paths and authentication metadata.
The successful coordination comment omitted that metadata.
It also rejected the repository's instructed `--no-verify` push flag.
The accepted push used hooks enabled.
