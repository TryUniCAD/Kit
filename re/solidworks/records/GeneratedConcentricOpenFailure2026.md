# First generated concentric native open failure

Both generated assemblies failed native acceptance at the zero-warning open gate. Each returned a nonnull document, error 0 and warning 32. All four native source controls passed. No generated geometry, mate, actual returned path, edit, save or fresh reopen was measured by that failed trial.

Task `B04-SW2026-MATES-CONCENTRIC`; owner `/root/assembly_occurrence`; delivery PR #121. Root owns the VM, transport and integration. The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), [RE playbook](../../Playbook/README.md), [original observer method](GeneratedConcentricObserver2026.md), and [pre-run reconciliation](GeneratedConcentricNativeQueue2026.md) remain applicable.

## Preserve the actual result

The unchanged packet is `5b90a632eab95d19fdf4f676798ec2bc44a6f0d464595a8198be25984d77ad34`. Six fresh processes ran: four passing controls and two failing generated opens. Both generated reopen phases were skipped. Each control completed 28 numeric checks; the generated phases completed zero numeric checks. All inputs remained unchanged and all cleanup records were clean. [Sanitized first-failure receipt](../measurements/2026/GeneratedConcentricOpenFailure01.json)

| Generated case | Raw record SHA-256                                                 | Open result                                |
| -------------- | ------------------------------------------------------------------ | ------------------------------------------ |
| Feature        | `329dc8ad5968e3de5afcd0ca5800b7b547b9135c495fc4715065fe66a9609b90` | Nonnull `CDispatch`, errors 0, warnings 32 |
| Brep           | `2c041394487fcd77f93f7d5849fde771a70655a60de85ea02442af3af4803e52` | Nonnull `CDispatch`, errors 0, warnings 32 |

The official 2026 enum identifies 32 as `swFileLoadWarning_NeedsRegen`. The separate read-only warning is 2. This is a regeneration warning, not evidence of a null document, an invalid document-kind argument, or a measured path mismatch. [Official warning enumeration](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swFileLoadWarning_e.html?id=3b36a39206d34f468a0d2c24bef11595)

## Exact first failing predicate

The frozen helper correctly infers assembly document type 2 from `.SLDASM`, uses silent plus read-only options 3, and passes an empty configuration argument to `OpenDoc6`. Its by-reference error and warning values are returned separately. The original outer recorder retained the argument as a `WindowsPath` type marker rather than recording the path text. The exact requested path is therefore reconstructed from the immutable job and helper, not falsely presented as a direct inner-call observation.

The observer then evaluates `model is not None and errors==warnings==0 and same_file(GetPathName,parent)`. Nonnull succeeds. The chained comparison first tests `0==32`, which is false. `GetPathName` and `same_file` are never evaluated for either generated case. The warning gate is the first demonstrated failure; the message's other alternatives remain unmeasured.

The existing [assembly rebuild decision record](AssemblyRebuildDecision2026.md) separates child update state, reference staleness and local assembly rebuild state. Earlier paired saves show that child persistence can matter, but those other layouts do not prove this warning's cause. No stamp, flag, face tag or orientation field is patched from that analogy.

## Smallest independent follow-up

The new [preparer](../../tooling/sw2026/PrepareConcentricOpenDiagnostic01.py) copies exactly 33 declared baseline files, preserving all 22 original tool sources, both original prediction cases, input identities and evidence. It adds one [diagnostic observer](../../tooling/sw2026/InspectConcentricOpenDiagnostic01.py), the exact failed-native receipt and a separate manifest. No generated CAD byte or production source changes.

Four fresh processes run Feature only:

1. The original strict D01 before control, with its unchanged zero-warning and full native checks.
2. A standalone read-only open of the exact generated child. Record its actual type/path, rebuild/save/error state, active configuration, update stamp, visible-body count, actual cylinder, live dimensions, complete tree and independently predicted geometry before and after forced rebuild.
3. A cold read-only open of the exact generated parent. Record the explicit `OpenDoc6` arguments and separate returned status values, then actual returned path/type. Record parent and child rebuild/save/error state, real component identities, configurations, resolution, body counts and stamps. Reuse the unchanged strict occurrence/mate/face/tree/geometry capture before and after forced rebuild, retaining any capture failure explicitly.
4. The original strict D01 after control, independently executable after any diagnostic failure.

The diagnostic permits only the already measured warning 32 or zero to continue its observations. This is a diagnostic boundary, not an acceptance waiver. It never saves, relocates, changes a parameter, preloads a child into the parent process, or rewrites an input. Each candidate record has `native_acceptance=false`; its original zero-warning predicate is retained as a separate Boolean. Strict capture failures retain the actual exception in their before- or after-rebuild context. `diagnostic_completed` reports that the observation sequence finished, not that the model qualified.

| Frozen diagnostic item   | SHA-256                                                            |
| ------------------------ | ------------------------------------------------------------------ |
| Trial                    | `c0fd9c34be82a7b506b49d90a1a41688228e57175defb3ff6a805af5e6d1a363` |
| Native recipe            | `74cb54b21ab2c5f23ae3129b614f66c0e2f782867d104ebfe959f851fc3edb80` |
| Complete packet manifest | `bee4a972e540934ccca713d5465f1199aba862066a17f61a47630fa7a8601600` |

Root captures the additive sources, verifies the packet in the pinned guest runtime, then runs the exact recipe. Its after control and summary remain independent of candidate success. The old native records and queue snapshot remain unchanged. Host verification, compilation and static undefined-name checks pass. The new diagnostic has not run natively; all held-out source contents remain sealed.
