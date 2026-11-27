# Repository and decoding planning

Open the [organization project](https://github.com/orgs/TryUniCAD/projects/1) for shared dates and agent claims, or [the local scheduling board](Generated/Board.html) for filters, draft schedule edits and copyable prompts.

Use this page before selecting or handing off repository work. It joins the existing
planning sources without transferring their ownership or changing acceptance criteria.

## Read the current views

- [Dependency Gantt and graph](Generated/Gantt.md): repository milestones and research prerequisites
- [Visual Gantt](Generated/Gantt.svg): directly viewable without a server or JavaScript
- [Standalone visual](Generated/Gantt.html): the same chart in a local HTML file
- [Task index](Generated/Tasks.md): parent tasks, detailed research rows, owners, dependencies and exit conditions
- [Feature scopes](Generated/Features.md): every curated SOLIDWORKS subfeature and Fusion API feature declaration in the saved catalogues
- [Open deliveries](Generated/Deliveries.md): dated PR collision and stack inventory
- [Calendar windows](Generated/Calendar.md): explicitly supplied engineering windows only
- [Source manifest](Generated/Manifest.json): exact source hashes and inventory counts

The scheduling board uses calendar dates. Its initial five-working-day windows are
proposed investigation timeboxes, not feature completion promises. Planning capacity
is an explicit assumption in `SchedulePolicy`; it does not appoint people or reserve
a CAD host. The dependency diagram separately shows prerequisite tiers. Recorded
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
Repeated historical IDs retain their section context. Prose-only claims remain in the
linked owning registers and must also be read before starting. `Generated/Scopes.jsonl`
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

The scheduler supplies tentative investigation windows for known backlog scopes.
Override a window only with an explicit estimate basis; do not turn forecasts into
accepted commitments. Shared changes belong in the GitHub Project; repo schedule
edits are exported as a draft `Links.json` and require review and regeneration.
`Schedules` entries contain `TaskId`, ISO `Start`, ISO `Finish` and a nonempty `Basis`.
They are estimates, not acceptance dates. Label research windows as investigations and retain unknown completion dates. Inspect the dependency chart and task
exit conditions when estimating dependent work.

## Decoding campaign handoff

`FusionRevolveContrast` is a proposed separate campaign, not an active claim:
unequal two-sided solid revolutions about an explicit construction axis. The recipient
must refresh ownership and inspect existing revolve controls before selecting genuinely
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
available to an active assistant, not directly to a static browser file. Launch
buttons therefore disclose that runtime dispatch is unconfigured rather than
pretending to submit jobs. Assigning a GitHub-supported coding agent to a converted
issue may launch that configured integration; project text fields alone do not.
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
