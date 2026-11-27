# Planning project maintenance

## Behavior

The planning tools support native project status initialization, readback audits,
single-writer import leases, equivalent-duplicate reconciliation and native assignee
updates that preserve existing assignment history. Historical Codex tasks use the
verified feature/task introduction author or exact delivery PR author.
The unassigned-backlog view filters native assignees and Todo status; Agent text
is a runtime/contact field and does not determine native assignment.
Agents must set In Progress before work and Done only after their bounded exit
evidence, as required by [the agent workflow](../../Planning/AgentWorkflow.md).

The inventory now retains all 585 curated SOLIDWORKS subfeatures, 2,037 saved Fusion
API types and 1,958 native decoding domains. The native inventory also preserves
3,563 schema/version records, 1,991 members and 3,225 observed commands.
These are saved-input coverage counts, not universal vendor support claims.
Explicit PR links identify bounded active contributions without promoting whole
feature families to complete.

The SDK inventory adds nine read tasks, nine write tasks and 81 ordered conversion
routes. Stable task identity mappings preserve imported scope IDs when rows move.
Prose claims remain distinct from tabular tasks and feature inventories.

## Usage

`re/automation/Planning/Project.py` accepts `--populate` or `--status-only`, with
an explicit `--owner-id`, a private `--token-file` and a nonsecret `--state` path.
The latter initializes native Done/In Progress states from owning records and
retains newer completed or active project states. Existing field values survive
reconstruction of the local progress file.

`Batch.py --token-file PATH --state /tmp/KitPlanningImport.json` imports missing
records under the same project lease. Writes default to serialized records after
parallel creation and field batches returned service errors. Creation uses GraphQL
and field publication uses REST so their rate budgets remain separate. Repeat `--only SCOPE_ID`
to restrict a recovery run to explicitly selected scopes. `ClearForecasts.py
--token-file PATH --apply` removes only dates matching this task's earlier generated
forecasts; it preserves manual date edits and records exact removals.

`Audit.py --token-file PATH` reads current project coverage and status mismatches
into `Documentation/Planning/ProjectSnapshot.json` without changing remote items.
`Duplicates.py --token-file PATH` prepares an equivalence report; `--apply` merges
only verified generated duplicates and retains manual information. Matching copied
bodies are insufficient unless they also match a known generated source; unknown
prompt versions remain for explicit review.
No token is stored in the repo or browser bundle. No tool launches a model or CAD
application, and project assignment does not launch an agent.

## Verification

Recorded source generation and freshness checks pass for the saved inputs. Process
coverage checks catalogue denominators, drift, cycles and competing import leases
through the existing shared test suite. Remote project readback exposed duplicates
and missing native states; the repair retains explicit reports instead of claiming
complete synchronization before readback. Current-head CI, configured review and
merge-group acceptance remain separate gates.

See the [single-writer gotcha](../../Gotchas/Research/Planning/ProjectImportsNeedOneWriter.md).

## Observed synchronization blocker

Project creation and readback work, but both GraphQL field mutations and REST
field updates repeatedly returned HTTP 502 during this import. A smaller retry
also failed; forecast removal encountered a connection timeout, and a later REST
draft batch returned malformed responses. A bounded recovery imported the newest
claimed delivery before the full import failed again.
[ProjectSnapshot.json](../../Planning/ProjectSnapshot.json) records actual coverage
and status gaps, and [ForecastRemoval.json](../../Planning/ForecastRemoval.json)
retains verified removals and failures. Missing records and uncleared old dates
remain unfinished remote synchronization work; the local feature board is undated.

The undated board shows recorded state and scope type in place of empty calendar
tracks. A representative source-record preview passed desktop and 390-pixel
rendering without console errors; the full local-file browser flow was not verified
because browser automation disallows local file URLs.
