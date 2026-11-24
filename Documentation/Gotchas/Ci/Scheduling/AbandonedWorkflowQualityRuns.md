# Abandoned workflow quality runs retain shared lanes

Removing a merge candidate does not necessarily stop every workflow associated with its SHA.
The trusted cleanup originally listed only `MergeQueue.yml` runs and accepted only that workflow path.
Its other identity checks therefore never reached old `WorkflowQuality.yml` jobs.
Those jobs share Linux and Windows lane names with current candidates.

[Run 45384862770](https://github.com/TryUniCAD/Kit/actions/runs/45384862770) retained work for more than two hours after creation.
Its synthetic branch was deleted and its SHA was absent from the active queue.
Six additional obsolete workflow-quality runs remained pending.

Enumerate merge-group workflows and allow only the two known heavy workflow families through the existing cancellation checks.
Require a missing ref and independent current queue evidence before cancelling.
Preserve active candidates, manual audits, forks, unknown workflows, and uncertain evidence.
See [the cleanup change](../../../Changes/Ci/Scheduling/AbandonedWorkflowLanes.md).
