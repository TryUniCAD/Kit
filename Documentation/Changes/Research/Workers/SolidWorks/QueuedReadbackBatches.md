<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Queue routine SOLIDWORKS discovery checks

Use the existing [combined discovery runner](ReadbackPerformance.md) with one capacity-one application resource. Run the listener and supervisor against the same installation and A03 store. Start the supervisor without an idle timeout when it should wait for future batches.

Record each request with a stable check ID. Use `principal` for P01/P03, `cut` for P04, and `discovery` for both. The queue targets the existing fixed 25-file roster and provides each request with the same job ID and evidence. Repeating a check ID with the same scope returns its existing assignment. Use a new check ID for a later run.

With `$StorePath` and `$InstallationPath` set to the private controller store and installation JSON, enqueue checks as they arise.

```powershell
python -B re/automation/SolidWorksReadbackBatch.py --store $StorePath --installation $InstallationPath enqueue new-profile principal
python -B re/automation/SolidWorksReadbackBatch.py --store $StorePath --installation $InstallationPath enqueue cut-validation cut
```

Run the watcher in a separate terminal. It releases pending checks on the first poll after earlier SOLIDWORKS work clears. The default poll is two seconds. The watcher checks the capacity-one controller resource, the shared Windows oracle lease, and whether a SOLIDWORKS process is already running. Set `--wait-seconds` if you want to collect requests for a minimum time before release. The supervisor and listener run the released job.

```powershell
python -B re/automation/SolidWorksReadbackBatch.py --store $StorePath --installation $InstallationPath watch
```

If at least 10 checks are pending and the oldest has waited five minutes, the watcher temporarily reserves the next slot. The controller holds new jobs using the same resource, and the standalone Boss witness waits at the shared admission check. Work already in progress can finish. Earlier jobs can resume when the batch settles. You can adjust the limits with `--priority-count` and `--priority-seconds`. If the watcher exits abruptly, Windows releases its lock and the controller reservation expires. A program using only the original oracle lease can still delay the batch, and a manually opened SOLIDWORKS session must close before a new run can start.

Use `flush` to attempt an immediate release subject to the same application checks, or `status` to see each request's job, state, and available evidence digests. Checks received after a release wait for the next batch. Both pending checks and their assigned jobs survive a watcher restart. Earlier controller jobs must use the same capacity-one application resource to participate in priority admission.

Each released job uses one owned SOLIDWORKS process, before and after controls, and serial readbacks. Use the separate operations for independent restart evidence and the existing paired replay. The queue does not accept P02 or P05 requests.

[Native testing and ownership procedure](../../../../Tasks/Research/AutomationNativeTesting.md)
