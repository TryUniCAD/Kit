# Scheduled scope planning

## Behavior

Kit now has a repository planning index, forecast schedule, React scope board and
organization GitHub Project. The views join B01–B14, research register rows, all
curated SOLIDWORKS subfeatures, Fusion API feature declarations and a dated open-PR
inventory. Product and UI/UX proposals are explicit backlog entries.

The [planning procedure](../../Planning/README.md) defines ownership and maintenance.
Root and research agent instructions and the canonical repository skill require
agents to update scope, owner, dependencies, schedules, blockers and revision evidence.

The board provides calendar bars, current-work and inventory views, search, area,
owner and type filters, pagination, task details, editable draft windows and schedule
export. Every scope has a copyable agent prompt. GitHub project items retain a fenced
prompt that GitHub can copy directly. Assignment does not start an agent runtime.
Local and Hoplite launch controls disclose their unavailable integrations.

## Usage

Run `uv run --locked python re/automation/Planning/Build.py` to regenerate recorded
views, then add `--check` to detect drift. Open
`Documentation/Planning/Generated/Board.html` for the local board. Rebuild the React
assets from `re/automation/Planning/Board` using the pinned package lock and
`npm ci --ignore-scripts` followed by `npm run build`.

The project provisioner uses an explicitly supplied credential file with `project`
scope. It never writes credentials to repository files. Its nonsecret project/item
mapping is `Documentation/Planning/Project.json`. Published remote items are left
unchanged on subsequent population runs so manual ownership and date edits survive.

## Limits

Five-working-day forecasts are investigation timeboxes under proposed planning
capacity. They are not feature delivery estimates, actual staffing or native-host
reservations. API declarations and typed ownership do not qualify semantics.
Unmapped scopes require a live claim search. Detailed catalogues for every other
format and a committed product UI specification remain missing obligations.
Historical register states are retained as observations and must be refreshed before
task selection. No CAD capability or conversion acceptance is established here.

## Verification

The generator completed against the recorded main and catalogue sources and emitted
deterministic inventories and schedule data. The React production bundle built from
pinned dependencies. Process regressions exercise real generation, stale-output
rejection and dependency-cycle rejection through the existing test-suite path.
Remote PR CI, configured review and merge-group acceptance remain separate delivery
gates; no local unit-test execution or native CAD verification is claimed.
