# Continuous SOLIDWORKS research capture

New catalogue runs use one owned SOLIDWORKS process across native batches.
The application stays open while separate controller decoder jobs consume completed bundles.
Each native batch closes its documents before reopening and measuring the saved files.
The native application resource remains serial with capacity one.
Persistent runs dispatch one case per controller capture job.
Each completed case can start decoding while SOLIDWORKS handles the next case.
Application startup is shared across those jobs.

The private host configuration accepts `verification_mode`.
The default, `document_reopen`, enables the persistent owner.
Use `fresh_process` to retain independent authoring and verification processes.
Saved runs retain their original host configuration and source revision.

The owner verifies an empty session, background lifetime control, document closure, baseline unloading, and unchanged baseline hashes.
Existing geometry, driving edit, restoration, healthy control and complete archive roster checks still apply.
Routine receipts use `document_reopen` and do not count as fresh-process native acceptance.
The final CAD acceptance criteria still require independent fresh-process evidence.

The owner starts before the supervisor and stays alive across its worker sessions.
It stops when the run finishes or pauses.
A resume creates a new queue generation and preserves previous requests, receipts and logs.
An owner failure stops the run; recovery requires a resume after inspecting the retained failure.
An unrelated SOLIDWORKS process blocks startup.
Only the process launched by the owner enters its cleanup scope.

## Verification

The installed SOLIDWORKS interop compiler accepted the implementation.
Two consecutive P01 batches passed document reopening in the same process.
At `5c3ae3810c`, two consecutive three-case batches shared one process and passed all document-reopen checks.
Public decoding overlapped the second batch.
The same saved P01, P03 and P04 baselines produced equivalent recorded measurements in a separate fresh process.
The complete probe took 387.78 seconds, including the comparison process.
The [sanitized observation](../../../../../re/automation/BatchEvidence/ContinuousSessionObservation.json) records the tolerance and qualification limits.
A separate thin-extrusion probe failed its existing body-measurement check and remains unaccepted.
Its original and reopened volumes both measured 560 cubic millimetres.
At `18d72e23ee`, the real catalogue controller completed two capture jobs and two decoder jobs on their first attempts.
Both captures used one application process, and the first decoder overlapped the second capture.
Shutdown observed normal process exit without forced cleanup.
Resume created a new owner generation and retained all completed receipts without starting another job.
The [pipeline observation](../../../../../re/automation/BatchEvidence/ContinuousPipelineObservation.json) records the actual intervals and outcomes.
The command returned exit code 1 with `coverage_incomplete` because existing decoder findings remain unresolved.
It recorded no supervisor failure, orphan or stale result.
Current-head CI and review, and merge-group acceptance remain separate gates.
No general equivalence or throughput improvement is claimed.

For a native comparison, run `python re/automation/BatchEvidence/ProbeRoutine.py --cases CASES.json --host HOST.json --output OUTPUT`.
The case file contains a JSON list of validated configured cases.
Use the existing private host settings and a new output directory outside the checkout.
The probe retains native files, comparisons and decoder output together.

Task `A08c-ContinuousSolidWorks` is owned by Codex on `codex/solidworks-capture-batching`, delivered through [PR #288](https://github.com/TryUniCAD/Kit/pull/288).
It uses the batch preparation and native ownership foundation in that delivery.
Its exit requires consecutive native batches sharing one process, same-file fresh-process comparisons, concurrent decoding, recovery checks and current-revision CI and review.
