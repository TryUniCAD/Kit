<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Deterministic boundary follow-up

This offline coding follow-up starts from PR 158 revision `e976c927afe0fefcd82f3c6f23ca7f852983f563`.
The requested five-minute wait and pull preceded the isolated investigation.
The [ownership plan](https://github.com/TryUniCAD/Kit/pull/158#issuecomment-6982351753), [exact edit claims](https://github.com/TryUniCAD/Kit/pull/158#issuecomment-6984592452), and [verifier scope refinement](https://github.com/TryUniCAD/Kit/pull/158#issuecomment-6985032319) were posted before their respective edits.
Three agents used separate worktrees; root owns integration and publication.

## Verified changes

- [Inference dependency binding](../Controller/InferenceDependencyBinding.md) refuses a direct selector whose staged digest contradicts its accepted dependency result, including a consistently recalculated fingerprint.
  Artifact and candidate selectors retain their separate semantics.
- [Semantic session binding](../Controller/SemanticSessionBinding.md) reuses the shared session validator.
  Missing, undeclared, malformed, or inconsistent dependency custody fails before report publication.
- [Git source isolation](../Workers/Fusion/RunnerGitIsolation.md) removes inherited Git overrides from bootstrap and later committed-source reads.
  Exact source, dirty-file, installed-copy, and opt-in checks remain enforced.
- [Windows fixture cleanup](FusionFixtureCleanup.md) removes only the resolved fixture-owned clone and retries read-only, singly linked regular-file deletion once.
  Unrelated errors remain failures.
- `re/FreeCad/Oracle/VerifyRectangles.py` executes its two Git queries in assignments before asserting their results.
  Independent AST comparison, after inlining those assignments, exactly matches the previous program.
  Commands, arguments, ordering, timeouts, assertions, and the initial refusal of optimized Python are unchanged.
  This addresses the two existing assertion-side-effect reports without rerunning or relabelling native witnesses.

## Actual process evidence

Native Windows verification used CPython 3.14.6, pytest 9.1.1, and NumPy 2.4.6 from the existing locked environment.
No dependencies were installed into that shared runtime.
The observations below are process verification throughput, not unattended research-pilot throughput.

| Root verification                                                                        | Actual result                  | Elapsed |
| ---------------------------------------------------------------------------------------- | ------------------------------ | ------- |
| `InferenceIntegrityTests.py`                                                             | 24 passed                      | 16.85 s |
| `WindowsGitTests.py` installed-bootstrap subprocesses                                    | 14 passed                      | 15.67 s |
| `SemanticSessionTests.py` plus both `NeutralReaderRunnerTests.py::CheckNativeFlow` cases | 16 passed                      | 78.36 s |
| `FusionSupplementTests.py` actual admission commands and clone teardown                  | 7 passed, zero teardown errors | 75.67 s |

The inference positives include a real controller/supervisor parent-to-rescan chain.
The child records the accepted parent result digest and publishes `no_longer_affected` for authored evidence outside the assessed scope.
The semantic positives include actual controller-to-reader artifact selectors for both retained P01 formats.
They retain `semantic_qualification: unverified` and `native_acceptance: not_established`.
The bootstrap cases use an authored application-event surface around the real installed bootstrap; they do not establish licensed application startup.

The evidence agent's broader comparison sweep recorded 113 passes and seven sandbox permission refusals at controller input binding, before job submission.
All seven refused cases passed with the required permissions: a focused 25-case run passed in 104.85 seconds and the remaining P03 controller case passed in 26.26 seconds.
These are separate executions, not a fabricated single green sweep.
The original seven admission assertions previously passed with seven read-only-object teardown errors; the repaired run completed without those errors.
The existing private runner-home suite skipped all 12 cases on Windows because it requires macOS; those skips are not counted as passes.

Independent review covered every repair.
A non-author reran the four inference dependency cases, and another non-author ran all 14 authored semantic-session cases.
Root independently ran the bootstrap, inference, semantic-reader bridge, and admission commands recorded above.
The FreeCAD change has source/AST equivalence evidence only; no fresh native FreeCAD result is claimed.

## Reproduce

Use a clean isolated checkout of the published PR head containing this entry.
Use the repository's locked research dependencies on native Windows with permission to create private files and child processes.
Run each command once with a new task-owned temporary root if specifying `--basetemp`.

```powershell
python -B -m pytest -q tests/Research/Inference/InferenceIntegrityTests.py
python -B -m pytest -q tests/Research/Applications/RunnerHome/WindowsGitTests.py
python -B -m pytest -q tests/Research/Archives/Comparison/SemanticSessionTests.py "tests/Research/Archives/Comparison/NeutralReaderRunnerTests.py::CheckNativeFlow"
python -B -m pytest -q tests/Research/Archives/FusionAdmission/FusionSupplementTests.py
python -B -m pytest -q tests/Research/Archives/Comparison
```

Black, Ruff, focused steering, and Mypy passed all seven changed Python files outside `re/`.
Focused Pyright checks reported zero source errors; its three existing unrecognized configuration keys remain visible.
The research-source formatter checks preserve project exclusions; the small FreeCAD verifier was checked through the Black API.
No lint success is inferred from an excluded research path.

## Source identity

The first three integrated commits are `dfe2bd418`, `51f299dfd`, and `2467ae818617b08c6ed3dbc0c87512e3adb74c78`.
The final root commit contains the fixture cleanup, verifier assertion repair, and this report.
Its accepted full SHA is recorded in the publication comment on PR 158.
All 13 Python files below matched their staged Git blobs byte for byte after verification.

The SHA-256 of the sorted UTF-8 manifest, with one `<sha256>  <repository path>\n` line per file, is `4d4eacfe90689230462a68257313af6340f9acd5d704bec87e145366684f365f`.

| Python source path                                                         | SHA-256                                                            |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `re/FreeCad/Oracle/VerifyRectangles.py`                                    | `07e891d71a2467cc0a153ace11eb4a29af45cbfc577e11cf0b676545312d7dba` |
| `re/automation/ApplicationWorkers/ApplicationProtocol.py`                  | `df0ae5e8fdf7c0a5cd9a6895c08044f457aad144af06f6f28e788c79035a4f89` |
| `re/automation/ApplicationWorkers/BootstrapGitFixture.py`                  | `633feac3ecbd4249736b3ec0720bdac51f47295e874156aff5801b371226a5f3` |
| `re/automation/InferenceSession.py`                                        | `189988e246347d8d2a4da88fb3b1aff50f1e22ea554475a38a1e6180ba21a156` |
| `re/automation/PairedCaptures/Runner/KitCaptureRunner/KitCaptureRunner.py` | `fdcc61ccd95d72abc5970770a854319c1b1c5696d28709783739f08a564a2160` |
| `re/automation/SemanticComparisonRunner.py`                                | `e5bc44b1e2d3fc25d2e477f84f5034827d3ba17ac753480406498c8aa8879b7b` |
| `tests/Research/Applications/RunnerHome/WindowsGitTests.py`                | `b50f6af0d6abebd0bf939f3769af7851f09244529175c374d5ee416e6afef981` |
| `tests/Research/Archives/Comparison/SemanticSession.py`                    | `ab868f4a4f0ceb6c6bda7d4ca792748b39ceb52504b50fc4ddfc4b045bede7dd` |
| `tests/Research/Archives/Comparison/SemanticSessionTests.py`               | `b68a0e4df37367d23d79844e83b022d0cd7d39962051e40dc65292de0500f1fa` |
| `tests/Research/Archives/FusionAdmission/Checkout.py`                      | `b181d3128aefd53815cd9358283ca4b382383f62ec55591f5c66fef100fcecc2` |
| `tests/Research/Archives/FusionAdmission/CleanCheckout.py`                 | `fb7e542e23fb1a7bb1cf999c46254179677747d8fdf1fe728fac062116e20bb1` |
| `tests/Research/Archives/FusionAdmission/RetryReadonly.py`                 | `3515e355f01c9544104a3cb73e08e40b1e0b00ed4ae6c00a36b5ae529e95065a` |
| `tests/Research/Inference/InferenceIntegrityTests.py`                      | `62e6fba11178b83a3941092d40122f2b34b2ff8aa122be6d4895623bfb1f9ee7` |

## Recovery, parked work, and operator actions

Recovery gains are bounded to the exercised failures: contradictory packets refuse publication, inherited Git overrides cease controlling source reads, and disposable Windows clone cleanup completes.
No live pilot controller or store was restarted, migrated, or repaired.
No existing parked job was resumed or given new attempts.
A07's parked policy evidence and the separate A06b original-custody requirements remain with their existing owners.
No qualification or new cross-format capability is inferred from these integrity repairs.

Operator actions were isolated source integration, permission-enabled reruns after explicit sandbox refusals, and stopping only task-owned stalled formatter processes before using the same formatter module successfully.
There were no research model calls, native application operations, direct ledger edits, shared environment mutations, or historical receipt rewrites.
The frozen A15a source, runtime, observation store, and original evidence remain unchanged.
This coding goal does not restart or wait for the separate two-week observation window.

The complete tracked index and incoming PR history must pass the repository vendor-binary guard before publication.
The new follow-up paths contain Python and Markdown text only; no vendor DLL is included.
Fresh remote CI, configured review, native qualification, and merge-queue acceptance remain distinct gates.
The full-scope reviewer timing remains deferred while existing independent native acceptance evidence is outstanding.
No queue enrollment, auto-merge, or merge is authorized by this follow-up.
