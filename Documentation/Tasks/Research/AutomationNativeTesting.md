# Test automation on a licensed CAD machine

## Purpose

This handoff prepares the operator's Windows SOLIDWORKS machine for the automated decoding research pipeline.
It does not record a completed native test.
Implementation stops before licensed execution and merging, as the user requested.
Run the procedure only during the operator's later testing session.

The command review baseline is PR #158 revision `00ea6bbe7609853ce0f8224309e920f74b2b65b1`.
That historical baseline preserves all fifteen restored commits.
Actual testing must use the final accepted full SHA supplied in the PR handoff.
Replace every `REVIEWED_PR_HEAD` below with that same forty-character lowercase SHA before using any command or configuration.
Do not select a floating branch or reuse the historical review baseline as the current testing revision.
Recheck changed commands and contracts when the final source differs from the review baseline.
Never change a historical receipt or source pin to describe a new run.

SOLIDWORKS alone cannot establish Fusion capture, Fusion restart, or bidirectional conversion acceptance.
The two-week A15 operating pilot remains unstarted.
Passing process fixtures or native readback does not qualify the complete automated decoding feature.

## Before you start

Read the [CAD success criteria](../../Reference/Operations/CadSuccessCriteria.md), [research book](../../../re/Playbook/README.md), and [oracle procedure](../../Reference/Research/Oracles.md).
Use CAD only as an isolated research oracle.
Production decoding and conversion must remain independent of installed CAD software.

Reserve one licensed Windows desktop for one operator.
Save user work and leave all SOLIDWORKS processes closed before starting a listener.
Do not close, attach to, or terminate a shared user application.
An unexpected document, dialog, process, or license prompt stops the run.

Required software and custody:

| Item                | Required condition                                                                                                                            |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Windows             | Windows 10 or newer, interactive licensed desktop, local filesystem with locking and hard links                                               |
| Python              | Python 3.14 through `uv`, using the repository lock and Windows `pywin32==312` extra                                                          |
| SOLIDWORKS readback | Registered 64-bit build `34.4.1.1011`, with matching installed `SolidWorks.Interop.sldworks.dll` and sibling `SolidWorks.Interop.swconst.dll` |
| PowerShell          | 64-bit Windows PowerShell 5.1, Desktop edition, STA mode, available .NET Framework compilation support                                        |
| Git                 | Trusted Git on an absolute PATH entry, complete required history, unchanged source checkout                                                   |
| Private storage     | Operator-owned local checkout, endpoint, configuration, controller store, supervisor state, and unused evidence directories                   |
| Input authority     | Original capture receipts, native file hashes, specification, healthy control, and any independently supplied evidence pins                   |

Keep installed vendor assemblies, executables, licenses, symbols, and decompiled listings outside the checkout.
Do not upload them with the test evidence.
Keep private machine paths and process credentials out of public reports.
See the [research artifact policy](../../Reference/Research/ResearchArtifacts.md).

The readback launcher refuses a different build or interop version.
Report that mismatch instead of changing its constants or substituting assemblies.
The procedure has not established compatibility with another SOLIDWORKS build.

## Prepare the exact source and evidence

The following paths are examples.
Use unused operator-owned local locations with an existing private parent directory.
Save JSON configuration as UTF-8 without a byte-order mark.
Use forward slashes in JSON paths.

1. Obtain a clean checkout at the reviewed revision, preserving byte-exact source files.

   ```powershell
   git clone --config core.autocrlf=false --filter=blob:none --no-checkout https://github.com/TryUniCAD/Kit.git C:/Kit/Pr158
   git -C C:/Kit/Pr158 fetch origin REVIEWED_PR_HEAD
   git -C C:/Kit/Pr158 checkout --detach REVIEWED_PR_HEAD
   Set-Location C:/Kit/Pr158
   git --no-replace-objects rev-parse HEAD
   git diff --exit-code -- src re/automation pyproject.toml uv.lock
   ```

   Require `rev-parse HEAD` to equal the final accepted SHA used for every `REVIEWED_PR_HEAD` replacement.
   Keep this checkout unchanged throughout the run.
   Do not check out the original binary-bearing branch.

