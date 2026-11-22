<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fusion grid evidence integrity

A07 remains parked. This change repairs the inference consumer without claiming saved-policy proof or fresh native qualification.

## Scope

PR #158 item 2 starts from `5018f106b8287c83756233c677cc155e8b963357`.
The local branch is `codex/pr158-a07-body-selection`.
Three advisory agents independently checked receipt requirements, native access and inference consistency.
Root owns the implementation and verification.
A06b admission, comparison, shared registers, historical stores and P05 remain outside this change.

The [inference consumer](../../../../re/automation/InferenceGrid/Evidence.py) previously compared the report process with its dispatch host by PID only.
It did not independently check the restart handoff or compare saved archives between phases.
A coherently rehashed substituted process birth, absent handoff or substituted Phase B archive could reach the parked observation.

The new [phase witness checks](../../../../re/automation/InferenceGrid/PhaseWitness.py) require:

- The complete normalized process birth, including Windows FILETIME when supplied.
- Finite, ordered process birth, phase start, phase end and dispatch completion times.
- A Phase A restart handoff with the exact installation, host, plan, owner, reason and supported queue identifier shape.
- Identical handoff records in the accepted worker result and dispatch proof.
- No Phase B restart request.
- Exact equality of all three Phase A and Phase B archive records.

The dispatch artifact does not expose the original spool job identifier separately.
The consumer checks its handoff identifier shape and cross-record consistency.
It does not claim to independently reconstruct the original request or prove normal Fusion exit.
The existing native worker retains those ownership and lifecycle responsibilities.

The checks follow the existing native worker and counterpart contracts.
They do not change the inference status, policy meaning, source reader or acceptance flags.
See [the specific integrity gotcha](../../../Gotchas/Research/Workers/Inference/GridNeedsIndependentPhaseBindings.md).

## Frozen receipt and source pins

These pins come from the retained [deterministic inference record](DeterministicInference.md).
They identify historical evidence, not a new application run.

| Artifact                                        | Pin                                                                |
| ----------------------------------------------- | ------------------------------------------------------------------ |
| Original discovery capture revision             | `89c25945f5833ad9c3a1c6c683df510b5702dd54`                         |
| Historical replay source                        | `8425b5fbc9bbda0b19c9efbd8dc566d2ea6cc0c4`                         |
| Historical replay report SHA-256                | `66a1e22b04c02f004ef662b86d0506959c17efbd85ccca57bafaa1e77e5d1744` |
| Historical parked receipt SHA-256               | `06414a895e34601d8866dd0cccff87d82da1cbffd90b4829b0a2cdbd9d293fd2` |
| Frozen discovery plan SHA-256                   | `557028a830ea0fa5e55bb0ebf797e657f8be3b4e06046937bb1b7cb787c48818` |
| Two-body specification SHA-256                  | `298cf204b0e4329186b35d9cc46e36525e3ef2119dc7ddb870e73a5f86289d52` |
| Affected Fusion through-all archive SHA-256     | `5aacebd98ea8fa101d070572091fbd1b2270b496c2facc7e9125049082b2506f` |
| Affected SOLIDWORKS through-all archive SHA-256 | `e1f431f1f21ae294fbd3711503ce386bec4fb4916c3cc83b57c876f1ae283149` |

The fixed assessment ID is `inference:6577273e71eb648645c28662d9345eaf0f041b5713f225871398d6a1cbef5d13`.
The two affected archive jobs remain dependent on that assessment.
Provisioning on another host must issue a new parked receipt in its own A03 store.
Do not transplant the historical receipt into that store.

## Verification

The [synthetic protocol author](../../../../re/automation/InferenceGrid/ProtocolFixture.py) creates content-addressed sessions for the actual inference command.
Its archive payloads are explicitly authored protocol bytes, not native Fusion files.
Each negative control recomputes the report, receipt, dispatch, manifest, accepted result and session fingerprint.
This makes the intended inconsistency reach the relevant consumer check.

The [process suite](../../../../tests/Research/Inference/Scope/ScopeEvidenceTests.py) contains two positive controls and 25 refusals.
Both positive controls remain `waiting_evidence`, with `qualification=false` and the existing unqualified result flags.
The Windows case checks protocol identity parsing only.
It does not establish licensed Windows Fusion scope support.

At the original PR source, the process-birth, missing-handoff and archive-substitution controls all failed their refusal assertions.
The old worker returned zero and published a parked observation in all three cases.
With the repair, those controls refuse before publishing any result.
All source session and input bytes remain unchanged.

