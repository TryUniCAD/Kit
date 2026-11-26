# SOLIDWORKS reader and writer delivery plan

Build the reader and writer together, one editable feature family at a time.
This plan is for developers extending the SOLIDWORKS adapter and researchers qualifying its output.
The target is lossless conversion from native files to Kit JSON and back, with a live, editable feature tree.
Production conversion must run without SOLIDWORKS, donor files, or AI.
Use SOLIDWORKS in research to author independent controls and measure generated files.

## Establish the baseline

Kit has part and assembly readers, a neutral JSON model, a job controller, and deterministic inference tools.
The bounded part writer supports one unconstrained Front-plane loop of 3–64 straight segments and one blind boss depth.
Publication requires offline native measurement evidence for the exact generated archive.
Assembly writing and general editable part round trips remain open work.
See the [SDK roadmap](../../Roadmap.md) and [measured part writer contract](../Changes/Solidworks/Construction/SolidworksMeasuredPartPublication.md).

1. Pin the code revision, SOLIDWORKS build, case manifests, input hashes, and measurement tolerances.
2. Reconcile the research runtime that included PR #288 with the [automation register](../Reference/Research/AutomationSteps.md) before assigning work.
3. Record each feature and file version in a coverage table. Track reading, writing, native reopening, editing, rebuilding, and held-out acceptance separately.
4. Group unresolved findings by feature, record, and failure reason. Select the smallest reproducible example for each group.
5. Admit a capture as a control only after independent checks verify its expected values.

The November 25 retry run recorded 50 cases with unresolved decoding and 12 capture failures.
Seven failures concerned body measurements. Five concerned sketch profile regions or areas.
Reproduce one case from each group and investigate both the recipe expectation and the observed geometry.
Five separate fresh-process checks matched earlier baseline measurements on vendor-authored files.
The writer milestone below requires independent measurements on Kit-generated files.

## First milestone: one editable blind boss

Use a plain rectangular boss within the existing writer scope.
Reserve independently authored parts for acceptance before choosing or changing any field rule.
Keep the source inventory, tolerance settings, and measurement receipts with the cases.

1. Measure the source sketch, feature tree, driving depth, body count, volume, and centre of mass in SOLIDWORKS.
2. Read the source with the public reader. Compare the JSON model with the independent source inventory.
3. Use the research preparation path to generate a fresh candidate from that model. Derive every emitted field from documented format rules.
4. Measure a healthy control. Open the candidate in a fresh process, rebuild it, and compare the tree and geometry. Measure the control again.
5. Change only the driving depth in JSON. Generate another candidate and repeat the checks against an independently authored control at the new depth.
6. Edit the depth inside SOLIDWORKS, rebuild, and measure the change. Restore the depth, save, reopen, and measure again.
7. Publish through the public SDK with the matching offline receipt. Check that the published bytes match the measured candidate.

For example, a 20 × 30 mm rectangle gains 3,000 mm³ when its blind depth increases from 10 to 15 mm.
Calculate that expectation before running either codec. Check the feature history as well as the volume.

The milestone passes when both candidates preserve every required feature and pass the [CAD acceptance criteria](../Reference/Operations/CadSuccessCriteria.md).
Discard a measurement batch if either bracketing control fails.
Record the first failing stage, case, observed value, and expected value.
Keep unsupported input explicit and preserve the destination on refusal.

## Repeat the discovery loop

1. Choose a finding that blocks the next editable feature or affects several cases.
2. Inventory the affected streams. Separate authored dimensions and references from derived geometry, caches, and archive bookkeeping.
3. Use loader evidence to establish record order, field ownership, legal values, and version conditions.
4. Vary one input at a time. Include repeat saves to identify incidental changes.
5. Run the existing field searches. For ambiguous dimensions, swap distinct values to identify their owning features.
6. Record candidate rules and counterexamples. Freeze the candidates before inspecting independent holdouts.
7. Share proven field definitions between the reader and writer. Generate identifiers, cross-references, and derived geometry from the neutral model.
8. Trace each emitted field to its evidence. Run native acceptance and rescan affected cases after each accepted rule change.
9. Update the coverage table with the revision, vendor build, evidence, and remaining gaps.

Use the [deterministic inference runner](../Changes/Research/Controller/DeterministicInference.md) and the [research playbook](../../re/Playbook/README.md).
A research finding can remain open across runs. Keep its evidence so the next experiment can distinguish the remaining explanations.

## Expand coverage in dependency order

| Milestone                  | Add                                                                                          | Required observation                                                                                    |
| -------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Editable sketches          | Dimensions, relations, arcs, circles, and reference planes                                   | Changing a dimension moves the intended geometry and preserves constraints.                             |
| Dependent features         | Additional bosses, cuts, end conditions, and references                                      | An upstream edit updates the intended downstream feature.                                               |
| Compound parts             | Patterns, mirrors, fillets, chamfers, revolves, sweeps, lofts, and multiple bodies           | Feature order, references, topology, and body measurements survive edits.                               |
| Document state             | Configurations, suppression, equations, properties, and external references                  | Switching configuration or editing a parameter produces the expected tree and geometry after reopening. |
| Assemblies                 | Components, occurrences, transforms, mates, and document references                          | Components resolve and respond correctly to mate and dimension edits.                                   |
| Drawings and compatibility | Views, dimensions, annotations, links, remaining catalogue features, and additional versions | Referenced model changes propagate. Independent files pass for each claimed feature and version.        |

Use the feature catalogue to enumerate the full scope. Include cases that combine previously qualified features.
Record support for each document type and version in the [conversion backlog](ConversionBacklog.md) and its owning registers when evidence changes.

## Operate with zero AI calls by default

Run capture, comparison, inference, reading, writing, and verification as ordinary code.
Omit `--advisor` and leave `--codex-on-stall` disabled.
A stalled job retains its evidence while independent work continues. See the [research CLI procedure](../Tasks/ResearchCommandLine.md).

Consider one authorized advisory call only when a named gap blocks progress and all applicable deterministic experiments are exhausted.
When new controls or rules become available, automatically retry affected findings.
If advice is disabled or yields no testable prediction, keep the finding parked and continue independent work.
If advice is necessary, request one experiment and a prediction for each explanation.
Record the advice against the finding to avoid duplicate calls. Run the experiment through the same independent verification process.
Only measured evidence can qualify a rule.

## Measure progress and cost

Give one worker ownership of the licensed SOLIDWORKS session. Parallelize independent offline work.
Use document reopening for routine screening. Reserve fresh processes and bracketing controls for native acceptance.
Reuse measurements only when their input, dependencies, build, and revision bindings remain valid.

Report queue wait, authoring, saves, reopening, decoding, generation, and verification times separately.
Report accepted feature/version combinations, unresolved groups, failed checks, and actual AI calls beside the timings.
The first delivery is the blind-boss round trip, deliberate JSON edit, native edit-and-rebuild report, stage timings, and zero AI calls.
Full delivery requires independent acceptance for every promised document type, feature combination, and version.
