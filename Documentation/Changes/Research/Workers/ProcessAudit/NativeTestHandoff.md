# Licensed native testing handoff

The [operator task](../../../../Tasks/Research/AutomationNativeTesting.md) prepares a separate licensed Windows SOLIDWORKS machine for PR #158 testing.
It documents source-pinned A03 submission, the retained Windows supervisor, fixed native readback operations, evidence collection, and controlled recovery boundaries.
It preserves all fifteen restored commits at reviewed revision `00ea6bbe7609853ce0f8224309e920f74b2b65b1`.
That SHA is the historical command-review baseline, not the final machine-testing revision.
The operator must replace every `REVIEWED_PR_HEAD` with the single final accepted SHA supplied in the PR handoff.
It changes no decoder, writer, worker, CI, policy, or qualification flag.

The user has no local SOLIDWORKS or Fusion installation and requested a stop before licensed testing and merging.
The handoff therefore provides future operator instructions without claiming they executed.
It separates SOLIDWORKS native process exit and readback from Fusion's independent installation, capture-source custody, and same-installation restart requirements.
Windows Fusion Phase A does not establish Phase B or a complete native restart pair.
The A15 two-week operating pilot remains unstarted.

## Source review

The command and contract review used these retained sources at the exact reviewed revision:

| Source                                                                              | Checked behavior                                                                                                                           |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py`                      | `listen`/`dispatch` options, fixed P04 and P01/P03 rosters, build pin, five-minute cap, direct launch ownership, false qualification flags |
| `re/automation/PairedCaptures/SolidWorksAuthoring/ReadP04SolidWorks.ps1`            | PowerShell requirements, source and installed-assembly pins, unchanged input checks, plan/measurement/receipt publication                  |
| `re/automation/PairedCaptures/SolidWorksAuthoring/P04Readback.cs`                   | Read-only copies, before/after controls, control tolerance, native owner binding, supporting-face and principal-profile observations       |
| `re/automation/Supervisor.py`, `Runners.py`, `Controller.py`, `Records.py`          | Windows requirements, registry/session and batch fields, counted resources, lease/deadline bounds, current receipts and artifact access    |
| `Cli/KitCli/RunResearch.py`                                                         | Installed CLI refuses Windows supervisor, requiring the existing direct research entry for that lane                                       |
| `re/automation/ApplicationWorkers/ApplicationResult.json`                           | `unqualified_dispatch` and `native_qualified: false` remain mandatory                                                                      |
| `re/automation/ApplicationWorkers/RearmSolidWorks.py`, `SolidWorksRearmEvidence.py` | Same-listener owned exit, immutable timeout archival, attempt limits, independent offline pins                                             |
| `re/automation/CaptureHistory.py`, `CaptureLineage.json`                            | Preserved historical metadata and sealed source-input hydration without historical code checkout                                           |
| `re/automation/PairedCaptures/SolidWorksAuthoring/RunSolidWorks.ps1`                | Separate first/second authoring phases and existing capture arguments                                                                      |
| `re/automation/ApplicationWorkers/QueueFusionPhases.py`, `AuditFusionPhases.py`     | Pinned plan, accepted dependency outputs, durable queue receipt, independent retained-pair audit                                           |

The task links existing capture, recovery, reader, comparator, and Fusion procedures instead of introducing another native workflow.
Readback preparation uses the locked optional `dev` extra.
Actual field inference additionally needs the existing `dev` dependency group for NumPy.
Hashes bind selected bytes and relationships, not independent authenticity or semantic acceptance.
A valid readback receipt still does not qualify a reader, writer, conversion, automated reset policy, or operating pilot.

## Verification and limits

Verification consists of direct source inspection, Markdown formatting, relative-link review, changed-path policy, and whitespace checks.
No test, collection, controller, supervisor, reader, auditor, SDK, generator, COM call, application start, or application exit was executed.
No vendor binary or assembly was copied.
The actual licensed run, source custody review, native acceptance, configured review, and merge-group acceptance remain separate evidence requirements.
This documentation does not claim full ASD-STE100 or ISO/IEC/IEEE 2651x conformance.
