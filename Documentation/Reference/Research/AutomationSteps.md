# Research automation implementation steps

## Current scope

[PR #94](https://github.com/TryUniCAD/Kit/pull/94) now contains automation only: corpus custody, durable jobs and artifacts, controller and supervisor recovery, application-worker transport, the main-SDK reader bridge, semantic comparison, generic inference and evidence reporting. The [scope record](../../Changes/Research/AutomationOnlyScope.md) records the boundary.

The SDK starts from main `1d294381340a36ce8e4d9e288e73d995da12fcd7`. Broader native decoders, writer constructors, native shape/cache reconciliation, fixed native grids and their proof suites belong to follow-up work. They are preserved with their original source graph; they are not deleted, accepted or replaced by generic JSON evidence.

The full prior [step register at `fb723e0a920b4d03ad2d5635882860b800a9b61c`](https://github.com/Stephen316/Kit/blob/fb723e0a920b4d03ad2d5635882860b800a9b61c/Documentation/Reference/Research/AutomationSteps.md) and [original plan](https://github.com/Stephen316/Kit/blob/fb723e0a920b4d03ad2d5635882860b800a9b61c/Documentation/Reference/Research/AutomationPlan.md) retain the complete source-bound history and exit criteria. This page changes PR scope, not those acceptance conditions.

## Step register

Identifiers remain stable. `complete` requires matching evidence for that artifact scope. `checking` means current-candidate verification is pending. Historical checks do not establish current PR approval, merge-queue acceptance or native acceptance.

| ID  | Current disposition                                                                                  | Status   | Exit or remaining dependency                                                                                                          |
| --- | ---------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| A01 | Existing neutral-contract audit retained as historical context                                       | complete | No new neutral schema or production capability is introduced                                                                          |
| A02 | Corpus, paired specifications and lineage custody remain in scope                                    | blocked  | Independent admission and frozen-rule qualification remain incomplete; P05 stays reserved                                             |
| A03 | Durable controller, immutable artifacts, leases and recovery remain in scope                         | checking | Historical process verification exists; verify the assembled automation candidate through its applicable remote gates                 |
| A04 | Reader transport uses the existing main SOLIDWORKS API                                               | checking | Preserve full documents, input seals and unresolved observations; decoder expansion is a follow-up                                    |
| A05 | Reader transport uses the existing main Fusion API                                                   | checking | Read options are explicit; native grammar and missing independent source contracts remain follow-ups                                  |
| A06 | Bounded semantic graph comparison and reader artifact jobs remain in scope                           | checking | Preserve differences, ambiguity and unresolved domains; equality is only observed-graph agreement                                     |
| A07 | Generic fields, paired-gap, rescan and scheduling remain in scope                                    | checking | Reserved native proof profiles refuse; complete native source/proof dependencies remain in follow-ups                                 |
| A08 | Worker transport, process identity, ownership, acknowledgement and restart machinery remain in scope | checking | Actual signed-in Fusion Phase A, owned exit/restart and fresh Phase B still require their licensed installation and accepted evidence |
| A09 | Native field maps and codec construction                                                             | blocked  | Preserved follow-up source; generic inference does not replace understood grammar or native proof                                     |
| A10 | Optional model investigation                                                                         | planned  | Models remain off; no model runner or execution is authorized by this automation scope                                                |
| A11 | Portable Fusion writer                                                                               | blocked  | Follow-up source and independent native acceptance required                                                                           |
| A12 | Portable SOLIDWORKS writer                                                                           | blocked  | Follow-up generative serializer work; recorded programs and donor blocks remain prohibited                                            |
| A13 | Bidirectional native acceptance                                                                      | blocked  | Zero native pairs and neither cross-format native route are qualified                                                                 |
| A14 | Automation process, compatibility and source-integrity gates                                         | checking | Preserve all applicable current-candidate gates and independently enforced review requirements                                        |
| A15 | Unattended operating pilot                                                                           | planned  | The two-week pilot has not started; commissioning and historical activity reports do not substitute                                   |
| A16 | Broader features and CAD families                                                                    | blocked  | Preserved follow-up work, with family-specific native acceptance still required                                                       |

A10 never blocks deterministic work. A controller completion means that its registered operation finished; it does not validate the operation's semantic assertion. Application fixtures, offline decoding and computed geometry do not establish measured native acceptance.

## Corpus and historical lineage

The historical corpus remains pinned to `74a0bc353421c25f7a6c539897baadf593a05766`: 778 native inputs, 232 JSON evidence files and two historical notes. Paired custody separately retains 74 native files and ten original receipts. Keep recipe bytes, path spelling, modes, blob IDs, source revisions, measurements and hashes unchanged.

The automation-only tree binds its exact current capture input roster to the original source at `f5b23031c4163528a2e4f5029ab34102133b983e`. Historical introductions and authoring provenance remain evaluated on that original graph. Current bytes and aliases require their own checks; copying files onto a short history does not recreate their original provenance. The source history is metadata and whitelisted evidence custody, not an instruction to check out or execute an old SDK.

A02d remains blocked. The independently sealed Fusion source handoff is still unavailable for supplemental admission. The reservation at `f8a4dc7686dece8d44719b12721105a63864a365` on 2026-11-16 applies only to the original supplemental/future frozen-rule process; it does not assert an earlier freeze. Its reported preflight exited `2`, retained `qualification: not_evaluated` and admitted zero pairs. P05 has not been consumed as new discovery evidence.

The historical [supplemental baseline record](https://github.com/Stephen316/Kit/blob/fb723e0a920b4d03ad2d5635882860b800a9b61c/Documentation/Changes/Research/Controller/SupplementalEvidenceBaseline.md) and [raw-chain preflight record](https://github.com/Stephen316/Kit/blob/fb723e0a920b4d03ad2d5635882860b800a9b61c/Documentation/Changes/Research/Controller/PairedEvidenceManifest.md) remain source-bound follow-up evidence. Their native verifiers are not current automation commands.

## Retained automation contracts

- [Controller](ResearchController.md): transactional state, content-addressed artifacts, immutable job versions, dependency outputs, bounded claims and recovery
- [Supervisor](ResearchSupervisor.md): private sessions, process identity, resources, grouped work, output custody and interruption handling
- [Semantic comparison](SemanticComparison.md): existing main reader observations and complete codec artifacts, with bounded correspondence and explicit unresolved domains
- [Generic inference](../../Changes/Research/Controller/DeterministicInference.md): pinned authored streams, partial hypotheses, counterexamples, parked generic gaps and main-SDK rescans
- [Installed research CLI](../../Tasks/ResearchCommandLine.md): trusted checkout dispatch without importing research code into production conversion

New operations require new immutable rule/tool versions and job identities when their implementation changes. Reader receipts seal the actual SDK inventory and tool sources. Comparison reports seal their three implementation modules. Neither mechanism permits rebinding an old receipt to the new candidate.

## Source-bound observations and open evidence

The A03 process checkpoint `6a846c7d1a6e144cf04a7c30e32261c7be84ea68` covered persistence, invalidation, concurrent claims and bounded large queues. The later `eba0ab48` checkpoint recorded the metadata-only heartbeat repair. These are historical artifact observations, not current-candidate acceptance.

The private reader/comparison operation at `7317092e37f52d6bfc3f26449e2b16a5bd82e86b` and the later replay at `880bf0bed53f338933e819eb92b423670c8377d8` retain their original SDK/tool seals, five jobs, three reader observations and two comparisons. Baseline `different` and width `ambiguous` were observations, not semantic qualification. Preserve both original report sets and their private custody. [Source-bound replay evidence](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6929061748)

The Windows supervisor/process observation at `fc7670b29a7f9d847c102324dfb90a15c1439f4d` reported 111 process cases. It does not establish actual signed-in Fusion restart. Disposable-process lifecycle checks cannot replace a licensed Phase A, accepted exit/replacement evidence and fresh Phase B from the same installation. [Process evidence and limits](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6930649575)

The original 25-member native CI batch remains subject to its original authority blocker. Removing its fixed native gate from this PR does not accept or release that batch. Its [frozen roster and authority record](https://github.com/Stephen316/Kit/blob/fb723e0a920b4d03ad2d5635882860b800a9b61c/Documentation/Changes/Research/Controller/PendingCiRoster.md) stay in the preserved follow-up graph.

No local tests, collection, SDK, generator or native runs establish this rescope. Current remote process checks, configured review and merge-group acceptance remain separate. No merge is authorized by implementation work alone.

## Ownership and updates

Coordinate exact path ownership through PR comments before edits. Preserve other contributors' worktrees and source refs. Keep current commands in the owning guides and link historical source when discussing excluded native implementations. Record actual accepted source revisions and evidence; do not promote pending source reviews, receipts or infrastructure counts into CAD acceptance.
