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

## Important gap boundaries

### B04-SW2026-LOCAL-IMPORT-READBACK

The PR #121 takeover agent owns the strict local geometry reader extraction
on `codex/solidworks-local-import-readback`. It depends on the terminal fin
semantics in [PR #171](https://github.com/TryUniCAD/Kit/pull/171) and the typed
partition rules from [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
Exit requires the public SDK integrations to verify both disclosed planar
solids and their native feature ownership and body counts. The accepted
revision must also pass the absent-history, mismatched-mark, wrong-owner,
and metadata controls.
[Change entry](../Changes/Solidworks/Inspection/Parts/SolidworksLocalBodyReadback.md)

### B14-COMPANION-PUBLICATION

The PR #121 takeover agent owns this active destination-safety task. The
separate main-target PR from `codex/staged-companion-publication` extracts
the generic file publication correction from
[PR #121](https://github.com/TryUniCAD/Kit/pull/121).
It depends on the existing registry and staging directory next to the
destination. [Change entry](../Changes/Commands/CompanionPublication.md)

Exit requires revision-bound CI and review evidence. The registry integration
cases must preserve a concurrent companion file with replacement disabled
and restore earlier originals after a later backup fails.
[Integration cases](../../tests/Convert/Registry/RegistryRaceTests.py)

### B03-SW2026-ARCHIVE

The [archive evidence PR](https://github.com/TryUniCAD/Kit/pull/167) landed the
[exact-build research record](../../re/solidworks/records/Solidworks2026ArchiveCompatibility.md)
for the observed signature table, map handoff and count fields. The record
binds the build manifest and typed traces from [PR #121](https://github.com/TryUniCAD/Kit/pull/121).

B03's qualified comparisons and codecs and B04's portable writer remain
separate programme milestones. [PR #158](https://github.com/TryUniCAD/Kit/pull/158)
continues the programme scope defined in [PR #94](https://github.com/TryUniCAD/Kit/pull/94).

### B03-SW2026-ARCHIVE-CORE

The PR #121 takeover team owns the wire primitive extraction on
`codex/solidworks-archive-core` for a separate main-target delivery. It depends on
the exact-build archive evidence above and the
[pinned primitive rules](../../re/solidworks/records/ArchiveWirePrimitiveSlice2026.md).
Exit requires the synthetic process integration and the normal CI and review
gates on the delivered revision. Class descriptors, object maps and linked
stream integration have separate exits.
[Change entry](../Changes/Solidworks/SolidworksArchiveWirePrimitives.md)

### B03-SW2026-ARCHIVE-OBJECTS

The PR #121 takeover team owns the typed object and map extraction on
`codex/solidworks-archive-objects` for separate main-target delivery. It
depends on the [wire primitive PR](https://github.com/TryUniCAD/Kit/pull/173)
and the [pinned map evidence](../../re/solidworks/records/ArchiveObjectMapSlice2026.md).
Exit requires the linked graph process checks and the normal CI and review
gates on the delivered revision. Actual header and configuration stream
owners have separate exits.
[Change entry](../Changes/Solidworks/SolidworksArchiveObjectMaps.md)

### B03-SW2026-ARCHIVE-HEADERS

The PR #121 takeover team owns the standalone header extraction on
`codex/solidworks-archive-headers`. It depends on the
[typed object maps](https://github.com/TryUniCAD/Kit/pull/174) and
[pinned standalone header evidence](../../re/solidworks/records/StandaloneHeaderSlice2026.md).
Exit requires exact replay of both streams in the two tracked part controls,
including their distinct role test, and the normal CI and review gates.
Configuration binding, CMgr headers and inline Definition headers have
separate exits.
[Change entry](../Changes/Solidworks/SolidworksStandaloneHeaders.md)

### B03-SW2026-KEYWORDS-MODEL

The PR #121 takeover team owns the typed keyword row extraction on
`codex/solidworks-keyword-typed`. It depends on the accepted
[KeyWords framing](https://github.com/TryUniCAD/Kit/pull/181) and the
[field ownership record](../../re/solidworks/records/KeywordModelSlice2026.md).
Exit requires guarded independent wire assertions, XML readback, refusal
coverage, and revision-bound CI and review. Neutral graph projection and
part and assembly writer qualification have separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksTypedKeywordModels.md)

### B04-SW2026-CONFIG-UNITS

The PR #121 takeover team owns this unit-table reader on
`codex/solidworks-config-unit-tables` for separate main delivery. It reuses
the [typed maps](../../re/solidworks/records/ArchiveObjectMapSlice2026.md) and
[body field and counted row codecs](../../re/solidworks/records/BodyValueSlice2026.md).
Exit requires measured record and map identity for the disclosed ladder
and concave parts, invalid frame and owner refusals through the queue
processes, and current revision review and CI. The remaining executors,
configuration owners and full physical `Config-0` admission have separate
exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigUnitTables.md)

### B04-SW2026-CONFIG-MEMBERS

The PR #121 takeover team owns the next bounded configuration extraction
on `codex/solidworks-config-member-fields`. It follows the shared body
executor and unit-table work in [PR #185](https://github.com/TryUniCAD/Kit/pull/185).
Exit requires exact relation and feature color member readback from the
disclosed controls, independently authored repeated rows and class map
cases, and current revision review and CI. The remaining configuration
layouts and complete physical admission have separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigMemberFields.md)

### B04-SW2026-CONFIG-FIELD-ACTIONS

The PR #121 takeover team owns the bounded branch, virtual and fixed
field read extraction on `codex/solidworks-config-field-actions` for
separate main delivery. It depends on the unit-table and relation and
color member readers. Exit requires the two disclosed part controls,
the guarded invalid record cases and current revision queue and review
evidence. Full configuration admission and write coverage have separate
exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigFieldActions.md)

### B04-SW2026-CONFIG-VIEWS

The PR #121 takeover team owns this bounded `moView_c` reader on
`codex/solidworks-config-view-context`. It depends on the shared
member reader and field actions from #187. Exit requires both disclosed
view groups, the authored archive state and refusal cases, and current
revision queue and review evidence. Full configuration admission,
annotation view owners and populated presentation lists retain separate
exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigViewRecords.md)

### B04-SW2026-CONFIG-THREAD-MARK

The PR #121 takeover team owns this bounded thread and mark read
extraction on `codex/solidworks-config-thread-action` for separate main
delivery after the configuration field-action slice. Exit requires
the exact native record and map handoffs, guarded signed-word and
invalid record cases, and current revision queue and review evidence.
Populated thread maps and complete configuration support have separate
exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigThreadMarks.md)

### B04-SW2026-CONFIG-HEADER-LINK

The PR #121 takeover team owns the bounded part header handoff on
`codex/solidworks-config-model-header-link` for separate main delivery.
It depends on the standalone header and typed archive map codecs.
Exit requires exact named ModelHeader selection, preserved object
identities at the part's lightweight boundary, malformed physical
prefix refusals and current revision queue and review evidence.
Complete configuration admission and the property owner's physical
link remain separate work.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigHeaderLink.md)

### B04-SW2026-CONFIG-CACHES

The PR #121 takeover team owns the bounded part cache reader on
`codex/solidworks-config-caches` for separate main delivery. It depends
on the shared body field, counted row and branch readers. Exit requires
the disclosed mass and empty bounds intervals, malformed record
refusals and current revision queue and review evidence. Populated
bounds ownership and complete physical `Config-0` admission have
separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigCaches.md)

### B04-SW2026-CONFIG-ATOMS

The PR #121 takeover team owns this bounded part atom reader on
`codex/solidworks-config-atom-manager`. It uses the typed maps, header
objects and accepted concept fields. Exit requires both disclosed
manager and producer identities, guarded signed state and rejection
cases, and current revision queue and review evidence. Inline bodies,
handle modes and full configuration admission retain separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigAtomManager.md)

### B04-SW2026-CONFIG-ATOM-EMISSION

The PR #121 takeover team owns bounded kind-zero atom manager writing
on codex/solidworks-config-atom-codec. It uses the accepted atom record
reader and shared archive maps. Exit requires exact native record emission,
independent typed row and condition contrasts, guarded malformed cases,
and current revision queue and review evidence. Complete configuration
writing and native file admission have separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigAtomEmission.md)

### B04-SW2026-HISTORY-STREAMS

The PR #121 takeover team owns this standalone History and Biography
codec on `codex/solidworks-stream-history` for separate main delivery.
It reuses the archive body fields and the branch writer in PR #199.
Exit requires exact disclosed stream and map comparisons, independently
authored provenance and count cases, bounded refusals, and current
revision queue and review evidence. Complete part assembly and native
writer registration have separate exits.
[Change entry](../Changes/Solidworks/Archive/Metadata/SolidworksHistoryStreamCodec.md)

### B08-SW2026-TERMINAL-FIN

The PR #121 takeover agent owns this active reader compatibility task.
The separate main-target PR from `codex/solidworks-terminal-fin` extracts
the current Parasolid fin traversal correction. It depends on the existing
decoder and the disclosed L1 native fixture.
[Change entry](../Changes/Solidworks/Inspection/Model/SolidworksCurrentFinOrientation.md)

Exit requires revision-bound CI and review evidence. The strict public
reader must preserve the disclosed closed shell and positive signed volume.
A separately locked capsule passes the current rule and fails the older
semicircle traversal. Its signed volume and area match the fresh native
reference. [Fixture and comparisons](../../re/solidworks/records/SolidworksCurrentFinOrientation2026.md)

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

SOLIDWORKS dimension decoding is already covered by PR #149.
Its description explicitly excludes dimension rewriting.
Fusion's [drawing acceptance record](../Reference/Operations/FusionDrawingAcceptance.md)
records authored-drawing loadability and other acceptance gaps.
PR #151's local design export is a separate persistence experiment, not complete drawing or cross-format acceptance.
PR #121's public assembly research also remains separate from production assembly conversion qualification.

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
| [#121](https://github.com/TryUniCAD/Kit/pull/121) | odinglyn0                                     | Generative SOLIDWORKS 2026 research, controlled native part acceptance and assembly investigation. Production writing remains disabled. | [be866502](https://github.com/TryUniCAD/Kit/commit/be866502bf5c7d1caea488cbf9087f8d01099a40)  |
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
