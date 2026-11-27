# Repository and decoding planning

Open the [organization project](https://github.com/orgs/TryUniCAD/projects/1) for shared dates and agent claims, or [the local scheduling board](Generated/Board.html) for filters, draft schedule edits and copyable prompts.

Use this page before selecting or handing off repository work. It joins the existing
planning sources without transferring their ownership or changing acceptance criteria.

## Read the current views

Read [the agent workflow](AgentWorkflow.md) for the required start, update and handoff checklist.

- [Dependency Gantt and graph](Generated/Gantt.md): repository milestones and research prerequisites
- [Visual Gantt](Generated/Gantt.svg): directly viewable without a server or JavaScript
- [Standalone visual](Generated/Gantt.html): the same chart in a local HTML file
- [Task index](Generated/Tasks.md): parent tasks, detailed research rows, owners, dependencies and exit conditions
- [Feature scopes](Generated/Features.md): every curated SOLIDWORKS subfeature, every saved Fusion API type and native decoding domain in the saved catalogues
- [Open deliveries](Generated/Deliveries.md): dated PR collision and stack inventory
- [Calendar windows](Generated/Calendar.md): explicitly supplied engineering windows only
- [Source manifest](Generated/Manifest.json): exact source hashes and inventory counts

The scheduling board uses calendar dates. Only explicitly supplied windows are dated. Automatic
forecasts are disabled; the backlog does not imply investigation duration, delivery
commitments, staffing or a CAD host reservation. The dependency diagram separately shows prerequisite tiers. Recorded
status appears in text as well as color.
Source dependency cells, external blockers and native host reservations remain binding.
Parent edges do not enumerate every child dependency. A parent marked complete does
not close later child work. No runnable-task recommendation is inferred from the chart.

The feature inventory is a research denominator, not a support claim. SOLIDWORKS
catalogue stages remain unverified; Fusion API declarations do not establish wire
grammar, legal option combinations or production projection. Unmapped scopes require
an ownership search. They are not automatically available. Other format families and
release work remain covered by B01–B14; detailed catalogues for every family do not yet
exist. Add new inventories as they become available instead of declaring universal coverage.

## Sources and ownership

| Record                                                                    | Owns                                                                                       | Update policy                                                                   |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| [Conversion backlog](../Maintenance/ConversionBacklog.md)                 | B01–B14 scope, owner, delivery and exit                                                    | Update the affected entry with its implementation                               |
| [Automation steps](../Reference/Research/AutomationSteps.md)              | Research task claims and revision-bound evidence                                           | Preserve IDs, child scopes, failed attempts and programme delivery rules        |
| [SOLIDWORKS catalogue](../Reference/Research/SolidworksPlannerCatalog.md) | Families, subfeatures, option axes and dependency inventory                                | Extend the existing catalogue, not a parallel taxonomy                          |
| [Fusion catalogue](../Reference/Research/FusionPlannerCatalog.md)         | Build-bound declarations, feature inheritance and native schemas                           | Preserve declaration versus qualified-decoding distinctions                     |
| [Links.json](Links.json)                                                  | Planning cross-links, parent dependency edges, additional task claims and optional windows | Edit only explicit relationships and evidence; do not override owning registers |
| [PullRequests.json](PullRequests.json)                                    | Dated open-PR collision snapshot                                                           | Refresh from the forge; author means contact, not inferred feature owner        |

`Generated/Tasks.jsonl` preserves each parsed table row, source path, line and section.
Repeated historical IDs retain their section context. `Generated/Claims.jsonl` also preserves prose-only claims from the
linked owning registers, which must be read before starting. `Generated/Scopes.jsonl`
preserves scope definitions, option axes, acceptance criteria and explicit task links.
No automatic title matching assigns a feature to a PR.

The initial snapshot is dated 2026-11-27 at main
`331ef8ce95f7e46814c5086110be9a23478ca8a8`. Registers contain historical status,
including already merged deliveries described as active. An imported `complete` is
a register observation, not a fresh independent acceptance verdict. Refresh current
head/base and evidence before relying on any such row. No new CAD acceptance is claimed.

## Agent update procedure

1. Fetch main and refresh the owning register and live PR inventory before claiming work.
   Search current scopes and stacked PRs, including other owners' branches.
2. Claim a bounded task in its owning register. Record task ID, owner, exact scope,
   dependencies, branch, delivery PR, external resource and observable exit condition.
   Use the existing controller's exclusive native-host leases; this chart is not a lock.
3. Add an explicit `ScopeLinks` entry for each relevant catalogue scope. Use the IDs
   printed in the feature index. Link the owning task; never move ownership merely
   by editing this file. Parent edges belong in `Dependencies`; detailed child and
   external prerequisites remain in their owning register.
4. Keep capture, decode, semantics, write and native qualification separate. A link
   may record each stage as unverified, active, blocked, checking or complete.
   Each completed stage requires an evidence link and the exact 40-character tested
   revision. These structural checks do not independently validate the evidence.
5. Update the owning register and cross-links whenever scope, owner, dependencies,
   blocker, PR/base/head, acceptance evidence or handoff changes. Retain unresolved
   requirements. Record cancelled or superseded work rather than deleting history.
6. Refresh `PullRequests.json` from the forge when selecting work or changing delivery.
   Preserve actual author, head and base fields. Update `ObservedOn` and `MainRevision`
   in `Links.json` when refreshing the planning baseline. Do not stamp a fresh date
   onto an old PR snapshot. A snapshot does not prove checks, reviews or queue acceptance.
7. Regenerate and check the views with the pinned Python environment:

   ```sh
   uv run --locked python re/automation/Planning/Build.py
   uv run --locked python re/automation/Planning/Build.py --check
   ```

8. Commit the owning source edits and regenerated views together. Review the task
   diff and chart before publication. Never edit `Generated/` by hand.

Add a scope link using this structure; substitute real IDs and evidence:

```json
{
  "ScopeId": "sw:family:document:part-document",
  "TaskId": "A04",
  "Stages": {
    "decode": {
      "Status": "checking",
      "Evidence": "path or immutable evidence URL",
      "Revision": "exact tested revision"
    }
  }
}
```

Supply a window only with an explicit scheduling basis. Unscheduled backlog remains
visible without an invented investigation duration or delivery date. Shared changes belong in the GitHub Project; repo schedule
edits are exported as a draft `Links.json` and require review and regeneration.
`Schedules` entries contain `TaskId`, ISO `Start`, ISO `Finish` and a nonempty `Basis`.
They are estimates, not acceptance dates. Label research windows as investigations and retain unknown completion dates. Inspect the dependency chart and task
exit conditions when estimating dependent work.

## Decoding campaign handoff

`FusionRevolveContrast` now links the bounded campaign in [PR #393](https://github.com/TryUniCAD/Kit/pull/393),
owned by jdharcourt. [PR #394](https://github.com/TryUniCAD/Kit/pull/394) separately
records independent two-sided circular drafts. Both remain checking at their recorded
scope; native capture does not close strict admission, reconstruction or conversion.
A follow-up recipient must refresh ownership and existing controls before selecting
missing angle, axis and profile contrasts. It must use the existing research automation,
API oracles and deterministic CLI, retain failures and receipts, reserve holdouts and
prove rules against independent native measurements. Shared decoder changes require
coordinated ownership. The current planning agent owns only `PlanningViews`.

## Verification and limits

The builder runs offline with the Python standard library and reads the Fusion SQLite
catalogue in read-only mode. It rejects unknown parent edges, cycles, duplicate task
IDs, invalid scope links, stage names and malformed date windows. `--check` compares
all generated bytes against current recorded sources without rewriting them.
It does not query GitHub or run CAD software. Agents must refresh remote evidence.
The existing merge-queue test suite owns process-level regression execution.

## Agent assignment and runtime dispatch

Use the project's `Agent` field to record the exact agent/session claim, and keep
`Recorded status`, dates, dependencies and the owning register aligned. Existing PR
authors are contacts, not inferred owners of every related catalogue feature.
The current-work view shows open deliveries separately from scheduled backlog.

Open a scope for its fenced prompt and use GitHub's code-block copy control, or use
**Copy agent prompt** in the local board. The recipient must verify the live claim,
current scheduled window, required prerequisite evidence and resource lease before
starting. Copying does not reserve work. A scope is unavailable when already claimed,
outside its authorized window, stale, or missing prerequisite evidence.

No supported Hoplite launch API was found in this session. T3 delegation tools are
available to an active assistant, not directly to a static browser file. The board copies runner-specific handoffs and dispatch requests. The recipient
checks the live claim; copying does not submit a runtime job. Repository issues are
disabled, so issue-based agent launching is unavailable.
Native direct launch is a tracked follow-up requiring a supported adapter and atomic
claim/recheck protocol before external side effects.

## Project synchronization

`Project.py` provisions the recorded org project and imports missing scoped draft
items using a project-only credential passed through a private file. Never commit
credentials. It retains project/item identifiers for resumable population and leaves
already published fields unchanged, preserving manual agent claims and schedules.
Update those fields through GitHub when work changes, then update the owning repo
register in the delivery PR. This is explicit synchronization, not a background
two-way sync service. The repo board remains a dated offline snapshot.

The provisioner is invoked with `--owner-id`, `--token-file` and a separate `--state`
path outside the repository. Add `--populate` to import missing scope items. The
credential file must be supplied through a private secret channel; never paste its
contents into commands, source or logs. The local progress file records published
IDs and can be reconstructed from remote scope markers after uncertain responses.
Project mutations use the supported GraphQL creation and bulk-field REST APIs.

## Coverage and status audit

[Coverage.json](Generated/Coverage.json) counts every saved catalogue row: 585
SOLIDWORKS subfeatures, 2,037 Fusion API types and 1,958 native decoding domains.
[NativeInventory.jsonl](Generated/NativeInventory.jsonl) preserves all 3,563 saved
native schema/version rows, 1,991 members and 3,225 observed commands. Technical
declarations stay unscheduled until a bounded investigation is defined; they remain
visible in the chart inventory and project. This is complete for the saved inputs,
not a claim of every vendor version or legal option combination.

[StatusAudit.json](Generated/StatusAudit.json) separates source-recorded completed
tasks, active tasks, open deliveries and explicitly linked feature contributions.
A feature with bounded open work is In Progress while its qualification remains
unverified. Completed task rows are Done at their recorded scope, not at the whole
feature level. Use the source links to resolve stale or missing evidence.

Use `Project.py --status-only` with the same private credential and progress-file
arguments to initialize blank native project statuses from the recorded task state.
Existing Done and In Progress states are preserved; Todo can be promoted when
source records establish active or completed bounded work. Agents must set In Progress before
starting and Done after acceptance, as required by the agent workflow.

The repository currently reports issues disabled. GitHub issue-based agent launching
is unavailable; the board copies dispatch requests instead of opening an unusable
issue page. Project assignment remains coordination metadata, not a runtime launch.

## SDK scope and historical ownership

[SdkScopes.json](SdkScopes.json) records nine format read obligations, nine write
obligations and all 81 ordered conversion routes, including same-format routes.
The SDK board view exposes their dependencies and remaining acceptance boundaries.
SOLIDWORKS and Fusion feature details separately retain Read, Write and Conversion
preparation tracks. Existing bounded implementations do not close full-format tasks.
Unestimated SDK work remains visible without an invented delivery date.

[TaskIdentities.json](TaskIdentities.json) pins existing research task identities;
new source/task identities are deterministic and survive register reordering. Preserve
these mappings when editing task names or moving records between owning sources.

Use native Assignees on project items and delivery PRs in addition to Agent/Runner.
For historical Codex entries, [AssigneeMappings.json](AssigneeMappings.json) records
the verified feature/task introduction author or exact PR author and evidence.
`Assignments.py --token-file PATH --apply` adds verified accounts without clearing
existing assignments; omitted `--apply` writes an audit only. Unavailable users,
missing imports and ambiguous records remain explicit gaps. A bot PR author cannot
be assigned as a user; retain its contact and record the missing responsible account.