2. Install the locked research dependencies without running a test suite.

   ```powershell
   uv sync --frozen --no-default-groups --extra dev --python 3.14
   uv run --no-sync --python 3.14 python re/automation/CaptureHistory.py fetch
   ```

   The second command fetches the declared historical metadata and permitted sealed inputs.
   It uses `CaptureLineage.json`, including its original source revision and input-tree digest.
   A changed preserved source ref, missing object, or hash mismatch is a refusal.
   Do not replace its authority with a current checkout hash.
   See [capture history binding](../../Changes/Research/Automation/CaptureHistoryBinding.md).

3. Retain the checkout SHA, configuration bytes, runner registry, `pyproject.toml`, and `uv.lock` with independent SHA-256 pins.
   Retain every supplied plan, source input, option, tolerance profile, schema, and rule/tool version before dispatch.
   Record the installed application, interop, constants, Python, and operator-session versions.
   The native launcher records installed executable and assembly hashes in its plan.
   Version labels alone do not prove which source executed.

Use the [deterministic research CLI](../ResearchCommandLine.md) for its supported reader, corpus, and controller commands.
The installed CLI currently refuses `supervisor` on Windows.
The direct `Supervisor.py` entry below uses the retained Windows implementation and the same A03 contracts.
It does not replace the pipeline with handwritten decoding or bypass controller settlement.

## Run a queued SOLIDWORKS readback

This example selects the fixed eleven-file P04 discovery roster.
It reopens committed native inputs in read-only scratch copies.
It does not generate a converted SOLIDWORKS file or edit the original captures.

1. Create `C:/KitPrivate/Installation.json` with the exact source pin:

   ```json
   {
     "version": 1,
     "installation": "solidworks:handoff",
     "application": "solidworks",
     "endpoint": "C:/KitPrivate/Endpoint",
     "source_root": "C:/Kit/Pr158",
     "source_revision": "REVIEWED_PR_HEAD"
   }
   ```

