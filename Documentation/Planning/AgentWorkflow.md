# Agent planning workflow

Use this procedure at task start, at each state change and before handoff.
The project coordinates work; owning registers and revision-bound evidence decide
acceptance. Forecast windows do not qualify a feature or reserve a CAD host.

## Select and claim

1. Open [the organization project](https://github.com/orgs/TryUniCAD/projects/1).
   Read **Current work** first to identify existing owners and delivery PRs.
2. Use **Scheduled roadmap** for dates and the relevant area. Read the estimate
   basis. Use [the dependency graph](Generated/Gantt.md), [task gates](Generated/Tasks.md)
   and [feature scopes](Generated/Features.md) to find the owning source.
3. Refresh live PRs, exact heads and existing claims. Unassigned, unmapped and
   unverified are different states. None alone establishes task availability.
4. Choose a bounded scope within its authorized window. If the scope or estimate
   changes, update the plan explicitly. Do not start taken or blocked work.
5. Claim the child in its owning register before implementation or capture. Record
   task/scope ID, owner/session, exact scope, dependencies, branch, delivery PR,
   external resource and observable exit condition.
6. Set **Runner** and **Agent** in the project. Re-read the live claim. If another
   owner claimed it concurrently, coordinate before proceeding. Project edits are
   not atomic execution leases; native capture still uses the controller lease.
   Set the project's native **Status** to **In Progress before starting work**.
7. Add explicit catalogue/task links in `Links.json`. A related PR title does not
   assign an entire feature family to its author.

## Prepare an agent handoff

Use **Copy agent prompt**, **Copy local handoff** or **Copy Hoplite handoff** in
[the local board](Generated/Board.html), or copy the fenced prompt in a project item.
The recipient must repeat the live ownership, schedule, prerequisite and resource
checks. Copying a prompt does not claim or launch work.

**Copy dispatch request** prepares a prompt for a configured runtime. Repository
issues are disabled, so issue-based launching is unavailable. Direct local and
Hoplite runtime launch integrations are also unavailable; do not report a launch
from a project text-field assignment.

## Keep work current

| Event                    | Required update in project and owning register                             |
| ------------------------ | -------------------------------------------------------------------------- |
| Work starts              | Owner/session, bounded scope, branch, window and prerequisites             |
| Evidence arrives         | Tested revision, evidence links and the affected qualification stage       |
| Work blocks              | Named blocker, required external change and affected child tasks           |
| Scope or dates change    | Reason, revised estimate basis, dependencies and unfinished requirements   |
| PR opens or changes      | Delivery URL, actual head/base and remaining acceptance limits             |
| Work pauses or transfers | Remaining work, next action, evidence custody and owner disposition        |
| Scope finishes           | Exit evidence and accepted revision; broader parent requirements stay open |

Keep **capture**, **decode**, **semantics**, **write** and **native** separate.
A decode receipt, open PR, green PR checks or generated file does not establish
conversion acceptance. One supported variant does not complete a catalogue family.
Never clear another owner's claim merely to make a scope dispatchable.

Set native **Status** to **Done only after the claimed scope's exit evidence is
recorded**. Keep `Recorded status` and the owning register aligned. If the scope is
blocked, record the blocker explicitly and retain the owner disposition. A completed
bounded child does not make its parent feature or every vendor version Done.
The importer maps source-recorded complete tasks to Done and active/checking/open
work to In Progress when the project status is empty. It preserves existing Done and In Progress states; Todo may be promoted from
explicit source records. Audit stale disagreements rather than overwriting an agent's
newer progress from an old repo snapshot.

## Regenerate and publish

1. Edit the owning register or existing catalogue first. Represent every new project,
   decoding, product, UI/UX, documentation, infrastructure or release scope there or
   as an explicitly proposed additional task in `Links.json`.
2. Update explicit `ScopeLinks`, parent `Dependencies`, supplied `Schedules` and
   delivery details. Record exact evidence revisions for completed stages.
3. Refresh the dated PR collision inventory when selecting or changing delivery.
   Never stamp a new date onto an old snapshot.
4. Export local schedule edits as a draft `Links.json`, review against the current
   repo version and apply only intended changes. Update shared project dates
   explicitly; the offline board is not an automatic two-way sync service.
5. Rebuild pinned React assets if their source changed, then run:

   ```sh
   uv run --locked python re/automation/Planning/Build.py
   uv run --locked python re/automation/Planning/Build.py --check
   ```

6. Inspect task and Gantt diffs. Commit source and generated views together.
   Never edit generated views directly. Follow [the planning guide](README.md) for
   asset builds and project synchronization.

If project access is unavailable, update repo records and identify the pending sync.
Do not report a remote update as successful without readback.

## Handoff checklist

Supply task/scope ID, owner/session, exact scope, branch and PR/head, current window,
dependencies, evidence by stage, unresolved requirements, blocker and next action.
The receiving agent refreshes main, project claims and live PRs before proceeding.

The repository currently reports issues disabled. GitHub issue-based agent launching
is unavailable; the board copies dispatch requests instead of opening an unusable
issue page. Project assignment remains coordination metadata, not a runtime launch.

## Native assignees

Assign native GitHub **Assignees** only after a bounded scope is explicitly claimed
or delegated. Set verified responsible accounts together with native In Progress;
leave unclaimed future work unassigned. Historical completed work retains its author
with Done. Set assignees on both the project draft/issue and the delivery PR.
Keep the exact runtime/session in Agent and the provider in Runner; these fields
serve different purposes. Do not infer whole-feature ownership from a related PR.
For historical tasks recorded only as Codex, use the verified GitHub author of the
feature/task introduction or exact delivery PR. Record the source commit or PR
with the mapping. If no author can be verified, record the gap instead of guessing.

Retain the responsible assignees when setting Done so completed work has ownership
history. At an explicit handoff, update the current responsible accounts and record
the previous owner, evidence custody and next action. Preserve unrelated assignees
unless the handoff specifically replaces their responsibility. Duplicate repair must
also preserve native assignees and flag conflicting assignment sets for coordination.