The locked task environment uses CPython 3.14.7, pytest 9.1.1, NumPy 2.4.6 and Black 26.10.1.
The first broader run used an environment without NumPy and was superseded after a frozen dependency sync.
The locked run passed 62 cases, including all 27 new controls, in 14.13 seconds overall.
Its controller case failed because the sandbox withheld startup process identity.
A separate retry with owned-process inspection permitted passed that case in 12.54 seconds.
Thus all 63 focused case IDs have passing observations across the recorded runs.
The final 27-case grid suite also passed in 10.12 seconds after the test typing review.
The failed execution remains separate from those passing observations.

```sh
.venv/bin/python -m pytest -q \
  tests/Research/Inference/Scope/ScopeEvidenceTests.py \
  tests/Research/Inference/InferenceBoundaryTests.py \
  tests/Research/Inference/InferenceIntegrityTests.py \
  tests/Research/Inference/InferenceControllerTests.py
```

The existing `InferenceArchiveGate.py` also passed through the real controller and supervisor in a new disposable store.
It verified 16 P03 rescans, four P04 termination rescans, reuse of 18 unchanged P03 receipts and nine affected jobs after one rule change.
The two dependent body-selection rescans remained at zero attempts after forged evidence was refused.
Its separate synthetic holdout controls passed without reading P05.
The offline report SHA-256 is `fc2e9c49b7b97027838c452017961786cdd127c190a4ac04f5524ff017d3f68b`.
Its newly issued parked receipt is `7b68318e7885d280ab2e0893b22214f3df98a5526a306f27e68820e1db57ea0f`.
These new offline identifiers do not replace the historical receipt or establish fresh native evidence.

The first permitted archive run refused the symlinked macOS `/var` temporary ancestor at output custody.
The successful run selected the canonical temporary root without changing any guard:

```sh
env TMPDIR=/private/tmp .venv/bin/python re/automation/InferenceArchiveGate.py --output /private/tmp/a07-archive-gate.json
```

Focused Ruff, Black, steering, Mypy and Pyright checks passed.
Pyright used the task environment explicitly and retained three existing unrecognized configuration-setting notices.
No type or review gate was changed.
The normal merge-queue test collection discovers the new `*Tests.py` process suite.
Remote checks and merge-group acceptance were not run for this unpublished local change.

## Tested consumer source

These SHA-256 pins identify the implementation used by the focused process checks.
The final local commit also binds the tests and this change record.

| Source                                           | SHA-256                                                            |
| ------------------------------------------------ | ------------------------------------------------------------------ |
| `re/automation/InferenceGrid/Evidence.py`        | `9f105c5ca4ca29c9ec8aeff9a0187ca0ccedfce4eb5013b9ab6cf5a382f15120` |
| `re/automation/InferenceGrid/PhaseWitness.py`    | `a197853c56def2c4e240f3bacc56e3dd070919dd140ed03bb281ce4f76e4990e` |
| `re/automation/InferenceGrid/ProtocolFixture.py` | `77fc629051d253db0b869f6e20775adffc99ba0b1ee1ca377f3ec1cb6ad1a2e7` |

## Exact remaining native requirement

No accepted independent two-body saved-policy evidence was available in the inspected material.
No CAD application was launched or attached for this repair.
A local Fusion installation and historical failed attempts do not establish a usable current-source capture endpoint.

1. Provision a new owner-private installation and A03 store at one exact clean source revision.
2. Register the inference and `capture.fusion` workers with a capacity-one Fusion resource.
3. Use [Provision.py](../../../../re/automation/InferenceGrid/Provision.py) and the supervisor to obtain that store's parked assessment receipt.
4. Prepare the [fixed two-body study](../FusionReadback/FusionScopeControl.md).
5. Queue both phases through the [supported phase queue](../Workers/FusionPhaseQueue.md), retaining its durable receipt.
6. Attach it with [Resume.py](../../../../re/automation/InferenceGrid/Resume.py), using that store's exact parked receipt and queue digest.
7. Obtain accepted Phase A, normal owned Fusion exit, same-build fresh Phase B, healthy controls and unchanged original archive hashes.
8. Audit the accepted reports, process births, source pins, controls, native exit evidence and all three saved archives.
9. Independently prove the saved target-policy field with controlled black-box saves and public API authority.
10. Validate that rule on unrelated held-out designs without consuming P05.

The expected volumes are A: 8000 to 7200 mm³ in every case.
B changes from 1000 to 600 mm³ for automatic and explicit-A+B.
B remains at 1000 mm³ for explicit-A.
Automatic and explicit-A+B intentionally have the same physical result.
Their resolved participant lists cannot distinguish the saved authoring policy.
All Fusion `observed_policy` values therefore remain null.
One-body agreement cannot resolve this question.

A normal supervisor-worker exit does not prove normal Fusion application exit.
Synthetic protocol checks and archived discovery replay cannot substitute for fresh native observations.
Follow the [Fusion black-box research restriction](../../../Reference/Research/FusionDonorBan.md).
No production decoder policy rule is justified by the available evidence.