2. Create `C:/KitPrivate/Runners.json`:

   ```json
   {
     "runners": {
       "capture.solidworks": {
         "pool": "native",
         "argv": [
           "C:/Kit/Pr158/.venv/Scripts/python.exe",
           "C:/Kit/Pr158/re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py",
           "--installation",
           "C:/KitPrivate/Installation.json",
           "dispatch",
           "{session}"
         ],
         "result_schema": "C:/Kit/Pr158/re/automation/ApplicationWorkers/ApplicationResult.json",
         "application_installation": "C:/KitPrivate/Installation.json",
         "threads": 1,
         "initial_peak_memory_mib": 4096
       }
     }
   }
   ```

   The memory estimate is an operator starting estimate, not a measured native limit.
   Review available memory and the [supervisor capacity rules](../../Reference/Research/ResearchSupervisor.md#resource-admission-and-memory-stops).
   Retain the selected registry bytes with the run.

3. Create `C:/KitPrivate/Supervisor.json`:

   ```json
   {
     "state": "C:/KitPrivate/SupervisorState",
     "controller": { "adapter": "a03", "store": "C:/KitPrivate/Store" },
     "registry": "C:/KitPrivate/Runners.json",
     "worker": "supervisor:solidworks-handoff",
     "pools": { "native": { "max_sessions": 1 } },
     "resources": { "application:solidworks:handoff": 1 },
     "stop_grace_seconds": 10,
     "poll_seconds": 0.2
   }
   ```

4. Create `C:/KitPrivate/Batch.json`:

   ```json
   {
     "jobs": [
       {
         "id": "readback:solidworks:p04:01",
         "kind": "capture.solidworks",
         "inputs": {},
         "resources": ["application:solidworks:handoff"],
         "options": {
           "source_revision": "REVIEWED_PR_HEAD"
         },
         "rule_version": "p04-readback@REVIEWED_PR_HEAD",
         "tool_version": "solidworks-worker@REVIEWED_PR_HEAD",
         "max_attempts": 1,
         "lease_seconds": 60,
         "timeout_seconds": 300
       }
     ]
   }
   ```

   Resources are label arrays in jobs and capacity maps in supervisor configuration.
   The worker accepts no caller-selected native input for this operation.
   Its plan binds the fixed roster and current source revision.
   Dispatch is capped at five minutes even when a controller deadline is longer.

5. Initialize the new store and define its initially unavailable resource:

   ```powershell
   uv run --no-sync --python 3.14 python re/automation/Controller.py --store C:/KitPrivate/Store init --max-running 1
   uv run --no-sync --python 3.14 python re/automation/Controller.py --store C:/KitPrivate/Store resource application:solidworks:handoff --capacity 1
   ```

6. In a separate operator terminal, start the listener with the actual installed interop path:

   ```powershell
   uv run --no-sync --python 3.14 python re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py --installation C:/KitPrivate/Installation.json listen --interop 'C:/Program Files/SOLIDWORKS Corp/SOLIDWORKS/SolidWorks.Interop.sldworks.dll'
   ```

   Replace the example interop location with its verified installed path.
   Confirm exclusive endpoint ownership before making its resource available.
   Do not start a second listener or delete a fence to obtain admission.

7. Submit the batch through the supervisor and run it:

   ```powershell
   uv run --no-sync --python 3.14 python re/automation/Controller.py --store C:/KitPrivate/Store resource application:solidworks:handoff --available
   uv run --no-sync --python 3.14 python re/automation/Supervisor.py --config C:/KitPrivate/Supervisor.json submit C:/KitPrivate/Batch.json
   uv run --no-sync --python 3.14 python re/automation/Supervisor.py --config C:/KitPrivate/Supervisor.json run --idle-seconds 30
   uv run --no-sync --python 3.14 python re/automation/Supervisor.py --config C:/KitPrivate/Supervisor.json jobs --job readback:solidworks:p04:01
   ```

   Retain the supervisor's stdout and stderr as separate evidence files.
   A successful interpreter exit alone does not prove successful readback.
   The accepted controller outcome and artifact checks below determine the result.

For the fourteen-file P01/P03 roster, use `--readback-operation p01-p03-readback` before both `listen` and `dispatch`.
Add `"readback_operation": "p01-p03-readback"` beside `source_revision` in job options.
Use a separate run identity and operation-specific immutable version labels.
Finish or resolve the previous operation before replacing its listener configuration.
For the five-file P02 circular roster, use `--readback-operation p02-readback` before both `listen` and `dispatch`.
Add `"readback_operation": "p02-readback"` beside `source_revision` in job options.
Each accepted circle observation requires verified bindings before and after rebuild.
Use the same owned process, control and timeout recovery checks below.
P05 remains reserved for frozen-rule holdout acceptance.

## Check native exit, restart, and recovery

The listener directly launches the registered executable and retains its process handle.
The collector verifies the COM PID, creation FILETIME, canonical executable, desktop session, build, and initially empty document set.
Successful readback requires the ticketed native process to exit through that retained handle.
A PID alone, launcher exit, or changed supervisor PID is insufficient.

After the first accepted job and acknowledgement, submit another batch with a new job ID, such as `readback:solidworks:p04:02`.
Keep the same pinned installation and source.
Compare both accepted native ownership tickets and control results.
Require distinct native process identities and observed exit of each process.
This measures two fresh native jobs on one installation.
It does not establish an automated fifty-job reset or crash-recovery policy.

Preserve the original store, supervisor state, registry, and installation when restarting the supervisor.
An interrupted accepted acknowledgement must retain the same result, receipt, generation, fingerprint, and attempt after recovery.
See [acknowledgement recovery](../../Changes/Research/Workers/ApplicationAckRecovery.md).
Do not fabricate an interruption checkpoint or treat an ordinary second launch as that witness.

The initial example permits one attempt and enables no forced native cleanup.
Timeout testing requires a separately reserved unattended desktop and an explicit operator decision.
The listener's `--recover-owned-timeout` and `--recover-owned-failure` flags permit only their documented owned-process cleanup.
They do not authorize termination of another application session.
Keep missing ownership proof quarantined.
See [owned recovery](../../Changes/Research/Workers/SolidWorks/OwnedReadback.md) and [collector failure](../../Changes/Research/Workers/SolidWorks/CollectorFailure.md).

For a deliberate two-attempt timeout campaign, set `max_attempts` to `2` and choose `lease_seconds` no greater than `timeout_seconds`.
The historical 25-second deadline is a fault-injection case, not a normal performance target.
Automatic rearm requires the same live listener and confirmed exit of the exact ticketed process.
Retain both attempt receipts, the archive manifest, native recovery records, and the final quarantine.
A second timed-out attempt proves budget exhaustion, not successful recovery into a completed native workload.
Use the [offline rearm verifier](../../Changes/Research/Workers/SolidWorks/OfflineRearmEvidence.md) with independently retained hashes.
Never enter supervisor owner credentials into command arguments or publish lease files.

## Collect and judge the evidence

1. Require the A03 job outcome `completed` and a verified current attempt.
2. Resolve its accepted receipt and result through controller status.
3. Verify every accepted output with `Controller.py --store C:/KitPrivate/Store artifact <sha256>`.
4. Retain the `readback.plan`, `readback.measurements`, `readback.receipt`, and `dispatch` artifacts with hashes and byte counts.
5. Retain the native ownership ticket carried by the measurements and its matching dispatch digest.
6. Record acknowledgement success separately from native exit and measurement success.
7. Preserve paginated controller events with one fixed `through` bound for the complete observation window.

Use the [controller commands](../../Reference/Research/ResearchController.md#commands) for status, event pagination, and verified artifact paths.
Quiesce the store before backing up its database and objects together.
Keep an independent hash roster of evidence files before transferring them for review.
Inspect private paths, credentials, user information, and archive members before publishing evidence.
Do not edit signed or hashed records to redact them.
Retain originals privately and publish a separate sanitized summary.

| Observation      | Pass condition for this readback slice                                                                               | Failure or incomplete condition                                                                    |
| ---------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Inputs and plan  | Exact Git revision, specification, control, capture receipt roster, native hashes, sizes, and source bytes unchanged | Missing, changed, substituted, or unbound input                                                    |
| Native identity  | Matching launch handle and canonical owner ticket, build `34.4.1.1011`, zero initial documents, observed owned exit  | Unknown owner, wrong build, open documents, unresolved exit, or unexpected native exit disposition |
| Healthy controls | Both observations are `observed`, rebuild succeeds, one solid, volume within `0.001 mm³` of `881814.3482038013 mm³`  | Either control fails or is missing, invalidating the batch                                         |
| P04              | All eleven fixed files observed, supporting faces verified before and after rebuild                                  | Partial roster, failed face verification, load/rebuild error, or unexpected warning                |
| P01/P03          | All fourteen fixed profiles observed with the native sketch and Boss bindings                                        | Missing profile, support, driving dimension, direction, or measurement                             |
| Durable storage  | All four output roles accepted with matching hashes and sizes, current receipt/result, verified acknowledgement      | Session copy alone, stale result, altered artifact, or pending acceptance fence                    |
| Qualification    | Result retains `claim: unqualified_dispatch` and `native_qualified: false`                                           | Promoting this readback to native conversion acceptance                                            |

The control's center of mass is recorded, but its fixed launcher threshold checks only body count and volume.
Review feature trees, bindings, units, centers, edits, and restores against the applicable recipe independently.
The collector permits only the expected read-only load-warning bit.
Preserve all other warnings and errors as failures.
P01 is intentionally a sketch-only control, so a solid-body requirement does not apply to that recipe.

Fresh independent authoring uses the existing [SOLIDWORKS capture harness](../../Reference/Research/SolidWorksCaptureAuthoring.md).
Keep its first/second phases and normal application restart distinct from read-only supplemental readback.
Use new output locations and preserve every edit, restore, baseline, source hash, and receipt.
P02 is reserved for qualification and P05 for frozen-rule holdout evaluation.
Do not use either to tune discovery rules.

Feed accepted observations into the existing reader, semantic comparison, and deterministic inference pipeline.
Before actual field inference, synchronize the existing locked `dev` dependency group as well as the optional `dev` extra:

```powershell
uv sync --frozen --no-default-groups --extra dev --group dev --python 3.14
```

NumPy belongs to the dependency group and is not installed by the optional extra alone.
The earlier minimal synchronization remains sufficient for the documented readback startup.
Use [dependency output selectors](../../Changes/Research/Controller/DependencyOutputInputs.md) instead of rebinding unrelated global evidence.
Declare geometry units, all five quantity tolerances, strictness, configuration, candidate bounds, and immutable source versions before evaluation.
Follow the [native reader worker](../../Changes/Research/Readers/Comparison/NeutralReaderWorker.md) and [comparison worker](../../Changes/Research/Controller/SemanticComparisonWorker.md) contracts.
An unresolved comparator result or explicit unsupported mode remains unresolved.
Do not bypass it with name masking, a carrier, missing metadata, or analytic expectations.

## Fusion requires another qualified installation

Do not run Fusion commands on a machine that only has SOLIDWORKS.
The full same-installation Phase A/Phase B restart path requires its supported signed-in Fusion host and private add-in endpoint.
The retained Windows Fusion opt-in supports ordinary Phase A only.
Phase B and the two-body scope workflow still require their existing macOS counterpart.
See [Windows Phase A limits](../../Changes/Research/Workers/WindowsFusionPhaseA.md).

On that separate host, prepare the exact-source plan, queue both phases, and preserve the durable queue receipt.
Use [queued Fusion phases](../../Changes/Research/Workers/FusionPhaseQueue.md) and [fresh-process evidence](../../Changes/Research/FusionReadback/FusionFreshProcessEvidence.md).
Audit the accepted pair with `AuditFusionPhases.py --store <store> --queue-receipt <receipt>`.
Require healthy controls, accepted Phase A output bindings, the same application build, a later distinct process, and observed old-process exit.
Disposable-child process cases do not establish these native facts.

Original Fusion capture-source custody and the existing admission verifier handoff remain separate dependencies.
See [supplemental preflight](../../Changes/Research/Controller/PairedEvidenceManifest.md).
SOLIDWORKS evidence cannot fill missing Fusion slots or release the reserved pairs.
A13 bidirectional native acceptance and A15 pilot completion remain open until their own criteria pass.

## If the task fails

| Symptom                                                        | Action and stop condition                                                                              |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Unsupported build, missing license, or absent Fusion           | Stop that lane and retain the exact prerequisite failure                                               |
| Source, plan, input, or assembly hash mismatch                 | Preserve the failure and repair custody before another run                                             |
| User documents, modal dialog, or unknown application ownership | Preserve user work and stop native dispatch                                                            |
| Timeout, quarantine, or pending acknowledgement                | Preserve the endpoint, spool, controller store, and supervisor state for the documented recovery owner |
| Missing artifacts or blocked admission                         | Keep the job incomplete without inventing receipts or changing gate conditions                         |

Do not change CI gates, protection settings, family reservations, native qualification flags, or historic receipts to obtain a pass.
Stop after collecting the operator's evidence for independent review.
Do not enroll, merge, or close a pull request under this handoff.

## Related information

- [Research controller](../../Reference/Research/ResearchController.md)
- [Research supervisor](../../Reference/Research/ResearchSupervisor.md)
- [Queued SOLIDWORKS readback](../../Changes/Research/Workers/SolidWorksQueuedReadback.md)
- [Windows queue identities](../../Gotchas/Research/Workers/WindowsQueueClientIdentity.md)
- [Step register](../../Reference/Research/AutomationSteps.md)
- [Handoff source and verification record](../../Changes/Research/Workers/ProcessAudit/NativeTestHandoff.md)
