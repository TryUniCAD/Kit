# Conversion completion backlog

`A08c-SolidWorksOpenRetry` is active in the [automation register](../Reference/Research/AutomationSteps.md#status-and-ownership).
It adds bounded native startup recovery and stage measurements to the continuous capture dependency in PR #288.

## Purpose and authority

`A08c-ContinuousSolidWorks` is active under the [automation register](../Reference/Research/AutomationSteps.md#status-and-ownership).
Codex owns persistent research capture and document reopening on `codex/solidworks-capture-batching`.
Delivery is [PR #288](https://github.com/TryUniCAD/Kit/pull/288).
The bounded P01/P03/P04 comparison, controller overlap and resume evidence are recorded in the change entry.
Current-revision readiness and broader native qualification remain pending.
The production conversion boundary and fresh-process acceptance requirements are unchanged.

Use this register to find work on the path from the current SDK to the [completion roadmap](../../Roadmap.md).
Each task records its delivery boundary, owner, dependency and observable completion condition.
This register does not authorize a merge or assign new work to a person.
The [encoder child steps](../Reference/Research/AutomationSteps.md#deterministic-encoder-work) track the first deterministic SOLIDWORKS and Fusion round trips.

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
| B01 | Supported version, feature and route matrix            | Active    | Codex B01 matrix worker; scoped delivery below        | Current source and PR inventory              | Every intended family has explicit file types, vendor versions, feature scope and directional routes, with evidence or named gaps.                    |
| B02 | Independent paired semantic qualification              | Blocked   | PR #94 register: A02d, A04c, A05c                     | Licensed native readback and source evidence | Initial paired sketches, bosses and cuts have independent inventories, resolved bindings and measured controls.                                       |
| B03 | Graph comparison and proven format rules               | Blocked   | PR #94 register: A06, A07, A09                        | B02                                          | Ambiguities, field rules and counterexamples are traceable. Qualified comparisons and held-out codecs pass remote gates.                              |
| B04 | Portable neutral-to-native writers                     | Blocked   | PR #94 register: A11, A12; coordinate PR #121         | B03 and independently understood grammar     | Both writers derive every byte and required relationship from portable semantics, without donor blocks or a CAD runtime.                              |
| B05 | First bidirectional editable conversion                | Planned   | PR #94 register: A13                                  | B02–B04 and application workers              | Both initial directions pass public SDK, preservation, independent edits, restore, rebuild, save and fresh-process reopen.                            |
| B06 | Ordinary part histories and schema coverage            | Planned   | PR #94 register: A16; child owners unassigned         | B05 and feature-specific evidence            | Qualified sketches, constraints, expressions, cuts, revolutions, finishing operations, patterns and geometry pass held-out route acceptance.          |
| B07 | Complete assembly, configuration and drawing semantics | Planned   | PR #94 register: A16; coordinate drawing PRs          | B06 and independent native controls          | Supported documents preserve all occurrences, mates, variants, dependencies, drawing dimensions and links through edit/rebuild and reopen.            |
| B08 | Integrate existing native-format and evidence work     | Active    | Each existing PR below owns its scoped delivery       | Each PR's implementation and gates           | Accepted implementations are integrated without reviving donor writers. Their exact capability limits enter B01 and B12.                              |
| B09 | Remaining CAD family adapters                          | Planned   | PR #94 register: A16 child claims                     | B01, B05 and family-specific grammar         | All nine roadmap families have qualified native reads and independent writes for their declared version scope.                                        |
| B10 | CLI workflow and error usability                       | Available | Unassigned; separate scoped PR                        | Existing CLI and documented supported cases  | Representative users install, select formats, convert, inspect results and recover from refusal without undocumented assistance.                      |
| B11 | Documentation accuracy, accessibility and evaluation   | Available | Unassigned; separate scoped PR                        | Current public contracts                     | Task guides match source and support limits. Rendered/narrow-view and representative-user findings are resolved or recorded explicitly.               |
| B12 | Directional conversion acceptance matrix               | Planned   | Unassigned release owner; reuse PR #94's A13 evidence | B01 and each supported route                 | Every promised direction/version passes all CAD criteria on independent cases. Unsupported combinations refuse before output mutation.                |
| B13 | Unattended research and operating evidence             | Planned   | PR #94 register: A15                                  | A07, A08b and A14; A10 only when enabled     | The two-week pilot records recovery, parked jobs, interventions and independently accepted documents unlocked.                                        |
| B14 | Release, runtime and security qualification            | Planned   | Unassigned release owner; separate scoped PRs         | Qualified release subset, B10–B12            | Clean supported installations, runtime isolation, bounded inputs, destination safety, required security gates and reproducible release evidence pass. |

M6 requires all promised routes, not merely the first narrow release subset.
B14 can qualify earlier subsets while B06–B09 continue.
B03's parent is not complete merely because its deterministic scheduler has process evidence.
B04's parent is not complete merely because controlled constructor probes exist.

## B14-RecordDecodeCache: JSON reconstruction performance

Codex owns the scoped type-information cache on `codex/cache-record-types`, based on main `625bdbf9efa35d0fdc4939c59f68561aa927db4b`.
Delivery is [PR #286](https://github.com/TryUniCAD/Kit/pull/286).
Dependencies are the existing interchange codec and public document APIs.
The exit requires identical canonical JSON, preserved validation and compatibility behavior, current-head CI, and configured review.
The [change entry](../Changes/Research/Readers/Performance/RecordLayoutCache.md) records the paired measurements and verification.
This task does not change the supported format boundary or close B14 release qualification.

## Important gap boundaries

### B10-RunDefaults

Codex owns the profile-independent catalogue shortcut on `codex/desktop-run-defaults`.
It depends on the installed CLI bridge and the explicitly selected trusted research checkout.
The [change entry](../Changes/Commands/SavedRunDefaults.md) defines configuration and limits.
Its exit requires actual installed-command checks without a shell profile, current-head CI and configured review.
[PR #290](https://github.com/TryUniCAD/Kit/pull/290) records the revision and verification evidence.
This child task does not claim the broader B10 usability exit or CAD conversion acceptance.
Native batch execution remains separately owned by [PR #288](https://github.com/TryUniCAD/Kit/pull/288).

### A08h-OwnedExit: SOLIDWORKS catalogue shutdown repair

Task `A08h-OwnedExit` is active in the [owning register](../Reference/Research/AutomationSteps.md#a08h-ownedexit-catalogue-capture-shutdown).
Codex owns the scoped repair on `codex/solidworks-capture-shutdown`, with
delivery in [PR #289](https://github.com/TryUniCAD/Kit/pull/289).
The exit requires licensed native replay of the failed P04 captures and batch
controls, normal process exits, independent reopen and dependent decoder
receipts, plus the applicable publication gates. Six previously failed
cut-extrude cases passed both native phases and ran the decoder. The
driving-dimension singleton passed after the standalone worker retried a
shutdown timeout. The combined probe passed the singleton on the first
attempt after the empty-session exit request. The final worker and batch
retry recovered the same case on a third fresh attempt after two timeouts.
The written-recipe geometry repair has separate delivery in
[PR #291](https://github.com/TryUniCAD/Kit/pull/291).

Task `A08h-CaseIsolation` consolidates the shutdown and thin-wall repair and
adds per-case catalogue rejection handling. Its exit requires real process
evidence that healthy sibling decoders can run when a bad bundle is withheld.
[Owning register](../Reference/Research/AutomationSteps.md#a08h-caseisolation)

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

### B04-SW2026-PARTITION-MARKS

The PR #121 takeover team owns this archive reader on
`codex/solidworks-partition-marks`. It reuses the active partition and
rollback validators delivered in [PR #172](https://github.com/TryUniCAD/Kit/pull/172).
Exit requires the selected and predecessor IDs, the validation-only API
result, and the guarded ownership and framing controls on the accepted revision.
Binding these IDs to individual feature records is a separate delivery.
[Change entry](../Changes/Solidworks/Archive/SolidworksPartitionMarks.md)

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

### B04-SW2026-PARTPROPS

The scoped literal text reader follows PR #178's typed configuration
directory. The takeover workstream owns [PR #183](https://github.com/TryUniCAD/Kit/pull/183).
The branch binds one saved active configuration, its physical streams
and the compatible literal property managers. Three strict public
source reads recover 23 values with their geometry intact. Two further
saved property sets retain their earlier geometry refusals. The
advanced baseline and 12 malformed variants keep the prior modeled
document. The shared registry refuses unsupported native property
state before a fresh projection or a JSON-to-JSON publication.
Interchange inspection retains the original diagnostic and provenance.
The legacy wheel fixture's empty text scopes use a complete structural
absence proof. The local #183 integration binds every literal result to
the complete `Config-0` codec in [PR #233](https://github.com/TryUniCAD/Kit/pull/233).
Five guarded physical framing variants and two separate owner contrasts
withhold all literal text and preserve the inspected model. Strict legacy and native inspections retain
their models while export respects the accepted portability gates.
A separate neutral snapshot with a modeled prism preserves its
inspection status and refuses publication in both SDK paths. Exit requires the
foundation on main, current review and native queue acceptance.
[Slice record](../../re/solidworks/records/LiteralPartTextReaderSlice2026.md)
[Change entry](../Changes/Solidworks/Inspection/Properties/SolidworksLiteralPartTextReader.md)

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
It reuses the archive body fields and the branch writer accepted in
[#199](https://github.com/TryUniCAD/Kit/pull/199).
Exit requires exact disclosed stream and map comparisons, independently
authored provenance and count cases, bounded refusals, and current
revision queue and review evidence. Complete part assembly and native
writer registration have separate exits.
[Change entry](../Changes/Solidworks/Archive/Metadata/SolidworksHistoryStreamCodec.md)

### B04-SW2026-DEFINITION

The PR #121 takeover team owns the ordinary part Definition codec on
`codex/solidworks-ordinary-part-definition`. The delivery depends on PR #199
for shared field actions. Guarded typed readback and fresh stream generation
have supporting evidence. Delivery requires current-revision CI and review.
Native qualification applies to a complete generated part.
[Change entry](../Changes/Solidworks/Archive/SolidworksOrdinaryPartDefinition.md)

### B04-SW2026-PART-DEFINITION-VIEW

The PR #121 takeover team owns the saved document view reader on
`codex/solidworks-saved-part-view`. Its complete Definition boundary comes
from [PR #205](https://github.com/TryUniCAD/Kit/pull/205). Exit requires the
same orientation and pan/zoom values on the pinned parts, guarded
orthographic refusals, and current revision review and queue evidence.
Session window selection and public presentation transfer have separate exits.
[Change entry](../Changes/Solidworks/Inspection/Presentation/SolidworksSavedPartView.md)

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

### B04-SW2026-CONFIG-FIELD-MODES

The PR #121 takeover team owns the shared field modes and bounded
layout extraction on `codex/solidworks-config-field-modes`. It depends
on the accepted body and ModelHeader primitives and shares its
normalization path with the scene and atom slices. Exit requires
exact physical leaf and normalized word reads, independent authored
branch and repeat checks, and current revision review and CI.
Directly owned bodies and whole configuration admission follow
separately.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigFieldModes.md)

### B04-SW2026-CONFIG-VIEWS

The PR #121 takeover team owns this bounded `moView_c` reader on
`codex/solidworks-config-view-context`. It depends on the shared
member reader and field actions from #187. Exit requires both disclosed
view groups, the authored archive state and refusal cases, and current
revision queue and review evidence. Full configuration admission,
annotation view owners and populated presentation lists retain separate
exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigViewRecords.md)

### B04-SW2026-CONFIG-ANNOTATION-FRAMES

The PR #121 takeover team owns the configuration detailing defaults and
tolerance frame slice on `codex/solidworks-config-annotation-frames` for
separate main delivery. It depends on the admitted part/ModelHeader map,
formatting records and shared field actions. Exit requires the two tracked
archive replays, guarded owner refusals, and current-revision review and CI.
Annotation views, populated tolerance owners and complete configuration
admission have separate dependencies.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigAnnotationFrames.md)

### B04-SW2026-CONFIG-THREAD-MARK

The PR #121 takeover team owns this bounded thread and mark read
extraction on `codex/solidworks-config-thread-action` for separate main
delivery after the configuration field-action slice. Exit requires
the exact native record and map handoffs, guarded signed-word and
invalid record cases, and current revision queue and review evidence.
Populated thread maps and complete configuration support have separate
exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigThreadMarks.md)

### B04-SW2026-CONFIG-SECTIONS

The PR #121 takeover team owns this scoped reader on
`codex/solidworks-config-section-framing`. It reuses the shared body
executor, standalone model header and inherited maps. Exit requires the
physical section bounds, true direct alias and empty ghost owner for both
tracked model controls, guarded framing refusals and current revision review
and queue evidence. Complete section bodies, broader context and public
configuration admission retain separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigSections.md)

### B04-SW2026-ASSEMBLY-DEFINITION

The PR #121 takeover team owns the ordinary version-19000 assembly
Definition stream on `codex/solidworks-assembly-definition`. It depends on
[PR #205](https://github.com/TryUniCAD/Kit/pull/205) for the shared Definition
framing and field codecs. Delivery requires exact scoped stream replay and
fresh-process control results, configured review and native queue acceptance.
Assembly composition and public writing have separate exits.
[Change entry](../Changes/Solidworks/Archive/Assembly/SolidworksAssemblyDefinitionCodec.md)

### B04-SW2026-CONFIG-SECTION-EMISSION

The PR #121 takeover team owns the bounded writer actions on
`codex/solidworks-config-section-emission` for separate main delivery.
They depend on the accepted section reader, standalone header selection
and shared typed body writer. Exit requires the two authored sibling
frames, exact pinned ghost payload comparisons, guarded refusals and
current revision review and queue evidence. Full Config-0 generation
and native admission have separate exits.
[Change entry](../Changes/Solidworks/Archive/Configuration/SolidworksConfigSectionEmission.md)

### B04-SW2026-ASSEMBLY-HEADER-ALIASES

The PR #121 takeover team owns the shared direct header action on
`codex/solidworks-assembly-direct`. It depends on section emission from
[PR #216](https://github.com/TryUniCAD/Kit/pull/216) and the linked reader.
Exit requires matching alias order and object identity in the guarded
assembly actions, retained part behavior, and current revision review
and queue evidence. Complete assembly configuration, mate, and native
document generation have separate exits.
[Change entry](../Changes/Solidworks/Archive/Configuration/SolidworksAssemblyHeaderAliases.md)

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

### B04-SW2026-FRESH-PART-HEADERS

The PR #121 takeover team owns the fresh ordinary part header graphs
on `codex/solidworks-fresh-part-headers` for separate main delivery.
The slice uses the accepted standalone Header, CMgrHdr2 and direct
ModelHeader map rules. Exit requires independent wire and ownership
comparisons, existing fixture parity, review and queue evidence.
Linked part emission and public writer admission have separate exits.
[Construction evidence](../../re/solidworks/records/FreshPartHeaders2026.md)

### B04-SW2026-CONFIG-LW-MATERIAL

The PR #121 takeover team owns the ordinary material and model-data
read slice on `codex/solidworks-config-material-owners`. It uses
the accepted part header handoff and lightweight node grammar.
Exit requires both measured suffixes and map identities, guarded
authored contrasts and refusals, and current revision review and queue
evidence. Complete configuration admission and material assignment
retain separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigMaterialOwners.md)

### B04-SW2026-CONFIG-CACHES

The PR #121 takeover team owns the bounded part cache reader on
`codex/solidworks-config-caches` for separate main delivery. It depends
on the shared body field, counted row and branch readers. Exit requires
the disclosed mass and empty bounds intervals, malformed record
refusals and current revision queue and review evidence. Populated
bounds ownership and complete physical `Config-0` admission have
separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigCaches.md)

The complementary emitter on `codex/solidworks-config-cache-writing` uses
the accepted shared body writer and cache owner rules. Exit requires exact
saved field replay, independent one- and two-slot emission, preserved
maps and current revision review and queue evidence. The prepared scope
covers empty bounds only.
[Cache emission](../Changes/Solidworks/Archive/Configuration/SolidworksConfigCacheWriting.md)

### B04-SW2026-CONFIG-ATOMS

The PR #121 takeover team owns this bounded part atom reader on
`codex/solidworks-config-atom-manager`. It uses the typed maps, header
objects and accepted concept fields. Exit requires both disclosed
manager and producer identities, guarded signed state and rejection
cases, and current revision queue and review evidence. Inline bodies,
handle modes and full configuration admission retain separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigAtomManager.md)

### B04-SW2026-ORDINARY-CONFIG

The #121 takeover team owns the ordinary Config-0 graph on
codex/solidworks-ordinary-config-graph. It combines the accepted part
ModelHeader, section, unit, member, scene and annotation owners with the
remaining ordinary model rules. Four disclosed files reproduce the
complete physical stream. The guard rejects truncated sections and
wrong unit owner aliases. Current review and queue acceptance govern the
archive delivery. The literal property call site and published native
part writer use separate deliveries.
[Ordinary graph evidence](../../re/solidworks/records/OrdinaryPartConfigGraph2026.md)

### B04-SW2026-CONFIG-FINISH-HELPER

The PR #121 takeover team owns the bounded surface-finish reader
on `codex/solidworks-config-finish-delivery`. It uses
the accepted character format and ordinary part/ModelHeader map.
It reuses the annotation helper declaration from accepted PR #226.
Exit requires the guarded part replays, authored wire and map contrast,
current-revision review, and applicable CI.
[Dependency PR #226](https://github.com/TryUniCAD/Kit/pull/226) ·
[Change entry](../Changes/Solidworks/Archive/Configuration/SolidworksConfigFinishHelpers.md)

### B04-SW2026-CONFIG-FONT-FIELDS

The PR #121 takeover team owns this bounded reader on
`codex/solidworks-config-annotation-font` for separate main delivery.
It reuses the accepted scalar, text and embedded field readers and the
part header handoff. Exit requires exact native field and map comparisons,
guarded malformed cases and current revision queue and review evidence.
The composed label, annotation and detail definitions have separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigFontFields.md)

### B04-SW2026-CONFIG-LABEL-FIELDS

The PR #121 takeover team owns this bounded reader on
`codex/solidworks-config-label-fields` for separate main delivery.
It depends on the shared embedded field reader and the font and width
layouts. Exit requires exact comparisons of the full label group in
both disclosed parts, signed condition contrasts, refused active layer
objects, and current revision queue and review evidence.
Concrete layer ownership and full physical Config-0 have separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigLabelFields.md)

### B04-SW2026-CONFIG-SCENE

The PR #121 takeover team owns this bounded scene and light
normalization reader on `codex/solidworks-config-light-actions`.
It follows the ordinary feature-action and thread record slices.
Exit requires both physical part scene profiles, exact archive
ownership, the authored normalization contrast, invalid record cases
and current revision queue and review evidence. Broader presentation
and complete configuration admission retain separate exits.
[Change entry](../Changes/Solidworks/Archive/SolidworksConfigSceneRecords.md)

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

The NX, CATIA and Creo implementation PRs closed without merging on 2026-11-16.
Their work on containers, retained payloads and bounded geometry remains research evidence for scoped A16 child claims. Each claimed route requires independent native acceptance after A13 and A15. [NX #115](https://github.com/TryUniCAD/Kit/pull/115), [CATIA #116](https://github.com/TryUniCAD/Kit/pull/116), [Creo #117](https://github.com/TryUniCAD/Kit/pull/117)
Rhino and standalone AutoCAD have no matching implementation PR in the inspected inventory.
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

### A08i-ThinWall

The SOLIDWORKS catalogue correction passed source-pinned wall-side checks,
independent reopen and decoder execution for the three written cases.
Portable semantic findings remain open.
[Delivery PR #291](https://github.com/TryUniCAD/Kit/pull/291)
[Owning register](../Reference/Research/AutomationSteps.md#a08i-thinwall)

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

`A06g-BulkDecodedComparison` delivered the standalone command in [PR #273](https://github.com/TryUniCAD/Kit/pull/273), merged as `12b98c78`.
It depends on the existing semantic comparator and codec and reads decoded JSON without running either decoder.
The [owning register](../Reference/Research/AutomationSteps.md#a06g-bulkdecodedcomparison-standalone-bulk-command) links the final process evidence and queue acceptance.
The [change entry](../Changes/Research/Readers/Comparison/BulkDecodedComparison.md) records the qualification limits.
The installed comparison command and unified folder are separate work in [PR #275](https://github.com/TryUniCAD/Kit/pull/275).
The production writer snapshot records the measured [.SLDPRT part scope](../Changes/Solidworks/Construction/SolidworksMeasuredPartPublication.md). The cross-format milestones remain open.

The next critical-path task is B02: fresh native Fusion readback and paired semantic qualification on PR #94.
The inspected register names that missing evidence before A06 can qualify its graph comparisons.
Check that register again before running or claiming anything.
The next independent available task is B01, followed by B10/B11 work that can use already qualified examples.
No new research implementation, application run, user evaluation or conversion qualification is claimed by this planning change.

## Prepared encoder input replay

The shared encoder worker owns [A13a-FusionPreparedInputs](../Reference/Research/AutomationSteps.md#a13a-fusionpreparedinputs-per-role-fusion-writer-input-replay).
[PR #305](https://github.com/TryUniCAD/Kit/pull/305) adds per-role Fusion writer JSON to the existing research pipeline within the constrained constructor scope.
[PR #303](https://github.com/TryUniCAD/Kit/pull/303) records Fusion saved-cuboid writer research with observed same-source replay.
[PR #304](https://github.com/TryUniCAD/Kit/pull/304) records SOLIDWORKS native evidence for a separate, source-free candidate with one Top annotation view.
Both format tasks still require complete source admission and independent native acceptance for their wider scopes.

## Encoder follow-up research

The Fusion worker owns [A05c-FusionSavedCuboid20261125](../Reference/Research/AutomationSteps.md#a05c-fusionsavedcuboid20261125-vendor-resaved-cuboid-reading-and-writing).
[PR #299](https://github.com/TryUniCAD/Kit/pull/299) is checking the read-only reader for the scoped vendor-resaved constrained cuboid family.
Saved-graph writing and independent held-out native verification remain open.
The SOLIDWORKS worker owns [A12b](../Reference/Research/AutomationSteps.md#a12b-vendor-authored-blind-boss-admission).
The task covers vendor-authored blind bosses and requires complete source semantics, archive-free JSON, and independently measured native output.
The shared encoder worker owns [A08d-FileScopeAttribution](../Reference/Research/AutomationSteps.md#a08d-filescopeattribution-stream-provenance-for-strict-fusion-inputs).
Delivery is [PR #298](https://github.com/TryUniCAD/Kit/pull/298).
The task corrects physical stream coverage reporting for strict Fusion reads and keeps the existing native qualification requirements.
These follow-ups depend on the [bounded round-trip work in PR #297](https://github.com/TryUniCAD/Kit/pull/297).

## Native sketch ownership and blind boss evidence

The shared encoder worker owns [A06d-NativeSketchOwnership](../Reference/Research/AutomationSteps.md#a06d-nativesketchownership-saved-solidworks-sketch-ownership-in-comparison).
[PR #302](https://github.com/TryUniCAD/Kit/pull/302) adds reader-reported native sketch ownership to comparison reports. Independent semantic qualification remains required.
[PR #300](https://github.com/TryUniCAD/Kit/pull/300) is the research evidence delivery for [A12b](../Reference/Research/AutomationSteps.md#a12b-vendor-authored-blind-boss-admission).
Whole-source admission, writing, and measured native acceptance remain open.

## Shared research queue coordination

Task `A08b-SharedQueue` is active in the [owning register](../Reference/Research/AutomationSteps.md#a08b-sharedqueue-shared-research-requests-and-advice-budgets).
Codex owns `codex/shared-research-queue`; delivery is [PR #272](https://github.com/TryUniCAD/Kit/pull/272).
Dependencies are the existing controller, supervisor, priority scheduler and optional advisor integration.
The scope is shared local job requests, duplicate suppression, resource-aware admission, obsolete-work cancellation and shared advisor budgets.
The exit requires process-boundary concurrency and recovery evidence and current-head PR readiness.
This work changes research scheduling only; B02, B03, B05 and native conversion acceptance remain open.

## Native feature ladder evidence follow-up

Task `A08h-Ladders2026` is a scoped evidence publication under the [owning register](../Reference/Research/AutomationSteps.md#a08h-ladders2026-native-campaign-evidence).
Codex owns packaging on `feat/deterministic-campaign-20261122`; delivery PR is [#263](https://github.com/TryUniCAD/Kit/pull/263).
Dependencies are merged PRs #158 and #207 and the licensed native workers.
The exit requires a verified corpus manifest, sanitized records, explicit failure outcomes, and current-head publication readiness.
The [campaign summary](../../re/FeatureLadders2026/README.md) does not change the production snapshot or close B02, B03, B05 or B13.
Native recovery and semantic qualification remain blocked as recorded in that package.

## Bounded Fusion rectangle reader follow-up

Task `A05-RectangleRecovery` is active under the [automation register](../Reference/Research/AutomationSteps.md#a05-rectanglerecovery-bounded-reader-qualification).
Codex owns the bounded unconstrained reverse-XY and positive-YZ reader work on `fix/native-rectangle-qualification-20261122`.
Delivery PR is [#265](https://github.com/TryUniCAD/Kit/pull/265); current-head CI and configured review are pending. Queue candidate `06b002441448d2e961629215cdc09768ea8b1530` passed the original Windows fixture path but was rejected after the combined policy/native job exhausted its ten-minute deadline. The [scheduling repair](../Changes/Ci/NativeCompatibilityScheduling.md) preserves all paths and adds the user-authorized twelve-minute shard buffer; fresh queue acceptance remains required. Dependencies are merged PR #263, the strict reader, and independent licensed controls.
The exit requires numerical source comparison, public SDK and CLI replay, retained refusal coverage, shared-suite integration, and current-head CI and review.
Native writing and full conversion acceptance remain open. SOLIDWORKS host recovery is separate.

## Recovered SOLIDWORKS native ladder evidence

Task `A08h-LadderRecovery` was published through the [owning register](../Reference/Research/AutomationSteps.md#a08h-ladderrecovery-recovered-native-corpus).
Codex published the evidence on `feat/solidworks-ladder-recovery-20261122`; delivery PR [#267](https://github.com/TryUniCAD/Kit/pull/267) merged as `b9b9430ac3ce09afb171183cfc778878be90bfdb`.
The [package](../../re/solidworks/FeatureLadderRecovery/README.md) preserves 111 complete-batch strict decodes and two original failed-batch salvages.
The archived reports retain 96 incorrect top/right placements.
The separately scoped [principal-plane reader repair](../Changes/Solidworks/Inspection/Parts/SolidworksPlanePlacement.md) now matches all 144 native ladder centroids in full and design-only reads.
The exit requires verified hashes, sanitized records, retained failed attempts, explicit semantic gaps and current-head publication readiness.
Dependencies are merged PR #263, the research controller and native source measurements. No production conversion boundary changes.

## Decimal native placement evidence for B02–B05

Task `A08h-Placement20261123` is owned by Codex in the [automation register](../Reference/Research/AutomationSteps.md#a08h-placement20261123-decimal-native-reader-evidence), with delivery PR [#274](https://github.com/TryUniCAD/Kit/pull/274).
The [fresh scope](../../re/NativePlacement2026/README.md) settled 48 native attempts and 255 strict committed-file replays. Capture is incomplete: 47 full batches plus two saved files from one COM failure yield 143 of 144 planned native inputs.
Main retains 45 measured SOLIDWORKS placement mismatches. The separately owned [PR 270](https://github.com/TryUniCAD/Kit/pull/270) candidate passes 138 fresh source comparisons; [PR 269](https://github.com/TryUniCAD/Kit/pull/269) receives fresh decimal evidence for XZ and reverse-YZ refusals. Those contributions remain revision-bound and separate from production readiness.
Dependencies are merged PRs #263/#265/#267, the existing controller and licensed source measurements. Publication exits on verified hashes, honest failure/semantic accounting and fresh CI/review. Existing writer ownership, including [PR 121](https://github.com/TryUniCAD/Kit/pull/121), remains separate; no donor writer is restored. B02/B03/B04/B05 remain unfinished and the production conversion boundary does not change.

## Principal-plane reader placement repair

Task `A04-PlanePlacement` is offline verified in the [owning register](../Reference/Research/AutomationSteps.md#a04-planeplacement-timestamp-independent-principal-references).
Codex owns `codex/solidworks-plane-placement`, based on main `9e2049c73028b8f4d00d142a35a3fb42f1c23b92`.
Delivery is [PR #270](https://github.com/TryUniCAD/Kit/pull/270), authorized for publication on 2026-11-23.
Dependencies are merged PRs #263 and #267 and their unchanged native source observations.
The bounded exit requires correct public-reader placement, timestamp variability, malformed-reference guards, and unchanged older part output.
The [change entry](../Changes/Solidworks/Inspection/Parts/SolidworksPlanePlacement.md) records the completed offline checks.
Review and queue follow-ups require explicit refusal of unsupported sketch rotations and contradictory principal identities, while preserving origin owner fallback.
Fresh revision-bound shared-suite and merge-group verification remain pending for these follow-ups.
Fresh native acceptance, the broader typed scene path, and cross-format conversion remain unqualified.

## Automatic SOLIDWORKS paired-case batching

Task `A08h-PairedBatch` is owned by Codex on `codex/solidworks-capture-batching`.
The [owning register](../Reference/Research/AutomationSteps.md) records automatic P01–P05 batching through the existing native runner.
Dependencies are catalogue authoring, native ownership, and accepted controller artifacts.
Delivery is [PR #288](https://github.com/TryUniCAD/Kit/pull/288).
Source `231ffae38c7a9ca83705c6705e7d382d05c1e208` passed the measured three-case native batch with two normal process exits and three automatically completed decoder jobs.
Current-head publication checks and configured review are tracked in the delivery PR. Merge-group acceptance remains separate.
The exit requires measured batch session reuse, independent reopening, per-case decoder receipts, and current-revision CI and configured review.
The [change entry](../Changes/Research/Supervisor/Catalogue/PairedCaseBatching.md) retains verification limits.
Production decoding and conversion qualification remain open.

## Circular rim fillet qualification packs

`A08h-RimFillet20261125` is a checking B06 child owned by Codex on `feat/native-conversion-campaign-20261125`.
The [register](../Reference/Research/AutomationSteps.md#a08h-rimfillet20261125-circular-rim-fillet-readwrite-packs) records dependencies and delivery.
The [pack](../../re/Fusion/RimFilletPack/README.md) provides source-free writer acceptance and executable typed read/write regressions.
The seven original snapshot-width refusals are retained; a width-preserving repair now passes 22 typed/native comparisons. All public neutral conversion refusals remain open. Delivery is [PR #301](https://github.com/TryUniCAD/Kit/pull/301). The production boundary and PRs #121/#297 remain unchanged.

## A08h-FusionTwoSidedDraft20261127 research evidence

Codex owns independently drafted two-sided circular Fusion extrusion evidence on `feat/fusion-two-sided-draft-20261127`.
The [owning child](../Reference/Research/AutomationSteps.md#a08h-fusiontwosideddraft20261127) records dependencies, native-resource ownership and exit requirements.
The [package](../../re/Fusion/TwoSidedDraft20261127/README.md) preserves native sources, signed parameter roles, strict refusals and separate fresh-process witnesses.
Delivery: [PR #394](https://github.com/TryUniCAD/Kit/pull/394). B02–B05 and the supported production boundary remain unchanged.
The existing child claim is retained while the Planning register remains a separate unmerged delivery.

## B01-SupportMatrix: consolidate existing support evidence

Codex owns `feat/project-next-steps-20261127`, based on main `1619f00bf532caad262d1557bd69281179e5c497`.
Scope: the [project-wide support matrix](../Reference/Operations/SupportMatrix.md), reusing existing catalogues and acceptance records.
Dependencies: current public contracts, production source, automation ownership and PR #368's separately owned SOLIDWORKS census.
Delivery: [PR #375](https://github.com/TryUniCAD/Kit/pull/375).
The scoped snapshot is published for checking; unresolved version/type choices remain follow-up work.
Exit: every roadmap family and directional route has an explicit status, source evidence or named gap, plus current-head CI and configured approval.
Unresolved vendor-version promises remain open; B12 acceptance and native conversion work are not completed by this register.
See the [change entry](../Changes/Planning/SupportMatrix.md).

## B10-FormatDiscovery: focused CLI format lookup

Codex CLI worker owns `feat/b10-cli-usability-20261127`.
Scope: `kit formats [FORMAT]` lookup by primary identifier or alias, visible text aliases and unknown-format recovery.
Dependencies: existing registry discovery and its unchanged JSON list schema.
Delivery: [PR #376](https://github.com/TryUniCAD/Kit/pull/376).
Exit: real-process discovery/refusal coverage, current-head CI and configured approval.
Queue repair: preserve the intended text reminder and update directional CLI coverage to assert all three lines and directional aliases.
The directional-format file and focused CLI process cases pass locally under explicit repair authorization.
Remote PR checks and merge-group acceptance remain distinct evidence.
Representative-user workflow evaluation and the broader B10 exit remain open.

## B11-FirstUseGuides: installation and recovery guidance

Codex documentation worker owns `feat/b11-documentation-usability-20261127`.
Scope: installation, first use, format selection and result recovery guidance.
Dependencies: current public metadata/API and the B10 CLI contract.
Delivery: [PR #377](https://github.com/TryUniCAD/Kit/pull/377).
See the [first-use change entry](https://github.com/TryUniCAD/Kit/blob/8c2a2affc/Documentation/Changes/Guides/FirstUseWorkflow.md) on that delivery branch.
Exit: source-backed corrections, link/render evidence where available, current-head CI and configured approval.
Representative-user evaluation and the broader B11 exit remain open.
