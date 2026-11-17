# Conversion completion backlog

## Purpose and authority

Use this register to find work on the path from the current SDK to the [completion roadmap](../../Roadmap.md).
Each task records its delivery boundary, owner, dependency and observable completion condition.
This register does not authorize a merge or assign new work to a person.

The baseline is main `e04e7b78699d3f567409937007b00b567620078a`, inspected on 2026-11-15.
The open PR inventory below was read from GitHub on that date.
PR head links pin the observations. They do not establish current review or CI readiness.
Refresh the inventory before claiming work.

[PR #94's step register](https://github.com/Stephen316/Kit/blob/25d9104cebfa2106e0f950cc01c49b9b61d0c879/Documentation/Reference/Research/AutomationSteps.md)
owns its A01–A16 status and individual claims.
Its [plan](https://github.com/Stephen316/Kit/blob/25d9104cebfa2106e0f950cc01c49b9b61d0c879/Documentation/Reference/Research/AutomationPlan.md)
keeps programme implementation on that PR, including later feature and format expansion.
The broad plan does not mean that every later gap is actively being implemented.
Record a child claim there before starting overlapping work.
Existing separate PRs retain their own delivery boundaries.

## Status and ownership rules

| Status    | Meaning                                                                                      |
| --------- | -------------------------------------------------------------------------------------------- |
| Available | No matching implementation PR was identified. Prerequisites permit a scoped task claim.      |
| Active    | An identified PR or owning register records current implementation.                          |
| Blocked   | An identified prerequisite or missing evidence prevents the next dependent acceptance step.  |
| Planned   | In scope for a later milestone. Implementation ownership or prerequisites remain unresolved. |
| Complete  | The exit condition has revision-bound evidence. A PR link alone is insufficient.             |

`Unassigned` means no task owner is established by the inspected evidence.
A PR author is a contact for that PR, not an inferred owner of all future work.
For programme tasks, the linked step register supplies individual ownership.
Availability is a dated observation, not a permanent reservation.

## Work register

| ID  | Deliverable                                            | Status    | Owner and delivery                                    | Depends on                                   | Exit condition                                                                                                                                        |
| --- | ------------------------------------------------------ | --------- | ----------------------------------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| B01 | Supported version, feature and route matrix            | Available | Unassigned; separate scoped PR                        | Current source and PR inventory              | Every intended family has explicit file types, vendor versions, feature scope and directional routes, with evidence or named gaps.                    |
| B02 | Independent paired semantic qualification              | Blocked   | PR #94 register: A02d, A04c, A05c                     | Licensed native readback and source evidence | Initial paired sketches, bosses and cuts have independent inventories, resolved bindings and measured controls.                                       |
| B03 | Graph comparison and proven format rules               | Blocked   | PR #94 register: A06, A07, A09                        | B02                                          | Ambiguities, field rules and counterexamples are traceable. Qualified comparisons and held-out codecs pass remote gates.                              |
| B04 | Portable neutral-to-native writers                     | Blocked   | PR #94 register: A11, A12; coordinate PR #121         | B03 and independently understood grammar     | Both writers derive every byte and required relationship from portable semantics, without donor blocks or a CAD runtime.                              |
| B05 | First bidirectional editable conversion                | Planned   | PR #94 register: A13                                  | B02–B04 and application workers              | Both initial directions pass public SDK, preservation, independent edits, restore, rebuild, save and fresh-process reopen.                            |
| B06 | Ordinary part histories and schema coverage            | Planned   | PR #94 register: A16; child owners unassigned         | B05 and feature-specific evidence            | Qualified sketches, constraints, expressions, cuts, revolutions, finishing operations, patterns and geometry pass held-out route acceptance.          |
| B07 | Complete assembly, configuration and drawing semantics | Planned   | PR #94 register: A16; coordinate drawing PRs          | B06 and independent native controls          | Supported documents preserve all occurrences, mates, variants, dependencies, drawing dimensions and links through edit/rebuild and reopen.            |
| B08 | Integrate existing native-format and evidence work     | Active    | Each existing PR below owns its scoped delivery       | Each PR's implementation and gates           | Accepted implementations are integrated without reviving donor writers. Their exact capability limits enter B01 and B12.                              |
| B09 | Remaining CAD family adapters                          | Planned   | PR #94 register: A16; coordinate PRs #115–#117        | B01, B05 and family-specific grammar         | All nine roadmap families have qualified native reads and independent writes for their declared version scope.                                        |
| B10 | CLI workflow and error usability                       | Available | Unassigned; separate scoped PR                        | Existing CLI and documented supported cases  | Representative users install, select formats, convert, inspect results and recover from refusal without undocumented assistance.                      |
| B11 | Documentation accuracy, accessibility and evaluation   | Available | Unassigned; separate scoped PR                        | Current public contracts                     | Task guides match source and support limits. Rendered/narrow-view and representative-user findings are resolved or recorded explicitly.               |
| B12 | Directional conversion acceptance matrix               | Planned   | Unassigned release owner; reuse PR #94's A13 evidence | B01 and each supported route                 | Every promised direction/version passes all CAD criteria on independent cases. Unsupported combinations refuse before output mutation.                |
| B13 | Unattended research and operating evidence             | Planned   | PR #94 register: A15                                  | A07, A08b and A14; A10 only when enabled     | The two-week pilot records recovery, parked jobs, interventions and independently accepted documents unlocked.                                        |
| B14 | Release, runtime and security qualification            | Planned   | Unassigned release owner; separate scoped PRs         | Qualified release subset, B10–B12            | Clean supported installations, runtime isolation, bounded inputs, destination safety, required security gates and reproducible release evidence pass. |

M6 requires all promised routes, not merely the first narrow release subset.
B14 can qualify earlier subsets while B06–B09 continue.
B03's parent is not complete merely because its deterministic scheduler has process evidence.
B04's parent is not complete merely because controlled constructor probes exist.

### B04-SW2026: SOLIDWORKS 2026 native reading and writing

Owner: the PR #121 takeover agent, delivering through [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
Status: active implementation. The production adapter remains read-only.
Scope: native reading and generative writing for SLDPRT, SLDASM and SLDDRW in PR #121, with an adjacent-release qualification procedure.
Dependencies: independently proven field rules, complete semantic construction, held-out native acceptance, and the applicable B03 evidence.
The broader B04 programme remains blocked on its own dependencies.

The [shared archive implementation](../Changes/Solidworks/Model/SolidworksArchiveObjectModel.md)
adds memory-only counts, typed strings, tags, object identities, counters, and configuration-map handoffs.
Source `0b6e657648a08845ed19939dfe588b2e1c851248` passed its PR CI, including the object/map integration and separate-process string checks.
The [native held-out part trials](../../re/solidworks/measurements/2026/GeneratedRevolveHeldout06.json) qualify ordinary single boss revolves in the research generator.
The [native held-out assembly trials](../../re/solidworks/measurements/2026/GeneratedDimensionedAssembliesHeldout05.json) qualify three and four placements of one rectangular child with no mates.
The [drawing inspection receipt](../../re/solidworks/measurements/2026/DrawingSdkViewRead01.json) covers opt-in inspection of an ordinary sheet and its external part view.
The [first generated blank drawing](../../re/solidworks/measurements/2026/GeneratedBlankDrawingNative01.json) opens, rebuilds and accepts a scale edit. That initial candidate fails native save.
The [native drawing UI diagnostic](../../re/solidworks/measurements/2026/DrawingBlankUiOmission01.json) reproduces native save and reopen with the selected UI groups omitted together.
The [generated front drawing trial](../../re/solidworks/measurements/2026/GeneratedFrontDrawingNative01.json) passes native open, rebuild and view movement with its generated child. Native save returns error 1 while the same-role reduced control saves and reopens.
The [blank drawing event trace](../../re/solidworks/records/DrawingSaveEvents2026.md) places the generated blank failure after entry to native SaveAs dispatch and before third-party storage callbacks. Three matched controls save and reopen.
The [native drawing branch map](../../re/solidworks/records/DrawingSavePostEventBranches2026.md) identifies the listener aggregate and destination storage gates between those events.
The [drawing target-state repeat](../../re/solidworks/measurements/2026/DrawingBlankSaveEventStateNative01.json) distinguishes the generated empty target from the absent target after a deliberate veto with the same API status and callbacks.
The [matched drawing aggregate trace](../../re/solidworks/measurements/2026/DrawingBlankSaveAggregateSoftwareMatchedNative01.json) observes zero in both traced lanes. The [matched document return trace](../../re/solidworks/measurements/2026/DrawingBlankSaveDocumentReturnNative01.json) places the generated failure inside the document save dispatch, whose return is 0 for the generated lane and 1 for the reduced-native control.
The [storage gate trace](../../re/solidworks/measurements/2026/DrawingBlankSaveStorageGateNative01.json) reaches both storage saves and observes valid roots. The generated failure remains after root validity and before event 9.
The [property-section construction](../../re/solidworks/records/DrawingPropertySections2026.md) computes the source-proven section, typed values, fresh IDs and name dictionary from neutral sheet metadata. Its [nine-process native trial](../../re/solidworks/measurements/2026/DrawingBlankPropertySectionsNative01.json) retains generated SaveAs error 1 after clean open, rebuild and scale edit. All four reference lanes save and reopen. The document-properties storage interval remains under investigation.
The [inner property-storage trace](../../re/solidworks/measurements/2026/DrawingBlankPropertyStorageModeNative01.json) selects ZIP mode 1 and valid property, summary and storage owners on both inputs. The native inner call returns 1, while the generated save finishes error 1 with the inner return site armed and unobserved. All seven processes retain healthy controls and qualified debugger cleanup.
The [property save brackets](../../re/solidworks/measurements/2026/DrawingBlankPropertySaveBracketsNative01.json) observe general property and summary saves return 1 in both lanes. Both SOLIDWORKS property bags have a retained DOM and XML mode 1. The generated save finishes error 1 with this final bag's return stop unobserved across seven controlled processes.
The source-derived [property prefix construction](../../re/solidworks/records/DrawingPropertyPrefix2026.md) binds the literal `vt` name used when native save edits the retained DOM. Changing only that XML lexical binding unlocks SaveAs and fresh reopen of the disclosed generated blank sheet after a scale edit. All ten phases pass with healthy pristine, repacked and reduced controls. The SDK reads the saved scale and dimensions. [Native result](../../re/solidworks/measurements/2026/DrawingBlankPropertyPrefixNative01.json)
The [linked property-prefix trial](../../re/solidworks/measurements/2026/DrawingFrontPropertyPrefixNative01.json) passes actual view movement, drawing save and fresh reopen with the generated part link, configuration, geometry and all sixteen drawing feature rows preserved. Both pristine brackets and the reduced native control pass across eight processes. The two original pre-writer drawing sources remain sealed.
The [scaled layout readback](../../re/solidworks/measurements/2026/DrawingScaledViewSdkRead01.json) projects native Front, Top, Right and Isometric views through the SDK. Four disclosed sources retain exact Definition and Header2 bytes and pass 36 transformed point comparisons and four neutral JSON round trips. The original two held-out drawing inputs remain sealed.
The [planar mate endpoint construction](../../re/solidworks/records/AssemblyPlanarEndpointConstruction2026.md) preserves inherited occurrence and datum identities in generated records.
The [complete coincident assembly construction](../../re/solidworks/records/AssemblyCoincidentConstruction2026.md) generates the complete mate list and independent header and counter state.
The [first native coincident mate trial](../../re/solidworks/measurements/2026/GeneratedCoincidentMateNative01.json) preserves both plane references through rebuild, child dimension edit, synchronized save and reopen from coplanar placements.
The [displaced coincident mate trial](../../re/solidworks/measurements/2026/GeneratedCoincidentMateActiveSolve01.json) corrects the authored offset on native open and preserves both plane references through rebuild. Held-out mate acceptance remains open.
The [typed planar mate readback](../../re/solidworks/measurements/2026/PlanarMateProjection01.json) resolves twelve actual occurrence and plane links across six research pairs, reads explicit alignment, and recovers the ordinary driving distance. Public assembly admission remains open.
The [SDK planar mate projection](../../re/solidworks/records/PlanarMateSdkProjection2026.md) takes the typed graph and returns the ordered occurrence and datum identities. Its guarded process regression generates a new editable distance, compares the actual part plane IDs and rejects an unrelated part with the same basename. Automatic admission still requires the linked archive loaders.
The [planar distance constructor rules](../../re/solidworks/records/PlanarDistanceMateConstruction2026.md) bind the ordinary driving graph and its ID allocation order. The [generated distance pair](../../re/solidworks/measurements/2026/GeneratedDistanceMateBundle01.json) round-trips six logical streams with zero runtime file reads. Its [exact-path native replay](../../re/solidworks/records/GeneratedDistanceMateNativeOpen2026.md) measures the 71.375 mm solve and clean rebuild with both child references resolved. The raw aggregate fails its unauthored sketch parameter assertion. A [separate disclosed trial](../../re/solidworks/records/GeneratedDistanceMateEdit2026.md) verifies the edit to 88.125 mm, both saves, a fresh reopen and the typed saved-file readback. Presentation and held-out qualification remain open.
The [standalone SDK header graph](../../re/solidworks/records/SharedSdkHeaderGraph2026.md) re-emits 31 streams exactly across 17 disclosed files. Four guarded assembly bundles use it for their two header streams and retain their earlier generated file hashes.
The [SDK configuration handoff](../../re/solidworks/records/ConfigHeaderHandoff2026.md) uses those same decoded header nodes through linked Config, ResolvedFeatures and available MatesList readback in twelve disclosed and generated files. The remaining production body grammars are open.
The [shared scalar migration and census](../../re/solidworks/records/LinkedGraphScalarConstruction2026.md) covers 81,283 typed scalar reads across twelve measured files. The research field executor delegates numeric reads and writes to the SDK primitive layer. The [ordinary context and string-map rules](../../re/solidworks/records/ContextAndStringMapArchive2026.md) close the two remaining ordinary profile owners through pinned native code and mapped framework spans. Five real process integrations and 42 strict stream checks pass. Extended string aliases, populated-map native behavior and production body grammar promotion remain open.
The [ordinary SDK configuration manager](../../re/solidworks/records/CmgrBodyGrammar2026.md) decodes configuration metadata on the normal part and assembly paths and serializes the same typed manager graph. Twelve complete managers round-trip byte for byte across 46 exercised schemas. The research bridge retains 42 linked and mate stream checks and byte-identical guarded four-document generation. Full linked body admission and writer qualification remain open.
The [nested assembly reference trace](../../re/solidworks/records/NestedAssemblyReferenceState2026.md) binds separate configuration and stamp rules for a subassembly target. The [disclosed archive audit](../../re/solidworks/records/DisclosedNestedAssemblyArchiveAudit2026.md) checks 42 streams across seven saved definitions and binds both healthy native reopens. The [pre-writer source lock](../../re/solidworks/v2026/heldout/NestedAssemblySourceLock01.json) binds both independently measured sealed cases before recursive writer construction.
The [recursive assembly composer](../../re/solidworks/records/GeneratedNestedAssembly2026.md) emits one file per neutral definition and shared repeated targets. The first candidate passes 28 stream comparisons with zero runtime file reads. Its [controlled native trial](../../re/solidworks/records/GeneratedNestedAssemblyNative2026.md) passes open, rebuild, a live depth edit, synchronized three-file saves and fresh reopen across four processes. The [saved-state audit](../../re/solidworks/records/GeneratedNestedAssemblySavedState2026.md) passes 36 scoped stream comparisons. A [separate repeated trial](../../re/solidworks/records/GeneratedRepeatedNestedAssembly2026.md) passes native shared-leaf edit, four-file save and fresh reopen with seven expanded paths and five solids across four controlled processes. Its typed audit passes 48 stream comparisons. Both pre-writer locked ordinary rigid layouts pass the [blind evaluation](../../re/solidworks/records/SealedNestedAssemblyEvaluation2026.md) across eight native processes. Source-tree and presentation parity, other assembly semantics and production integration remain open.
The [aligned parallel mate constructor](../../re/solidworks/records/AssemblyParallelMateConstruction2026.md) generates a second mate class through the same registration and endpoint graph.
The [native parallel comparison](../../re/solidworks/measurements/2026/GeneratedParallelMateNative01.json) passes open and rebuild with exact plane references, preserved rotation and a nonzero plane gap. Persistence and held-out qualification remain open.
The [populated rectangle partition projection](../../re/solidworks/records/GeneratedRectanglePartition2026.md) generates the linked cache and rollback streams. The [standalone trial](../../re/solidworks/measurements/2026/GeneratedRectangleAttachmentNative04.json) records warning 32 and zero bodies at open with the attachment. Explicit rebuild restores the expected solid.
The [forward edge-anchor comparison](../../re/solidworks/measurements/2026/GeneratedRectangleEdgeAnchorNative01.json) retains that initial-open warning on both matched inputs and the same analytic solid after rebuild.
Complete field classification, broad part and assembly semantics and held-out drawing qualification remain unfinished.
The [strict neutral inventory](../../re/solidworks/measurements/2026/NeutralCorpusRead01.json) reads 162 available FCStd identities through the SDK. It finds native feature definitions in 132 documents and assembly graphs in two. Original benchmark membership and generated-output verification remain open.
Production conversion totals remain zero. See the [coverage register](../../re/solidworks/CorpusCoverage.md).
Configured review is deferred until the full scope and pre-review acceptance evidence are complete.

Exit condition: the reader and writer preserve complete native part, assembly and drawing semantics on held-out inputs under all CAD criteria.
The writer derives every emitted byte from neutral inputs or format rules.
The 165-part and five-assembly generated audit, editable native round trips, fail-closed adapter and current-revision delivery gates must pass.

#### Active PR #121 workstreams

The takeover agent owns the serialized Windows oracle. Each workstream delivers through PR #121 and retains the parent CAD acceptance criteria.

| Task | Owner | Current scope | Dependencies | Exit condition |
| --- | --- | --- | --- | --- |
| B04-SW2026-CMGR | `/root/flag_ownership` | Ordinary version-19000 manager codec and normal SDK metadata integration verified on the exercised manager profile. | Shared archive primitives, independent map base 1, the 46-schema CMgr closure and pinned native format rules. | Exact typed read/write parity and alias preservation across the measured corpus, real process checks and explicit unsupported-profile diagnostics, with existing callers preserved. [Receipt](../../re/solidworks/measurements/2026/SdkCmgrGraph01.json) |
| B04-SW2026-CONFIG | `/root/flag_ownership` | Promote the measured ordinary Config-0 object graph to the SDK. | The shared field executor, 158 exercised schemas, direct ModelHeader bindings and continuous map state. | Match byte identity, alias ownership and terminal map counts for complete measured Config-0 graphs through the SDK. Preserve existing public behavior when the linked graph is outside the supported profile. |
| B04-SW2026-REFPLANES | `/root/assembly_occurrence` | D01 passes native offset edit, save and fresh reopen. Its [native source receipt](../../re/solidworks/measurements/2026/ReferencePlaneSourceD01Native01.json) binds the driving plane and radius owners and the measured geometry. Four disclosed source designs pass native author and reopen. Both held-out sources have a [pre-writer lock](../../re/solidworks/v2026/heldout/ReferencePlaneSourceLock01.json). Complete the typed distance-plane correlation and neutral construction before frozen evaluation. | Exact 2026 model loader, root-owned native authoring and sealed source locks. | Generated reference-plane and plane-supported sketch features pass independent held-out parameter edit, rebuild, save and reopen checks with analytic geometry and zero native diagnostics. |
| B04-SW2026-DRAWPROPS | `/root/configuration_header` | The disclosed generated blank and linked front drawing pass native save and fresh reopen. The [scaled composer](../../re/solidworks/records/DrawingScaledSupports2026.md) generates the source-proven projection and support frames for four named views. Measure those generated pairs natively before evaluating the pre-writer locked drawings. | Qualified outer and inner call traces, exact module hashes and root-owned controlled measurements. | Neutral-generated blank and linked-view drawings edit, save and reopen successfully, with independently proven field construction and held-out qualification. |
Protocol byte identity, an open PR, source training measurements, and green static checks do not complete this child.

## Important gap boundaries

### Fusion schemas

The [saved-document coverage record](../Changes/Fusion/Records/FusionSavedDocumentCoverage.md#remaining-boundaries)
identifies 48 missing class schemas: 14 older versions and 34 absent classes.
These affect older documents, PCB data, assembly constraints, appearance overrides and browser features.
The general decoding programme is related, but its current A05 scope does not explicitly promise all 48 schemas.
Track a scoped child under B06 and PR #94's expansion register before claiming implementation.
Do not count rejected, deliberately inconsistent research files as missing production support without inspecting their cause.

### Fusion configurations

The [configuration model boundary](../Reference/Research/FusionDataModel.md#configurations)
supports only the observed empty configuration sidecars.
Populated tables, rules, rows and cells remain unknown.
The inspected account cannot author configured controls because of a licence restriction.
Obtain independent configured controls through an authorized account before deriving the grammar.
This is B07 expansion work within PR #94's broad plan, not a completed or actively claimed A05 deliverable.

### Other native formats

NX, Creo and CATIA already have open implementation PRs.
Their containers, retained payloads and bounded geometry work do not establish arbitrary parametric conversion.
Coordinate B08/B09 with those PRs before adding another adapter effort.
Rhino, standalone AutoCAD and Parashell have no matching implementation PR in the inspected inventory.
They still belong to the broader A16 expansion scope and require explicit child claims.

### Drawings and assemblies

PR #149 merged its bounded SOLIDWORKS drawing dimension decoder.
It exposes decoded angle parameters through the opt-in drawing reader. Drawing dimension rewriting remains in scope for B04-SW2026.
Fusion's [drawing acceptance record](../Reference/Operations/FusionDrawingAcceptance.md)
records authored-drawing loadability and other acceptance gaps.
PR #151's local design export is a separate persistence experiment, not complete drawing or cross-format acceptance.
PR #121 covers the 2026 part, assembly and drawing routes described under B04-SW2026.

## Existing PR inventory

All rows were open at inspection. The contact is the observed GitHub author.
Inspect the current diff and owning register because a PR description can lag its implementation.
No row below declares readiness, successful queue acceptance or permission to merge.

| PR                                                | Contact                                       | Delivery boundary and remaining distinction                                                                                             | Observed head                                                                                 |
| ------------------------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| [#94](https://github.com/TryUniCAD/Kit/pull/94)   | Stephen316; individual owners in its register | Research controller, workers, readers and planned conversion programme. Broad future scope is not active implementation of every gap.   | [25d9104c](https://github.com/Stephen316/Kit/commit/25d9104cebfa2106e0f950cc01c49b9b61d0c879) |
| [#108](https://github.com/TryUniCAD/Kit/pull/108) | odinglyn0                                     | Historical bounded SOLIDWORKS family/writer work and drawing reads. Reconcile with the current recorded-payload ban before integration. | [0ccac121](https://github.com/TryUniCAD/Kit/commit/0ccac1215c7df1d5e6015ca31a1a839618d66508)  |
| [#115](https://github.com/TryUniCAD/Kit/pull/115) | odinglyn0                                     | NX native adapter and ongoing grammar/authoring work. Container reconstruction is distinct from complete editable conversion.           | [1cf32597](https://github.com/TryUniCAD/Kit/commit/1cf32597e597a050c8a16cece42672e214308c6e)  |
| [#116](https://github.com/TryUniCAD/Kit/pull/116) | odinglyn0                                     | CATIA native BRep and parametric investigation. Full feature history and target acceptance remain distinct requirements.                | [b498e5a0](https://github.com/TryUniCAD/Kit/commit/b498e5a08e9132638a784a0b6b7b6710cafb7ed6)  |
| [#117](https://github.com/TryUniCAD/Kit/pull/117) | odinglyn0                                     | Creo PSB adapter and ongoing semantic/authoring research. Inspect its diff beyond the initial replay description.                       | [dafae525](https://github.com/TryUniCAD/Kit/commit/dafae5254bf8de910042e98a779df6419bf72d35)  |
| [#120](https://github.com/TryUniCAD/Kit/pull/120) | Stephen316                                    | Publishes historical SOLIDWORKS decode evidence and corrects licensing documentation. Runtime ports remain separate.                    | [89bb7b32](https://github.com/TryUniCAD/Kit/commit/89bb7b32759f3ca00a1abed733761ff3f70ab98d)  |
| [#121](https://github.com/TryUniCAD/Kit/pull/121) | odinglyn0                                     | Generative SOLIDWORKS 2026 archive primitives, shared object/map implementation, controlled native construction research and assembly investigation. Production writing remains disabled. | [71449990](https://github.com/TryUniCAD/Kit/commit/71449990c9236a4987c024877f9879d0524226e6)  |
| [#124](https://github.com/TryUniCAD/Kit/pull/124) | odinglyn0                                     | Authored SOLIDWORKS metadata constructors. Component evidence does not establish a complete writer.                                     | [e0724fc5](https://github.com/TryUniCAD/Kit/commit/e0724fc50d13012c62eab9b13546b53b90f18556)  |
| [#148](https://github.com/TryUniCAD/Kit/pull/148) | odinglyn0                                     | Fusion journal live-topology evidence. Its stated scope excludes PrismHistory and full topology graph reconstruction.                   | [74935fb1](https://github.com/TryUniCAD/Kit/commit/74935fb13c2f7f7aab79e028c9515bd5acc3270d)  |
| [#149](https://github.com/TryUniCAD/Kit/pull/149) | odinglyn0                                     | SOLIDWORKS drawing dimension parameter decoding. It does not rewrite dimensions.                                                        | [d08040da](https://github.com/TryUniCAD/Kit/commit/d08040da58e2907e6ab0c7abb3e19fcba5906b6f)  |
| [#150](https://github.com/TryUniCAD/Kit/pull/150) | odinglyn0                                     | Bounded removal of historically flaky pending-gate cases. It does not qualify CAD conversion.                                           | [3c92c155](https://github.com/TryUniCAD/Kit/commit/3c92c15575cb807a1c118765d3a2bb7c0925dd7e)  |
| [#151](https://github.com/TryUniCAD/Kit/pull/151) | odinglyn0                                     | Fusion design import, local native export and Kit readback. Cloud save and broader acceptance remain separate.                          | [c4d7173d](https://github.com/TryUniCAD/Kit/commit/c4d7173d0f5ddb570470af493050d27107e146fe)  |

## Choose and maintain a task

1. Read the task, dependencies, current PR diff and owning register.
2. Refresh GitHub state and exact head revisions.
3. Confirm whether the work is active, broadly planned or available.
4. Record the owner and precise scope before implementation.
5. Use the existing programme PR when its explicit ownership rule applies.
6. Otherwise open the task's own isolated PR under repository policy.
7. Record the dependency or evidence gap when blocked.
8. Link revision-bound evidence before marking the exit condition complete.
9. Update the roadmap when the production boundary or milestone changes.

When a PR merges, retain its evidence link and record the merge SHA.
When a PR closes without merging, record its replacement or return the task to planning.
Do not erase required coverage merely because an implementation was removed.
Keep remaining gaps, parked tasks and limitations visible.

## Immediate handoff

The next critical-path task is B02: fresh native Fusion readback and paired semantic qualification on PR #94.
The inspected register names that missing evidence before A06 can qualify its graph comparisons.
Check that register again before running or claiming anything.
The next independent available task is B01, followed by B10/B11 work that can use already qualified examples.
No new research implementation, application run, user evaluation or conversion qualification is claimed by this planning change.
