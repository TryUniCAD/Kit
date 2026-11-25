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
Wider native comparisons, concurrent decoding, process checks, CI, review and queue acceptance remain pending.
No general equivalence or throughput improvement is claimed.

Task `A08c-ContinuousSolidWorks` is owned by Codex on `codex/solidworks-warm-session`, delivered through [PR #295](https://github.com/TryUniCAD/Kit/pull/295).
It depends on the twelve-case batching delivery in PR #288.
Its exit requires consecutive native batches sharing one process, same-file fresh-process comparisons, concurrent decoding, recovery checks and current-revision CI and review.
